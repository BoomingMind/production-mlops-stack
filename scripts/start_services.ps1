# MLOps AQI Prediction - Docker Startup Script
# This script builds and starts all services using Docker Compose

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  MLOps AQI Weather Prediction - Startup Script" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[1/5] Checking Docker status..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running"
    }
    Write-Host "      Docker is running" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "[2/5] Checking environment variables..." -ForegroundColor Yellow
if (Test-Path .env) {
    Write-Host "      .env file found" -ForegroundColor Green
} else {
    Write-Host "      WARNING: .env file not found" -ForegroundColor Red
    Write-Host "      Please create .env file with AWS credentials" -ForegroundColor Red
    exit 1
}

# Stop existing containers
Write-Host ""
Write-Host "[3/5] Stopping existing containers..." -ForegroundColor Yellow
docker-compose down > $null 2>&1
Write-Host "      Containers stopped" -ForegroundColor Green

# Build the application
Write-Host ""
Write-Host "[4/5] Building Docker images..." -ForegroundColor Yellow
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "      Build completed successfully" -ForegroundColor Green

# Start all services
Write-Host ""
Write-Host "[5/5] Starting all services..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  All services started successfully!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Display service URLs
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  FastAPI Application:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Documentation:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health Check:         http://localhost:8000/health" -ForegroundColor White
Write-Host "  Prometheus Metrics:   http://localhost:8000/metrics" -ForegroundColor White
Write-Host ""
Write-Host "  MLflow UI:            http://localhost:5000" -ForegroundColor White
Write-Host "  Prometheus:           http://localhost:9090" -ForegroundColor White
Write-Host "  Grafana:              http://localhost:3000" -ForegroundColor White
Write-Host "    Username: admin" -ForegroundColor Gray
Write-Host "    Password: admin" -ForegroundColor Gray
Write-Host ""

# Show container status
Write-Host "Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "To view logs: docker-compose logs -f [service-name]" -ForegroundColor Yellow
Write-Host "To stop all services: docker-compose down" -ForegroundColor Yellow
Write-Host ""
