# MLOps Monitoring Stack Startup Script
# This script starts MLflow, Prometheus, and Grafana

Write-Host "Starting MLOps Monitoring Stack..." -ForegroundColor Green
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Cyan
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}
Write-Host "Docker is running" -ForegroundColor Green
Write-Host ""

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "mlruns" | Out-Null
New-Item -ItemType Directory -Force -Path "mlflow-artifacts" | Out-Null
New-Item -ItemType Directory -Force -Path "monitoring\evidently\workspace" | Out-Null
New-Item -ItemType Directory -Force -Path "monitoring\evidently\reports" | Out-Null
Write-Host "Directories created" -ForegroundColor Green
Write-Host ""

# Start Docker Compose
Write-Host "Starting services with Docker Compose..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Access Your Services:" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "MLflow UI:       http://localhost:5000" -ForegroundColor Cyan
    Write-Host "Prometheus:      http://localhost:9090" -ForegroundColor Cyan
    Write-Host "Grafana:         http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
    Write-Host "Node Exporter:   http://localhost:9100/metrics" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host " Next Steps:" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Run model training notebook:" -ForegroundColor White
    Write-Host "   notebooks/03_model_train.ipynb" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. View experiments in MLflow:" -ForegroundColor White
    Write-Host "   http://localhost:5000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Setup Evidently dashboard:" -ForegroundColor White
    Write-Host "   Run: notebooks/04_evidently_monitoring.ipynb" -ForegroundColor Gray
    Write-Host "   Then: evidently ui --workspace ./monitoring/evidently/workspace --port 7000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Check system metrics in Grafana:" -ForegroundColor White
    Write-Host "   http://localhost:3000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To stop services: docker-compose down" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "Failed to start services" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}
