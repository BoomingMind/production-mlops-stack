# 🌍 MLOps Project - AQI Weather Prediction System

_Production-ready pipeline to predict AQI from weather data with experiment tracking, drift monitoring, and an inference API._

[![MLOps](https://img.shields.io/badge/MLOps-Production-blue)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal)](https://fastapi.tiangolo.com)
[![MLflow](https://img.shields.io/badge/MLflow-2.9-orange)](https://mlflow.org)

> Production-ready MLOps pipeline for Air Quality Index (AQI) prediction using weather parameters with comprehensive monitoring and experiment tracking.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Features](#features)
- [Monitoring Stack](#monitoring-stack)
- [Cloud Integration](#cloud-integration)
- [Make Targets](#make-targets)
- [API Documentation](#api-documentation)
- [FAQ](#faq)

---

## 🎯 Overview

**Elevator Pitch:** Real-time AQI prediction system leveraging weather data with production-grade MLOps practices including experiment tracking, data drift monitoring, and comprehensive observability.

This project implements an end-to-end machine learning pipeline that:
-  Fetches weather and AQI data from APIs and stores in AWS S3
-  Tracks experiments with **MLflow**
-  Monitors data drift with **Evidently AI**
-  Collects system metrics with **Prometheus + Grafana**
-  Serves predictions via **FastAPI**
-  Containerized with **Docker**
-  Automated CI/CD with **GitHub Actions**

---

##  Quick Start

### TL;DR

macOS/Linux (bash/zsh):
```bash
git clone https://github.com/AbdullahIqbal26904/MLOPS_Project.git && cd MLOPS_Project && make dev
```

Windows (PowerShell):
```powershell
git clone https://github.com/AbdullahIqbal26904/MLOPS_Project.git; cd MLOPS_Project; make dev
```

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- AWS Account (for S3 storage)

### Installation

```bash
# Clone the repository
git clone https://github.com/AbdullahIqbal26904/MLOPS_Project.git
cd MLOPS_Project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your AWS credentials and API keys
```

### Run Everything with Docker Compose

```bash
# Start all services (MLflow, Prometheus, Grafana)
docker-compose up -d

# Check service status
docker-compose ps
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **MLflow UI** | http://localhost:5000 | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Evidently Dashboard** | http://localhost:7000 | - |
| **FastAPI Docs** | http://localhost:8000/docs | - |

---

## Architecture

```mermaid
graph LR
    A[Data Sources] --> B[S3 Storage]
    B --> C[Data Processing]
    C --> D[Model Training]
    D --> E[MLflow Registry]
  E --> F[Inference API (FastAPI)]
    F --> G[Prometheus]
    G --> H[Grafana]
    C --> I[Evidently]
    I --> J[Drift Dashboard]
```

### Component Breakdown

1. **Data Ingestion**: Hourly weather/AQI data from OpenWeather API → S3
2. **Feature Engineering**: Cleaning, imputation, feature creation
3. **Model Training**: Multiple models tracked with MLflow
4. **Model Registry**: Best model stored in MLflow + S3
5. **Inference API**: FastAPI with Prometheus metrics
6. **Monitoring**: 
   - **Evidently**: Data drift at localhost:7000
   - **Prometheus**: System metrics at localhost:9090
   - **Grafana**: Dashboards at localhost:3000

---

## Features

### MLflow Experiment Tracking
- **Tracking URI**: `http://localhost:5000`
- **Features**:
  - Automatic experiment logging
  - Parameter and metric tracking
  - Model versioning
  - Model registry integration
  - Artifact storage

**Usage**:
```python
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("AQI_Weather_Prediction")

with mlflow.start_run():
    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_metric("rmse", 0.85)
    mlflow.sklearn.log_model(model, "model")
```

### Evidently Data Drift Monitoring

**Exposed at**: `http://localhost:7000`

Monitors:
- Feature distribution drift
- Target drift (AQI changes)
- Data quality issues
- Model performance degradation

**To start Evidently dashboard**:
```bash
evidently ui --workspace ./monitoring/evidently/workspace --port 7000
```

### Prometheus + Grafana Monitoring

**Collected Metrics**:
1. **CPU Utilization**: `node_cpu_seconds_total`
2. **Memory Usage**: `node_memory_MemAvailable_bytes`
3. **Disk Usage**: `node_filesystem_avail_bytes`
4. **API Latency**: `http_request_duration_seconds`
5. **Prediction Count**: `prediction_requests_total`
6. **Error Rate**: `api_errors_total`

**Screenshots**:

![Grafana Dashboard](./docs/screenshots/grafana_dashboard.png)
*System monitoring dashboard showing CPU, memory, and API metrics*

---

## Cloud Integration

### AWS Services Used

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **S3** | Data storage | Bucket: `my-feature-store-data` |
| **EC2** | (Optional) API hosting | - |

### Setup Instructions

1. **Create S3 Bucket**:
```bash
aws s3 mb s3://my-feature-store-data
```

2. **Configure AWS Credentials**:
```bash
# In .env file
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

3. **Upload Data**:
```python
# Automatically handled by notebooks/01_data_fetch_hourly.ipynb
```

---

## Make Targets

```makefile
make dev          # Setup development environment
make test         # Run pytest with coverage
make lint         # Run ruff & black
make docker       # Build Docker image
make run          # Start all services
make stop         # Stop all services
make clean        # Clean temporary files
make audit        # Run pip-audit (fails on critical CVEs)
```

---

## API Documentation

### Endpoints

#### `POST /predict`
Predict AQI based on weather parameters.

**Request**:
```json
{
  "co": 250.5,
  "no2": 12.3,
  "pm2_5": 25.4,
  "temperature_2m": 28.5,
  ...
}
```

**Response**:
```json
{
  "aqi_index": 45.2,
  "calculated_aqi": 46.0,
  "prediction_time": "2025-10-22T14:30:00",
  "model_version": "v1.0"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

#### `GET /health`
Health check endpoint.

#### `GET /metrics`
Prometheus metrics endpoint.

---

## FAQ

### Common build/run issues

1) "make: command not found"
- Windows: Install make via Chocolatey (Admin PowerShell): `choco install make`
- macOS: `brew install make` (or use `xcode-select --install` to get build tools)

2) Docker says "docker-compose: command not found"
- Docker Desktop v2+ uses the new syntax `docker compose`. You can run either `docker-compose up -d` or `docker compose up -d` depending on your version.

3) Ports already in use (5000, 8000, 3000, 9090)
- Stop conflicting apps, or change ports in `docker-compose.yml` and restart: `docker compose down && docker compose up -d`

4) `pip install` fails with compiler errors on Windows (e.g., "Microsoft Visual C++ Build Tools" required)
- Install Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Or use prebuilt wheels where possible and ensure Python 3.11 is installed from python.org

5) Virtual environment activation issues
- Windows (PowerShell): `venv\Scripts\Activate.ps1` (you might need to run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once)
- macOS/Linux: `source venv/bin/activate`

### Q: How do I view MLflow experiments?
**A**: Navigate to `http://localhost:5000` after running `docker-compose up`.

### Q: Where is the Evidently dashboard?
**A**: 
1. Run the notebook: `notebooks/04_evidently_monitoring.ipynb`
2. Execute: `evidently ui --workspace ./monitoring/evidently/workspace --port 7000`
3. Access: `http://localhost:7000`

### Q: How to setup on Windows?
**A**: 
- Use PowerShell
- Install Docker Desktop for Windows
- Use `venv\Scripts\activate` instead of `source venv/bin/activate`

### Q: How to setup on macOS?
**A**:
- Use Terminal (zsh/bash)
- Install Docker Desktop for Mac
- Ensure Python 3.11 is available: `brew install python@3.11`
- Create venv: `python3.11 -m venv venv` and activate with `source venv/bin/activate`
- If `make` is missing: `brew install make`

### Q: Model not loading in API?
**A**: 
1. Ensure model is uploaded to S3: Check `s3://my-feature-store-data/models/best_model.pkl`
2. Verify AWS credentials in `.env`
3. Check API logs: `docker-compose logs api`

### Q: Grafana showing "No Data"?
**A**:
1. Verify Prometheus is scraping: `http://localhost:9090/targets`
2. Check if `node-exporter` is running: `docker-compose ps`
3. Wait 1-2 minutes for metrics to populate

---

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTION.md](CONTRIBUTION.md)

## Contact

- **Team Lead**: Abdullah Iqbal
- **Repository**: https://github.com/AbdullahIqbal26904/MLOPS_Project