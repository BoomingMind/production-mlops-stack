"""
Unit tests for the Flask AQI Prediction API
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def mock_model():
    """Mock ML model for testing"""
    model = Mock()
    # Return predictions for both aqi_index and Calculated_AQI
    model.predict = Mock(return_value=np.array([[45.5, 50.2]]))
    return model


@pytest.fixture
def mock_scaler():
    """Mock scaler for testing"""
    scaler = Mock()
    scaler.transform = Mock(return_value=np.array([[0.5] * 22]))
    return scaler


@pytest.fixture
def mock_df():
    """Mock historical dataframe"""
    # Create a simple dataframe with required columns
    dates = pd.date_range(start="2024-01-01", periods=100, freq="H")
    df = pd.DataFrame(
        {
            "year": dates.year,
            "month": dates.month,
            "day": dates.day,
            "hour": dates.hour,
            "temperature_2m": np.random.uniform(20, 35, 100),
            "relative_humidity_2m": np.random.uniform(40, 80, 100),
            "wind_speed_10m": np.random.uniform(0, 10, 100),
            "aqi_index": np.random.uniform(30, 80, 100),
            "Calculated_AQI": np.random.uniform(30, 80, 100),
        }
    )
    return df


@pytest.fixture
def client(mock_model, mock_scaler, mock_df):
    """Create test client with mocked dependencies"""
    # Mock S3 and model loading
    with patch("my_flask_app.app.boto3.client"), patch(
        "my_flask_app.app.joblib.load"
    ) as mock_joblib, patch("my_flask_app.app.pd.read_csv") as mock_read_csv:
        # Setup mocks
        mock_joblib.side_effect = [mock_model, mock_scaler]
        mock_read_csv.return_value = mock_df

        # Import after patching
        from my_flask_app.app import app as flask_app

        # Set global variables
        import my_flask_app.app as app_module

        app_module.model = mock_model
        app_module.scaler = mock_scaler
        app_module.df = mock_df
        app_module.features = [
            col
            for col in mock_df.columns
            if col not in ["aqi_index", "Calculated_AQI", "date"]
        ]

        flask_app.config["TESTING"] = True

        with flask_app.test_client() as test_client:
            yield test_client


def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert "message" in data
    assert data["message"] == "AQI Prediction API"
    assert "version" in data
    assert "endpoints" in data


def test_health_endpoint_healthy(client):
    """Test the health check endpoint when healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "components" in data
    assert data["components"]["model"] == "loaded"
    assert data["components"]["scaler"] == "loaded"
    assert data["components"]["data"] == "loaded"


def test_predict_current_endpoint(client, mock_model):
    """Test the current prediction endpoint"""
    response = client.get("/api/predict/current")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "prediction" in data
    assert "predicted_aqi_index" in data["prediction"]
    assert "predicted_calculated_aqi" in data["prediction"]
    assert "aqi_category" in data["prediction"]
    assert "datetime" in data["prediction"]

    # Verify model was called
    assert mock_model.predict.called


def test_predict_endpoint_default(client, mock_model):
    """Test the prediction endpoint with default parameters"""
    response = client.get("/api/predict")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "predictions" in data
    assert "prediction_info" in data
    assert "statistics" in data

    # Default is 3 days = 72 hours
    assert data["prediction_info"]["days"] == 3
    assert data["prediction_info"]["total_hours"] == 72
    assert len(data["predictions"]) == 72


def test_predict_endpoint_with_days(client):
    """Test the prediction endpoint with custom days parameter"""
    response = client.get("/api/predict?days=5")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["prediction_info"]["days"] == 5
    assert data["prediction_info"]["total_hours"] == 120
    assert len(data["predictions"]) == 120


def test_predict_hourly_endpoint_default(client):
    """Test the hourly prediction endpoint with default parameters"""
    response = client.get("/api/predict/hourly")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "predictions" in data

    # Default is 24 hours
    assert data["total_hours"] == 24
    assert len(data["predictions"]) == 24


def test_predict_hourly_endpoint_custom_hours(client):
    """Test the hourly prediction endpoint with custom hours"""
    response = client.get("/api/predict/hourly?hours=48")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["total_hours"] == 48
    assert len(data["predictions"]) == 48


def test_predict_daily_endpoint_default(client):
    """Test the daily summary endpoint with default parameters"""
    response = client.get("/api/predict/daily")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "daily_summary" in data

    # Default is 3 days
    assert data["days"] == 3
    assert len(data["daily_summary"]) == 3


def test_predict_daily_endpoint_custom_days(client):
    """Test the daily summary endpoint with custom days"""
    response = client.get("/api/predict/daily?days=7")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["days"] == 7
    assert len(data["daily_summary"]) == 7

    # Check structure of daily summary
    for day_data in data["daily_summary"]:
        assert "date" in day_data
        assert "aqi_index" in day_data
        assert "calculated_aqi" in day_data
        assert "aqi_category" in day_data
        assert "min" in day_data["aqi_index"]
        assert "max" in day_data["aqi_index"]
        assert "mean" in day_data["aqi_index"]


def test_aqi_category_good():
    """Test AQI category classification - Good"""
    from my_flask_app.app import get_aqi_category

    assert get_aqi_category(30) == "Good"
    assert get_aqi_category(50) == "Good"


def test_aqi_category_moderate():
    """Test AQI category classification - Moderate"""
    from my_flask_app.app import get_aqi_category

    assert get_aqi_category(51) == "Moderate"
    assert get_aqi_category(100) == "Moderate"


def test_aqi_category_unhealthy_sensitive():
    """Test AQI category classification - Unhealthy for Sensitive Groups"""
    from my_flask_app.app import get_aqi_category

    assert get_aqi_category(101) == "Unhealthy for Sensitive Groups"
    assert get_aqi_category(150) == "Unhealthy for Sensitive Groups"


def test_aqi_category_unhealthy():
    """Test AQI category classification - Unhealthy"""
    from my_flask_app.app import get_aqi_category

    assert get_aqi_category(151) == "Unhealthy"
    assert get_aqi_category(200) == "Unhealthy"


def test_aqi_category_very_unhealthy():
    """Test AQI category classification - Very Unhealthy"""
    from my_flask_app.app import get_aqi_category

    assert get_aqi_category(201) == "Very Unhealthy"
    assert get_aqi_category(300) == "Very Unhealthy"


def test_aqi_category_hazardous():
    """Test AQI category classification - Hazardous"""
    from my_flask_app.app import get_aqi_category

    assert get_aqi_category(301) == "Hazardous"
    assert get_aqi_category(500) == "Hazardous"


def test_health_endpoint_model_not_loaded():
    """Test health endpoint when model is not loaded"""
    with patch("my_flask_app.app.model", None), patch(
        "my_flask_app.app.scaler", None
    ), patch("my_flask_app.app.df", None), patch(
        "my_flask_app.app.load_model_and_scaler", return_value=False
    ), patch(
        "my_flask_app.app.load_historical_data", return_value=False
    ):
        from my_flask_app.app import app as flask_app

        flask_app.config["TESTING"] = True

        with flask_app.test_client() as test_client:
            response = test_client.get("/health")
            assert response.status_code == 503
            data = response.get_json()
            assert data["status"] == "unhealthy"


def test_predict_current_without_model():
    """Test prediction endpoint when model is not loaded"""
    with patch("my_flask_app.app.load_model_and_scaler", return_value=False), patch(
        "my_flask_app.app.load_historical_data", return_value=False
    ):
        from my_flask_app.app import app as flask_app

        flask_app.config["TESTING"] = True

        with flask_app.test_client() as test_client:
            response = test_client.get("/api/predict/current")
            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data


# Additional coverage tests
def test_predict_endpoint_min_days(client):
    """Test prediction endpoint with minimum days (1)"""
    response = client.get("/api/predict?days=0")  # Should clamp to 1
    assert response.status_code == 200
    data = response.get_json()
    assert data["prediction_info"]["days"] == 1


def test_predict_endpoint_max_days(client):
    """Test prediction endpoint with maximum days (7)"""
    response = client.get("/api/predict?days=10")  # Should clamp to 7
    assert response.status_code == 200
    data = response.get_json()
    assert data["prediction_info"]["days"] == 7


def test_predict_hourly_min_hours(client):
    """Test hourly prediction with minimum hours"""
    response = client.get("/api/predict/hourly?hours=0")  # Should clamp to 1
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_hours"] == 1


def test_predict_hourly_max_hours(client):
    """Test hourly prediction with maximum hours"""
    response = client.get("/api/predict/hourly?hours=200")  # Should clamp to 168
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_hours"] == 168
