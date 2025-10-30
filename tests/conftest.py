"""
Test configuration and fixtures
"""
import pytest
import os
import sys

# Add src directory to Python path
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
