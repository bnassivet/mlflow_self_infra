import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv


def serve_light():
    load_dotenv()
    port = os.environ.get("MLFLOW_PORT", "5010")
    db_path = Path.home() / "volumes/mlflow-light/db/mlflow.db"
    artifacts_path = Path.home() / "volumes/mlflow-light/artifacts"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts_path.mkdir(parents=True, exist_ok=True)

    # Note: We use subprocess.run to launch the MLflow server in the foreground, which allows us to see logs directly in the terminal.
    # Print subprocess.run paramaters for debugging
    print("Running subprocess with the following parameters:")
    print(f"Command: mlflow server --backend-store-uri sqlite:///{db_path} --default-artifact-root {artifacts_path} --host 0.0.0.0 --port {port}")
    subprocess.run([
        "mlflow", "server",
        "--backend-store-uri", f"sqlite:///{db_path}",
        "--default-artifact-root", str(artifacts_path),
        "--host", "0.0.0.0",
        "--port", port,
    ], env={**os.environ})
