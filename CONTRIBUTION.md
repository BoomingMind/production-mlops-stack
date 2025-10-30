# Contribution Guide

This document captures team member details, task ownership, branching conventions, and how to contribute effectively to the project.

## Team Members

| Name | ERP/Student ID | Role | Contact |
|------|-----------------|------|---------|
| Abdullah Iqbal | 26904 | Pipelines (CI/CD), Data Ingestion & Preprocessing | a.iqbal.26904@khi.iba.edu.pk |
| Hussain Ali Shah | <ERP-ID> | API Development (FastAPI) | <email/handle> |
| Haseeb Ahmed | 26077 | Model Training & Prediction | <email/handle> |
| Fatima Naeem | <ERP-ID> | Dockerization | <email/handle> |


## Task Mapping (Who did what)

| Area | Tasks | Owner |
|------|-------|-------|
| Data Preparation | Data fetching, cleaning/preprocessing, basic EDA, feature engineering | Abdullah Iqbal |
| Model Training | Model development, training/tuning, validation, prediction pipeline | Haseeb Ahmed |
| Inference API | FastAPI service, endpoints, input/output schema | Hussain Ali Shah |
| CI/CD Pipelines | Automated workflows for lint, tests, coverage, Docker build/push, deploy | Abdullah Iqbal |
| Dockerization | Dockerfile, docker-compose, image optimization | Fatima Naeem |
| Monitoring | Prometheus metrics, Grafana dashboards, Evidently drift | — (TBD) |
| Cloud | S3/EC2/Lambda/CloudWatch (if used) | — (TBD) |

## Branch Naming Convention

Follow short, consistent prefixes:

- `feat/<short-description>` — New features or endpoints
- `fix/<short-description>` — Bug fixes
- `infra/<short-description>` — CI/CD, Docker, Makefile, provisioning
- `docs/<short-description>` — Documentation only
- `chore/<short-description>` — Misc chores (no functional change)

Examples:
- `feat/predictions-by-date`
- `fix/metrics-latency-labels`
- `infra/ghcr-publish`

### Branches used in this project
- `feat/fast-api` — API development (Hussain Ali Shah)
- `feat/model-training` — Model training and prediction (Haseeb Ahmed)
> If additional branches were used (e.g., for CI/CD or Dockerization), list them here as well (e.g., `infra/ci-cd`, `infra/dockerization`).

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
