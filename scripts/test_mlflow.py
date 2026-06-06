"""
Example script to test MLflow setup with PostgreSQL and RustFS
Run this after starting the Docker Compose services
"""

import mlflow
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score, f1_score
import numpy as np

# Configure MLflow
mlflow.set_tracking_uri("http://localhost:5010")

# Configure RustFS (S3) for artifact storage
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'
os.environ['AWS_ACCESS_KEY_ID'] = 'rustfs'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'rustfs123'

def train_model():
    """Train a simple model and log to MLflow"""
    
    # Set experiment name
    mlflow.set_experiment("iris-classification-demo")
    
    # Load data
    print("Loading iris dataset...")
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=42
    )
    
    # Train model with MLflow tracking
    with mlflow.start_run(run_name="random-forest-v1"):
        print("Training model...")
        
        # Log parameters
        n_estimators = 100
        max_depth = 5
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("model_type", "RandomForest")
        
        # Train model
        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42
        )
        clf.fit(X_train, y_train)
        
        # Make predictions
        y_pred = clf.predict(X_test)
        
        # Log metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        
        print(f"Accuracy: {accuracy:.4f}")
        print(f"F1 Score: {f1:.4f}")
        
        # Log model
        mlflow.sklearn.log_model(clf, "model")
        
        # Create and log a simple artifact
        feature_importance = dict(zip(iris.feature_names, clf.feature_importances_))
        
        with open("feature_importance.txt", "w") as f:
            f.write("Feature Importance:\n")
            for feature, importance in sorted(feature_importance.items(), 
                                             key=lambda x: x[1], 
                                             reverse=True):
                f.write(f"{feature}: {importance:.4f}\n")
        
        mlflow.log_artifact("feature_importance.txt")
        os.remove("feature_importance.txt")
        
        # Log tags
        mlflow.set_tag("dataset", "iris")
        mlflow.set_tag("framework", "scikit-learn")
        
        run_id = mlflow.active_run().info.run_id
        print(f"\n✅ Run completed successfully!")
        print(f"Run ID: {run_id}")
        print(f"View in MLflow UI: http://localhost:5010")
        
    return run_id

def load_and_predict(run_id):
    """Load a logged model and make predictions"""
    
    print(f"\nLoading model from run: {run_id}")
    model_uri = f"runs:/{run_id}/model"
    loaded_model = mlflow.sklearn.load_model(model_uri)
    
    # Make a prediction
    test_data = np.array([[5.1, 3.5, 1.4, 0.2]])  # Example iris data
    prediction = loaded_model.predict(test_data)
    
    iris = load_iris()
    print(f"Prediction for {test_data[0]}: {iris.target_names[prediction[0]]}")

if __name__ == "__main__":
    print("=" * 60)
    print("MLflow Demo - Iris Classification")
    print("=" * 60)
    
    try:
        # Train and log a model
        run_id = train_model()
        
        # Load and use the model
        load_and_predict(run_id)
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("Check the MLflow UI at http://localhost:5010")
        print("Check RustFS console at http://localhost:9001")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Docker Compose services are running:")
        print("  docker-compose up -d")
        print("\nThen wait a moment for services to initialize.")
