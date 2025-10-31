"""
Extra unit tests to increase coverage for src/api/main.py
"""
import numpy as np
import pytest
from unittest.mock import Mock


def test_build_feature_vector_with_feature_names(monkeypatch):
    """Verify _build_feature_vector aligns by feature names and computes engineered fields."""
    # Import inside test to avoid import-time side effects
    import src.api.main as main_module

    # Prepare a scaler mock that exposes feature names including engineered and stray index
    feature_names = [
        "co",
        "no",
        "no2",
        "o3",
        "so2",
        "pm2_5",
        "pm10",
        "nh3",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "wind_direction_10m",
        "surface_pressure",
        "dew_point_2m",
        "apparent_temperature",
        "shortwave_radiation",
        "et0_fao_evapotranspiration",
        "year",
        "month",
        "day",
        "hour",
        # engineered + stray
        "day_of_week",
        "is_weekend",
        "Unnamed: 0",
    ]

    scaler_mock = Mock()
    scaler_mock.feature_names_in_ = np.array(feature_names, dtype=object)
    scaler_mock.n_features_in_ = len(feature_names)

    # Set the global scaler in module
    monkeypatch.setattr(main_module, "scaler", scaler_mock)

    # Build a valid PredictionInput for a known weekday (2025-10-31 is Friday -> 4, not weekend)
    PredictionInput = main_module.PredictionInput
    input_payload = PredictionInput(
        co=250.5,
        no=0.5,
        no2=12.3,
        o3=45.6,
        so2=7.8,
        pm2_5=25.4,
        pm10=40.2,
        nh3=3.2,
        temperature_2m=28.5,
        relative_humidity_2m=65.0,
        precipitation=0.0,
        wind_speed_10m=5.2,
        wind_direction_10m=180.0,
        surface_pressure=1013.25,
        dew_point_2m=20.3,
        apparent_temperature=30.1,
        shortwave_radiation=500.0,
        et0_fao_evapotranspiration=0.25,
        year=2025,
        month=10,
        day=31,
        hour=14,
    )

    vec = main_module._build_feature_vector(input_payload)
    assert vec.shape == (1, len(feature_names))

    # Validate engineered fields placement and values
    dow_idx = feature_names.index("day_of_week")
    weekend_idx = feature_names.index("is_weekend")
    unnamed_idx = feature_names.index("Unnamed: 0")

    assert vec[0, dow_idx] == 4.0  # Friday
    assert vec[0, weekend_idx] == 0.0  # Not weekend
    assert vec[0, unnamed_idx] == 0.0  # Unnamed/index should zero-fill


def test_build_feature_vector_off_by_one_without_names(monkeypatch):
    """When no feature names, and expected is base+1, a leading zero should be prepended."""
    import src.api.main as main_module

    # No feature names; expected count = base (22) + 1
    scaler_mock = Mock()
    scaler_mock.feature_names_in_ = None
    scaler_mock.n_features_in_ = 23
    monkeypatch.setattr(main_module, "scaler", scaler_mock)

    PredictionInput = main_module.PredictionInput
    inp = PredictionInput(
        co=1,
        no=2,
        no2=3,
        o3=4,
        so2=5,
        pm2_5=6,
        pm10=7,
        nh3=8,
        temperature_2m=9,
        relative_humidity_2m=10,
        precipitation=11,
        wind_speed_10m=12,
        wind_direction_10m=13,
        surface_pressure=14,
        dew_point_2m=15,
        apparent_temperature=16,
        shortwave_radiation=17,
        et0_fao_evapotranspiration=18,
        year=2025,
        month=10,
        day=31,
        hour=14,
    )

    vec = main_module._build_feature_vector(inp)
    assert vec.shape == (1, 23)
    assert vec[0, 0] == 0.0  # prepended dummy index


def test_model_info_unavailable_returns_503(client, monkeypatch):
    """model_info should return 503 if model is not loaded."""
    import src.api.main as main_module

    monkeypatch.setattr(main_module, "model", None)
    response = client.get("/model/info")
    assert response.status_code == 503
    data = response.json()
    assert "Model not loaded" in data.get("detail", "")
