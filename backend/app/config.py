# backend/app/config.py
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in .env")

DATA_DIR = BASE_DIR / "backend" / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Root folder for *all* vectorstores (chroma, faiss, pinecone, etc.)
VECTORSTORE_ROOT = BASE_DIR / "backend" / "vectorstore"
