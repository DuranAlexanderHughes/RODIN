from __future__ import annotations

from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from .config import OPENAI_API_KEY


_VERIFIER_SYSTEM = """You are a careful copy editor for a lore Q&A system.

Task:
- Make MINIMAL edits to the SUMMARY.
- Fix typos, malformed phrases, and obvious word-choice errors.
- Do NOT substantially shorten or restructure the text.
- Do NOT add new facts.
- Only remove/soften claims if they are clearly unsupported by the evidence AND material to the answer.
- Prefer plain, direct wording.

Output:
- Return ONLY the corrected summary text (no bullet points, no headings, no JSON).
"""


def verify_and_polish_summary(
    summary: str,
    evidence: str,
    model_name: str = "gpt-4.1-mini",
) -> str:
    """
    Post-process a summary using an LLM verifier pass grounded on evidence excerpts.
    Returns a corrected summary string.
    """
    # Keep this deterministic (temp=0) and conservative
    verifier = init_chat_model(
        model_name,
        model_provider="openai",
        api_key=OPENAI_API_KEY,
        temperature=0.0,
    )

    msg = HumanMessage(
        content=(
            "SUMMARY:\n"
            f"{summary}\n\n"
            "EVIDENCE (retrieved excerpts):\n"
            f"{evidence}\n\n"
            "Return the corrected SUMMARY only."
        )
    )

    out = verifier.invoke([SystemMessage(content=_VERIFIER_SYSTEM), msg])

    # LangChain returns an AIMessage; the text is in .content
    corrected = (out.content or "").strip()

    # Safety fallback: if the verifier returns empty, keep original
    return corrected if corrected else summary
