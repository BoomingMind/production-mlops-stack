"""
Document Retriever Module

Handles document storage and retrieval using ChromaDB.
Simple and clean implementation without over-engineering.
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional

from src.rag.config import RAGConfig


class DocumentRetriever:
    """
    Handles document storage and retrieval using ChromaDB.

    Usage:
        retriever = DocumentRetriever()

        # Add documents
        retriever.add_documents(chunks, metadatas)

        # Query
        results = retriever.query("What is AQI?")
    """

    def __init__(self):
        """Initialize ChromaDB client and collection."""
        # Create persistent client
        self.client = chromadb.PersistentClient(path=str(RAGConfig.CHROMA_DIR))

        # Use sentence-transformers for embeddings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=RAGConfig.EMBEDDING_MODEL,
            device="cpu",
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=RAGConfig.COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"description": "AQI knowledge base"},
        )

        print(f"✅ ChromaDB initialized. Collection: {RAGConfig.COLLECTION_NAME}")
        print(f"   Documents in collection: {self.collection.count()}")

    def add_documents(
        self,
        chunks: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """
        Add document chunks to the collection.

        Args:
            chunks: List of text chunks
            metadatas: Optional list of metadata dicts for each chunk
            ids: Optional list of IDs (auto-generated if not provided)

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        # Default empty metadata if not provided
        if metadatas is None:
            metadatas = [{}] * len(chunks)

        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(chunks))]

        # Respect chromadb max batch sizes by adding in batches
        batch_size = getattr(RAGConfig, "MAX_BATCH_SIZE", 5000)
        total_added = 0

        for start in range(0, len(chunks), batch_size):
            end = min(start + batch_size, len(chunks))
            batch_docs = chunks[start:end]
            batch_meta = metadatas[start:end]
            batch_ids = ids[start:end]

            self.collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids,
            )

            total_added += len(batch_docs)

        print(
            f"✅ Added {total_added} chunks to collection (in batches of up to {batch_size})"
        )
        return total_added

    def query(
        self, query_text: str, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the collection for relevant documents.

        Args:
            query_text: The query string
            top_k: Number of results to return (default from config)

        Returns:
            List of results with text, metadata, and distance
        """
        if top_k is None:
            top_k = RAGConfig.TOP_K

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append(
                {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )

        return formatted_results

    def get_all_sources(self) -> List[str]:
        """Get list of all unique source files in the collection."""
        # Get all metadata
        all_data = self.collection.get(include=["metadatas"])

        sources = set()
        for metadata in all_data["metadatas"]:
            if "source" in metadata:
                sources.add(metadata["source"])

        return list(sources)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        return {
            "collection_name": RAGConfig.COLLECTION_NAME,
            "document_count": self.collection.count(),
            "sources": self.get_all_sources(),
        }

    def clear_collection(self):
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(RAGConfig.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=RAGConfig.COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"description": "AQI knowledge base"},
        )
        print("✅ Collection cleared")


if __name__ == "__main__":
    # Quick test
    retriever = DocumentRetriever()
    print(f"\nCollection stats: {retriever.get_collection_stats()}")
