# src/train_model.py
import boto3
import pandas as pd
from io import StringIO, BytesIO
import os
import numpy as np
import mlflow
import mlflow.sklearn
from datetime import datetime
import json
import joblib
from dotenv import load_dotenv

# Import sklearn components
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def load_data_from_s3():
    """Load data from S3 bucket"""
    load_dotenv()

    bucket_name = "my-feature-store-data"
    s3_key = "pipeline-data/data.csv"

    # Create an S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    # Fetch the object from S3
    response = s3.get_object(Bucket=bucket_name, Key=s3_key)

    # Read the CSV content
    csv_data = response["Body"].read().decode("utf-8")

    # Convert to DataFrame
    df = pd.read_csv(StringIO(csv_data))

    print(f"Data loaded. Shape: {df.shape}")
    print("Null values:")
    print(df.isnull().sum())

    return df


def prepare_data(df):
    """Prepare data for training"""
    target_columns = ["aqi_index", "Calculated_AQI"]
    targets = df[target_columns]
    X = df.drop(columns=target_columns)

    # Final check for datetime columns
    X = X.select_dtypes(exclude=["datetime64[ns]"])

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, targets, test_size=0.2, random_state=42
    )

    return X_train, X_test, y_train, y_test, target_columns


def initialize_models():
    """Initialize all models to evaluate"""
    models = {
        "Random_Forest": RandomForestRegressor(
            n_estimators=300, max_depth=10, random_state=42
        ),
        "Gradient_Boosting": MultiOutputRegressor(
            GradientBoostingRegressor(n_estimators=300, max_depth=3, random_state=42)
        ),
        "Linear_Regression": LinearRegression(),
        "Ridge_Regression": Ridge(alpha=1.0),
        "SVR": MultiOutputRegressor(SVR()),
        "Neural_Network": MultiOutputRegressor(
            MLPRegressor(max_iter=200, random_state=42)
        ),
    }
    return models


def train_and_evaluate(models, X_train, X_test, y_train, y_test, target_columns):
    """Train models and log to MLflow"""
    results = []
    best_model = None
    best_model_name = None
    best_avg_rmse = float("inf")

    for model_name, model in models.items():
        # Start MLflow run for each model
        with mlflow.start_run(
            run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ):
            print(f"Training {model_name}...")

            # Log model parameters
            if hasattr(model, "get_params"):
                mlflow.log_params(model.get_params())

            # Train model
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            # Calculate metrics for each target
            model_results = {"Model": model_name}
            rmse_scores = []

            for i, col in enumerate(target_columns):
                rmse = np.sqrt(mean_squared_error(y_test.iloc[:, i], y_pred[:, i]))
                mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
                r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])

                rmse_scores.append(rmse)
                model_results[f"RMSE_{col}"] = rmse
                model_results[f"MAE_{col}"] = mae
                model_results[f"R²_{col}"] = r2

                # Log metrics to MLflow for each target
                mlflow.log_metric(f"rmse_{col}", rmse)
                mlflow.log_metric(f"mae_{col}", mae)
                mlflow.log_metric(f"r2_{col}", r2)

                print(f"  Target: {col}")
                print(f"    RMSE: {rmse:.4f}")
                print(f"    MAE: {mae:.4f}")
                print(f"    R²: {r2:.4f}")

            # Calculate average RMSE across all targets
            avg_rmse = np.mean(rmse_scores)
            avg_mae = np.mean([model_results[f"MAE_{col}"] for col in target_columns])
            avg_r2 = np.mean([model_results[f"R²_{col}"] for col in target_columns])

            model_results["Avg_RMSE"] = avg_rmse
            results.append(model_results)

            # Log aggregate metrics
            mlflow.log_metric("avg_rmse", avg_rmse)
            mlflow.log_metric("avg_mae", avg_mae)
            mlflow.log_metric("avg_r2", avg_r2)

            # Log model
            mlflow.sklearn.log_model(model, f"model_{model_name}")

            # Add tags
            mlflow.set_tag("model_type", model_name)
            mlflow.set_tag("targets", str(target_columns))

            print(f"  Average RMSE: {avg_rmse:.4f}\n")

            if avg_rmse < best_avg_rmse:
                best_avg_rmse = avg_rmse
                best_model = model
                best_model_name = model_name

    return results, best_model, best_model_name, best_avg_rmse


def register_best_model(best_model, best_model_name, best_avg_rmse):
    """Register the best model in MLflow Model Registry"""
    print(f"\nBest model: {best_model_name} (Average RMSE = {best_avg_rmse:.4f})")

    # Register the best model
    with mlflow.start_run(
        run_name=f"BEST_{best_model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ):
        mlflow.sklearn.log_model(
            best_model, "best_model", registered_model_name="AQI_Weather_Best_Model"
        )
        mlflow.log_metric("best_avg_rmse", best_avg_rmse)
        mlflow.set_tag("best_model", best_model_name)
        mlflow.set_tag("production_ready", "true")

    print(f"Model '{best_model_name}' registered in MLflow Model Registry")


def upload_model_to_s3(model, bucket_name="my-feature-store-data"):
    """Upload trained model to S3"""
    S3_MODEL_KEY = "models/best_model.pkl"
    S3_METADATA_KEY = "models/best_model_metadata.json"

    # Create an S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    # Save model to BytesIO buffer
    model_buffer = BytesIO()
    joblib.dump(model, model_buffer)
    model_buffer.seek(0)
    s3.upload_fileobj(model_buffer, Bucket=bucket_name, Key=S3_MODEL_KEY)
    print(f"Model uploaded to s3://{bucket_name}/{S3_MODEL_KEY}")

    # Save version metadata
    metadata = {
        "sklearn_version": joblib.__version__,
        "numpy_version": np.__version__,
        "model_type": type(model).__name__,
        "upload_timestamp": datetime.now().isoformat(),
    }

    metadata_buffer = BytesIO()
    metadata_buffer.write(json.dumps(metadata, indent=2).encode("utf-8"))
    metadata_buffer.seek(0)
    s3.upload_fileobj(metadata_buffer, Bucket=bucket_name, Key=S3_METADATA_KEY)
    print(f"Metadata uploaded to s3://{bucket_name}/{S3_METADATA_KEY}")


def main():
    """Main training pipeline"""
    print("Starting AQI Weather Prediction Training Pipeline...")

    # Configure MLflow
    # Use environment variable or default to Docker service
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5001")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow Tracking URI: {tracking_uri}")

    # Set experiment
    mlflow.set_experiment("AQI_Weather_Prediction")

    try:
        # Step 1: Load data
        print("\n1. Loading data from S3...")
        df = load_data_from_s3()

        # Step 2: Prepare data
        print("\n2. Preparing data...")
        X_train, X_test, y_train, y_test, target_columns = prepare_data(df)

        # Step 3: Initialize models
        print("\n3. Initializing models...")
        models = initialize_models()

        # Step 4: Train and evaluate
        print("\n4. Training and evaluating models...")
        results, best_model, best_model_name, best_avg_rmse = train_and_evaluate(
            models, X_train, X_test, y_train, y_test, target_columns
        )

        # Step 5: Register best model
        print("\n5. Registering best model...")
        register_best_model(best_model, best_model_name, best_avg_rmse)

        # Step 6: Upload to S3 (optional)
        print("\n6. Uploading best model to S3...")
        upload_model_to_s3(best_model)

        # Step 7: Print summary
        print("\n7. Training Summary:")
        results_df = pd.DataFrame(results)
        print(results_df.to_string())

        # Save results locally
        results_df.to_csv("/app/data/training_results.csv", index=False)
        print("\nResults saved to '/app/data/training_results.csv'")

        return results_df

    except Exception as e:
        print(f"Error in training pipeline: {str(e)}")
        raise


if __name__ == "__main__":
    main()
