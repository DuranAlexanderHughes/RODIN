from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal, Optional

from .agent import build_agent  # do NOT import tools here
from .agent import bioshock_lore_response as BioShockLoreResponse  # your dataclass

app = FastAPI(title="RODIN BioShock Lore Agent")

agent = build_agent()


class AskRequest(BaseModel):
    user_id: str = Field(..., description="Stable user identifier (Discord user id, etc.)")
    message: str = Field(..., description="User's question")
    thread_id: str | None = Field(None, description="Optional conversation/thread id")


class SourceRefModel(BaseModel):
    title: str
    chunk_index: int
    snippet: str


class BioShockLoreResponseModel(BaseModel):
    summary: str
    key_entities: list[str] = Field(default_factory=list)
    timeline_events: list[str] = Field(default_factory=list)
    sources: list[SourceRefModel] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    notes: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    structured: BioShockLoreResponseModel


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    thread_id = req.thread_id or req.user_id

    result = agent.invoke(
        {"messages": [{"role": "user", "content": req.message}]},
        config={"configurable": {"thread_id": thread_id}},
    )

    structured: BioShockLoreResponse = result["structured_response"]

    structured_model = BioShockLoreResponseModel(
        summary=structured.summary,
        key_entities=list(structured.key_entities or []),
        timeline_events=list(structured.timeline_events or []),
        sources=[
            SourceRefModel(title=s.title, chunk_index=s.chunk_index, snippet=s.snippet)
            for s in (structured.sources or [])
        ],
        confidence=structured.confidence,
        notes=structured.notes,
    )

    return AskResponse(
        answer=structured_model.summary,
        structured=structured_model,
    )
