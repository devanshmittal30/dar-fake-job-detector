"""tests/test_evaluate.py
Unit tests for model evaluation artifacts, metrics, and error analysis.
"""

import json
from pathlib import Path
import pandas as pd
import pytest


def test_metrics_json_structure_and_values():
    """Verify that models/metrics.json exists and adheres to the specified structure."""
    metrics_path = Path("models/metrics.json")
    assert metrics_path.exists(), "models/metrics.json not found."

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # Check top-level structure: model > split > metric
    assert "lr" in metrics
    assert "rf" in metrics
    assert "test" in metrics["lr"]
    assert "test" in metrics["rf"]

    lr_test = metrics["lr"]["test"]
    rf_test = metrics["rf"]["test"]

    # Verify scalar metric presence and sanity
    for m in [lr_test, rf_test]:
        assert "accuracy" in m and 0.90 <= m["accuracy"] <= 1.0
        assert "precision" in m and 0.50 <= m["precision"] <= 1.0
        assert "recall" in m and 0.50 <= m["recall"] <= 1.0
        assert "f1" in m and 0.50 <= m["f1"] <= 1.0
        assert "roc_auc" in m and 0.90 <= m["roc_auc"] <= 1.0
        assert "pr_auc" in m and 0.70 <= m["pr_auc"] <= 1.0
        assert "confusion_matrix" in m

    # Logistic Regression must have higher F1 than Random Forest
    assert lr_test["f1"] > rf_test["f1"]


def test_error_analysis_file():
    """Verify models/error_analysis.csv contains 10 false positives and 10 false negatives."""
    err_path = Path("models/error_analysis.csv")
    assert err_path.exists(), "models/error_analysis.csv does not exist."

    df = pd.read_csv(err_path)
    assert len(df) == 20
    assert "error_type" in df.columns
    assert "predicted_prob" in df.columns
    assert "label" in df.columns
    assert "text" in df.columns
    assert "viva_reason" in df.columns

    fp_count = (df["error_type"].str.contains("False Positive")).sum()
    fn_count = (df["error_type"].str.contains("False Negative")).sum()
    assert fp_count == 10
    assert fn_count == 10


def test_evaluation_plots_exist():
    """Verify that all 4 required evaluation plots are saved in app/static/img/plots/."""
    plots_dir = Path("app/static/img/plots")
    expected_plots = [
        "eval_confusion_matrices.png",
        "eval_metric_comparison.png",
        "eval_roc_pr_curves.png",
        "eval_top_words_coefficients.png"
    ]
    for plot_name in expected_plots:
        plot_path = plots_dir / plot_name
        assert plot_path.exists(), f"Missing evaluation plot: {plot_name}"
        assert plot_path.stat().st_size > 5000, f"Plot file seems empty: {plot_name}"


def test_default_model_configured():
    """Verify that default_model in models/model_config.json is set to 'lr'."""
    config_path = Path("models/model_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    assert config.get("default_model") == "lr"
