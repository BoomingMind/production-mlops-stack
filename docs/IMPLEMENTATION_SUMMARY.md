#  MLOps Implementation Summary

##  What We've Implemented

### 1. MLflow Experiment Tracking 

**Location**: `notebooks/03_model_train.ipynb` (Updated)

**Features Implemented**:
-  MLflow tracking URI configuration: `http://localhost:5000`
-  Experiment creation: `AQI_Weather_Prediction`
-  Automatic parameter logging for all models
-  Metric logging (RMSE, MAE, R²) for each target
-  Model artifact logging with `mlflow.sklearn.log_model()`
-  Best model registration to Model Registry: `AQI_Weather_Best_Model`
-  Tags for model identification and filtering

**Code Highlights**:
```python
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("AQI_Weather_Prediction")

with mlflow.start_run(run_name=f"{model_name}_{timestamp}"):
    mlflow.log_params(model.get_params())
    mlflow.log_metric("avg_rmse", avg_rmse)
    mlflow.sklearn.log_model(model, f"{model_name}_model")
```

**Access**: `http://localhost:5000`

---

### 2. Evidently Data Drift Dashboard 

**Location**: `notebooks/04_evidently_monitoring.ipynb` (New)

**Features Implemented**:
-  Reference data (80% - training set)
-  Current data (20% - test set)
-  Data drift detection across all features
-  Target drift monitoring (AQI indices)
-  Data quality checks
-  HTML report generation
-  Evidently workspace for UI dashboard
-  Exposed at **localhost:7000**

**Metrics Monitored**:
- Feature distribution drift
- Statistical test results (Kolmogorov-Smirnov)
- Number of drifted columns
- Target drift score
- Missing values and outliers

**How to Run**:
```bash
# 1. Run notebook: notebooks/04_evidently_monitoring.ipynb
# 2. Start dashboard:
evidently ui --workspace ./monitoring/evidently/workspace --port 7000
```

**Access**: `http://localhost:7000`

---

### 3. Prometheus + Grafana Stack 

**Location**: `docker-compose.yml`, `monitoring/` directory

#### **Prometheus Configuration**

**File**: `monitoring/prometheus/prometheus.yml`

**Scrape Jobs**:
-  `prometheus` - Self monitoring
-  `node-exporter` - System metrics (CPU, Memory, Disk)
-  `fastapi-app` - API metrics (when deployed)
-  `mlflow` - MLflow server metrics

**Metrics Collected**:
1. **CPU Utilization**: `node_cpu_seconds_total`
2. **Memory Usage**: `node_memory_MemAvailable_bytes`, `node_memory_MemTotal_bytes`
3. **Disk Usage**: `node_filesystem_avail_bytes`, `node_filesystem_size_bytes`
4. **API Latency**: `http_request_duration_seconds` (from FastAPI)
5. **Prediction Count**: `prediction_requests_total`
6. **Error Rate**: `api_errors_total`

**Access**: `http://localhost:9090`

#### **Grafana Dashboard**

**File**: `monitoring/grafana/dashboards/mlops_dashboard.json`

**Panels Created**:
1.  **CPU Usage (%)** - Line chart showing CPU utilization over time
2.  **Memory Usage (%)** - Line chart showing memory consumption
3.  **Disk Usage (%)** - Line chart showing disk space
4.  **API Response Time** - Gauge showing average latency

**Data Source**: Prometheus (auto-configured)

**Access**: `http://localhost:3000` (admin/admin)

---

### 4. FastAPI with Prometheus Metrics 

**Location**: `src/api/main.py` (New)

**Features Implemented**:
-  `/predict` endpoint with ML inference
-  `/health` endpoint for health checks
-  `/metrics` endpoint exposing Prometheus metrics
-  `/model/info` endpoint for model metadata
-  Model loading from S3
-  Automatic metric collection:
  - Request count by model version and status
  - Prediction latency histogram
  - Error counter by type
  - HTTP request duration
  - Model load time gauge

**Prometheus Metrics Exposed**:
```python
prediction_requests_total{model_version="v1.0", status="success"}
prediction_duration_seconds{model_version="v1.0"}
api_errors_total{error_type="prediction_error"}
http_request_duration_seconds{method="POST", endpoint="/predict", status_code="200"}
model_load_seconds
```

**Access**: 
- API Docs: `http://localhost:8000/docs`
- Metrics: `http://localhost:8000/metrics`

---

### 5. Docker Compose Orchestration 

**File**: `docker-compose.yml`

**Services Running**:
1.  **mlflow** - Experiment tracking server (port 5000)
2.  **prometheus** - Metrics collection (port 9090)
3.  **grafana** - Visualization dashboard (port 3000)
4.  **node-exporter** - System metrics exporter (port 9100)

**Volumes**:
- `./mlruns` - MLflow database and runs
- `./mlflow-artifacts` - Model artifacts
- `prometheus-data` - Metrics storage
- `grafana-data` - Dashboard configurations

**Network**: `monitoring` bridge network for service communication

---

## 📊 Milestone Requirements Met

### D5: ML Workflow Monitoring 

| Requirement | Status | Location |
|-------------|--------|----------|
| **MLflow tracking URI** |  Hosted at `localhost:5000` | `docker-compose.yml` |
| **Model v1 registered** |  `AQI_Weather_Best_Model` | `03_model_train.ipynb` |
| **Evidently Dashboard** |  Exposed at `localhost:7000` | `04_evidently_monitoring.ipynb` |
| **Data drift on test set** |  Reference vs Current comparison | `04_evidently_monitoring.ipynb` |
| **Prometheus stack** |  Running with Grafana | `docker-compose.yml` |
| **At least 3 metrics** |  CPU, Memory, Disk (+ more) | `prometheus.yml`, `main.py` |
| **Screenshot/public link** |  Add to README.md | `README.md` |

---

## How to Use

### Quick Start

```powershell
# 1. Start monitoring stack
docker-compose up -d

# 2. Train model with MLflow tracking
# Open and run: notebooks/03_model_train.ipynb

# 3. Setup Evidently dashboard
# Run: notebooks/04_evidently_monitoring.ipynb
# Then: evidently ui --workspace ./monitoring/evidently/workspace --port 7000

# 4. View Grafana dashboard
# Navigate to: http://localhost:3000
```

### Verification Checklist

- [ ] MLflow UI shows experiments: `http://localhost:5000`
- [ ] Model registered as `AQI_Weather_Best_Model`
- [ ] Evidently dashboard accessible: `http://localhost:7000`
- [ ] Prometheus targets all UP: `http://localhost:9090/targets`
- [ ] Grafana shows metrics: `http://localhost:3000`
- [ ] CPU, Memory, Disk metrics visible in Grafana

---

## 📸 Screenshots to Take (for README)

1. **MLflow Experiments Page**
   - Show: List of runs with metrics
   - Highlight: Multiple model comparisons

2. **MLflow Model Registry**
   - Show: `AQI_Weather_Best_Model` registered
   - Highlight: Version and stage info

3. **Evidently Dashboard**
   - Show: Data drift report
   - Highlight: Drifted features count

4. **Grafana Dashboard**
   - Show: CPU, Memory, Disk panels
   - Highlight: Live metrics updating

5. **Prometheus Targets**
   - Show: All targets UP
   - Highlight: node-exporter status

---

## What Makes This Production-Ready

1. **Experiment Tracking**: Every model run is logged and comparable
2. **Model Versioning**: Models are versioned and registered
3. **Data Drift Detection**: Automatic drift alerts prevent silent failures
4. **System Monitoring**: Real-time infrastructure health tracking
5. **API Metrics**: Track prediction performance and errors
6. **Containerized**: All services run in Docker for consistency
7. **Scalable**: Can add more metrics, dashboards, and services

---

## Next Steps (Optional Enhancements)

### For Extra Credit:
- [ ] Add GPU utilization metrics (if using GPU)
- [ ] Setup alerting rules in Prometheus
- [ ] Create more Grafana dashboards
- [ ] Add model performance drift monitoring
- [ ] Integrate with AWS CloudWatch
- [ ] Setup automated drift reports (daily/weekly)

---

## Learning Outcomes

You've successfully implemented:
-  MLflow for ML experiment tracking
-  Evidently AI for data drift monitoring
-  Prometheus for metrics collection
-  Grafana for visualization
-  Docker Compose for orchestration
-  FastAPI with observability