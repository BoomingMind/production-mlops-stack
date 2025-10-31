.PHONY: help dev install test lint docker run stop clean evidently audit security

help:
	@echo "Available targets:"
	@echo "  make dev        - Setup development environment"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run linters (ruff, black)"
	@echo "  make docker     - Build Docker image"
	@echo "  make run        - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make evidently  - Start Evidently dashboard"
	@echo "  make clean      - Clean temporary files"

dev: install
	@echo "Setting up development environment..."
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  Windows: venv\\Scripts\\activate"
	@echo "  Linux/Mac: source venv/bin/activate"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed"

test:
	@echo "Running tests..."
	@which pytest > /dev/null 2>&1 || { echo " pytest not found. Run 'make install' first."; exit 1; }
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term --cov-fail-under=80
	@echo "Tests complete. Coverage report: htmlcov/index.html"

lint:
	@echo "Running linters..."
	@which ruff > /dev/null 2>&1 || { echo " ruff not found. Run 'make install' first."; exit 1; }
	@which black > /dev/null 2>&1 || { echo " black not found. Run 'make install' first."; exit 1; }
	ruff check src/ tests/
	black --check src/ tests/
	@echo "Linting complete"

format:
	@echo "Formatting code..."
	black src/ tests/
	ruff check --fix src/ tests/
	@echo "Code formatted"

docker:
	@echo "Building Docker image..."
	docker build -t aqi-prediction-api:latest .
	@echo "Docker image built"

run:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started"
	@echo ""
	@echo "Access services at:"
	@echo "  MLflow:     http://localhost:5000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3000"
	@echo ""

stop:
	@echo "Stopping all services..."
	docker-compose down
	@echo "Services stopped"

evidently:
	@echo "Starting Evidently dashboard..."
	@echo "Run this after executing notebooks/04_evidently_monitoring.ipynb"
	evidently ui --workspace ./monitoring/evidently/workspace --port 7000

audit security:
	@echo "Running dependency vulnerability scan (pip-audit, fail on critical CVEs)..."
	python -m pip install --upgrade pip > NUL 2>&1 || true
	pip install --disable-pip-version-check --quiet pip-audit
	@if exist requirements.txt (
		pip-audit --requirement requirements.txt --fail-on critical --progress-spinner off
	) else (
		echo "No requirements.txt found; auditing current environment..." && pip-audit --fail-on critical --progress-spinner off
	)
	@echo "Security audit complete"

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	@echo "✅ Cleanup complete"

logs:
	@echo "Showing service logs..."
	docker-compose logs -f

mlflow:
	@echo "Starting MLflow server locally..."
	mlflow server --backend-store-uri sqlite:///mlruns/mlflow.db --default-artifact-root ./mlflow-artifacts --host 0.0.0.0 --port 5000

api:
	@echo "Starting FastAPI server..."
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
