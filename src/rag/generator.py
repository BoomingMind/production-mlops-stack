"""
Response Generator Module

Handles LLM response generation using Groq with retrieved context.
"""

import json
from typing import List, Dict, Any, Optional

from groq import Groq

from src.rag.config import RAGConfig


class ResponseGenerator:
    """
    Generates responses using Groq LLM with RAG context.
    
    Usage:
        generator = ResponseGenerator()
        response = generator.generate(
            query="What precautions for AQI 150?",
            context_chunks=[{"text": "...", "metadata": {...}}, ...]
        )
    """
    
    def __init__(self):
        """Initialize Groq client."""
        self.client = Groq(api_key=RAGConfig.get_groq_api_key())
        self.model = RAGConfig.LLM_MODEL
        print(f"✅ Groq client initialized with model: {self.model}")
    
    def _format_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a context string."""
        if not context_chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            source = chunk.get("metadata", {}).get("source", "Unknown")
            text = chunk.get("text", "")
            context_parts.append(f"[Source {i}: {source}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the RAG prompt with query and context."""
        return f"""You are an expert Air Quality Index (AQI) advisor. Use the following context to answer the user's question about air quality, health effects, and precautions.

CONTEXT:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Answer based on the provided context
2. If the context doesn't contain relevant information, say so
3. Provide practical, actionable advice when applicable
4. Be concise but comprehensive

Respond in JSON format:
{{
    "answer": "Your detailed answer here",
    "sources_used": ["list of source names used"],
    "confidence": "high/medium/low based on context relevance"
}}"""
    
    def generate(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]],
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the LLM with RAG context.
        
        Args:
            query: User's question
            context_chunks: Retrieved context chunks from the retriever
            temperature: Optional temperature override
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        if temperature is None:
            temperature = RAGConfig.LLM_TEMPERATURE
        
        # Format context
        context = self._format_context(context_chunks)
        
        # Build prompt
        prompt = self._build_prompt(query, context)
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful air quality advisor. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=RAGConfig.MAX_TOKENS
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            parsed = self._parse_json_response(raw_response)
            
            return {
                "success": True,
                "answer": parsed.get("answer", ""),
                "sources_used": parsed.get("sources_used", []),
                "confidence": parsed.get("confidence", "unknown"),
                "context_chunks": len(context_chunks),
                "model": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "answer": f"Error generating response: {str(e)}",
                "sources_used": [],
                "confidence": "none",
                "error": str(e)
            }
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from the model's response."""
        text = response_text.strip()
        
        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        return json.loads(text)


if __name__ == "__main__":
    # Quick test
    generator = ResponseGenerator()
    
    # Test with sample context
    sample_context = [
        {
            "text": "AQI above 150 is unhealthy for sensitive groups including children and elderly.",
            "metadata": {"source": "test.txt"}
        }
    ]
    
    result = generator.generate(
        query="What should I do when AQI is 150?",
        context_chunks=sample_context
    )
    print(json.dumps(result, indent=2))
