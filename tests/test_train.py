"""tests/test_train.py
Unit tests for model training outputs, model pipelines, and configuration.
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pytest

from ml.train import find_optimal_threshold


def test_find_optimal_threshold():
    """Verify that find_optimal_threshold finds the threshold maximizing F1."""
    # Synthetic labels and predicted probabilities
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_probs = np.array([0.1, 0.2, 0.4, 0.6, 0.7, 0.9])

    threshold, f1 = find_optimal_threshold(y_true, y_probs)
    assert 0.4 < threshold <= 0.6
    assert f1 == 1.0  # Perfect separation at t ~ 0.5


def test_model_files_exist_and_under_size_limit():
    """Verify that both model files exist and are strictly under 50 MB."""
    lr_path = Path("models/lr_pipeline.joblib")
    rf_path = Path("models/rf_pipeline.joblib")

    assert lr_path.exists(), "models/lr_pipeline.joblib does not exist."
    assert rf_path.exists(), "models/rf_pipeline.joblib does not exist."

    lr_size_mb = lr_path.stat().st_size / (1024 * 1024)
    rf_size_mb = rf_path.stat().st_size / (1024 * 1024)

    assert lr_size_mb < 50.0, f"Logistic Regression model too large: {lr_size_mb:.2f} MB"
    assert rf_size_mb < 50.0, f"Random Forest model too large: {rf_size_mb:.2f} MB"


def test_models_load_and_predict():
    """Verify that both pipelines load cleanly and execute predict_proba on sample text."""
    lr_pipeline = joblib.load("models/lr_pipeline.joblib")
    rf_pipeline = joblib.load("models/rf_pipeline.joblib")

    # Check required pipeline steps
    assert "tfidf" in lr_pipeline.named_steps
    assert "clf" in lr_pipeline.named_steps
    assert "tfidf" in rf_pipeline.named_steps
    assert "clf" in rf_pipeline.named_steps

    sample_texts = [
        "Earn $5000 weekly data entry work from home no experience needed wire fee",
        "Senior software engineer building backend services with python and sql"
    ]

    for model, name in [(lr_pipeline, "LR"), (rf_pipeline, "RF")]:
        probs = model.predict_proba(sample_texts)
        assert probs.shape == (2, 2), f"{name} output shape mismatch"
        # Probabilities sum to 1
        assert np.allclose(probs.sum(axis=1), 1.0), f"{name} probabilities do not sum to 1"
        # Suspicious text should have higher fake probability than normal text
        assert probs[0, 1] > probs[1, 1], f"{name} did not assign higher score to scam text"


def test_model_config_structure():
    """Verify that models/model_config.json contains all required schema keys."""
    config_path = Path("models/model_config.json")
    assert config_path.exists(), "models/model_config.json does not exist."

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Check key structure
    required_keys = [
        "thresholds",
        "uncertain_band",
        "sklearn_version",
        "training_date",
        "dataset_names",
        "dataset_row_counts",
        "training_row_count",
        "best_parameters"
    ]
    for key in required_keys:
        assert key in config, f"Missing key in model_config.json: {key}"

    # Verify threshold values are valid probabilities
    assert 0.0 < config["thresholds"]["lr"] < 1.0
    assert 0.0 < config["thresholds"]["rf"] < 1.0
    assert config["uncertain_band"] == 0.10
    assert config["training_row_count"] == 12599
