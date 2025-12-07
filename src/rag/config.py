"""
RAG Configuration Module

Simple configuration for the RAG pipeline.
"""

import os
from pathlib import Path


class RAGConfig:
    """Configuration settings for RAG pipeline."""

    # Paths - resolve to absolute path at class definition time
    # From src/rag/config.py -> go up 3 levels to reach project root
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"
    CHROMA_DIR = PROJECT_ROOT / "data" / "chromadb"

    # ChromaDB settings
    COLLECTION_NAME = "aqi_knowledge"

    # Chunking settings
    CHUNK_SIZE = 500  # characters per chunk
    CHUNK_OVERLAP = 50  # overlap between chunks

    # Embedding model (using sentence-transformers)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # LLM settings (using Groq)
    LLM_MODEL = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE = 0.3
    MAX_TOKENS = 500

    # Retrieval settings
    TOP_K = 3  # number of chunks to retrieve
    # ChromaDB batch settings (ensure batch size <= chromadb max)
    MAX_BATCH_SIZE = 5000

    # ==========================================================================
    # Guardrails Settings
    # ==========================================================================

    # Input Guards
    ENABLE_INPUT_GUARDRAILS = True
    ENABLE_PII_DETECTION = True
    ENABLE_PROMPT_INJECTION_FILTER = True
    ENABLE_TOPIC_FILTER = True
    SANITIZE_PII = True  # If True, redact PII instead of blocking

    # Output Guards
    ENABLE_OUTPUT_GUARDRAILS = True
    ENABLE_TOXICITY_FILTER = True
    ENABLE_HALLUCINATION_FILTER = True
    TOXICITY_THRESHOLD = 0.5  # Score threshold (0-1)
    HALLUCINATION_THRESHOLD = 0.5  # Score threshold (0-1)
    STRICT_SOURCE_CHECK = True  # Verify cited sources exist
    LOW_CONFIDENCE_THRESHOLD = 0.3  # Block if confidence below this

    # Guardrail Logging
    ENABLE_GUARDRAIL_LOGGING = True
    ENABLE_PROMETHEUS_METRICS = True
    GUARDRAIL_LOG_FILE = None  # Optional: path to log file

    @classmethod
    def get_groq_api_key(cls) -> str:
        """Get Groq API key from environment."""
        # Check both GROQ_API_KEY and OPENAI_API_KEY for compatibility
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY or OPENAI_API_KEY not found in environment")
        return api_key
