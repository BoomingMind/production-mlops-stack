#!/usr/bin/env python3
"""
Document Ingestion Pipeline

This script handles:
1. Loading documents from data/knowledge/ (PDFs and text files)
2. Splitting documents into chunks
3. Storing chunks in ChromaDB for retrieval

Usage:
    python src/ingest.py
    
    # Or with Makefile
    make rag-ingest
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.config import RAGConfig
from src.rag.retriever import DocumentRetriever


def load_text_file(file_path: Path) -> str:
    """Load content from a text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_pdf_file(file_path: Path) -> str:
    """Load content from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        
        reader = PdfReader(file_path)
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    except ImportError:
        print("⚠️  pypdf not installed. Install with: pip install pypdf")
        return ""
    except Exception as e:
        print(f"⚠️  Error reading PDF {file_path}: {e}")
        return ""


def chunk_text(
    text: str, 
    chunk_size: int = None, 
    overlap: int = None
) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The text to split
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = RAGConfig.CHUNK_SIZE
    if overlap is None:
        overlap = RAGConfig.CHUNK_OVERLAP
    
    # Clean the text
    text = text.strip()
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Get chunk
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence or word boundary
        if end < len(text):
            # Look for last sentence ending
            last_period = chunk.rfind(". ")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size // 2:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position (with overlap)
        start = end - overlap
    
    return chunks


def load_documents(knowledge_dir: Path) -> List[Tuple[str, str]]:
    """
    Load all documents from the knowledge directory.
    
    Returns:
        List of (filename, content) tuples
    """
    documents = []
    
    if not knowledge_dir.exists():
        print(f"⚠️  Knowledge directory not found: {knowledge_dir}")
        return documents
    
    # Supported file types
    text_extensions = {".txt", ".md"}
    pdf_extensions = {".pdf"}
    
    for file_path in knowledge_dir.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            
            if ext in text_extensions:
                print(f"Loading text file: {file_path.name}")
                content = load_text_file(file_path)
                if content:
                    documents.append((file_path.name, content))
                    
            elif ext in pdf_extensions:
                print(f"Loading PDF file: {file_path.name}")
                content = load_pdf_file(file_path)
                if content:
                    documents.append((file_path.name, content))
    
    return documents


def ingest_documents(clear_existing: bool = True) -> Dict:
    """
    Main ingestion function.
    
    Loads all documents from data/knowledge/, chunks them,
    and stores them in ChromaDB.
    
    Args:
        clear_existing: Whether to clear existing documents first
        
    Returns:
        Dictionary with ingestion statistics
    """
    print("=" * 60)
    print("DOCUMENT INGESTION PIPELINE")
    print("=" * 60)
    
    # Initialize retriever
    retriever = DocumentRetriever()
    
    # Optionally clear existing documents
    if clear_existing:
        print("\n🗑️  Clearing existing collection...")
        retriever.clear_collection()
    
    # Load documents
    print(f"\nLoading documents from: {RAGConfig.KNOWLEDGE_DIR}")
    documents = load_documents(RAGConfig.KNOWLEDGE_DIR)
    
    if not documents:
        print("No documents found!")
        return {"status": "error", "message": "No documents found"}
    
    print(f"\nLoaded {len(documents)} documents")
    
    # Process each document
    total_chunks = 0
    all_chunks = []
    all_metadatas = []
    
    for filename, content in documents:
        print(f"\nProcessing: {filename}")
        
        # Chunk the document
        chunks = chunk_text(content)
        print(f"   Created {len(chunks)} chunks")
        
        # Create metadata for each chunk
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": filename,
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
        
        total_chunks += len(chunks)
    
    # Store in ChromaDB
    print(f"\nStoring {total_chunks} chunks in ChromaDB...")
    retriever.add_documents(all_chunks, all_metadatas)
    
    # Print summary
    stats = retriever.get_collection_stats()
    
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Documents processed: {len(documents)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Chunks in collection: {stats['document_count']}")
    print(f"Sources: {stats['sources']}")
    print("=" * 60)
    
    return {
        "status": "success",
        "documents_processed": len(documents),
        "chunks_created": total_chunks,
        "collection_stats": stats
    }


if __name__ == "__main__":
    result = ingest_documents()
    print(f"\nResult: {result}")
