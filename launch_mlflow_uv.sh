#!/bin/bash

# Launch MLflow light with uv (no Docker, no venv setup)
# Metadata: SQLite at ~/volumes/mlflow-light/db/mlflow.db
# Artifacts: ~/volumes/mlflow-light/artifacts

mkdir -p ~/volumes/mlflow-light/db
mkdir -p ~/volumes/mlflow-light/artifacts

uvx --with 'mlflow[genai]' mlflow server \
  --backend-store-uri sqlite:///$(eval echo ~/volumes/mlflow-light/db/mlflow.db) \
  --default-artifact-root $(eval echo ~/volumes/mlflow-light/artifacts) \
  --host 0.0.0.0 \
  --port 5010
