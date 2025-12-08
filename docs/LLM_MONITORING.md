# LLM Monitoring & Evaluation

This document describes the LLM monitoring and evaluation setup for the AQI Prediction API with RAG capabilities.

## Overview

The monitoring system tracks:
- **Latency**: Request duration for LLM calls, RAG retrieval, and guardrails
- **Token Usage**: Input/output token counts per request
- **Cost Estimation**: Estimated API costs based on token usage
- **Guardrail Violations**: Input and output safety check failures
- **Response Quality**: Confidence scores and retrieval metrics

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Flask API                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  RAG Query   │──│  LLM Metrics │──│   Prometheus Client  │   │
│  │   Endpoint   │  │    Module    │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────┬───────────┘   │
│                                                  │               │
│  ┌──────────────┐  ┌──────────────┐              │               │
│  │  Guardrails  │──│   Logger     │──────────────┤               │
│  │   (I/O)      │  │              │              │               │
│  └──────────────┘  └──────────────┘              │               │
└──────────────────────────────────────────────────┼───────────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────┐
                                        │    Prometheus    │
                                        │   :9090/metrics  │
                                        └────────┬─────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────┐
                                        │     Grafana      │
                                        │   :3000/dashboards│
                                        └──────────────────┘
```

## Prometheus Metrics

### Request Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_requests_total` | Counter | model, endpoint, status | Total LLM requests |
| `llm_requests_in_progress` | Gauge | model | Current in-flight requests |
| `llm_request_duration_seconds` | Histogram | model, endpoint, status | Request latency distribution |
| `llm_request_latency_seconds` | Summary | model | Latency summary (quantiles) |

### Token & Cost Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_tokens_input_total` | Counter | model | Total input tokens used |
| `llm_tokens_output_total` | Counter | model | Total output tokens generated |
| `llm_tokens_total` | Counter | model | Total tokens (input + output) |
| `llm_tokens_per_request` | Histogram | model, token_type | Token distribution per request |
| `llm_cost_usd_total` | Counter | model | Total estimated cost in USD |
| `llm_cost_per_request_usd` | Histogram | model | Cost per request distribution |

### Guardrail Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_guardrail_checks_total` | Counter | stage, result | Total guardrail checks |
| `llm_guardrail_violations_total` | Counter | stage, violation_type | Violations by type |
| `llm_guardrail_duration_seconds` | Histogram | stage | Guardrail check duration |

### RAG Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `rag_queries_total` | Counter | status | Total RAG queries |
| `rag_retrieval_duration_seconds` | Histogram | - | Document retrieval time |
| `rag_documents_retrieved` | Histogram | - | Documents per query |
| `rag_generation_duration_seconds` | Histogram | - | LLM generation time |
| `llm_response_confidence` | Histogram | model | Response confidence scores |

## API Endpoints

### `/metrics`
Prometheus-compatible metrics endpoint.

```bash
curl http://localhost:8000/metrics
```

### `/api/llm/stats`
JSON endpoint for LLM usage statistics.

```bash
curl http://localhost:8000/api/llm/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "prometheus_enabled": true
  },
  "prometheus_enabled": true,
  "timestamp": "2024-12-08 10:30:00"
}
```

### `/api/rag/guardrails/stats`
Guardrail event statistics.

```bash
curl http://localhost:8000/api/rag/guardrails/stats
```

## Grafana Dashboards

Two dashboards are provided:

### 1. MLOps AQI System Monitoring
- CPU, Memory, Disk usage
- API response times
- Location: `monitoring/grafana/dashboards/mlops_dashboard.json`

### 2. LLM & RAG Monitoring Dashboard
- LLM request overview (requests, latency, tokens, cost)
- Latency percentiles (P50, P90, P99)
- Token usage and cost trends
- Guardrail check results and violations
- RAG pipeline metrics
- System metrics

Location: `monitoring/grafana/dashboards/llm_monitoring_dashboard.json`

## Evidently Data Drift Monitoring

The Evidently notebook (`notebooks/05_rag_evidently_monitoring.ipynb`) monitors:

### Corpus Drift
- Text content statistics (length, word count)
- Embedding drift (PCA-reduced semantic vectors)
- Source distribution changes

### LLM Usage Drift
- Query patterns
- Token usage trends
- Latency distribution changes
- Confidence score drift

### Guardrail Metrics
- Violation type distribution
- Check duration trends

### Running the Notebook

```bash
cd notebooks
jupyter notebook 05_rag_evidently_monitoring.ipynb
```

Reports are saved to `reports/evidently/` directory.

## Cost Tracking

Model costs are configured in `src/monitoring/llm_metrics.py`:

```python
MODEL_COSTS = {
    "llama-3.3-70b-versatile": {
        "input": 0.59,   # per 1M tokens
        "output": 0.79,
    },
    "llama-3.1-8b-instant": {
        "input": 0.05,
        "output": 0.08,
    },
    # ... more models
}
```

Update these values as pricing changes.

## Setup

### 1. Start Monitoring Stack

```bash
docker-compose up -d prometheus grafana
```

### 2. Access Dashboards

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### 3. Import Dashboards

Dashboards are auto-provisioned from `monitoring/grafana/dashboards/`.

### 4. Run Drift Monitoring

```bash
# One-time run
python -c "import subprocess; subprocess.run(['jupyter', 'nbconvert', '--execute', 'notebooks/05_rag_evidently_monitoring.ipynb'])"

# Or schedule with cron
0 2 * * * cd /path/to/project && jupyter nbconvert --execute notebooks/05_rag_evidently_monitoring.ipynb
```

## Alert Thresholds

Recommended alert thresholds:

| Metric | Warning | Critical |
|--------|---------|----------|
| P95 Latency | > 5s | > 10s |
| Error Rate | > 1% | > 5% |
| Guardrail Violations | > 5% | > 10% |
| Avg Confidence | < 0.7 | < 0.5 |
| Hourly Cost | > $1 | > $5 |
| Dataset Drift Score | > 0.2 | > 0.3 |

## Troubleshooting

### Metrics not appearing in Prometheus

1. Check if API is running: `curl http://localhost:8000/health`
2. Check metrics endpoint: `curl http://localhost:8000/metrics`
3. Verify Prometheus config targets

### Grafana dashboards empty

1. Check Prometheus data source connection
2. Verify time range selection
3. Check if metrics are being scraped

### Evidently reports failing

1. Ensure ChromaDB has data: Run `make rag-ingest`
2. Check Python environment has `evidently`, `chromadb`, `sentence-transformers`
