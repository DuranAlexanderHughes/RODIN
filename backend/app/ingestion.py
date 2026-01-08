from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

import xml.etree.ElementTree as ET

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --- Paths ---

BASE_DIR = Path(__file__).resolve().parents[2]  # points at RODIN/
DUMP_PATH = BASE_DIR / "backend" / "data" / "raw" / "bioshock_pages_current.xml"

# Adjust if your folder is actually "Data" (case-insensitive on Windows anyway)


# --- Types ---

SourceKind = Literal["article", "forum"]


@dataclass
class RawPage:
    title: str
    ns: int
    text: str
    kind: SourceKind


# block all non-article pages
BLOCKED_PREFIXES = (
    "User:",
    "User talk:",
    "Talk:",
    "Forum:",
    "Message Wall:",
    "Blog:",
)


def classify_page(ns: int, title: str) -> SourceKind:
    """
    Return 'article' for main canon pages,
    'forum' for talk/user/forum/etc.
    """
    if ns != 0:
        return "forum"
    if title.startswith(BLOCKED_PREFIXES):
        return "forum"
    return "article"


# --- XML parsing into RawPage objects ---


def iter_raw_pages() -> Iterable[RawPage]:
    """Stream RawPage objects from the MediaWiki XML dump."""
    if not DUMP_PATH.exists():
        raise FileNotFoundError(f"Dump not found at: {DUMP_PATH}")

    tree = ET.parse(DUMP_PATH)
    root = tree.getroot()

    for page in root.findall(".//{*}page"):
        title_el = page.find("./{*}title")
        ns_el = page.find("./{*}ns")
        text_el = page.find(".//{*}text")

        title = title_el.text if title_el is not None else "<NO TITLE>"
        ns = int(ns_el.text) if ns_el is not None and ns_el.text.isdigit() else -1
        text = text_el.text if text_el is not None else ""

        kind = classify_page(ns, title)

        yield RawPage(
            title=title,
            ns=ns,
            text=text,
            kind=kind,
        )


# --- Chunking into LangChain Documents ---


def build_text_splitter() -> RecursiveCharacterTextSplitter:
    """Create a text splitter tuned for wiki-like lore pages."""
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " "],
    )


def iter_article_documents() -> Iterable[Document]:
    """
    Yield LangChain Documents for article pages (canon-ish),
    chunked and with metadata.
    """
    splitter = build_text_splitter()

    for page in iter_raw_pages():
        # Only keep article pages for this iterator
        if page.kind != "article":
            continue

        # Skip pure redirects like '#REDIRECT [[BioShock]]'
        if page.text.strip().upper().startswith("#REDIRECT"):
            continue

        # Split into chunks
        chunks = splitter.split_text(page.text)

        for idx, chunk in enumerate(chunks):
            yield Document(
                page_content=chunk,
                metadata={
                    "page_title": page.title,
                    "ns": page.ns,
                    "source_kind": page.kind,  # "article"
                    "chunk_index": idx,
                },
            )


def load_article_documents(limit: int | None = None) -> list[Document]:
    """
    Convenience function: load article documents into a list.
    If limit is set, only take that many Documents (for quick tests).
    """
    docs: list[Document] = []
    for i, doc in enumerate(iter_article_documents()):
        docs.append(doc)
        if limit is not None and i + 1 >= limit:
            break
    return docs


# --- Self-test ---

if __name__ == "__main__":
    print(f"Using dump: {DUMP_PATH}")
    docs = load_article_documents(limit=10)
    print(f"Loaded {len(docs)} article-chunks (limit=10).")

    for d in docs[:3]:
        print("--------------------------------------------------")
        print(f"Title: {d.metadata['page_title']}")
        print(f"Chunk index: {d.metadata['chunk_index']}")
        print(f"Source kind: {d.metadata['source_kind']}")
        print(f"Content preview: {d.page_content[:200]!r}")
