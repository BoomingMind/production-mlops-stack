"""
FastAPI Application for AQI Weather Prediction
with Prometheus Metrics Integration
"""
import os
import time
import boto3
import joblib
import numpy as np
import pandas as pd
import json
from io import BytesIO
from typing import List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import mlflow
import mlflow.sklearn

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AQI Weather Prediction API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict": "/predict (POST)",
            "predictions_latest": "/predictions/latest",
            "predictions_by_date": "/predictions/by-date/{date}",
            "predictions_summary": "/predictions/summary",
            "model_info": "/model/info",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_loaded = model is not None
    scaler_loaded = scaler is not None
    
    return {
        "status": "healthy" if (model_loaded and scaler_loaded) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": model_loaded,
        "scaler_loaded": scaler_loaded,
        "model_version": model_version
    }

# ==================== MIDDLEWARE ====================
@app.middleware("http")
async def add_metrics_middleware(request, call_next):
    """Middleware to track HTTP request metrics"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).observe(duration)
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
