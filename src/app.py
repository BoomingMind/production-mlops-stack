from flask import Flask, jsonify, request
import os
import boto3
import joblib
import numpy as np
import pandas as pd
import json
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RAG imports (lazy loading to avoid startup issues)
rag_retriever = None
rag_generator = None

app = Flask(__name__)

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
        print("✅ Model loaded successfully")

        # Load scaler
        print(f"Loading scaler from S3: {bucket_name}/{scaler_key}")
        scaler_buffer = BytesIO()
        s3.download_fileobj(Bucket=bucket_name, Key=scaler_key, Fileobj=scaler_buffer)
        scaler_buffer.seek(0)
        scaler = joblib.load(scaler_buffer)
        print("✅ Scaler loaded successfully")

        return True
    except Exception as e:
        print(f"❌ ERROR: Could not load model or scaler from S3: {str(e)}")
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

        print(f"✅ Historical data loaded: {len(df)} rows, {len(features)} features")
        return True
    except Exception as e:
        print(f"❌ ERROR: Could not load historical data from S3: {str(e)}")
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
    return jsonify(
        {
            "message": "AQI Prediction API",
            "version": "2.0",
            "endpoints": {
                "/health": "Health check endpoint",
                "/api/predict": "Get AQI predictions (query params: days=1-7)",
                "/api/predict/hourly": "Get hourly predictions (query params: hours=1-168)",
                "/api/predict/daily": "Get daily summary predictions (query params: days=1-7)",
                "/api/predict/current": "Get prediction for the next hour",
                "/api/rag/query": "POST - Ask questions about air quality (RAG)",
                "/api/rag/sources": "GET - List indexed knowledge sources",
            },
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
                    "aqi_category": get_aqi_category(avg_aqi)
                    if not np.isnan(avg_aqi)
                    else None,
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
    """Lazy load RAG components."""
    global rag_retriever, rag_generator
    
    if rag_retriever is None or rag_generator is None:
        try:
            # Add project root to path for imports
            import sys
            from pathlib import Path
            
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from src.rag.retriever import DocumentRetriever
            from src.rag.generator import ResponseGenerator
            
            rag_retriever = DocumentRetriever()
            rag_generator = ResponseGenerator()
            return True
        except Exception as e:
            print(f"❌ Failed to load RAG components: {e}")
            import traceback
            traceback.print_exc()
            return False
    return True


@app.route("/api/rag/query", methods=["POST"])
def rag_query():
    """
    Query the RAG system with a question about air quality.
    
    Request body:
        {
            "query": "What precautions should I take when AQI is 150?"
        }
    
    Returns:
        JSON response with answer and sources
    """
    try:
        # Load RAG components
        if not load_rag_components():
            return jsonify({
                "success": False,
                "error": "RAG system not available. Run 'make rag-ingest' first."
            }), 503
        
        # Get query from request
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'query' in request body"
            }), 400
        
        query = data["query"]
        
        # Retrieve relevant documents
        context_chunks = rag_retriever.query(query)
        
        if not context_chunks:
            return jsonify({
                "success": False,
                "error": "No relevant documents found. Ensure documents are ingested."
            }), 404
        
        # Generate response
        result = rag_generator.generate(query, context_chunks)
        
        return jsonify({
            "success": result.get("success", False),
            "query": query,
            "answer": result.get("answer", ""),
            "sources_used": result.get("sources_used", []),
            "confidence": result.get("confidence", "unknown"),
            "context_chunks_retrieved": result.get("context_chunks", 0),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
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
            return jsonify({
                "success": False,
                "error": "RAG system not available. Run 'make rag-ingest' first."
            }), 503
        
        stats = rag_retriever.get_collection_stats()
        
        return jsonify({
            "success": True,
            "collection_name": stats["collection_name"],
            "document_count": stats["document_count"],
            "sources": stats["sources"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Load model and data on startup
    print("=" * 60)
    print("INITIALIZING AQI PREDICTION API")
    print("=" * 60)

    if load_model_and_scaler() and load_historical_data():
        print("\n✅ API Ready!")
        print("=" * 60)
    else:
        print("\n⚠️  API starting with limited functionality")
        print("   Model and data will be loaded on first request")
        print("=" * 60)

    # Disable debug mode in production (when running in container)
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8000, debug=debug_mode)
