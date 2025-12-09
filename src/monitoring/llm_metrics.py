"""
LLM Metrics Module

Provides comprehensive Prometheus metrics for LLM monitoring including:
- Request latency tracking
- Token usage (input, output, total)
- Cost estimation
- Guardrail violation tracking
- Model performance metrics

Usage:
    from src.monitoring.llm_metrics import get_llm_metrics
    
    metrics = get_llm_metrics()
    
    # Track a request
    with metrics.track_request("llama-3.3-70b-versatile"):
        response = llm.generate(...)
    
    # Record token usage
    metrics.record_tokens(input_tokens=100, output_tokens=50, model="llama-3.3-70b-versatile")
    
    # Record guardrail violations
    metrics.record_guardrail_violation(stage="input", violation_type="pii_detected")
"""

import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from functools import wraps

# Try to import prometheus_client, fallback gracefully if not available
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, Info, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain"


# =============================================================================
# Cost Configuration (per 1M tokens)
# =============================================================================
# Groq pricing as of Dec 2024 (update as needed)
MODEL_COSTS = {
    "llama-3.3-70b-versatile": {
        "input": 0.59,   # $0.59 per 1M input tokens
        "output": 0.79,  # $0.79 per 1M output tokens
    },
    "llama-3.1-70b-versatile": {
        "input": 0.59,
        "output": 0.79,
    },
    "llama-3.1-8b-instant": {
        "input": 0.05,
        "output": 0.08,
    },
    "mixtral-8x7b-32768": {
        "input": 0.24,
        "output": 0.24,
    },
    "gemma2-9b-it": {
        "input": 0.20,
        "output": 0.20,
    },
    # Default for unknown models
    "default": {
        "input": 1.00,
        "output": 1.00,
    }
}


class LLMMetrics:
    """
    Comprehensive LLM metrics collector for Prometheus.
    
    Tracks:
    - Request latency (histogram)
    - Token usage (input, output, total)
    - Cost estimation (USD)
    - Guardrail violations
    - RAG retrieval metrics
    - Model usage statistics
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one metrics instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize Prometheus metrics."""
        if self._initialized:
            return
            
        self._initialized = True
        self.prometheus_available = PROMETHEUS_AVAILABLE
        
        if not PROMETHEUS_AVAILABLE:
            print("⚠️  prometheus_client not available. Metrics will be no-ops.")
            self._init_fallback_metrics()
            return
        
        self._init_prometheus_metrics()
        print("✅ LLM Prometheus metrics initialized")
    
    def _init_prometheus_metrics(self):
        """Initialize actual Prometheus metrics."""
        
        # =====================================================================
        # Request Latency Metrics
        # =====================================================================
        self.request_latency = Histogram(
            "llm_request_duration_seconds",
            "LLM request duration in seconds",
            ["model", "endpoint", "status"],
            buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0]
        )
        
        self.request_latency_summary = Summary(
            "llm_request_latency_seconds",
            "LLM request latency summary",
            ["model"]
        )
        
        # =====================================================================
        # Token Usage Metrics
        # =====================================================================
        self.tokens_input_total = Counter(
            "llm_tokens_input_total",
            "Total input tokens used",
            ["model"]
        )
        
        self.tokens_output_total = Counter(
            "llm_tokens_output_total",
            "Total output tokens generated",
            ["model"]
        )
        
        self.tokens_total = Counter(
            "llm_tokens_total",
            "Total tokens (input + output)",
            ["model"]
        )
        
        self.tokens_per_request = Histogram(
            "llm_tokens_per_request",
            "Token distribution per request",
            ["model", "token_type"],
            buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000]
        )
        
        # =====================================================================
        # Cost Metrics
        # =====================================================================
        self.cost_total = Counter(
            "llm_cost_usd_total",
            "Total estimated cost in USD",
            ["model"]
        )
        
        self.cost_per_request = Histogram(
            "llm_cost_per_request_usd",
            "Cost per request in USD",
            ["model"],
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
        )
        
        # =====================================================================
        # Guardrail Metrics
        # =====================================================================
        self.guardrail_checks_total = Counter(
            "llm_guardrail_checks_total",
            "Total guardrail checks performed",
            ["stage", "result"]  # stage: input/output, result: passed/blocked/sanitized
        )
        
        self.guardrail_violations_total = Counter(
            "llm_guardrail_violations_total",
            "Total guardrail violations by type",
            ["stage", "violation_type"]
        )
        
        self.guardrail_latency = Histogram(
            "llm_guardrail_duration_seconds",
            "Guardrail check duration in seconds",
            ["stage"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
        )
        
        # =====================================================================
        # RAG Metrics
        # =====================================================================
        self.rag_queries_total = Counter(
            "rag_queries_total",
            "Total RAG queries processed",
            ["status"]  # success/error
        )
        
        self.rag_retrieval_latency = Histogram(
            "rag_retrieval_duration_seconds",
            "RAG document retrieval duration",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
        )
        
        self.rag_documents_retrieved = Histogram(
            "rag_documents_retrieved",
            "Number of documents retrieved per query",
            buckets=[1, 2, 3, 5, 10, 20]
        )
        
        self.rag_generation_latency = Histogram(
            "rag_generation_duration_seconds",
            "RAG response generation duration",
            buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0]
        )
        
        # =====================================================================
        # Confidence Metrics
        # =====================================================================
        self.response_confidence = Histogram(
            "llm_response_confidence",
            "Distribution of response confidence scores",
            ["model"],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        # =====================================================================
        # Request Counts
        # =====================================================================
        self.requests_total = Counter(
            "llm_requests_total",
            "Total LLM requests",
            ["model", "endpoint", "status"]
        )
        
        # Current in-flight requests
        self.requests_in_progress = Gauge(
            "llm_requests_in_progress",
            "Number of requests currently being processed",
            ["model"]
        )
        
        # =====================================================================
        # Model Info
        # =====================================================================
        self.model_info = Info(
            "llm_model",
            "Information about the LLM model being used"
        )
        
    def _init_fallback_metrics(self):
        """Initialize no-op fallback metrics when Prometheus is unavailable."""
        # Create simple counters for non-Prometheus environments
        self._fallback_stats = {
            "requests_total": 0,
            "tokens_input": 0,
            "tokens_output": 0,
            "cost_total": 0.0,
            "guardrail_violations": 0,
            "latency_sum": 0.0,
            "latency_count": 0,
        }
    
    # =========================================================================
    # Token & Cost Recording
    # =========================================================================
    
    def record_tokens(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "default"
    ):
        """
        Record token usage and calculate cost.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name for cost calculation
        """
        if not self.prometheus_available:
            self._fallback_stats["tokens_input"] += input_tokens
            self._fallback_stats["tokens_output"] += output_tokens
            return
        
        total_tokens = input_tokens + output_tokens
        
        # Record token counts
        self.tokens_input_total.labels(model=model).inc(input_tokens)
        self.tokens_output_total.labels(model=model).inc(output_tokens)
        self.tokens_total.labels(model=model).inc(total_tokens)
        
        # Record token distribution
        self.tokens_per_request.labels(model=model, token_type="input").observe(input_tokens)
        self.tokens_per_request.labels(model=model, token_type="output").observe(output_tokens)
        self.tokens_per_request.labels(model=model, token_type="total").observe(total_tokens)
        
        # Calculate and record cost
        cost = self._calculate_cost(input_tokens, output_tokens, model)
        self.cost_total.labels(model=model).inc(cost)
        self.cost_per_request.labels(model=model).observe(cost)
        
        return cost
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate cost in USD based on token usage."""
        pricing = MODEL_COSTS.get(model, MODEL_COSTS["default"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    # =========================================================================
    # Latency Tracking
    # =========================================================================
    
    @contextmanager
    def track_request(
        self,
        model: str = "default",
        endpoint: str = "rag_query"
    ):
        """
        Context manager to track request latency.
        
        Usage:
            with metrics.track_request("llama-3.3-70b-versatile"):
                response = llm.generate(...)
        """
        start_time = time.time()
        status = "success"
        
        if self.prometheus_available:
            self.requests_in_progress.labels(model=model).inc()
        
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            
            if self.prometheus_available:
                self.requests_in_progress.labels(model=model).dec()
                self.request_latency.labels(
                    model=model,
                    endpoint=endpoint,
                    status=status
                ).observe(duration)
                self.request_latency_summary.labels(model=model).observe(duration)
                self.requests_total.labels(
                    model=model,
                    endpoint=endpoint,
                    status=status
                ).inc()
            else:
                self._fallback_stats["requests_total"] += 1
                self._fallback_stats["latency_sum"] += duration
                self._fallback_stats["latency_count"] += 1
    
    def record_latency(
        self,
        duration: float,
        model: str = "default",
        endpoint: str = "rag_query",
        status: str = "success"
    ):
        """Record a request latency directly."""
        if self.prometheus_available:
            self.request_latency.labels(
                model=model,
                endpoint=endpoint,
                status=status
            ).observe(duration)
            self.request_latency_summary.labels(model=model).observe(duration)
            self.requests_total.labels(
                model=model,
                endpoint=endpoint,
                status=status
            ).inc()
    
    # =========================================================================
    # Guardrail Metrics
    # =========================================================================
    
    def record_guardrail_check(
        self,
        stage: str,
        passed: bool,
        sanitized: bool = False,
        duration: Optional[float] = None
    ):
        """
        Record a guardrail check result.
        
        Args:
            stage: "input" or "output"
            passed: Whether the check passed
            sanitized: Whether content was sanitized (for input)
            duration: Optional duration of the check
        """
        if not self.prometheus_available:
            return
        
        if passed:
            result = "sanitized" if sanitized else "passed"
        else:
            result = "blocked"
        
        self.guardrail_checks_total.labels(stage=stage, result=result).inc()
        
        if duration is not None:
            self.guardrail_latency.labels(stage=stage).observe(duration)
    
    def record_guardrail_violation(
        self,
        stage: str,
        violation_type: str
    ):
        """
        Record a specific guardrail violation.
        
        Args:
            stage: "input" or "output"
            violation_type: Type of violation (e.g., "pii_email", "prompt_injection")
        """
        if not self.prometheus_available:
            self._fallback_stats["guardrail_violations"] += 1
            return
        
        self.guardrail_violations_total.labels(
            stage=stage,
            violation_type=violation_type
        ).inc()
    
    @contextmanager
    def track_guardrail(self, stage: str):
        """
        Context manager to track guardrail check duration.
        
        Usage:
            with metrics.track_guardrail("input"):
                result = input_guard.validate(query)
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if self.prometheus_available:
                self.guardrail_latency.labels(stage=stage).observe(duration)
    
    # =========================================================================
    # RAG Metrics
    # =========================================================================
    
    def record_rag_query(self, status: str = "success"):
        """Record a RAG query."""
        if self.prometheus_available:
            self.rag_queries_total.labels(status=status).inc()
    
    def record_rag_retrieval(self, duration: float, num_documents: int):
        """Record RAG retrieval metrics."""
        if self.prometheus_available:
            self.rag_retrieval_latency.observe(duration)
            self.rag_documents_retrieved.observe(num_documents)
    
    def record_rag_generation(self, duration: float):
        """Record RAG generation latency."""
        if self.prometheus_available:
            self.rag_generation_latency.observe(duration)
    
    def record_confidence(self, confidence: float, model: str = "default"):
        """Record response confidence score."""
        if self.prometheus_available:
            self.response_confidence.labels(model=model).observe(confidence)
    
    # =========================================================================
    # Model Info
    # =========================================================================
    
    def set_model_info(self, model_name: str, version: str = "1.0", provider: str = "groq"):
        """Set model information."""
        if self.prometheus_available:
            self.model_info.info({
                "name": model_name,
                "version": version,
                "provider": provider
            })
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_metrics(self) -> bytes:
        """Generate Prometheus metrics output."""
        if self.prometheus_available:
            from prometheus_client import generate_latest
            return generate_latest()
        return b""
    
    def get_content_type(self) -> str:
        """Get the content type for metrics endpoint."""
        if self.prometheus_available:
            from prometheus_client import CONTENT_TYPE_LATEST
            return CONTENT_TYPE_LATEST
        return "text/plain"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics as a dictionary (for non-Prometheus use)."""
        if not self.prometheus_available:
            avg_latency = 0.0
            if self._fallback_stats["latency_count"] > 0:
                avg_latency = self._fallback_stats["latency_sum"] / self._fallback_stats["latency_count"]
            
            return {
                "requests_total": self._fallback_stats["requests_total"],
                "tokens_input": self._fallback_stats["tokens_input"],
                "tokens_output": self._fallback_stats["tokens_output"],
                "cost_total_usd": self._fallback_stats["cost_total"],
                "guardrail_violations": self._fallback_stats["guardrail_violations"],
                "average_latency_seconds": avg_latency,
            }
        
        # When Prometheus is available, return empty dict 
        # (metrics are collected by Prometheus)
        return {"prometheus_enabled": True}


# Singleton instance
_llm_metrics: Optional[LLMMetrics] = None


def get_llm_metrics() -> LLMMetrics:
    """Get the singleton LLMMetrics instance."""
    global _llm_metrics
    if _llm_metrics is None:
        _llm_metrics = LLMMetrics()
    return _llm_metrics


# Decorator for tracking function execution
def track_llm_call(model: str = "default", endpoint: str = "rag_query"):
    """
    Decorator to track LLM call latency.
    
    Usage:
        @track_llm_call(model="llama-3.3-70b-versatile")
        def generate_response(query):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_llm_metrics()
            with metrics.track_request(model=model, endpoint=endpoint):
                return func(*args, **kwargs)
        return wrapper
    return decorator
