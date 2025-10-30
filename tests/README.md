# Tests Directory

This directory contains all unit and integration tests for the MLOps AQI Prediction project.

## Running Tests

```bash
# Run all tests with coverage
make test

# Or manually
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage threshold
pytest tests/ --cov=src --cov-fail-under=80
```

## Test Structure

- `conftest.py` - Shared test fixtures and configuration
- `test_api.py` - API endpoint tests
- `test_data/` - Sample test data (if needed)

## Coverage Requirements

- Minimum coverage: 80%
- CI/CD pipeline enforces this threshold
- Coverage reports are generated in `htmlcov/` directory

## Writing Tests

All tests should follow these conventions:
- Use descriptive test names starting with `test_`
- Mock external dependencies (S3, models, etc.)
- Test both success and failure cases
- Use pytest fixtures for common setup
