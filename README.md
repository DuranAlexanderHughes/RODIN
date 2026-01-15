# RODIN — Retrieval-Oriented Domain Intelligence Node

RODIN is a domain-specific Retrieval-Augmented Generation (RAG) system and
agent-based assistant built around the BioShock universe. It ingests a
MediaWiki dump, builds a vectorized knowledge base, exposes a structured
OpenAI-powered agent via an API, and integrates with Discord as an interactive
lore assistant.

The system is designed with extensibility in mind and is intentionally
structured to support future domains (e.g., tabletop RPG campaigns) and
multiple vector backends.

---

## High-Level Architecture

```
MediaWiki Dump (BioShock Wiki)
↓
Ingestion + Filtering (articles vs forum/meta)
↓
Chunking + Metadata
↓
Vector Store (Chroma, persisted locally)
↓
Retriever (semantic similarity)
↓
OpenAI Agent (structured output + verifier pass)
↓
FastAPI Backend (/ask, /health)
↓
Discord Bot (!lore command)
```

---

## Key Features

• Domain-specific RAG pipeline (BioShock lore)
• MediaWiki XML dump ingestion (no live scraping)
• Canon-oriented filtering (articles vs forum/meta)
• Chunked documents with metadata
• Persistent vector store (Chroma)
• Rich structured agent responses:

- summary
- key entities
- timeline events
- cited sources
- confidence level
  • Verifier pass to correct typos and wording errors
  • FastAPI backend for clean service separation
  • Discord bot integration with embeds
  • Debug mode and backend health checks
  • Designed for future multi-domain expansion

---

## Project Structure

```
RODIN/
├── backend/
│ ├── **init**.py
│ ├── app/
│ │ ├── **init**.py
│ │ ├── config.py # Environment & path config
│ │ ├── ingestion.py # XML dump parsing + chunking
│ │ ├── rag.py # Vector store build/load + retrieval
│ │ ├── agent.py # OpenAI agent + schema
│ │ ├── verifier.py # Post-generation summary verifier
│ │ └── api.py # FastAPI endpoints
│ ├── data/
│ │ ├── raw/ # MediaWiki XML dump
│ │ └── processed/ # (reserved for future use)
│ └── vectorstore/
│ └── chroma/ # Persisted Chroma index
│
├── bot/
│ └── bot.py # Discord bot client
│
├── .env # Secrets & runtime config
├── .env.example # Example env file
├── .rodin-venv/ # Python virtual environment
├── requirements.txt
└── README.txt
```

---

## Environment Variables

Required variables in .env:

OPENAI_API_KEY=sk-...
DISCORD_BOT_TOKEN=...
BACKEND_URL=http://127.0.0.1:8000

---

## Setup & Running

1. Create and activate virtual environment

   python -m venv .rodin-venv
   source .rodin-venv/bin/activate (Linux/macOS)
   .rodin-venv\Scripts\activate (Windows)

2. Install dependencies

   pip install -r requirements.txt

3. Place MediaWiki dump

   backend/data/raw/bioshock_pages_current.xml

4. Build vector store (first run only)

   python -m backend.app.rag

5. Run backend API

   uvicorn backend.app.api:app --reload

6. Run Discord bot (separate terminal)

   python -m bot.bot
   python -m bot.bot --debug # debug mode

---

## FastAPI Endpoints

GET /health
Returns service health status.

POST /ask
Accepts a lore question and returns: - summary - structured response - sources - confidence

---

## Discord Bot

Command:
!lore <question>

Example:
!lore What is Rapture?

The bot responds with:

- a summarized answer
- confidence indicator
- cited source pages

---

## Design Philosophy

• Explicit boundaries between ingestion, retrieval, reasoning, and interface
• Structured outputs over free text
• Grounding through retrieval, not memorization
• Fail-fast configuration (no silent defaults)
• Designed for observability and future evaluation
• Minimal magic, maximum clarity

---

## Planned Enhancements

• Slash command support (/lore)
• Retriever score thresholding
• Canon vs speculation modes
• Additional vector backends (FAISS, Pinecone)
• Streaming vectorstore build
• Evaluation harness (grounding, faithfulness)
• Multi-domain routing (BioShock, DnD, etc.)

---

## License / Usage

This project is intended for educational, experimental, and personal use.
BioShock and related content remain the property of their respective owners.

---
