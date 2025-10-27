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

# ==================== GLOBAL VARIABLES ====================
model = None
scaler = None
model_version = "v1.0"
load_dotenv()

# ==================== LIFESPAN EVENT ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown"""
    # Startup
    start_time = time.time()
    global model, scaler, model_version
    
    try:
        bucket_name = 'my-feature-store-data'
        model_key = 'models/best_model.pkl'
        scaler_key = 'models/scaler.pkl'
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Download model
        print("📥 Loading model from S3...")
        model_buffer = BytesIO()
        s3.download_fileobj(bucket_name, model_key, model_buffer)
        model_buffer.seek(0)
        model = joblib.load(model_buffer)
        print("✅ Model loaded successfully")
        
        # Download scaler
        print("📥 Loading scaler from S3...")
        scaler_buffer = BytesIO()
        s3.download_fileobj(bucket_name, scaler_key, scaler_buffer)
        scaler_buffer.seek(0)
        scaler = joblib.load(scaler_buffer)
        print("✅ Scaler loaded successfully")
        
        load_duration = time.time() - start_time
        model_load_time.set(load_duration)
        model_version_gauge.set(1.0)
        
        print(f"\n🚀 Application startup complete in {load_duration:.2f}s")
        print(f"   Model type: {type(model).__name__}")
        print(f"   Model version: {model_version}")
        
    except Exception as e:
        error_counter.labels(error_type='model_loading').inc()
        print(f"❌ Error loading model/scaler: {e}")
        print("⚠️  WARNING: Model not loaded. API will return errors for predictions.")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")

# Initialize FastAPI app
app = FastAPI(
    title="AQI Weather Prediction API",
    description="MLOps API for predicting AQI based on weather parameters",
    version="1.0.0",
    lifespan=lifespan
)

# ==================== CORS MIDDLEWARE ====================
# Add CORS middleware to allow frontend applications to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PROMETHEUS METRICS ====================
# Counter: Total number of predictions made
prediction_counter = Counter(
    'prediction_requests_total',
    'Total number of prediction requests',
    ['model_version', 'status']
)

# Histogram: Prediction latency
prediction_latency = Histogram(
    'prediction_duration_seconds',
    'Time spent processing prediction request',
    ['model_version']
)

# Gauge: Model loading time
model_load_time = Gauge(
    'model_load_seconds',
    'Time taken to load the model'
)

# Gauge: Current model version
model_version_gauge = Gauge(
    'current_model_version',
    'Current model version in use'
)

# Counter: Errors
error_counter = Counter(
    'api_errors_total',
    'Total number of API errors',
    ['error_type']
)

# Histogram: HTTP request duration
http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'status_code']
)

# ==================== PYDANTIC MODELS ====================
class PredictionInput(BaseModel):
    """Input schema for prediction endpoint"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "co": 250.5,
                "no": 0.5,
                "no2": 12.3,
                "o3": 45.6,
                "so2": 7.8,
                "pm2_5": 25.4,
                "pm10": 40.2,
                "nh3": 3.2,
                "temperature_2m": 28.5,
                "relative_humidity_2m": 65.0,
                "precipitation": 0.0,
                "wind_speed_10m": 5.2,
                "wind_direction_10m": 180.0,
                "surface_pressure": 1013.25,
                "dew_point_2m": 20.3,
                "apparent_temperature": 30.1,
                "shortwave_radiation": 500.0,
                "et0_fao_evapotranspiration": 0.25,
                "year": 2025,
                "month": 10,
                "day": 22,
                "hour": 14
            }
        }
    )
    
    co: float
    no: float
    no2: float
    o3: float
    so2: float
    pm2_5: float
    pm10: float
    nh3: float
    temperature_2m: float
    relative_humidity_2m: float
    precipitation: float
    wind_speed_10m: float
    wind_direction_10m: float
    surface_pressure: float
    dew_point_2m: float
    apparent_temperature: float
    shortwave_radiation: float
    et0_fao_evapotranspiration: float
    year: int
    month: int
    day: int
    hour: int

class PredictionOutput(BaseModel):
    """Output schema for prediction endpoint"""
    aqi_index: float
    calculated_aqi: float
    prediction_time: str
    model_version: str

class HourlyPrediction(BaseModel):
    """Schema for a single hourly prediction"""
    datetime: str
    date: str
    hour: int
    predicted_aqi_index: float
    predicted_calculated_aqi: float
    aqi_category: str

class PredictionResultsResponse(BaseModel):
    """Output schema for fetching prediction results"""
    predictions: List[HourlyPrediction]
    total_hours: int
    prediction_period: Dict[str, str]
    daily_summary: Dict[str, Dict[str, float]]
    metadata: Dict[str, Any]  # Allow any type for metadata values

# ==================== ENDPOINTS ====================
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

@app.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    """
    Predict AQI based on input weather parameters
    """
    start_time = time.time()
    
    try:
        # Check if model and scaler are loaded
        if model is None or scaler is None:
            error_counter.labels(error_type='model_not_loaded').inc()
            raise HTTPException(status_code=503, detail="Model or scaler not loaded")
        
        # Prepare input features
        features = np.array([[
            input_data.co, input_data.no, input_data.no2, input_data.o3,
            input_data.so2, input_data.pm2_5, input_data.pm10, input_data.nh3,
            input_data.temperature_2m, input_data.relative_humidity_2m,
            input_data.precipitation, input_data.wind_speed_10m,
            input_data.wind_direction_10m, input_data.surface_pressure,
            input_data.dew_point_2m, input_data.apparent_temperature,
            input_data.shortwave_radiation, input_data.et0_fao_evapotranspiration,
            input_data.year, input_data.month, input_data.day, input_data.hour
        ]])
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Make prediction
        prediction = model.predict(features_scaled)
        
        # Record metrics
        duration = time.time() - start_time
        prediction_latency.labels(model_version=model_version).observe(duration)
        prediction_counter.labels(model_version=model_version, status='success').inc()
        
        # Prepare response
        return PredictionOutput(
            aqi_index=float(prediction[0][0]),
            calculated_aqi=float(prediction[0][1]),
            prediction_time=datetime.now().isoformat(),
            model_version=model_version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_counter.labels(error_type='prediction_error').inc()
        prediction_counter.labels(model_version=model_version, status='error').inc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    Returns metrics in Prometheus format
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/model/info")
async def model_info():
    """Get information about the current model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_version": model_version,
        "model_type": type(model).__name__,
        "loaded": True,
        "features_expected": 22
    }

@app.get("/predictions/latest", response_model=PredictionResultsResponse)
async def get_latest_predictions():
    """
    Fetch the latest prediction results from S3
    Returns hourly predictions for the next 3 days
    """
    try:
        import pandas as pd
        import json
        
        bucket_name = 'my-feature-store-data'
        predictions_key = 'predictions/hourly_predictions_next_3_days.csv'
        daily_summary_key = 'predictions/daily_summary_next_3_days.csv'
        metadata_key = 'predictions/prediction_metadata.json'
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Load hourly predictions
        try:
            predictions_obj = s3.get_object(Bucket=bucket_name, Key=predictions_key)
            predictions_df = pd.read_csv(BytesIO(predictions_obj['Body'].read()))
        except Exception as e:
            error_counter.labels(error_type='predictions_not_found').inc()
            raise HTTPException(
                status_code=404, 
                detail=f"Prediction results not found. Please run the prediction notebook first. Error: {str(e)}"
            )
        
        # Load daily summary (optional - we can compute from hourly data if needed)
        daily_summary = {}
        try:
            # Compute daily summary from hourly predictions instead of loading from file
            predictions_df['Date_only'] = predictions_df['Date']
            for date in predictions_df['Date_only'].unique():
                day_data = predictions_df[predictions_df['Date_only'] == date]
                daily_summary[str(date)] = {
                    'aqi_index_min': float(day_data['Predicted_AQI_Index'].min()),
                    'aqi_index_max': float(day_data['Predicted_AQI_Index'].max()),
                    'aqi_index_mean': float(day_data['Predicted_AQI_Index'].mean()),
                    'calculated_aqi_min': float(day_data['Predicted_Calculated_AQI'].min()),
                    'calculated_aqi_max': float(day_data['Predicted_Calculated_AQI'].max()),
                    'calculated_aqi_mean': float(day_data['Predicted_Calculated_AQI'].mean())
                }
        except Exception as e:
            print(f"Warning: Could not compute daily summary: {e}")
        
        # Load metadata
        try:
            metadata_obj = s3.get_object(Bucket=bucket_name, Key=metadata_key)
            metadata_content = metadata_obj['Body'].read().decode('utf-8')
            metadata = json.loads(metadata_content)
        except Exception as e:
            metadata = {}
            print(f"Warning: Could not load metadata: {e}")
        
        # Convert predictions to list of dicts
        hourly_predictions = []
        for _, row in predictions_df.iterrows():
            hourly_predictions.append(HourlyPrediction(
                datetime=row['DateTime'],
                date=row['Date'],
                hour=int(row['Hour']),
                predicted_aqi_index=float(row['Predicted_AQI_Index']),
                predicted_calculated_aqi=float(row['Predicted_Calculated_AQI']),
                aqi_category=row['AQI_Category']
            ))
        
        # Prepare prediction period info
        prediction_period = {
            'start': predictions_df['DateTime'].iloc[0] if len(predictions_df) > 0 else '',
            'end': predictions_df['DateTime'].iloc[-1] if len(predictions_df) > 0 else ''
        }
        
        return PredictionResultsResponse(
            predictions=hourly_predictions,
            total_hours=len(hourly_predictions),
            prediction_period=prediction_period,
            daily_summary=daily_summary,
            metadata=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_counter.labels(error_type='fetch_predictions_error').inc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictions: {str(e)}")

@app.get("/predictions/by-date/{date}")
async def get_predictions_by_date(date: str):
    """
    Get predictions for a specific date (format: YYYY-MM-DD)
    Returns 24 hourly predictions for the specified date
    """
    try:
        import pandas as pd
        
        bucket_name = 'my-feature-store-data'
        predictions_key = 'predictions/hourly_predictions_next_3_days.csv'
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Load predictions
        predictions_obj = s3.get_object(Bucket=bucket_name, Key=predictions_key)
        predictions_df = pd.read_csv(BytesIO(predictions_obj['Body'].read()))
        
        # Filter by date
        date_predictions = predictions_df[predictions_df['Date'] == date]
        
        if len(date_predictions) == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"No predictions found for date: {date}. Available dates: {predictions_df['Date'].unique().tolist()}"
            )
        
        # Convert to list of dicts
        results = []
        for _, row in date_predictions.iterrows():
            results.append({
                'datetime': row['DateTime'],
                'hour': int(row['Hour']),
                'predicted_aqi_index': float(row['Predicted_AQI_Index']),
                'predicted_calculated_aqi': float(row['Predicted_Calculated_AQI']),
                'aqi_category': row['AQI_Category']
            })
        
        return {
            'date': date,
            'total_hours': len(results),
            'predictions': results,
            'summary': {
                'min_aqi': float(date_predictions['Predicted_AQI_Index'].min()),
                'max_aqi': float(date_predictions['Predicted_AQI_Index'].max()),
                'avg_aqi': float(date_predictions['Predicted_AQI_Index'].mean())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_counter.labels(error_type='fetch_date_predictions_error').inc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictions for date: {str(e)}")

@app.get("/predictions/summary")
async def get_predictions_summary():
    """
    Get a quick summary of predictions including:
    - Overall statistics
    - Daily breakdown
    - AQI category distribution
    """
    try:
        import pandas as pd
        
        bucket_name = 'my-feature-store-data'
        predictions_key = 'predictions/hourly_predictions_next_3_days.csv'
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Load predictions
        predictions_obj = s3.get_object(Bucket=bucket_name, Key=predictions_key)
        predictions_df = pd.read_csv(BytesIO(predictions_obj['Body'].read()))
        
        # Overall statistics
        overall_stats = {
            'total_hours': len(predictions_df),
            'avg_aqi': float(predictions_df['Predicted_AQI_Index'].mean()),
            'min_aqi': float(predictions_df['Predicted_AQI_Index'].min()),
            'max_aqi': float(predictions_df['Predicted_AQI_Index'].max()),
            'std_aqi': float(predictions_df['Predicted_AQI_Index'].std())
        }
        
        # Daily breakdown
        daily_stats = {}
        for date in predictions_df['Date'].unique():
            day_data = predictions_df[predictions_df['Date'] == date]
            daily_stats[date] = {
                'avg_aqi': float(day_data['Predicted_AQI_Index'].mean()),
                'min_aqi': float(day_data['Predicted_AQI_Index'].min()),
                'max_aqi': float(day_data['Predicted_AQI_Index'].max()),
                'hours': len(day_data)
            }
        
        # AQI category distribution
        category_dist = predictions_df['AQI_Category'].value_counts().to_dict()
        category_percentages = {}
        for category, count in category_dist.items():
            category_percentages[category] = {
                'count': int(count),
                'percentage': float(count / len(predictions_df) * 100)
            }
        
        # Best and worst hours
        best_hour = predictions_df.loc[predictions_df['Predicted_AQI_Index'].idxmin()]
        worst_hour = predictions_df.loc[predictions_df['Predicted_AQI_Index'].idxmax()]
        
        return {
            'overall_statistics': overall_stats,
            'daily_breakdown': daily_stats,
            'category_distribution': category_percentages,
            'best_air_quality': {
                'datetime': best_hour['DateTime'],
                'aqi': float(best_hour['Predicted_AQI_Index']),
                'category': best_hour['AQI_Category']
            },
            'worst_air_quality': {
                'datetime': worst_hour['DateTime'],
                'aqi': float(worst_hour['Predicted_AQI_Index']),
                'category': worst_hour['AQI_Category']
            }
        }
        
    except Exception as e:
        error_counter.labels(error_type='fetch_summary_error').inc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictions summary: {str(e)}")

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
