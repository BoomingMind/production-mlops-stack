# AQI Prediction API - Endpoints Documentation

## Overview
FastAPI application for AQI (Air Quality Index) prediction with integrated Prometheus metrics and prediction results fetching capabilities.

## Base URL
```
http://localhost:8000
```

---

## Endpoints

### 1. Root Endpoint
**GET** `/`

Returns API information and available endpoints.

**Response Example:**
```json
{
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
```

---

### 2. Health Check
**GET** `/health`

Check API health status and model loading state.

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T14:30:00",
  "model_loaded": true,
  "model_version": "v1.0"
}
```

---

### 3. Single Prediction
**POST** `/predict`

Make a single AQI prediction based on input weather parameters.

**Request Body:**
```json
{
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
  "day": 23,
  "hour": 14
}
```

**Response Example:**
```json
{
  "aqi_index": 75.23,
  "calculated_aqi": 68.45,
  "prediction_time": "2025-10-23T14:30:00",
  "model_version": "v1.0"
}
```

---

### 4. Get Latest Predictions (NEW)
**GET** `/predictions/latest`

Fetch all 72 hourly predictions for the next 3 days from S3.

**Response Example:**
```json
{
  "predictions": [
    {
      "datetime": "2025-10-24 00:00",
      "date": "2025-10-24",
      "hour": 0,
      "predicted_aqi_index": 65.23,
      "predicted_calculated_aqi": 58.45,
      "aqi_category": "Moderate"
    },
    // ... 71 more hourly predictions
  ],
  "total_hours": 72,
  "prediction_period": {
    "start": "2025-10-24 00:00",
    "end": "2025-10-26 23:00"
  },
  "daily_summary": {
    "2025-10-24": {
      "aqi_index_min": 45.12,
      "aqi_index_max": 89.34,
      "aqi_index_mean": 67.23,
      "calculated_aqi_min": 42.15,
      "calculated_aqi_max": 85.67,
      "calculated_aqi_mean": 63.89
    },
    // ... summaries for other days
  },
  "metadata": {
    "prediction_timestamp": "2025-10-23 14:00:00",
    "model_type": "RandomForestRegressor",
    "features_used": 22
  }
}
```

**Use Cases:**
- Display full 3-day forecast
- Generate visualizations
- Export predictions to other systems

---

### 5. Get Predictions by Date (NEW)
**GET** `/predictions/by-date/{date}`

Get all 24 hourly predictions for a specific date.

**Parameters:**
- `date` (path parameter): Date in format `YYYY-MM-DD`

**Example Request:**
```
GET /predictions/by-date/2025-10-24
```

**Response Example:**
```json
{
  "date": "2025-10-24",
  "total_hours": 24,
  "predictions": [
    {
      "datetime": "2025-10-24 00:00",
      "hour": 0,
      "predicted_aqi_index": 65.23,
      "predicted_calculated_aqi": 58.45,
      "aqi_category": "Moderate"
    },
    // ... 23 more hourly predictions
  ],
  "summary": {
    "min_aqi": 45.12,
    "max_aqi": 89.34,
    "avg_aqi": 67.23
  }
}
```

**Use Cases:**
- Display single-day forecast
- Plan activities for a specific date
- Compare predictions across days

---

### 6. Get Predictions Summary (NEW)
**GET** `/predictions/summary`

Get a comprehensive summary of all predictions including statistics and insights.

**Response Example:**
```json
{
  "overall_statistics": {
    "total_hours": 72,
    "avg_aqi": 67.23,
    "min_aqi": 45.12,
    "max_aqi": 95.67,
    "std_aqi": 12.34
  },
  "daily_breakdown": {
    "2025-10-24": {
      "avg_aqi": 65.23,
      "min_aqi": 45.12,
      "max_aqi": 85.34,
      "hours": 24
    },
    // ... other days
  },
  "category_distribution": {
    "Good": {
      "count": 12,
      "percentage": 16.67
    },
    "Moderate": {
      "count": 48,
      "percentage": 66.67
    },
    "Unhealthy for Sensitive Groups": {
      "count": 12,
      "percentage": 16.67
    }
  },
  "best_air_quality": {
    "datetime": "2025-10-24 05:00",
    "aqi": 45.12,
    "category": "Good"
  },
  "worst_air_quality": {
    "datetime": "2025-10-25 15:00",
    "aqi": 95.67,
    "category": "Moderate"
  }
}
```

**Use Cases:**
- Dashboard overview
- Quick insights for users
- Planning recommendations

---

### 7. Model Information
**GET** `/model/info`

Get information about the loaded model.

**Response Example:**
```json
{
  "model_version": "v1.0",
  "model_type": "RandomForestRegressor",
  "loaded": true,
  "features_expected": 22
}
```

---

### 8. Prometheus Metrics
**GET** `/metrics`

Get Prometheus-formatted metrics for monitoring.

**Response:** Plain text in Prometheus format

**Metrics Tracked:**
- `prediction_requests_total` - Total prediction requests
- `prediction_duration_seconds` - Prediction latency
- `model_load_seconds` - Model loading time
- `api_errors_total` - Total API errors
- `http_request_duration_seconds` - HTTP request duration

---

## AQI Categories

| AQI Range | Category |
|-----------|----------|
| 0-50 | Good |
| 51-100 | Moderate |
| 101-150 | Unhealthy for Sensitive Groups |
| 151-200 | Unhealthy |
| 201-300 | Very Unhealthy |
| 301+ | Hazardous |

---

## Running the API

### 1. Start the API Server
```bash
# From project root
python src/api/main.py

# Or with uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Test the API
```bash
# Run test suite
python test_prediction_api.py
```

---

## Prerequisites

### Environment Variables
Create a `.env` file with:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### S3 Bucket Structure
```
my-feature-store-data/
├── models/
│   ├── best_model.pkl
│   ├── scaler.pkl
│   └── best_model_metadata.json
├── predictions/
│   ├── hourly_predictions_next_3_days.csv
│   ├── daily_summary_next_3_days.csv
│   └── prediction_metadata.json
└── pipeline-data/
    └── data.csv
```

### Generate Predictions
Before using prediction endpoints, run:
```bash
# Execute prediction notebook to generate results
jupyter notebook notebooks/05_prediction.ipynb
```

---

## Error Handling

### Common Errors

**404 - Predictions Not Found**
```json
{
  "detail": "Prediction results not found. Please run the prediction notebook first."
}
```
**Solution:** Run `05_prediction.ipynb` notebook to generate predictions.

**503 - Model Not Loaded**
```json
{
  "detail": "Model not loaded"
}
```
**Solution:** Ensure model exists in S3 and AWS credentials are correct.

**500 - Internal Server Error**
```json
{
  "detail": "Failed to fetch predictions: [error details]"
}
```
**Solution:** Check S3 connectivity and file formats.

---

## Example Usage

### Python
```python
import requests

# Get latest predictions
response = requests.get("http://localhost:8000/predictions/latest")
data = response.json()

print(f"Total predictions: {data['total_hours']}")
for pred in data['predictions'][:5]:
    print(f"{pred['datetime']}: AQI={pred['predicted_aqi_index']:.1f}")
```

### cURL
```bash
# Get predictions summary
curl http://localhost:8000/predictions/summary

# Get predictions for specific date
curl http://localhost:8000/predictions/by-date/2025-10-24

# Make single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"co": 250.5, "no": 0.5, ...}'
```

### JavaScript/TypeScript
```javascript
// Fetch latest predictions
fetch('http://localhost:8000/predictions/latest')
  .then(response => response.json())
  .then(data => {
    console.log(`Total hours: ${data.total_hours}`);
    data.predictions.forEach(pred => {
      console.log(`${pred.datetime}: AQI=${pred.predicted_aqi_index}`);
    });
  });
```

---

## Monitoring

Access Prometheus metrics at `/metrics` endpoint to monitor:
- Request rates
- Error rates
- Latency percentiles
- Model performance

Integrate with Grafana for visualization (see `monitoring/` directory).