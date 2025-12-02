"""
Unit tests for the Flask AQI Prediction API
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock boto3 before importing the app module
sys.modules["boto3"] = MagicMock()

import my_flask_app.app as app_module  # noqa: E402


@pytest.fixture
def mock_model():
    """Mock ML model for testing"""
    model = Mock()

    # Return predictions for both aqi_index and Calculated_AQI
    # Use side_effect to return correct shape based on input
    def predict_side_effect(X):
        num_samples = X.shape[0]
        return np.array([[45.5, 50.2]] * num_samples)

    model.predict = Mock(side_effect=predict_side_effect)
    return model


@pytest.fixture
def mock_scaler():
    """Mock scaler for testing"""
    scaler = Mock()

    # Use side_effect to return correct shape based on input
    def transform_side_effect(X):
        if hasattr(X, "shape"):
            return np.array([[0.5] * X.shape[1]] * X.shape[0])
        return np.array([[0.5] * 22])

    scaler.transform = Mock(side_effect=transform_side_effect)
    return scaler


@pytest.fixture
def mock_df():
    """Mock historical dataframe with all required columns"""
    # Create a simple dataframe with all required columns including weather features
    np.random.seed(42)  # For reproducibility
    dates = pd.date_range(start="2024-01-01", periods=100, freq="h")
    df = pd.DataFrame(
        {
            "year": dates.year,
            "month": dates.month,
            "day": dates.day,
            "hour": dates.hour,
            "temperature_2m": np.random.uniform(20, 35, 100),
            "relative_humidity_2m": np.random.uniform(40, 80, 100),
            "dew_point_2m": np.random.uniform(10, 25, 100),
            "wind_speed_10m": np.random.uniform(0, 10, 100),
            "wind_direction_10m": np.random.uniform(0, 360, 100),
            "surface_pressure": np.random.uniform(1000, 1020, 100),
            "cloud_cover": np.random.uniform(0, 100, 100),
            "precipitation": np.random.uniform(0, 5, 100),
            "rain": np.random.uniform(0, 5, 100),
            "snowfall": np.random.uniform(0, 1, 100),
            "aqi_index": np.random.uniform(30, 80, 100),
            "Calculated_AQI": np.random.uniform(30, 80, 100),
        }
    )
    return df


@pytest.fixture
def client(mock_model, mock_scaler, mock_df):
    """Create test client with mocked dependencies"""
    # Save original values
    original_model = app_module.model
    original_scaler = app_module.scaler
    original_df = app_module.df
    original_features = app_module.features

    # Mock S3 and model loading
    with patch.object(
        app_module, "load_model_and_scaler", return_value=True
    ), patch.object(app_module, "load_historical_data", return_value=True):
        # Set global variables directly
        app_module.model = mock_model
        app_module.scaler = mock_scaler
        app_module.df = mock_df
        app_module.features = [
            col
            for col in mock_df.columns
            if col not in ["aqi_index", "Calculated_AQI", "date"]
        ]

        app_module.app.config["TESTING"] = True

        with app_module.app.test_client() as test_client:
            yield test_client

    # Restore original values
    app_module.model = original_model
    app_module.scaler = original_scaler
    app_module.df = original_df
    app_module.features = original_features


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
    assert app_module.get_aqi_category(30) == "Good"
    assert app_module.get_aqi_category(50) == "Good"


def test_aqi_category_moderate():
    """Test AQI category classification - Moderate"""
    assert app_module.get_aqi_category(51) == "Moderate"
    assert app_module.get_aqi_category(100) == "Moderate"


def test_aqi_category_unhealthy_sensitive():
    """Test AQI category classification - Unhealthy for Sensitive Groups"""
    assert app_module.get_aqi_category(101) == "Unhealthy for Sensitive Groups"
    assert app_module.get_aqi_category(150) == "Unhealthy for Sensitive Groups"


def test_aqi_category_unhealthy():
    """Test AQI category classification - Unhealthy"""
    assert app_module.get_aqi_category(151) == "Unhealthy"
    assert app_module.get_aqi_category(200) == "Unhealthy"


def test_aqi_category_very_unhealthy():
    """Test AQI category classification - Very Unhealthy"""
    assert app_module.get_aqi_category(201) == "Very Unhealthy"
    assert app_module.get_aqi_category(300) == "Very Unhealthy"


def test_aqi_category_hazardous():
    """Test AQI category classification - Hazardous"""
    assert app_module.get_aqi_category(301) == "Hazardous"
    assert app_module.get_aqi_category(500) == "Hazardous"


def test_health_endpoint_model_not_loaded():
    """Test health endpoint when model is not loaded"""
    # Save original values
    original_model = app_module.model
    original_scaler = app_module.scaler
    original_df = app_module.df

    try:
        # Set to None to simulate not loaded
        app_module.model = None
        app_module.scaler = None
        app_module.df = None

        with patch.object(
            app_module, "load_model_and_scaler", return_value=False
        ), patch.object(app_module, "load_historical_data", return_value=False):
            app_module.app.config["TESTING"] = True

            with app_module.app.test_client() as test_client:
                response = test_client.get("/health")
                assert response.status_code == 503
                data = response.get_json()
                assert data["status"] == "unhealthy"
    finally:
        # Restore original values
        app_module.model = original_model
        app_module.scaler = original_scaler
        app_module.df = original_df


def test_predict_current_without_model():
    """Test prediction endpoint when model is not loaded"""
    with patch.object(
        app_module, "load_model_and_scaler", return_value=False
    ), patch.object(app_module, "load_historical_data", return_value=False):
        app_module.app.config["TESTING"] = True

        with app_module.app.test_client() as test_client:
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


# Additional tests for increased coverage


def test_get_s3_client():
    """Test S3 client creation function"""
    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret",
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    ):
        with patch("my_flask_app.app.boto3.client") as mock_boto_client:
            mock_boto_client.return_value = Mock()
            from my_flask_app.app import get_s3_client

            _ = get_s3_client()  # Call the function, result not needed
            mock_boto_client.assert_called_once_with(
                "s3",
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
                region_name="us-east-1",
            )


def test_load_model_and_scaler_success():
    """Test successful loading of model and scaler from S3"""
    import my_flask_app.app as app_module

    # Save original values
    original_model = app_module.model
    original_scaler = app_module.scaler

    try:
        # Reset to None to trigger loading
        app_module.model = None
        app_module.scaler = None

        mock_s3 = Mock()
        mock_s3.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=b'{"test": "metadata"}'))
        }
        mock_s3.download_fileobj = Mock()

        with patch.object(
            app_module, "get_s3_client", return_value=mock_s3
        ), patch.object(app_module, "joblib") as mock_joblib:
            mock_joblib.load.return_value = Mock()

            result = app_module.load_model_and_scaler()
            assert result is True
            assert mock_s3.get_object.called
    finally:
        app_module.model = original_model
        app_module.scaler = original_scaler


def test_load_model_and_scaler_already_loaded():
    """Test that model and scaler are not reloaded if already present"""
    import my_flask_app.app as app_module

    # Save original values
    original_model = app_module.model
    original_scaler = app_module.scaler

    try:
        # Set mock values to simulate already loaded
        app_module.model = Mock()
        app_module.scaler = Mock()

        result = app_module.load_model_and_scaler()
        assert result is True
    finally:
        app_module.model = original_model
        app_module.scaler = original_scaler


def test_load_model_and_scaler_failure():
    """Test handling of S3 loading failure"""
    import my_flask_app.app as app_module

    # Save original values
    original_model = app_module.model
    original_scaler = app_module.scaler

    try:
        # Reset to None to trigger loading
        app_module.model = None
        app_module.scaler = None

        with patch.object(
            app_module, "get_s3_client", side_effect=Exception("S3 Error")
        ):
            result = app_module.load_model_and_scaler()
            assert result is False
    finally:
        app_module.model = original_model
        app_module.scaler = original_scaler


def test_load_historical_data_success():
    """Test successful loading of historical data from S3"""
    import my_flask_app.app as app_module

    # Save original values
    original_df = app_module.df
    original_features = app_module.features

    try:
        # Reset to None to trigger loading
        app_module.df = None
        app_module.features = None

        # Create mock CSV data
        mock_csv_data = """year,month,day,hour,temperature_2m,aqi_index,Calculated_AQI
2024,1,1,0,25.0,45.0,50.0
2024,1,1,1,26.0,46.0,51.0"""

        mock_s3 = Mock()
        mock_s3.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=mock_csv_data.encode()))
        }

        with patch.object(
            app_module, "get_s3_client", return_value=mock_s3
        ), patch.object(app_module.pd, "read_csv") as mock_read_csv:
            mock_df = pd.DataFrame(
                {
                    "year": [2024, 2024],
                    "month": [1, 1],
                    "day": [1, 1],
                    "hour": [0, 1],
                    "temperature_2m": [25.0, 26.0],
                    "aqi_index": [45.0, 46.0],
                    "Calculated_AQI": [50.0, 51.0],
                }
            )
            mock_read_csv.return_value = mock_df

            result = app_module.load_historical_data()
            assert result is True
    finally:
        app_module.df = original_df
        app_module.features = original_features


def test_load_historical_data_already_loaded():
    """Test that historical data is not reloaded if already present"""
    import my_flask_app.app as app_module

    # Save original values
    original_df = app_module.df
    original_features = app_module.features

    try:
        # Set mock values to simulate already loaded
        app_module.df = Mock()
        app_module.features = ["col1", "col2"]

        result = app_module.load_historical_data()
        assert result is True
    finally:
        app_module.df = original_df
        app_module.features = original_features


def test_load_historical_data_failure():
    """Test handling of historical data loading failure"""
    import my_flask_app.app as app_module

    # Save original values
    original_df = app_module.df
    original_features = app_module.features

    try:
        # Reset to None to trigger loading
        app_module.df = None
        app_module.features = None

        with patch.object(
            app_module, "get_s3_client", side_effect=Exception("S3 Error")
        ):
            result = app_module.load_historical_data()
            assert result is False
    finally:
        app_module.df = original_df
        app_module.features = original_features


def test_health_endpoint_exception():
    """Test health endpoint when an exception occurs"""
    import my_flask_app.app as app_module

    with patch.object(
        app_module, "load_model_and_scaler", side_effect=Exception("Test error")
    ):
        app_module.app.config["TESTING"] = True

        with app_module.app.test_client() as test_client:
            response = test_client.get("/health")
            assert response.status_code == 503
            data = response.get_json()
            assert data["status"] == "unhealthy"
            assert "error" in data


def test_predict_endpoint_exception(client):
    """Test predict endpoint when an exception occurs during prediction"""
    import my_flask_app.app as app_module

    # Save original
    original_generate = app_module.generate_future_features

    try:
        app_module.generate_future_features = Mock(
            side_effect=Exception("Prediction error")
        )

        response = client.get("/api/predict")
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data
    finally:
        app_module.generate_future_features = original_generate


def test_predict_hourly_endpoint_exception(client):
    """Test predict hourly endpoint when an exception occurs"""
    import my_flask_app.app as app_module

    # Save original
    original_generate = app_module.generate_future_features

    try:
        app_module.generate_future_features = Mock(
            side_effect=Exception("Hourly prediction error")
        )

        response = client.get("/api/predict/hourly")
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data
    finally:
        app_module.generate_future_features = original_generate


def test_predict_daily_endpoint_exception(client):
    """Test predict daily endpoint when an exception occurs"""
    import my_flask_app.app as app_module

    # Save original
    original_generate = app_module.generate_future_features

    try:
        app_module.generate_future_features = Mock(
            side_effect=Exception("Daily prediction error")
        )

        response = client.get("/api/predict/daily")
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data
    finally:
        app_module.generate_future_features = original_generate


def test_predict_current_endpoint_exception(client):
    """Test predict current endpoint when an exception occurs"""
    import my_flask_app.app as app_module

    # Save original
    original_generate = app_module.generate_future_features

    try:
        app_module.generate_future_features = Mock(
            side_effect=Exception("Current prediction error")
        )

        response = client.get("/api/predict/current")
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data
    finally:
        app_module.generate_future_features = original_generate


def test_predict_without_model_or_data():
    """Test predict endpoint when model/data fails to load"""
    import my_flask_app.app as app_module

    with patch.object(app_module, "load_model_and_scaler", return_value=False):
        app_module.app.config["TESTING"] = True

        with app_module.app.test_client() as test_client:
            response = test_client.get("/api/predict")
            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data


def test_predict_hourly_without_model_or_data():
    """Test predict hourly endpoint when model/data fails to load"""
    import my_flask_app.app as app_module

    with patch.object(app_module, "load_model_and_scaler", return_value=False):
        app_module.app.config["TESTING"] = True

        with app_module.app.test_client() as test_client:
            response = test_client.get("/api/predict/hourly")
            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data


def test_predict_daily_without_model_or_data():
    """Test predict daily endpoint when model/data fails to load"""
    import my_flask_app.app as app_module

    with patch.object(app_module, "load_model_and_scaler", return_value=False):
        app_module.app.config["TESTING"] = True

        with app_module.app.test_client() as test_client:
            response = test_client.get("/api/predict/daily")
            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data


def test_generate_future_features():
    """Test the generate_future_features function"""
    import my_flask_app.app as app_module

    # Save originals
    original_df = app_module.df
    original_features = app_module.features

    try:
        # Create mock data
        np.random.seed(42)
        dates = pd.date_range(start="2024-01-01", periods=100, freq="h")
        mock_df = pd.DataFrame(
            {
                "year": dates.year,
                "month": dates.month,
                "day": dates.day,
                "hour": dates.hour,
                "temperature_2m": np.random.uniform(20, 35, 100),
                "relative_humidity_2m": np.random.uniform(40, 80, 100),
                "dew_point_2m": np.random.uniform(10, 25, 100),
                "wind_speed_10m": np.random.uniform(0, 10, 100),
                "wind_direction_10m": np.random.uniform(0, 360, 100),
                "surface_pressure": np.random.uniform(1000, 1020, 100),
                "cloud_cover": np.random.uniform(0, 100, 100),
                "precipitation": np.random.uniform(0, 5, 100),
                "rain": np.random.uniform(0, 5, 100),
                "snowfall": np.random.uniform(0, 1, 100),
                "aqi_index": np.random.uniform(30, 80, 100),
                "Calculated_AQI": np.random.uniform(30, 80, 100),
            }
        )

        app_module.df = mock_df
        app_module.features = [
            col
            for col in mock_df.columns
            if col not in ["aqi_index", "Calculated_AQI", "date"]
        ]

        future_features, future_dates = app_module.generate_future_features(24)

        assert len(future_features) == 24
        assert len(future_dates) == 24
        assert "year" in future_features.columns
        assert "month" in future_features.columns
        assert "day" in future_features.columns
        assert "hour" in future_features.columns
    finally:
        app_module.df = original_df
        app_module.features = original_features
