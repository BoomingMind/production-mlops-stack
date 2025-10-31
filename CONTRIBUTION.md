# Contribution Guide

This document captures team member details, task ownership, branching conventions, and how to contribute effectively to the project.

## Team Members

| Name | ERP/Student ID | Role | Contact |
|------|-----------------|------|---------|
| Abdullah Iqbal | 26904 | Pipelines (CI/CD), Data Ingestion & Preprocessing | a.iqbal.26904@khi.iba.edu.pk |
| Hussain Ali Shah | 27131 | API Development (FastAPI) | h.shah.27131@khi.iba.edu |
| Haseeb Ahmed | 26077 | Model Training & Prediction | h.ahmed.26077@khi.iba.edu.pk |
| Fatima Naeem | 26933 | Dockerization | f.naeem.26933@khi.iba.edu.pk |


## Task Mapping (Who did what)

| Area | Tasks | Owner |
|------|-------|-------|
| Data Preparation | Data fetching, cleaning/preprocessing, basic EDA, feature engineering | Abdullah Iqbal |
| Model Training | Model development, training/tuning, validation, prediction pipeline | Haseeb Ahmed |
| Inference API | FastAPI service, endpoints, input/output schema, testing | Hussain Ali Shah |
| CI/CD Pipelines | Automated workflows for lint, tests, coverage, Docker build/push, deploy | Abdullah Iqbal |
| Dockerization | Dockerfile, docker-compose, image optimization | Fatima Naeem |
| Monitoring - Evidently | Evidently drift detection, data quality reports | Haseeb Ahmed |
| Monitoring - Prometheus/Grafana | Prometheus metrics, Grafana dashboards, monitoring setup | Fatima Naeem |
| Cloud Infrastructure | S3/EC2/Lambda/CloudWatch integration and deployment | Hussain Ali Shah |
| Documentation | README, API docs, implementation summaries | Abdullah Iqbal |
| Testing & Quality | Unit tests, integration tests, code coverage | Fatima Naeem |

## Branch Naming Convention

Follow short, consistent prefixes:

- `feat/data-fetching` — New features or endpoints
- `feat/data-processing` — Bug fixes
- `feat/evidently-dashboard` — CI/CD, Docker, Makefile, provisioning
- `feat/fast-api` — Documentation only
- `feat/model-training` — Misc chores (no functional change)


### Branches used in this project
- `feat/fast-api` — API development (Hussain Ali Shah)
- `feat/model-training` — Model training and prediction (Haseeb Ahmed)
- `feat/data-fetching` — Data fetching and ingestion (Abdullah Iqbal)
- `feat/data-processing` — Data preprocessing and cleaning (Abdullah Iqbal)
- `feat/evidently-dashboard` — Evidently monitoring setup (Haseeb Ahmed)
- `feat/prometheus-grafana-setup` — Prometheus/Grafana monitoring (Fatima Naeem)
- `feat/test-scripts` — Testing infrastructure (Fatima Naeem)
- `automated-pipeline` — CI/CD automation (Abdullah Iqbal)
- `dockerization` — Docker containerization (Fatima Naeem)

## Commit Message Style

Use imperative mood and concise scope:
- `feat: add /predictions/summary endpoint`
- `fix: handle scaler feature_names_in_ mismatch`
- `ci: enforce 80% coverage`
- `docs: add architecture diagram`

## How to Contribute

1. Create a feature branch from `main` using the naming convention above.
2. Ensure local checks pass:
   - `make lint`
   - `make test` (coverage >= 80%)
   - `pre-commit run --all-files`
3. Open a Pull Request with a clear description and screenshots where helpful.
4. Address review comments; squash & merge when approved.

## Pre-commit Hooks

Install and run once per repo clone:

```bash
pre-commit install
pre-commit run --all-files
```

Mandatory hooks are configured in `.pre-commit-config.yaml`:
- trailing-whitespace
- end-of-file-fixer
- detect-secrets
- black (format) — optional but recommended
- ruff (lint) — optional but recommended

## Acknowledgements

Please add any external resources, inspiration, or datasets that helped during the project.
