"""
RAG (Retrieval-Augmented Generation) Module

This module provides:
- Document retrieval using ChromaDB
- LLM response generation using Groq
- Configuration management
"""

from src.rag.config import RAGConfig
from src.rag.retriever import DocumentRetriever
from src.rag.generator import ResponseGenerator

__all__ = ["RAGConfig", "DocumentRetriever", "ResponseGenerator"]
