"""
Test configuration and fixtures
"""
import pytest
import os
import sys
from unittest.mock import Mock

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory"""
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture(scope="session")
def sample_prediction_input():
    """Sample prediction input for testing"""
    return {
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
        "day": 30,
        "hour": 14,
    }


# Global fixtures to be reused across test modules
@pytest.fixture
def mock_model():
    """Mock ML model returning two outputs for aqi_index and calculated_aqi."""
    model = Mock()
    # Two-output shape: [aqi_index, calculated_aqi]
    model.predict = Mock(return_value=[[42.0, 100.0]])
    return model


@pytest.fixture
def mock_scaler():
    """Mock scaler with a simple transform passthrough of correct shape."""
    scaler = Mock()
    # Return a 2D array with 22 features scaled
    scaler.transform = Mock(return_value=[[0.5] * 22])
    # Provide attributes used by code under test
    scaler.n_features_in_ = 22
    scaler.feature_names_in_ = None
    return scaler
