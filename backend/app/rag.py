# backend/app/rag.py
from __future__ import annotations

from pathlib import Path
from typing import List, Literal

from langchain_openai import OpenAIEmbeddings
#from langchain_community.vectorstores import # depicated and to be removed in 1.0
from langchain_chroma import Chroma
from langchain_core.documents import Document


from .config import OPENAI_API_KEY, VECTORSTORE_ROOT
from .ingestion import iter_article_documents

VectorBackend = Literal["chroma"]  # later: add "faiss", "pinecone", etc.


def get_embeddings() -> OpenAIEmbeddings:
    """Return an OpenAI embeddings instance."""
    return OpenAIEmbeddings(api_key=OPENAI_API_KEY)


def get_vectorstore_dir(backend: VectorBackend) -> Path:
    """
    Return the directory where this backend's persisted data should live.

    Example:
      backend='chroma' -> backend/vectorstore/chroma/
    """
    vs_dir = VECTORSTORE_ROOT / backend
    vs_dir.mkdir(parents=True, exist_ok=True)
    return vs_dir


def build_or_load_chroma() -> Chroma:
    """
    Build a Chroma vectorstore from article Documents if one doesn't exist
    in backend/vectorstore/chroma, otherwise load the existing one.
    """
    vs_dir = get_vectorstore_dir("chroma")
    embeddings = get_embeddings()

    # If directory is non-empty, assume we already have a persisted index
    if any(vs_dir.iterdir()):
        return Chroma(
            embedding_function=embeddings,
            persist_directory=str(vs_dir),
        )

    # Otherwise, build from documents
    print(f"No existing Chroma index found in {vs_dir}. Building a new one...")
    docs_iter = iter_article_documents()

    # TODO (v2): switch to a streaming build instead of materializing the whole list.
    docs_list: List[Document] = list(docs_iter)
    print(f"Embedding {len(docs_list)} chunks into Chroma...")

    vs = Chroma.from_documents(
        documents=docs_list,
        embedding=embeddings,
        persist_directory=str(vs_dir),
    )
    print("Chroma vectorstore built and persisted.")
    return vs


# Simple router if/when you add other backends
_vectorstore_cache: dict[VectorBackend, object] = {}


def get_vectorstore(backend: VectorBackend = "chroma"):
    """Lazy-load or build the vectorstore for the given backend."""
    if backend in _vectorstore_cache:
        return _vectorstore_cache[backend]

    if backend == "chroma":
        vs = build_or_load_chroma()
    # elif backend == "faiss"
    #     vs = build_or_load_faiss()
    # elif backend == "pinecone"
    #     vs = build_or_load_pinecone()
    else:
        raise ValueError(f"Unsupported vector backend: {backend!r}")

    _vectorstore_cache[backend] = vs
    return vs


def retrieve_lore(query: str, k: int = 4, backend: VectorBackend = "chroma") -> List[Document]:
    """
    Retrieve top-k lore chunks for a given query from the specified backend.
    Currently supports 'chroma'; TODO: add 'faiss', 'pinecone', etc.
    """
    vs = get_vectorstore(backend=backend)
    retriever = vs.as_retriever(search_kwargs={"k": k})
    return retriever.invoke(query)


if __name__ == "__main__":
    vs_dir = get_vectorstore_dir("chroma")
    print(f"Chroma vectorstore directory: {vs_dir}")

    docs = retrieve_lore("What is Rapture?", k=3, backend="chroma")

    print("\nTop 3 retrieved chunks for query: 'What is Rapture?'")
    for i, d in enumerate(docs, start=1):
        title = d.metadata.get("page_title", "<no title>")
        idx = d.metadata.get("chunk_index", "?")
        preview = (d.page_content[:200] + "...") if len(d.page_content) > 200 else d.page_content

        print("--------------------------------------------------")
        print(f"Result #{i}")
        print(f"Title: {title} (chunk {idx})")
        print(f"Preview: {preview!r}")
