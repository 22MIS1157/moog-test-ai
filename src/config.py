"""
MoogTestAI — Configuration Module

Loads environment variables and initializes LLM and embedding model instances
used across all agents and the RAG pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# LLM Provider Selection
# ---------------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "openai"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# ChromaDB (Vector Store) Configuration
# ---------------------------------------------------------------------------
CHROMA_PERSIST_DIR = str(PROJECT_ROOT / "chroma_db")
CHROMA_COLLECTION_NAME = "moog_design_docs"

# ---------------------------------------------------------------------------
# RAG Configuration
# ---------------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_TOP_K = 5

# ---------------------------------------------------------------------------
# Reservation / Expiry Settings for test sessions (minutes)
# ---------------------------------------------------------------------------
DEFAULT_RESERVATION_WINDOW_MINUTES = 10

# ---------------------------------------------------------------------------
# Data Directories
# ---------------------------------------------------------------------------
PILOT_DESIGN_DIR = str(PROJECT_ROOT / "data" / "pilot_design")
TEST_RESULTS_DIR = str(PROJECT_ROOT / "data" / "test_results")


def get_llm():
    """Return a LangChain-compatible LLM instance based on the configured provider."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            api_key=OPENAI_API_KEY,
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,
            google_api_key=GOOGLE_API_KEY,
        )


def get_embeddings():
    """Return a LangChain-compatible embedding model for vector store operations."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    else:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY,
        )
