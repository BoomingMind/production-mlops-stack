"""
Test script for the Prediction API endpoints
Run this after starting the FastAPI server
"""
import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def test_root():
    """Test root endpoint"""
    print("\n" + "="*60)
    print("Testing Root Endpoint")
    print("="*60)
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("Testing Health Check")
    print("="*60)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*60)
    print("Testing Model Info")
    print("="*60)
    response = requests.get(f"{BASE_URL}/model/info")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_single_prediction():
    """Test single prediction endpoint"""
    print("\n" + "="*60)
    print("Testing Single Prediction")
    print("="*60)
    
    # Sample input data
    data = {
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
    
    response = requests.post(f"{BASE_URL}/predict", json=data)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_latest_predictions():
    """Test fetching latest predictions (72 hours)"""
    print("\n" + "="*60)
    print("Testing Latest Predictions (Next 3 Days)")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/predictions/latest")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total Hours: {data['total_hours']}")
        print(f"Prediction Period: {data['prediction_period']}")
        print(f"\nFirst 5 predictions:")
        for pred in data['predictions'][:5]:
            print(f"  {pred['datetime']}: AQI={pred['predicted_aqi_index']:.2f}, Category={pred['aqi_category']}")
        
        print(f"\nDaily Summary:")
        for date, summary in data['daily_summary'].items():
            print(f"  {date}: Avg={summary['aqi_index_mean']:.2f}, Min={summary['aqi_index_min']:.2f}, Max={summary['aqi_index_max']:.2f}")
    else:
        print(f"Error: {response.json()}")

def test_predictions_by_date():
    """Test fetching predictions for a specific date"""
    print("\n" + "="*60)
    print("Testing Predictions by Date")
    print("="*60)
    
    # Test with tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    response = requests.get(f"{BASE_URL}/predictions/by-date/{tomorrow}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Date: {data['date']}")
        print(f"Total Hours: {data['total_hours']}")
        print(f"Summary: {data['summary']}")
        print(f"\nSample predictions (every 4 hours):")
        for i, pred in enumerate(data['predictions']):
            if i % 4 == 0:  # Show every 4th hour
                print(f"  Hour {pred['hour']:02d}:00 - AQI={pred['predicted_aqi_index']:.2f}, Category={pred['aqi_category']}")
    else:
        print(f"Error: {response.json()}")

def test_predictions_summary():
    """Test fetching predictions summary"""
    print("\n" + "="*60)
    print("Testing Predictions Summary")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/predictions/summary")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nOverall Statistics:")
        print(f"  Total Hours: {data['overall_statistics']['total_hours']}")
        print(f"  Average AQI: {data['overall_statistics']['avg_aqi']:.2f}")
        print(f"  Min AQI: {data['overall_statistics']['min_aqi']:.2f}")
        print(f"  Max AQI: {data['overall_statistics']['max_aqi']:.2f}")
        
        print(f"\nCategory Distribution:")
        for category, stats in data['category_distribution'].items():
            print(f"  {category}: {stats['count']} hours ({stats['percentage']:.1f}%)")
        
        print(f"\nBest Air Quality:")
        print(f"  {data['best_air_quality']['datetime']}: AQI={data['best_air_quality']['aqi']:.2f}")
        
        print(f"\nWorst Air Quality:")
        print(f"  {data['worst_air_quality']['datetime']}: AQI={data['worst_air_quality']['aqi']:.2f}")
    else:
        print(f"Error: {response.json()}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AQI PREDICTION API TEST SUITE")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Make sure the API is running: python src/api/main.py")
    
    try:
        # Basic endpoints
        test_root()
        test_health()
        test_model_info()
        
        # Prediction endpoints
        test_single_prediction()
        test_latest_predictions()
        test_predictions_by_date()
        test_predictions_summary()
        
        print("\n" + "="*60)
        print(" ALL TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n ERROR: Could not connect to API")
        print("Please start the API server first:")
        print("  python src/api/main.py")
    except Exception as e:
        print(f"\n ERROR: {e}")

if __name__ == "__main__":
    main()
