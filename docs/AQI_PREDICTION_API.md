# AQI Prediction API Documentation

## Overview
This Flask API provides endpoints to fetch Air Quality Index (AQI) predictions for future time periods using a pre-trained machine learning model stored in AWS S3.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. AWS credentials are managed via environment variables.

---

## Endpoints

### 1. Health Check
Check the API health status and component availability.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-02 10:30:00",
  "components": {
    "model": "loaded",
    "scaler": "loaded",
    "data": "loaded"
  }
}
```

**Status Codes:**
- `200`: Healthy - all components loaded
- `503`: Unhealthy - one or more components failed to load

---

### 2. Home / API Info
Get information about available endpoints.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "AQI Prediction API",
  "version": "1.0",
  "endpoints": {
    "/health": "Health check endpoint",
    "/api/predict": "Get AQI predictions (query params: days=1-7)",
    "/api/predict/hourly": "Get hourly predictions (query params: hours=1-168)",
    "/api/predict/daily": "Get daily summary predictions (query params: days=1-7)",
    "/api/predict/current": "Get prediction for the next hour"
  }
}
```

---

### 3. Get Predictions
Get detailed hourly AQI predictions for the next N days.

**Endpoint:** `GET /api/predict`

**Query Parameters:**
- `days` (optional): Number of days to predict (1-7, default: 3)

**Example Request:**
```bash
curl "http://localhost:8000/api/predict?days=3"
```

**Response:**
```json
{
  "success": true,
  "prediction_info": {
    "days": 3,
    "total_hours": 72,
    "start_datetime": "2025-12-02 11:00",
    "end_datetime": "2025-12-05 10:00",
    "generated_at": "2025-12-02 10:30:45"
  },
  "statistics": {
    "average_aqi": 45.67,
    "min_aqi": 28.34,
    "max_aqi": 89.12,
    "std_deviation": 12.45
  },
  "predictions": [
    {
      "datetime": "2025-12-02 11:00",
      "date": "2025-12-02",
      "hour": 11,
      "predicted_aqi_index": 42.50,
      "predicted_calculated_aqi": 45.30,
      "aqi_category": "Good"
    },
    // ... more predictions
  ]
}
```

**AQI Categories:**
- `Good`: 0-50
- `Moderate`: 51-100
- `Unhealthy for Sensitive Groups`: 101-150
- `Unhealthy`: 151-200
- `Very Unhealthy`: 201-300
- `Hazardous`: 301+

---

### 4. Get Hourly Predictions
Get hourly AQI predictions for a specific number of hours.

**Endpoint:** `GET /api/predict/hourly`

**Query Parameters:**
- `hours` (optional): Number of hours to predict (1-168, default: 24)

**Example Request:**
```bash
curl "http://localhost:8000/api/predict/hourly?hours=48"
```

**Response:**
```json
{
  "success": true,
  "total_hours": 48,
  "predictions": [
    {
      "datetime": "2025-12-02 11:00",
      "hour": 11,
      "predicted_aqi_index": 42.50,
      "predicted_calculated_aqi": 45.30,
      "aqi_category": "Good"
    },
    // ... more predictions
  ]
}
```

---

### 5. Get Daily Summary
Get daily summary statistics of AQI predictions.

**Endpoint:** `GET /api/predict/daily`

**Query Parameters:**
- `days` (optional): Number of days to predict (1-7, default: 3)

**Example Request:**
```bash
curl "http://localhost:8000/api/predict/daily?days=5"
```

**Response:**
```json
{
  "success": true,
  "days": 5,
  "daily_summary": [
    {
      "date": "2025-12-02",
      "aqi_index": {
        "min": 35.20,
        "max": 68.50,
        "mean": 48.30
      },
      "calculated_aqi": {
        "min": 38.10,
        "max": 72.40,
        "mean": 51.20
      },
      "aqi_category": "Good"
    },
    // ... more daily summaries
  ]
}
```

---

### 6. Get Current Hour Prediction
Get AQI prediction for the next/current hour.

**Endpoint:** `GET /api/predict/current`

**Example Request:**
```bash
curl "http://localhost:8000/api/predict/current"
```

**Response:**
```json
{
  "success": true,
  "prediction": {
    "datetime": "2025-12-02 11:00",
    "predicted_aqi_index": 42.50,
    "predicted_calculated_aqi": 45.30,
    "aqi_category": "Good",
    "generated_at": "2025-12-02 10:30:45"
  }
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

**Common Status Codes:**
- `200`: Success
- `500`: Internal Server Error (model loading failure, prediction error, etc.)
- `503`: Service Unavailable (health check failure)

---

## Environment Variables

The API requires the following environment variables to be set:

```bash
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_DEFAULT_REGION=eu-north-1
```

These should be configured in a `.env` file in the project root.

---

## Running the API

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file with AWS credentials
echo "AWS_ACCESS_KEY_ID=your-key" > .env
echo "AWS_SECRET_ACCESS_KEY=your-secret" >> .env
echo "AWS_DEFAULT_REGION=eu-north-1" >> .env
```

### Start the Server

```bash
# Development mode
python my_flask_app/app.py

# Or using Flask CLI
export FLASK_APP=my_flask_app/app.py
flask run --host=0.0.0.0 --port=8000
```

The API will be available at `http://localhost:8000`

---

## Example Usage with Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Get 3-day predictions
response = requests.get("http://localhost:8000/api/predict?days=3")
data = response.json()
print(f"Average AQI: {data['statistics']['average_aqi']}")

# Get current hour prediction
response = requests.get("http://localhost:8000/api/predict/current")
prediction = response.json()['prediction']
print(f"Next hour AQI: {prediction['predicted_aqi_index']} ({prediction['aqi_category']})")

# Get daily summary
response = requests.get("http://localhost:8000/api/predict/daily?days=5")
for day in response.json()['daily_summary']:
    print(f"{day['date']}: {day['aqi_index']['mean']} ({day['aqi_category']})")
```

---

## Example Usage with cURL

```bash
# Health check
curl http://localhost:8000/health

# Get 3-day predictions
curl "http://localhost:8000/api/predict?days=3"

# Get 48-hour predictions
curl "http://localhost:8000/api/predict/hourly?hours=48"

# Get daily summary for 5 days
curl "http://localhost:8000/api/predict/daily?days=5"

# Get current hour prediction
curl http://localhost:8000/api/predict/current
```

---

## Model Information

The API uses a pre-trained Random Forest model that:
- Predicts both `aqi_index` and `Calculated_AQI`
- Uses historical weather and air quality data for feature engineering
- Applies temporal patterns and variations for realistic predictions
- Is stored in AWS S3 bucket: `my-feature-store-data`

**Model artifacts:**
- `models/best_model.pkl` - Trained Random Forest model
- `models/scaler.pkl` - StandardScaler for feature scaling
- `models/best_model_metadata.json` - Model metadata and versioning
- `pipeline-data/data.csv` - Historical data for feature engineering

---

## Notes

- Predictions are generated using historical patterns and hourly averages
- The model includes temporal variations (±3%) for realistic forecasting
- Maximum prediction horizon is 7 days (168 hours)
- All timestamps are in the server's local timezone
- The API loads model and data on startup for optimal performance
- If initial loading fails, resources are loaded on first request

---

## Testing

Test the API using the provided test files:

```bash
# Run API tests
pytest tests/test_api.py

# Run additional API tests
pytest tests/test_api_extra.py
```

---

## Support

For issues or questions:
1. Check the health endpoint: `/health`
2. Review server logs for detailed error messages
3. Ensure AWS credentials are correctly configured
4. Verify the model has been trained using `03_model_train.ipynb`
