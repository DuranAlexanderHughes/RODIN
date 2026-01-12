from dotenv import load_dotenv
from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool, ToolRuntime
from langchain.agents.structured_output import ToolStrategy
from dataclasses import dataclass
from langchain_openai import ChatOpenAI

from typing import Annotated, Optional, List
from .config import OPENAI_API_KEY
from .rag import retrieve_lore

SYSTEM_PROMPT = """You are RODIN, a lore assistant for the BioShock universe.

You have access to a tool called get_bioshock_lore(query) that returns canon-ish wiki excerpts.

Rules:
- For lore questions, call get_bioshock_lore and ground your answer in retrieved excerpts.
- Do NOT invent major facts. If the excerpts do not support a claim, either omit it or mark confidence low.
- Populate the structured response fields:
  - summary: your final answer
  - key_entities: proper nouns (people/places/things)
  - timeline_events: only if relevant (include dates/years when present)
  - sources: include SourceRef entries only for excerpts you actually used
  - confidence: high only if excerpts clearly support the summary
  - notes: explain ambiguity or gaps when confidence is medium/low
"""

model = init_chat_model(
    "gpt-4.1-mini",           # model name
    model_provider="openai",  # important: use OpenAI provider
    temperature=0.5,
    timeout=10,
    max_tokens=1000,
)

checkpointer = InMemorySaver()

basic_model = ChatOpenAI(model="gpt-4o-mini")
advanced_model = ChatOpenAI(model="gpt-4o")

@dataclass
class bioshock_lore_response:
    """Response schema for retrieved BioShock lore"""
    summary: Annotated[
        str,
        "Direct answer to the user's question. Keep it concise but complete."
    ]
    key_entities: Annotated[
        List[str],
        "Key people/places/things mentioned. Use proper nouns when possible."
    ] = field(default_factory=list)

    timeline_events: Annotated[
        List[str],
        "Timeline-relevant events mentioned, if any. Each entry should be a short phrase with a date/year if present."
    ] = field(default_factory=list)

    sources: Annotated[
        List[SourceRef],
        "Source chunks used to produce the answer. Include only those actually relied upon."
    ] = field(default_factory=list)

    confidence: Annotated[
        Literal["low", "medium", "high"],
        "How confident the answer is based on retrieved evidence (not general world knowledge)."
    ] = "medium"

    notes: Annotated[
        Optional[str],
        "Optional notes about ambiguity, missing info, or why confidence is not high."
    ] = None

@dataclass
class SourceRef:
    title: Annotated[str, "Wiki page title the chunk came from."]
    chunk_index: Annotated[int, "Chunk index within that page (0-based)."]
    snippet: Annotated[str, "Short excerpt from the retrieved chunk (for UI/debugging)."]

@tool
def get_bioshock_lore(query: str) -> str:
    """
    Retrieve relevant BioShock wiki chunks for a query.

    Returns a compact textual payload that includes titles/chunk indices + excerpts.
    The agent must cite which chunks it used in the structured response.
    """
    docs = retrieve_lore(query, k=6, backend="chroma")

    lines: list[str] = []
    for d in docs:
        title = d.metadata.get("page_title", "<no title>")
        chunk_index = int(d.metadata.get("chunk_index", -1))
        text = d.page_content.strip().replace("\n", " ")

        # Keep excerpts short to reduce prompt bloat
        excerpt = text[:600] + ("..." if len(text) > 600 else "")

        lines.append(f"[TITLE={title} | CHUNK={chunk_index}] {excerpt}")

    return "\n\n".join(lines)

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Choose model based on conversation complexity."""
    # TODO: add way to keep seperate count per user and reset count after X amount of time has passed
    message_count = len(request.state["messages"])

    if message_count > 10:
        # Use an advanced model for longer conversations
        model = advanced_model
    else:
        # Otherwise stick to basic, cheaper model
        model = basic_model

    request.model = model
    return handler(request)

def build_agent():
    model = init_chat_model(
        "gpt-4.1-mini",
        model_provider="openai",
        api_key=OPENAI_API_KEY,
        temperature=0.3,
    )

    checkpointer = InMemorySaver()

    agent = create_agent(
        model=model,
        tools=[get_bioshock_lore],
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(bioshock_lore_response),
        checkpointer=checkpointer,
        middleware=[dynamic_model_selection]
    )
    return agent

if __name__ == "__main__":
    agent = build_agent()

    question = "What is Rapture?"
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": "local-test"}},
    )

    structured: LoreAnswer = result["structured_response"]

    print("\n--- STRUCTURED RESPONSE ---")
    print("Summary:", structured.summary)
    print("Confidence:", structured.confidence)
    print("Key entities:", structured.key_entities[:10])
    print("Timeline events:", structured.timeline_events[:10])
    print("Notes:", structured.notes)

    print("\nSources used:")
    for s in structured.sources:
        print(f"- {s.title} (chunk {s.chunk_index}): {s.snippet[:120]!r}")
