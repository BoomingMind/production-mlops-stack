"""
Integration tests for the deployed API
Tests the actual running container without mocks
"""
import requests
import pytest
import time
import os

# Base URL for integration tests - can be overridden via environment variable
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


@pytest.fixture(scope="module")
def wait_for_api():
    """Wait for API to be ready before running tests"""
    max_attempts = 60
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"\n✓ API is ready at {BASE_URL}")
                return True
        except requests.exceptions.RequestException:
            if i < max_attempts - 1:
                time.sleep(2)
    pytest.fail(f"API not ready after {max_attempts} attempts")


class TestHealthEndpoints:
    """Test health and status endpoints"""

    def test_health_endpoint(self, wait_for_api):
        """Test health check returns 200"""
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_root_endpoint(self, wait_for_api):
        """Test root endpoint returns service info"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestModelEndpoints:
    """Test model-related endpoints"""

    def test_model_info_endpoint(self, wait_for_api):
        """Test model info endpoint"""
        response = requests.get(f"{BASE_URL}/model/info", timeout=10)
        # Can be 200 (model loaded) or 503 (model not loaded)
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            # Should have model information
            assert isinstance(data, dict)


class TestPredictionEndpoints:
    """Test prediction functionality with real model"""

    @pytest.fixture
    def good_air_quality_payload(self):
        """Payload representing good air quality conditions"""
        return {
            "co": 200.0,
            "no": 0.1,
            "no2": 10.0,
            "o3": 40.0,
            "so2": 5.0,
            "pm2_5": 15.0,
            "pm10": 30.0,
            "nh3": 2.0,
            "temperature_2m": 25.0,
            "relative_humidity_2m": 60.0,
            "precipitation": 0.0,
            "wind_speed_10m": 5.0,
            "wind_direction_10m": 180.0,
            "surface_pressure": 1013.25,
            "dew_point_2m": 20.0,
            "apparent_temperature": 26.0,
            "shortwave_radiation": 500.0,
            "et0_fao_evapotranspiration": 0.2,
            "year": 2025,
            "month": 10,
            "day": 31,
            "hour": 14,
        }

    @pytest.fixture
    def moderate_air_quality_payload(self):
        """Payload representing moderate air quality conditions"""
        return {
            "co": 500.0,
            "no": 5.0,
            "no2": 40.0,
            "o3": 80.0,
            "so2": 20.0,
            "pm2_5": 50.0,
            "pm10": 100.0,
            "nh3": 10.0,
            "temperature_2m": 30.0,
            "relative_humidity_2m": 70.0,
            "precipitation": 0.0,
            "wind_speed_10m": 3.0,
            "wind_direction_10m": 90.0,
            "surface_pressure": 1010.0,
            "dew_point_2m": 22.0,
            "apparent_temperature": 32.0,
            "shortwave_radiation": 600.0,
            "et0_fao_evapotranspiration": 0.3,
            "year": 2025,
            "month": 10,
            "day": 31,
            "hour": 15,
        }

    @pytest.fixture
    def poor_air_quality_payload(self):
        """Payload representing poor air quality conditions"""
        return {
            "co": 1000.0,
            "no": 20.0,
            "no2": 100.0,
            "o3": 150.0,
            "so2": 50.0,
            "pm2_5": 150.0,
            "pm10": 250.0,
            "nh3": 30.0,
            "temperature_2m": 35.0,
            "relative_humidity_2m": 80.0,
            "precipitation": 0.0,
            "wind_speed_10m": 2.0,
            "wind_direction_10m": 45.0,
            "surface_pressure": 1008.0,
            "dew_point_2m": 25.0,
            "apparent_temperature": 38.0,
            "shortwave_radiation": 700.0,
            "et0_fao_evapotranspiration": 0.4,
            "year": 2025,
            "month": 10,
            "day": 31,
            "hour": 16,
        }

    def test_predict_good_air_quality(self, wait_for_api, good_air_quality_payload):
        """Test prediction with good air quality data"""
        response = requests.post(
            f"{BASE_URL}/predict", json=good_air_quality_payload, timeout=15
        )
        # Can be 200 (success) or 503 (model not loaded)
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            # Should have AQI prediction fields
            assert "aqi_index" in data or "predicted_aqi_index" in data
            assert "aqi_category" in data or "category" in data

    def test_predict_moderate_air_quality(
        self, wait_for_api, moderate_air_quality_payload
    ):
        """Test prediction with moderate air quality data"""
        response = requests.post(
            f"{BASE_URL}/predict", json=moderate_air_quality_payload, timeout=15
        )
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "aqi_index" in data or "predicted_aqi_index" in data

    def test_predict_poor_air_quality(self, wait_for_api, poor_air_quality_payload):
        """Test prediction with poor air quality data"""
        response = requests.post(
            f"{BASE_URL}/predict", json=poor_air_quality_payload, timeout=15
        )
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "aqi_index" in data or "predicted_aqi_index" in data

    def test_predict_missing_fields(self, wait_for_api):
        """Test prediction with missing required fields"""
        payload = {"co": 250.5, "no2": 12.3}  # Missing many fields
        response = requests.post(f"{BASE_URL}/predict", json=payload, timeout=10)
        assert response.status_code == 422  # Validation error

    def test_predict_invalid_types(self, wait_for_api):
        """Test prediction with invalid data types"""
        payload = {
            "co": "not_a_number",  # Invalid type
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
            "day": 31,
            "hour": 14,
        }
        response = requests.post(f"{BASE_URL}/predict", json=payload, timeout=10)
        assert response.status_code == 422


class TestMetricsAndDocs:
    """Test metrics and documentation endpoints"""

    def test_metrics_endpoint(self, wait_for_api):
        """Test Prometheus metrics endpoint"""
        response = requests.get(f"{BASE_URL}/metrics", timeout=10)
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_openapi_json(self, wait_for_api):
        """Test OpenAPI JSON endpoint"""
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_docs(self, wait_for_api):
        """Test Swagger UI endpoint"""
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        assert response.status_code == 200

    def test_redoc_docs(self, wait_for_api):
        """Test ReDoc endpoint"""
        response = requests.get(f"{BASE_URL}/redoc", timeout=10)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
