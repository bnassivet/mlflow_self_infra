"""
Example script to test MLflow setup with PostgreSQL and AWS S3
Run this after starting the Docker Compose services and configuring AWS credentials
"""

import mlflow
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score, f1_score
import numpy as np

# Configure MLflow
mlflow.set_tracking_uri("http://localhost:5000")

# Configure AWS credentials
# These should match the values in your .env file
print("⚠️  Make sure to set your AWS credentials as environment variables:")
print("  export AWS_ACCESS_KEY_ID=your_access_key")
print("  export AWS_SECRET_ACCESS_KEY=your_secret_key")
print("  export AWS_DEFAULT_REGION=us-east-1")
print()

# Check if AWS credentials are set
if not os.environ.get('AWS_ACCESS_KEY_ID'):
    print("❌ AWS_ACCESS_KEY_ID not set!")
    print("Set it with: export AWS_ACCESS_KEY_ID=your_key")
    exit(1)

if not os.environ.get('AWS_SECRET_ACCESS_KEY'):
    print("❌ AWS_SECRET_ACCESS_KEY not set!")
    print("Set it with: export AWS_SECRET_ACCESS_KEY=your_secret")
    exit(1)

def train_model():
    """Train a simple model and log to MLflow"""
    
    # Set experiment name
    mlflow.set_experiment("iris-classification-aws-demo")
    
    # Load data
    print("Loading iris dataset...")
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=42
    )
    
    # Train model with MLflow tracking
    with mlflow.start_run(run_name="random-forest-aws-s3"):
        print("Training model...")
        
        # Log parameters
        n_estimators = 100
        max_depth = 5
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("model_type", "RandomForest")
        mlflow.log_param("storage_backend", "AWS S3")
        
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
        
        # Log model (will be stored in S3)
        print("Logging model to S3...")
        mlflow.sklearn.log_model(clf, "model")
        
        # Create and log a simple artifact (will be stored in S3)
        feature_importance = dict(zip(iris.feature_names, clf.feature_importances_))
        
        with open("feature_importance.txt", "w") as f:
            f.write("Feature Importance:\n")
            for feature, importance in sorted(feature_importance.items(), 
                                             key=lambda x: x[1], 
                                             reverse=True):
                f.write(f"{feature}: {importance:.4f}\n")
        
        print("Logging artifact to S3...")
        mlflow.log_artifact("feature_importance.txt")
        os.remove("feature_importance.txt")
        
        # Log tags
        mlflow.set_tag("dataset", "iris")
        mlflow.set_tag("framework", "scikit-learn")
        mlflow.set_tag("cloud_provider", "AWS")
        
        run_id = mlflow.active_run().info.run_id
        artifact_uri = mlflow.get_artifact_uri()
        
        print(f"\n✅ Run completed successfully!")
        print(f"Run ID: {run_id}")
        print(f"Artifact URI: {artifact_uri}")
        print(f"View in MLflow UI: http://localhost:5000")
        
    return run_id

def load_and_predict(run_id):
    """Load a logged model from S3 and make predictions"""
    
    print(f"\nLoading model from S3 (run: {run_id})...")
    model_uri = f"runs:/{run_id}/model"
    
    try:
        loaded_model = mlflow.sklearn.load_model(model_uri)
        
        # Make a prediction
        test_data = np.array([[5.1, 3.5, 1.4, 0.2]])  # Example iris data
        prediction = loaded_model.predict(test_data)
        
        iris = load_iris()
        print(f"✅ Prediction for {test_data[0]}: {iris.target_names[prediction[0]]}")
    except Exception as e:
        print(f"❌ Error loading model from S3: {e}")
        print("Make sure your AWS credentials have read access to the S3 bucket")

if __name__ == "__main__":
    print("=" * 70)
    print("MLflow Demo - Iris Classification with AWS S3")
    print("=" * 70)
    
    try:
        # Train and log a model
        run_id = train_model()
        
        # Load and use the model from S3
        load_and_predict(run_id)
        
        print("\n" + "=" * 70)
        print("✅ Demo completed successfully!")
        print("=" * 70)
        print("📊 Check the MLflow UI at http://localhost:5000")
        print("☁️  Artifacts are stored in your AWS S3 bucket")
        print("\n💡 To view your S3 artifacts:")
        print("   aws s3 ls s3://your-bucket-name/mlflow-artifacts/ --recursive")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Docker Compose services are running:")
        print("   docker-compose -f docker-compose-aws.yml up -d")
        print("2. Check that AWS credentials are set:")
        print("   echo $AWS_ACCESS_KEY_ID")
        print("3. Verify S3 bucket exists and is accessible:")
        print("   aws s3 ls s3://your-bucket-name/")
        print("4. Check MLflow logs:")
        print("   docker-compose -f docker-compose-aws.yml logs mlflow")
