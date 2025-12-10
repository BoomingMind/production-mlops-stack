# ruff: noqa: E402
import sys
import os

# Add parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import time
import json
from io import BytesIO
from datetime import datetime, timedelta

# Third-party imports
import boto3
import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Local imports
from src.monitoring.llm_metrics import get_llm_metrics

# Load environment variables
load_dotenv()

# LLM Monitoring initialization
print("Starting LLM metrics import...")
llm_metrics = get_llm_metrics()
METRICS_AVAILABLE = True
print("Import successful, getting metrics instance...")
print(f"✅ LLM metrics initialized successfully: {llm_metrics}")
print(f"METRICS_AVAILABLE set to: {METRICS_AVAILABLE}")

# RAG imports (lazy loading to avoid startup issues)
rag_retriever = None
rag_generator = None
rag_input_guard = None
rag_output_guard = None
rag_guardrail_logger = None

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"])

# Global variables to store model, scaler, and data
model = None
scaler = None
df = None
features = None
target_columns = ["aqi_index", "Calculated_AQI"]
date_columns = ["year", "month", "day", "hour"]

# AWS S3 Configuration
bucket_name = "my-feature-store-data"
model_key = "models/best_model.pkl"
scaler_key = "models/scaler.pkl"
metadata_key = "models/best_model_metadata.json"
data_key = "pipeline-data/data.csv"


def get_s3_client():
    """Create and return S3 client"""
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "eu-north-1"),
    )


def load_model_and_scaler():
    """Load pre-trained model and scaler from AWS S3"""
    global model, scaler

    if model is not None and scaler is not None:
        return True

    try:
        s3 = get_s3_client()

        # Load metadata
        print("Loading metadata from S3...")
        metadata_obj = s3.get_object(Bucket=bucket_name, Key=metadata_key)
        metadata_content = metadata_obj["Body"].read().decode("utf-8")
        _ = json.loads(metadata_content)  # Validate JSON format

        # Load model
        print(f"Loading model from S3: {bucket_name}/{model_key}")
        model_buffer = BytesIO()
        s3.download_fileobj(Bucket=bucket_name, Key=model_key, Fileobj=model_buffer)
        model_buffer.seek(0)
        model = joblib.load(model_buffer)
        print("Model loaded successfully")

        # Load scaler
        print(f"Loading scaler from S3: {bucket_name}/{scaler_key}")
        scaler_buffer = BytesIO()
        s3.download_fileobj(Bucket=bucket_name, Key=scaler_key, Fileobj=scaler_buffer)
        scaler_buffer.seek(0)
        scaler = joblib.load(scaler_buffer)
        print("Scaler loaded successfully")

        return True
    except Exception as e:
        print(f"ERROR: Could not load model or scaler from S3: {str(e)}")
        return False


def load_historical_data():
    """Load historical data from AWS S3 for feature engineering"""
    global df, features

    if df is not None and features is not None:
        return True

    try:
        s3 = get_s3_client()

        print("Loading historical data from S3...")
        obj = s3.get_object(Bucket=bucket_name, Key=data_key)
        df = pd.read_csv(obj["Body"])

        # Process data
        df["date"] = pd.to_datetime(df[["year", "month", "day"]])
        df = df.dropna(subset=["aqi_index", "Calculated_AQI"])

        # Define features
        features = [
            col for col in df.columns if col not in target_columns and col != "date"
        ]

        print(f"Historical data loaded: {len(df)} rows, {len(features)} features")
        return True
    except Exception as e:
        print(f"ERROR: Could not load historical data from S3: {str(e)}")
        return False


def get_aqi_category(aqi):
    """Get AQI category based on standard AQI ranges"""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


def generate_future_features(num_hours):
    """Generate features for future hours using historical patterns"""
    global df, features

    # Generate future dates
    start_date = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(
        hours=1
    )
    future_dates = [start_date + timedelta(hours=i) for i in range(num_hours)]

    # Create DataFrame with date-time features
    future_features = pd.DataFrame(
        {
            "year": [d.year for d in future_dates],
            "month": [d.month for d in future_dates],
            "day": [d.day for d in future_dates],
            "hour": [d.hour for d in future_dates],
        }
    )

    # Get numeric features
    numeric_features = [col for col in features if col not in date_columns]

    # Calculate hourly patterns from historical data
    hourly_patterns = {}
    for hour in range(24):
        hour_data = df[df["hour"] == hour][numeric_features]
        if len(hour_data) > 0:
            hourly_patterns[hour] = hour_data.mean().to_dict()
        else:
            hourly_patterns[hour] = df[numeric_features].mean().to_dict()

    # Apply features to future data
    for idx, row in future_features.iterrows():
        hour = row["hour"]
        hour_pattern = hourly_patterns[hour]

        for feature, value in hour_pattern.items():
            future_features.loc[idx, feature] = value

    # Add temporal variations
    weather_features = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "wind_speed_10m",
        "wind_direction_10m",
        "surface_pressure",
        "cloud_cover",
        "precipitation",
        "rain",
        "snowfall",
    ]

    for i in range(1, len(future_features)):
        for feature in weather_features:
            if feature in future_features.columns:
                variation = np.random.uniform(-0.03, 0.03)
                future_features.loc[i, feature] = future_features.loc[
                    i - 1, feature
                ] * (1 + variation)

    # Ensure all required columns are present
    required_columns = [col for col in features if col in df.columns]
    for col in required_columns:
        if col not in future_features.columns:
            future_features[col] = df[col].mean()

    # Order columns to match training data
    future_features = future_features[required_columns]

    return future_features, future_dates


@app.route("/")
def home():
    """Home endpoint"""
    print("Home endpoint called")
    return jsonify(
        {
            "message": "AQI Prediction API",
            "version": "2.0",
            "endpoints": {
                "/health": "Health check endpoint",
                "/metrics": "Prometheus metrics endpoint",
                "/api/predict": "Get AQI predictions (query params: days=1-7)",
                "/api/predict/hourly": "Get hourly predictions (query params: hours=1-168)",
                "/api/predict/daily": "Get daily summary predictions (query params: days=1-7)",
                "/api/predict/current": "Get prediction for the next hour",
                "/api/rag/query": "POST - Ask questions about air quality (RAG)",
                "/api/rag/sources": "GET - List indexed knowledge sources",
                "/api/rag/guardrails/stats": "GET - Guardrail statistics",
                "/api/llm/stats": "GET - LLM usage statistics",
            },
        }
    )


@app.route("/debug")
def debug():
    return {
        "llm_metrics": str(llm_metrics),
        "METRICS_AVAILABLE": METRICS_AVAILABLE,
        "type": type(llm_metrics).__name__ if llm_metrics else "None",
    }


@app.route("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.

    Exposes LLM metrics for Prometheus scraping:
    - Request latency
    - Token usage
    - Cost estimation
    - Guardrail violations
    - RAG metrics
    """
    if not METRICS_AVAILABLE:
        return "Metrics not available", 503

    try:
        metrics_data = llm_metrics.get_metrics()
        print(f"Metrics data length: {len(metrics_data) if metrics_data else 0}")
        if not metrics_data:
            return "No metrics recorded yet", 200
        return Response(metrics_data, mimetype=llm_metrics.get_content_type())
    except Exception as e:
        print(f"Error getting metrics: {e}")
        import traceback

        traceback.print_exc()
        return "Metrics not available", 503


@app.route("/api/llm/stats")
def llm_stats():
    """
    Get LLM usage statistics.

    Returns:
        JSON with current LLM metrics and usage stats
    """
    if not METRICS_AVAILABLE:
        return jsonify({"success": False, "error": "LLM metrics not available"}), 503

    return jsonify(
        {
            "success": True,
            "stats": llm_metrics.get_stats(),
            "prometheus_enabled": llm_metrics.prometheus_available,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@app.route("/health")
def health():
    """Health check endpoint"""
    try:
        # Check if model and scaler are loaded
        model_loaded = model is not None
        scaler_loaded = scaler is not None
        data_loaded = df is not None

        # Try loading if not already loaded
        if not model_loaded or not scaler_loaded:
            load_model_and_scaler()
            model_loaded = model is not None
            scaler_loaded = scaler is not None

        if not data_loaded:
            load_historical_data()
            data_loaded = df is not None

        status = (
            "healthy"
            if (model_loaded and scaler_loaded and data_loaded)
            else "unhealthy"
        )

        return (
            jsonify(
                {
                    "status": status,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "components": {
                        "model": "loaded" if model_loaded else "not loaded",
                        "scaler": "loaded" if scaler_loaded else "not loaded",
                        "data": "loaded" if data_loaded else "not loaded",
                    },
                }
            ),
            200 if status == "healthy" else 503,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ),
            503,
        )


@app.route("/api/predict")
def predict():
    """Get AQI predictions for the next N days"""
    try:
        # Load model and data if not loaded
        if not load_model_and_scaler() or not load_historical_data():
            return jsonify({"error": "Failed to load model or data"}), 500

        # Get number of days from query params (default: 3, max: 7)
        days = request.args.get("days", default=3, type=int)
        days = min(max(days, 1), 7)  # Ensure between 1 and 7

        num_hours = days * 24

        # Generate future features
        future_features, future_dates = generate_future_features(num_hours)

        # Scale features
        future_scaled = scaler.transform(future_features)

        # Make predictions
        predictions = model.predict(future_scaled)

        # Create results
        results = []
        for i, date in enumerate(future_dates):
            aqi_index = float(np.round(predictions[i, 0], 2))
            results.append(
                {
                    "datetime": date.strftime("%Y-%m-%d %H:%M"),
                    "date": date.strftime("%Y-%m-%d"),
                    "hour": date.hour,
                    "predicted_aqi_index": aqi_index,
                    "predicted_calculated_aqi": float(np.round(predictions[i, 1], 2)),
                    "aqi_category": get_aqi_category(aqi_index),
                }
            )

        # Calculate statistics
        aqi_values = [r["predicted_aqi_index"] for r in results]
        calculated_aqi_values = [r["predicted_calculated_aqi"] for r in results]

        return jsonify(
            {
                "success": True,
                "prediction_info": {
                    "days": days,
                    "total_hours": num_hours,
                    "start_datetime": future_dates[0].strftime("%Y-%m-%d %H:%M"),
                    "end_datetime": future_dates[-1].strftime("%Y-%m-%d %H:%M"),
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
                "statistics": {
                    "average_aqi": round(np.mean(aqi_values), 2),
                    "min_aqi": round(np.min(aqi_values), 2),
                    "max_aqi": round(np.max(aqi_values), 2),
                    "std_deviation": round(np.std(aqi_values), 2),
                    "calculated_aqi_average": round(np.mean(calculated_aqi_values), 2),
                    "calculated_aqi_min": round(np.min(calculated_aqi_values), 2),
                    "calculated_aqi_max": round(np.max(calculated_aqi_values), 2),
                    "calculated_aqi_std_deviation": round(
                        np.std(calculated_aqi_values), 2
                    ),
                },
                "predictions": results,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/predict/hourly")
def predict_hourly():
    """Get hourly AQI predictions for the next N hours"""
    try:
        # Load model and data if not loaded
        if not load_model_and_scaler() or not load_historical_data():
            return jsonify({"error": "Failed to load model or data"}), 500

        # Get number of hours from query params (default: 24, max: 168 = 7 days)
        hours = request.args.get("hours", default=24, type=int)
        hours = min(max(hours, 1), 168)  # Ensure between 1 and 168

        # Generate future features
        future_features, future_dates = generate_future_features(hours)

        # Scale features
        future_scaled = scaler.transform(future_features)

        # Make predictions
        predictions = model.predict(future_scaled)

        # Create results
        results = []
        for i, date in enumerate(future_dates):
            aqi_index = float(np.round(predictions[i, 0], 2))
            results.append(
                {
                    "datetime": date.strftime("%Y-%m-%d %H:%M"),
                    "hour": date.hour,
                    "predicted_aqi_index": aqi_index,
                    "predicted_calculated_aqi": float(np.round(predictions[i, 1], 2)),
                    "aqi_category": get_aqi_category(aqi_index),
                }
            )

        return jsonify({"success": True, "total_hours": hours, "predictions": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/predict/daily")
def predict_daily():
    """Get daily summary AQI predictions for the next N days"""
    try:
        # Load model and data if not loaded
        if not load_model_and_scaler() or not load_historical_data():
            return jsonify({"error": "Failed to load model or data"}), 500

        # Get number of days from query params (default: 3, max: 7)
        days = request.args.get("days", default=3, type=int)
        days = min(max(days, 1), 7)  # Ensure between 1 and 7

        num_hours = days * 24

        # Generate future features
        future_features, future_dates = generate_future_features(num_hours)

        # Scale features
        future_scaled = scaler.transform(future_features)

        # Make predictions
        predictions = model.predict(future_scaled)

        # Create DataFrame for aggregation
        prediction_df = pd.DataFrame(
            {
                "date": [d.strftime("%Y-%m-%d") for d in future_dates],
                "aqi_index": predictions[:, 0],
                "calculated_aqi": predictions[:, 1],
            }
        )

        # Ensure we return exactly `days` calendar-day summaries starting from
        # the first future date. Grouping by unique dates can sometimes yield
        # an extra partial day if the start hour isn't midnight, so we
        # explicitly build the target date range and aggregate per date.
        start_day = future_dates[0].date()
        target_dates = [
            (start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)
        ]

        results = []
        for date in target_dates:
            day_rows = prediction_df[prediction_df["date"] == date]
            if day_rows.empty:
                # If there are no rows for this calendar date (can happen near
                # DST boundaries or with sparse future ranges), fill with NaNs
                # or carry forward the mean of available predictions.
                avg_aqi = float(np.nan)
                min_aqi = float(np.nan)
                max_aqi = float(np.nan)
                calc_mean = float(np.nan)
            else:
                min_aqi = float(day_rows["aqi_index"].min())
                max_aqi = float(day_rows["aqi_index"].max())
                avg_aqi = float(round(day_rows["aqi_index"].mean(), 2))
                calc_min = float(day_rows["calculated_aqi"].min())
                calc_max = float(day_rows["calculated_aqi"].max())
                calc_mean = float(round(day_rows["calculated_aqi"].mean(), 2))

            results.append(
                {
                    "date": date,
                    "aqi_index": {
                        "min": min_aqi,
                        "max": max_aqi,
                        "mean": avg_aqi,
                    },
                    "calculated_aqi": {
                        "min": calc_min if not day_rows.empty else float(np.nan),
                        "max": calc_max if not day_rows.empty else float(np.nan),
                        "mean": calc_mean,
                    },
                    "aqi_category": (
                        get_aqi_category(avg_aqi) if not np.isnan(avg_aqi) else None
                    ),
                }
            )

        return jsonify({"success": True, "days": days, "daily_summary": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/predict/current")
def predict_current():
    """Get AQI prediction for the current/next hour"""
    try:
        # Load model and data if not loaded
        if not load_model_and_scaler() or not load_historical_data():
            return jsonify({"error": "Failed to load model or data"}), 500

        # Generate features for next hour
        future_features, future_dates = generate_future_features(1)

        # Scale features
        future_scaled = scaler.transform(future_features)

        # Make prediction
        prediction = model.predict(future_scaled)[0]

        aqi_index = float(np.round(prediction[0], 2))
        calculated_aqi = float(np.round(prediction[1], 2))

        return jsonify(
            {
                "success": True,
                "prediction": {
                    "datetime": future_dates[0].strftime("%Y-%m-%d %H:%M"),
                    "predicted_aqi_index": aqi_index,
                    "predicted_calculated_aqi": calculated_aqi,
                    "aqi_category": get_aqi_category(aqi_index),
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# RAG (Retrieval-Augmented Generation) Endpoints
# =============================================================================


def load_rag_components():
    """Lazy load RAG components including guardrails."""
    global rag_retriever, rag_generator, rag_input_guard, rag_output_guard, rag_guardrail_logger

    if rag_retriever is None or rag_generator is None:
        try:
            # Add project root to path for imports
            import sys
            from pathlib import Path

            # `app.py` lives in `src/` so the project root is one level up
            project_root = Path(__file__).resolve().parent.parent
            # Insert project root at front of sys.path so `import src.*` works
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from src.rag.retriever import DocumentRetriever
            from src.rag.generator import ResponseGenerator
            from src.rag.guardrails import InputGuard, OutputGuard, GuardrailLogger

            rag_retriever = DocumentRetriever()
            rag_generator = ResponseGenerator()
            rag_input_guard = InputGuard()
            rag_output_guard = OutputGuard()
            rag_guardrail_logger = GuardrailLogger()
            print("✅ Guardrails initialized: InputGuard, OutputGuard, GuardrailLogger")
            return True
        except Exception as e:
            print(f"Failed to load RAG components: {e}")
            import traceback

            traceback.print_exc()
            return False
    return True


@app.route("/api/rag/query", methods=["POST"])
def rag_query():
    """
    Query the RAG system with a question about air quality.
    Includes guardrail checks for input validation and output moderation.
    Tracks LLM metrics for monitoring.

    Request body:
        {
            "query": "What precautions should I take when AQI is 150?"
        }

    Returns:
        JSON response with answer, sources, and guardrail info
    """
    request_start_time = time.time()
    model_name = "llama-3.3-70b-versatile"  # Default model from config

    try:
        # Load RAG components
        if not load_rag_components():
            if METRICS_AVAILABLE:
                llm_metrics.record_rag_query(status="error")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "RAG system not available. Run 'make rag-ingest' first.",
                    }
                ),
                503,
            )

        # Get query from request
        data = request.get_json()
        if not data or "query" not in data:
            return (
                jsonify({"success": False, "error": "Missing 'query' in request body"}),
                400,
            )

        query = data["query"]
        guardrail_events = []
        metrics_data = {
            "input_guard_duration": 0,
            "retrieval_duration": 0,
            "generation_duration": 0,
            "output_guard_duration": 0,
        }

        # =================================================================
        # INPUT VALIDATION (Guardrails Layer 1)
        # =================================================================
        input_guard_start = time.time()
        input_result = rag_input_guard.validate(query)
        metrics_data["input_guard_duration"] = time.time() - input_guard_start
        rag_guardrail_logger.log_input_result(input_result)

        # Track input guardrail metrics
        if METRICS_AVAILABLE:
            llm_metrics.record_guardrail_check(
                stage="input",
                passed=input_result.passed,
                sanitized=input_result.sanitized_input is not None,
                duration=metrics_data["input_guard_duration"],
            )
            # Record violations if any
            for violation in input_result.violations:
                llm_metrics.record_guardrail_violation(
                    stage="input", violation_type=violation.value
                )

        if not input_result.passed:
            # Log the blocked input event
            guardrail_events.append(
                {
                    "stage": "input",
                    "passed": False,
                    "violations": [v.value for v in input_result.violations],
                    "details": input_result.violation_details,
                }
            )

            if METRICS_AVAILABLE:
                llm_metrics.record_rag_query(status="blocked_input")

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Query blocked by input guardrails",
                        "error_details": input_result.violation_details,
                        "guardrails": {
                            "input_validated": False,
                            "output_validated": None,
                            "violations": [v.value for v in input_result.violations],
                            "events": guardrail_events,
                        },
                        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ),
                400,
            )

        # Use sanitized input if PII was redacted
        processed_query = input_result.sanitized_input or query

        guardrail_events.append(
            {
                "stage": "input",
                "passed": True,
                "sanitized": input_result.sanitized_input is not None,
            }
        )

        # =================================================================
        # DOCUMENT RETRIEVAL
        # =================================================================
        retrieval_start = time.time()
        context_chunks = rag_retriever.query(processed_query)
        metrics_data["retrieval_duration"] = time.time() - retrieval_start

        # Track retrieval metrics
        if METRICS_AVAILABLE:
            llm_metrics.record_rag_retrieval(
                duration=metrics_data["retrieval_duration"],
                num_documents=len(context_chunks) if context_chunks else 0,
            )

        if not context_chunks:
            if METRICS_AVAILABLE:
                llm_metrics.record_rag_query(status="no_documents")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No relevant documents found. Ensure documents are ingested.",
                    }
                ),
                404,
            )

        # =================================================================
        # LLM RESPONSE GENERATION
        # =================================================================
        generation_start = time.time()
        result = rag_generator.generate(processed_query, context_chunks)
        metrics_data["generation_duration"] = time.time() - generation_start

        # Track generation metrics
        if METRICS_AVAILABLE:
            llm_metrics.record_rag_generation(
                duration=metrics_data["generation_duration"]
            )

            # Record token usage if available
            tokens_used = result.get("tokens_used")
            if tokens_used:
                # Estimate input/output split (rough: 70% input, 30% output for RAG)
                input_tokens = int(tokens_used * 0.7)
                output_tokens = tokens_used - input_tokens
                llm_metrics.record_tokens(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=result.get("model", model_name),
                )

        if not result.get("success"):
            if METRICS_AVAILABLE:
                llm_metrics.record_rag_query(status="generation_error")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": result.get("answer", "Generation failed"),
                        "guardrails": {
                            "input_validated": True,
                            "output_validated": None,
                            "events": guardrail_events,
                        },
                    }
                ),
                500,
            )

        # =================================================================
        # OUTPUT VALIDATION (Guardrails Layer 2)
        # =================================================================
        output_guard_start = time.time()
        output_result = rag_output_guard.validate(
            response=result.get("answer", ""),
            context_chunks=context_chunks,
            claimed_sources=result.get("sources_used", []),
            confidence=result.get("confidence"),
        )
        metrics_data["output_guard_duration"] = time.time() - output_guard_start
        rag_guardrail_logger.log_output_result(output_result)

        # Track output guardrail metrics
        if METRICS_AVAILABLE:
            llm_metrics.record_guardrail_check(
                stage="output",
                passed=output_result.passed,
                duration=metrics_data["output_guard_duration"],
            )
            llm_metrics.record_confidence(
                confidence=output_result.confidence_score,
                model=result.get("model", model_name),
            )
            # Record violations if any
            for violation in output_result.violations:
                llm_metrics.record_guardrail_violation(
                    stage="output", violation_type=violation.value
                )

        guardrail_events.append(
            {
                "stage": "output",
                "passed": output_result.passed,
                "confidence_score": output_result.confidence_score,
                "violations": (
                    [v.value for v in output_result.violations]
                    if output_result.violations
                    else []
                ),
            }
        )

        if not output_result.passed:
            if METRICS_AVAILABLE:
                llm_metrics.record_rag_query(status="blocked_output")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Response blocked by output guardrails",
                        "error_details": output_result.violation_details,
                        "guardrails": {
                            "input_validated": True,
                            "output_validated": False,
                            "violations": [v.value for v in output_result.violations],
                            "confidence_score": output_result.confidence_score,
                            "events": guardrail_events,
                        },
                        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ),
                400,
            )

        # Calculate total request duration
        total_duration = time.time() - request_start_time

        # Track successful request metrics
        if METRICS_AVAILABLE:
            print(f"RAG: Recording metrics with instance: {llm_metrics}")
            llm_metrics.record_rag_query(status="success")
            llm_metrics.record_latency(
                duration=total_duration,
                model=result.get("model", model_name),
                endpoint="rag_query",
                status="success",
            )

        # Build successful response with guardrail information
        response_data = {
            "success": True,
            "query": query,
            "answer": result.get("answer", ""),
            "sources_used": result.get("sources_used", []),
            "confidence": result.get("confidence", "unknown"),
            "context_chunks_retrieved": result.get("context_chunks", 0),
            "tokens_used": result.get("tokens_used"),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "guardrails": {
                "input_validated": True,
                "output_validated": True,
                "confidence_score": output_result.confidence_score,
                "events": guardrail_events,
            },
            "metrics": {
                "total_duration_ms": round(total_duration * 1000, 2),
                "retrieval_duration_ms": round(
                    metrics_data["retrieval_duration"] * 1000, 2
                ),
                "generation_duration_ms": round(
                    metrics_data["generation_duration"] * 1000, 2
                ),
                "input_guard_duration_ms": round(
                    metrics_data["input_guard_duration"] * 1000, 2
                ),
                "output_guard_duration_ms": round(
                    metrics_data["output_guard_duration"] * 1000, 2
                ),
            },
        }

        return jsonify(response_data)

    except Exception as e:
        # Track error metrics
        if METRICS_AVAILABLE:
            total_duration = time.time() - request_start_time
            llm_metrics.record_rag_query(status="error")
            llm_metrics.record_latency(
                duration=total_duration,
                model=model_name,
                endpoint="rag_query",
                status="error",
            )
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/rag/guardrails/stats")
def rag_guardrail_stats():
    """
    Get guardrail statistics and metrics.

    Returns:
        JSON with guardrail event counts and violation statistics
    """
    try:
        if not load_rag_components():
            return jsonify({"success": False, "error": "RAG system not available"}), 503

        stats = rag_guardrail_logger.get_stats()
        recent_events = rag_guardrail_logger.get_recent_events(10)

        return jsonify(
            {"success": True, "statistics": stats, "recent_events": recent_events}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/rag/sources")
def rag_sources():
    """
    Get list of indexed document sources.

    Returns:
        JSON with collection statistics and sources
    """
    try:
        # Load RAG components
        if not load_rag_components():
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "RAG system not available. Run 'make rag-ingest' first.",
                    }
                ),
                503,
            )

        stats = rag_retriever.get_collection_stats()

        return jsonify(
            {
                "success": True,
                "collection_name": stats["collection_name"],
                "document_count": stats["document_count"],
                "sources": stats["sources"],
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Load model and data on startup
    print("=" * 60)
    print("INITIALIZING AQI PREDICTION API")
    print("=" * 60)

    if load_model_and_scaler() and load_historical_data():
        print("\nAPI Ready!")
        print("=" * 60)
    else:
        print("\nAPI starting with limited functionality")
        print("   Model and data will be loaded on first request")
        print("=" * 60)

    # Disable debug mode in production (when running in container)
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8000, debug=debug_mode)
