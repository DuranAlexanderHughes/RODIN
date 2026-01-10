from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool, ToolRuntime
from dataclasses import dataclass
from langchain_openai import ChatOpenAI

from typing import Annotated, Optional, List

load_dotenv()

SYSTEM_PROMPT = """You are an expert in the lore of the BioShock videogame series.

You have access to one tool:

- get_bioshock_lore: use this to query a vectorstore loaded with articles from the BioShock fandom wiki.

If a user asks you a question related to BioShock, make sure to consult with the BioShock fandom wiki and always attempt to give a canonical answer and site your source."""

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

@tool
def get_bioshock_lore(query: str) -> str:
    """Query the RAG to get additional context from the scraped and vectorized bioshock wiki for generating answer"""

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
