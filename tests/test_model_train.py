"""
Unit tests for model training pipeline.

Tests cover:
1. Data loading from S3
2. Data preparation
3. Model initialization
4. Training and evaluation
5. Model registration
6. Model upload to S3
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestDataLoading:
    """Tests for data loading functions."""

    @patch("src.model_train.boto3.client")
    @patch.dict(
        os.environ,
        {"AWS_ACCESS_KEY_ID": "test_key", "AWS_SECRET_ACCESS_KEY": "test_secret"},
    )
    def test_load_data_from_s3_success(self, mock_boto3_client):
        """Test successful data loading from S3."""
        # Mock S3 response
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        # Mock CSV data
        csv_data = "aqi_index,Calculated_AQI,col1,col2\n1,2,3,4\n5,6,7,8"
        mock_response = {"Body": MagicMock()}
        mock_response["Body"].read.return_value.decode.return_value = csv_data
        mock_s3.get_object.return_value = mock_response

        from src.model_train import load_data_from_s3

        df = load_data_from_s3()

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 4)
        assert list(df.columns) == ["aqi_index", "Calculated_AQI", "col1", "col2"]
        mock_s3.get_object.assert_called_once()

    @patch("src.model_train.boto3.client")
    def test_load_data_from_s3_missing_env_vars(self, mock_boto3_client):
        """Test data loading with missing environment variables."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        # Remove env vars
        with patch.dict(os.environ, {}, clear=True):
            from src.model_train import load_data_from_s3

            with pytest.raises(Exception):  # boto3 should fail without credentials
                load_data_from_s3()


class TestDataPreparation:
    """Tests for data preparation functions."""

    def test_prepare_data(self):
        """Test data preparation for training."""
        # Create sample dataframe
        data = {
            "aqi_index": [1, 2, 3, 4],
            "Calculated_AQI": [10, 20, 30, 40],
            "feature1": [0.1, 0.2, 0.3, 0.4],
            "feature2": [1.0, 2.0, 3.0, 4.0],
            "datetime_col": pd.date_range("2023-01-01", periods=4),
        }
        df = pd.DataFrame(data)

        from src.model_train import prepare_data

        X_train, X_test, y_train, y_test, target_columns = prepare_data(df)

        # Check shapes
        assert X_train.shape[0] + X_test.shape[0] == 4  # total rows
        assert y_train.shape[0] + y_test.shape[0] == 4
        assert y_train.shape[1] == 2  # two targets
        assert y_test.shape[1] == 2

        # Check target columns
        assert target_columns == ["aqi_index", "Calculated_AQI"]

        # Check that datetime column is excluded
        assert "datetime_col" not in X_train.columns
        assert "datetime_col" not in X_test.columns


class TestModelInitialization:
    """Tests for model initialization."""

    def test_initialize_models(self):
        """Test that models are initialized correctly."""
        from src.model_train import initialize_models

        models = initialize_models()

        expected_models = [
            "Random_Forest",
            "Gradient_Boosting",
            "Linear_Regression",
            "Ridge_Regression",
            "SVR",
            "Neural_Network",
        ]

        assert set(models.keys()) == set(expected_models)

        # Check that models are sklearn estimators
        for model in models.values():
            assert hasattr(model, "fit")
            assert hasattr(model, "predict")


class TestTrainingAndEvaluation:
    """Tests for training and evaluation functions."""

    @patch("src.model_train.mlflow")
    def test_train_and_evaluate(self, mock_mlflow):
        """Test training and evaluation of models."""
        # Mock MLflow
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()

        # Create sample data
        X_train = pd.DataFrame({"feature1": [1, 2, 3, 4], "feature2": [10, 20, 30, 40]})
        X_test = pd.DataFrame({"feature1": [5, 6], "feature2": [50, 60]})
        y_train = pd.DataFrame(
            {"aqi_index": [1, 2, 3, 4], "Calculated_AQI": [10, 20, 30, 40]}
        )
        y_test = pd.DataFrame({"aqi_index": [5, 6], "Calculated_AQI": [50, 60]})
        target_columns = ["aqi_index", "Calculated_AQI"]

        # Simple models for testing
        models = {
            "Linear_Regression": LinearRegression(),
            "Random_Forest": RandomForestRegressor(n_estimators=10, random_state=42),
        }

        from src.model_train import train_and_evaluate

        results, best_model, best_model_name, best_avg_rmse = train_and_evaluate(
            models, X_train, X_test, y_train, y_test, target_columns
        )

        # Check results
        assert len(results) == 2
        assert best_model is not None
        assert best_model_name in models.keys()
        assert isinstance(best_avg_rmse, float)

        # Check that MLflow was called
        assert mock_mlflow.start_run.call_count == 2  # one for each model
        assert mock_mlflow.log_metric.called
        assert mock_mlflow.sklearn.log_model.called

    @patch("src.model_train.mlflow")
    def test_register_best_model(self, mock_mlflow):
        """Test model registration in MLflow."""
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()

        model = LinearRegression()
        model_name = "Test_Model"
        avg_rmse = 1.5

        from src.model_train import register_best_model

        register_best_model(model, model_name, avg_rmse)

        # Check MLflow calls
        mock_mlflow.start_run.assert_called_once()
        mock_mlflow.sklearn.log_model.assert_called_once()
        mock_mlflow.log_metric.assert_called_once_with("best_avg_rmse", avg_rmse)
        mock_mlflow.set_tag.assert_called()

    @patch("src.model_train.boto3.client")
    @patch.dict(
        os.environ,
        {"AWS_ACCESS_KEY_ID": "test_key", "AWS_SECRET_ACCESS_KEY": "test_secret"},
    )
    def test_upload_model_to_s3(self, mock_boto3_client):
        """Test model upload to S3."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        model = LinearRegression()

        from src.model_train import upload_model_to_s3

        upload_model_to_s3(model)

        # Check that upload_fileobj was called twice (model and metadata)
        assert mock_s3.upload_fileobj.call_count == 2

    @patch("src.model_train.load_data_from_s3")
    @patch("src.model_train.prepare_data")
    @patch("src.model_train.initialize_models")
    @patch("src.model_train.train_and_evaluate")
    @patch("src.model_train.register_best_model")
    @patch("src.model_train.upload_model_to_s3")
    @patch("src.model_train.mlflow")
    @patch("src.model_train.pd.DataFrame.to_csv")
    def test_main_pipeline(
        self,
        mock_to_csv,
        mock_mlflow,
        mock_upload,
        mock_register,
        mock_train_eval,
        mock_init_models,
        mock_prepare,
        mock_load,
    ):
        """Test the main training pipeline."""
        # Mock returns
        mock_df = MagicMock()
        mock_load.return_value = mock_df

        mock_X_train = MagicMock()
        mock_X_test = MagicMock()
        mock_y_train = MagicMock()
        mock_y_test = MagicMock()
        mock_targets = ["aqi_index", "Calculated_AQI"]
        mock_prepare.return_value = (
            mock_X_train,
            mock_X_test,
            mock_y_train,
            mock_y_test,
            mock_targets,
        )

        mock_models = {"model1": MagicMock()}
        mock_init_models.return_value = mock_models

        mock_results = [{"Model": "model1", "Avg_RMSE": 1.0}]
        mock_best_model = MagicMock()
        mock_best_name = "model1"
        mock_best_rmse = 1.0
        mock_train_eval.return_value = (
            mock_results,
            mock_best_model,
            mock_best_name,
            mock_best_rmse,
        )

        from src.model_train import main

        main()

        # Check that all functions were called
        mock_load.assert_called_once()
        mock_prepare.assert_called_once_with(mock_df)
        mock_init_models.assert_called_once()
        mock_train_eval.assert_called_once()
        mock_register.assert_called_once_with(
            mock_best_model, mock_best_name, mock_best_rmse
        )
        mock_upload.assert_called_once_with(mock_best_model)
        mock_to_csv.assert_called_once()

        # Check MLflow setup
        mock_mlflow.set_tracking_uri.assert_called()
        mock_mlflow.set_experiment.assert_called_with("AQI_Weather_Prediction")
