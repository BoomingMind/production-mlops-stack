"""
Guardrails & Safety Mechanisms Module

This module provides input validation and output moderation for the RAG pipeline.

Components:
    - InputGuard: Validates user queries (PII detection, prompt injection filter)
    - OutputGuard: Moderates LLM responses (toxicity filter, hallucination detection)
    - GuardrailLogger: Logs all guardrail events to monitoring system

Usage:
    from src.rag.guardrails import InputGuard, OutputGuard, GuardrailLogger
    
    input_guard = InputGuard()
    output_guard = OutputGuard()
    logger = GuardrailLogger()
    
    # Validate input
    input_result = input_guard.validate(user_query)
    if not input_result.passed:
        logger.log_event(input_result)
        return error_response
    
    # Generate response...
    
    # Validate output
    output_result = output_guard.validate(response, context_chunks)
    if not output_result.passed:
        logger.log_event(output_result)
        return filtered_response
"""

from src.rag.guardrails.input_guards import InputGuard, InputValidationResult
from src.rag.guardrails.output_guards import OutputGuard, OutputValidationResult
from src.rag.guardrails.logger import GuardrailLogger, GuardrailEvent

__all__ = [
    "InputGuard",
    "InputValidationResult",
    "OutputGuard",
    "OutputValidationResult",
    "GuardrailLogger",
    "GuardrailEvent",
]
