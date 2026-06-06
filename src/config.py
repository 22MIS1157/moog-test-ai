"""
MoogTestAI — Configuration Module

Loads environment variables and initializes LLM and embedding model instances
used across all agents and the RAG pipeline.
"""

import os
import time
import random
import logging
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger("moog_test_ai")

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

# ---------------------------------------------------------------------------
# Retry Configuration
# ---------------------------------------------------------------------------
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "5"))
INITIAL_BACKOFF_SEC = float(os.getenv("LLM_INITIAL_BACKOFF", "5"))
MAX_BACKOFF_SEC = float(os.getenv("LLM_MAX_BACKOFF", "60"))


def _is_retryable_error(error: Exception) -> bool:
    """Check if an exception is a retryable rate-limit or transient error."""
    err_str = str(error).lower()
    retryable_patterns = [
        "429",
        "resource_exhausted",
        "rate limit",
        "quota exceeded",
        "too many requests",
        "503",
        "service unavailable",
        "temporarily unavailable",
    ]
    return any(pattern in err_str for pattern in retryable_patterns)


def _with_retry(func):
    """Decorator that adds exponential backoff retry for transient LLM errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        backoff = INITIAL_BACKOFF_SEC

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not _is_retryable_error(e):
                    raise

                last_exception = e
                if attempt == MAX_RETRIES:
                    break

                # Exponential backoff with jitter
                jitter = random.uniform(0, backoff * 0.3)
                wait_time = min(backoff + jitter, MAX_BACKOFF_SEC)
                logger.info(
                    f"Transient LLM error (attempt {attempt}/{MAX_RETRIES}). "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
                backoff = min(backoff * 2, MAX_BACKOFF_SEC)

        # All retries exhausted — raise a clean error
        raise RuntimeError(
            "The AI model is temporarily unavailable due to high demand. "
            "Please try again in a few minutes."
        ) from last_exception

    return wrapper


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
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.2,
            google_api_key=GOOGLE_API_KEY,
        )

        # Wrap the invoke method with retry logic
        original_invoke = llm.invoke
        object.__setattr__(llm, "invoke", _with_retry(original_invoke))

        return llm


def get_embeddings():
    """Return a LangChain-compatible embedding model for vector store operations."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    else:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=GOOGLE_API_KEY,
        )
