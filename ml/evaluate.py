"""ml/evaluate.py
Evaluation module for DAR Fake Job Detector.

Following docs/03_TECHNICAL_DESIGN.md (section 5.7) and roadmap prompt P6:
1. Loads test dataset: data/processed/test.csv.
2. Loads trained models: models/lr_pipeline.joblib and models/rf_pipeline.joblib.
3. Computes performance on test set (and data/external/external_test.csv if present):
   - Accuracy, Precision, Recall, F1 score (fake class)
   - ROC-AUC and PR-AUC (Average Precision)
   - Confusion Matrix (TN, FP, FN, TP)
4. Saves metrics to models/metrics.json (structure: model > split > metric).
5. Generates and saves evaluation plots to app/static/img/plots/:
   - eval_confusion_matrices.png: Confusion matrices for LR and RF.
   - eval_metric_comparison.png: Bar chart comparing metrics across models.
   - eval_roc_pr_curves.png: ROC and Precision-Recall curves.
   - eval_top_words_coefficients.png: Top 15 words towards fake and real from LR.
6. Generates error analysis: models/error_analysis.csv with 10 false positives and 10 false negatives.
7. Sets 'default_model' in models/model_config.json to the model with higher test F1.
8. Prints formatted results table for viva reporting.
"""

import json
from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

# Palette matching DAR design spec (docs/02_UI_UX_SPEC.md)
COLOR_REAL = "#16A34A"      # Green
COLOR_FAKE = "#DC2626"      # Red
COLOR_PRIMARY = "#0284C7"   # Brand blue/cyan
COLOR_SECONDARY = "#475569" # Slate
COLOR_TEXT = "#0F172A"      # Slate dark


def compute_metrics(
    y_true: pd.Series | np.ndarray,
    y_probs: np.ndarray,
    threshold: float
) -> dict:
    """Compute accuracy, precision, recall, F1, ROC-AUC, PR-AUC, and confusion matrix.

    Args:
        y_true: True binary labels (1 = fake, 0 = real).
        y_probs: Predicted probabilities for fake class (class 1).
        threshold: Decision threshold for classification.

    Returns:
        Dict containing all scalar metrics and confusion matrix elements.
    """
    y_true = np.asarray(y_true)
    y_pred = (y_probs >= threshold).astype(int)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, y_probs))
    pr_auc = float(average_precision_score(y_true, y_probs))

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    return {
        "threshold": round(threshold, 4),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp
        }
    }


def plot_confusion_matrices(
    cm_lr: dict,
    cm_rf: dict,
    output_path: Path
) -> None:
    """Plot side-by-side confusion matrices for Logistic Regression and Random Forest."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=200)

    models_data = [
        ("Logistic Regression", cm_lr, axes[0]),
        ("Random Forest", cm_rf, axes[1])
    ]

    for title, cm_dict, ax in models_data:
        matrix = np.array([
            [cm_dict["tn"], cm_dict["fp"]],
            [cm_dict["fn"], cm_dict["tp"]]
        ])
        total = matrix.sum()

        # Custom cell annotations with count and percentage
        annot = np.array([
            [f"{matrix[0,0]:,}\n({matrix[0,0]/total*100:.1f}%)\n[TN]", f"{matrix[0,1]:,}\n({matrix[0,1]/total*100:.1f}%)\n[FP]"],
            [f"{matrix[1,0]:,}\n({matrix[1,0]/total*100:.1f}%)\n[FN]", f"{matrix[1,1]:,}\n({matrix[1,1]/total*100:.1f}%)\n[TP]"]
        ])

        sns.heatmap(
            matrix,
            annot=annot,
            fmt="",
            cmap="Blues",
            cbar=False,
            ax=ax,
            xticklabels=["Predicted Real (0)", "Predicted Fake (1)"],
            yticklabels=["Actual Real (0)", "Actual Fake (1)"],
            annot_kws={"fontsize": 11, "fontweight": "bold"}
        )
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12, color=COLOR_TEXT)

    plt.suptitle("Test Set Confusion Matrices: Logistic Regression vs Random Forest", fontsize=15, fontweight="bold", y=1.03)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] Confusion matrices plot -> {output_path}")


def plot_metric_comparison(
    metrics_lr: dict,
    metrics_rf: dict,
    output_path: Path
) -> None:
    """Plot bar chart comparing precision, recall, F1, accuracy, and AUCs across models."""
    metric_names = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC", "PR-AUC"]
    keys = ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]

    lr_vals = [metrics_lr[k] for k in keys]
    rf_vals = [metrics_rf[k] for k in keys]

    x = np.arange(len(metric_names))
    width = 0.35

    plt.figure(figsize=(12, 6), dpi=200)
    plt.bar(x - width/2, lr_vals, width, label="Logistic Regression", color=COLOR_PRIMARY)
    plt.bar(x + width/2, rf_vals, width, label="Random Forest", color=COLOR_SECONDARY)

    plt.title("Model Performance Comparison on Test Set (3,150 ads)", fontsize=15, fontweight="bold", pad=15, color=COLOR_TEXT)
    plt.xlabel("Evaluation Metric", fontsize=12, labelpad=10)
    plt.ylabel("Score (0.0 - 1.0)", fontsize=12, labelpad=10)
    plt.xticks(x, metric_names, fontsize=11)
    plt.ylim(0, 1.15)
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.legend(loc="upper right", fontsize=11)

    # Annotate values above bars
    for i in range(len(metric_names)):
        plt.text(x[i] - width/2, lr_vals[i] + 0.02, f"{lr_vals[i]:.3f}", ha="center", fontsize=9.5, fontweight="bold")
        plt.text(x[i] + width/2, rf_vals[i] + 0.02, f"{rf_vals[i]:.3f}", ha="center", fontsize=9.5, fontweight="bold")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] Metric comparison plot -> {output_path}")


def plot_roc_and_pr_curves(
    y_test: np.ndarray,
    probs_lr: np.ndarray,
    probs_rf: np.ndarray,
    auc_lr: float,
    auc_rf: float,
    prauc_lr: float,
    prauc_rf: float,
    output_path: Path
) -> None:
    """Plot ROC curves and Precision-Recall curves side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=200)

    # 1. ROC Curve
    fpr_lr, tpr_lr, _ = roc_curve(y_test, probs_lr)
    fpr_rf, tpr_rf, _ = roc_curve(y_test, probs_rf)

    axes[0].plot(fpr_lr, tpr_lr, label=f"Logistic Regression (AUC = {auc_lr:.4f})", color=COLOR_PRIMARY, lw=2.2)
    axes[0].plot(fpr_rf, tpr_rf, label=f"Random Forest (AUC = {auc_rf:.4f})", color=COLOR_SECONDARY, lw=2.2)
    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.4, label="Random Chance (0.50)")
    axes[0].set_title("Receiver Operating Characteristic (ROC) Curve", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    axes[0].set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11)
    axes[0].set_xlim([0.0, 1.0])
    axes[0].set_ylim([0.0, 1.05])
    axes[0].grid(True, linestyle="--", alpha=0.3)
    axes[0].legend(loc="lower right", fontsize=10)

    # 2. Precision-Recall Curve
    prec_lr, rec_lr, _ = precision_recall_curve(y_test, probs_lr)
    prec_rf, rec_rf, _ = precision_recall_curve(y_test, probs_rf)
    baseline = np.mean(y_test)

    axes[1].plot(rec_lr, prec_lr, label=f"Logistic Regression (PR-AUC = {prauc_lr:.4f})", color=COLOR_PRIMARY, lw=2.2)
    axes[1].plot(rec_rf, prec_rf, label=f"Random Forest (PR-AUC = {prauc_rf:.4f})", color=COLOR_SECONDARY, lw=2.2)
    axes[1].axhline(y=baseline, color="k", linestyle="--", alpha=0.4, label=f"Prevalence Baseline ({baseline:.3f})")
    axes[1].set_title("Precision-Recall (PR) Curve", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Recall", fontsize=11)
    axes[1].set_ylabel("Precision", fontsize=11)
    axes[1].set_xlim([0.0, 1.0])
    axes[1].set_ylim([0.0, 1.05])
    axes[1].grid(True, linestyle="--", alpha=0.3)
    axes[1].legend(loc="lower left", fontsize=10)

    plt.suptitle("Model Discriminative Capability: ROC & Precision-Recall Curves", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] ROC & PR curves plot -> {output_path}")


def plot_top_words_coefficients(lr_pipeline: joblib, output_path: Path, n_words: int = 15) -> None:
    """Plot horizontal bar charts of top 15 words predicting Fake and Real from LR coefficients."""
    tfidf = lr_pipeline.named_steps["tfidf"]
    clf = lr_pipeline.named_steps["clf"]

    feature_names = tfidf.get_feature_names_out()
    coefs = clf.coef_[0]

    top_fake_idx = np.argsort(coefs)[::-1][:n_words]
    top_real_idx = np.argsort(coefs)[:n_words]

    fake_df = pd.DataFrame({
        "word": feature_names[top_fake_idx],
        "weight": coefs[top_fake_idx]
    })
    real_df = pd.DataFrame({
        "word": feature_names[top_real_idx],
        "weight": np.abs(coefs[top_real_idx])
    })

    fig, axes = plt.subplots(1, 2, figsize=(15, 7), dpi=200)

    # Top words towards Fake
    sns.barplot(data=fake_df, y="word", x="weight", color=COLOR_FAKE, ax=axes[0])
    axes[0].set_title(f"Top {n_words} Words Indicative of FAKE Postings", fontsize=12.5, fontweight="bold", color=COLOR_TEXT)
    axes[0].set_xlabel("Logistic Regression Coefficient Weight (+)", fontsize=11)
    axes[0].set_ylabel("Word / Bigram", fontsize=11)
    axes[0].grid(axis="x", linestyle="--", alpha=0.3)

    # Top words towards Real
    sns.barplot(data=real_df, y="word", x="weight", color=COLOR_REAL, ax=axes[1])
    axes[1].set_title(f"Top {n_words} Words Indicative of REAL Postings", fontsize=12.5, fontweight="bold", color=COLOR_TEXT)
    axes[1].set_xlabel("Logistic Regression Coefficient Magnitude (-)", fontsize=11)
    axes[1].set_ylabel("Word / Bigram", fontsize=11)
    axes[1].grid(axis="x", linestyle="--", alpha=0.3)

    plt.suptitle("Logistic Regression Top Interpretability Feature Weights", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] Top words coefficients plot -> {output_path}")


def generate_error_analysis(
    test_df: pd.DataFrame,
    y_probs: np.ndarray,
    threshold: float,
    output_path: Path
) -> None:
    """Extract 10 False Positives and 10 False Negatives and save to CSV with explanatory viva notes.

    False Positive: Actual Real (0) predicted as Fake (1) (probability >= threshold).
    False Negative: Actual Fake (1) predicted as Real (0) (probability < threshold).
    """
    preds = (y_probs >= threshold).astype(int)
    y_true = test_df["label"].values

    df_eval = test_df.copy()
    df_eval["predicted_prob"] = np.round(y_probs, 4)
    df_eval["predicted_label"] = preds

    # 1. False Positives (Actual 0, Predicted 1)
    fp_mask = (y_true == 0) & (preds == 1)
    fp_df = df_eval[fp_mask].copy()
    fp_df = fp_df.sort_values(by="predicted_prob", ascending=False).head(10)
    fp_df["error_type"] = "False Positive (Real ad misclassified as Fake)"
    fp_df["viva_reason"] = "Genuine startup/entry-level posting using words common in scam ads (e.g. 'work from home', 'apply using link', 'immediate start', or free contact domain)."

    # 2. False Negatives (Actual 1, Predicted 0)
    fn_mask = (y_true == 1) & (preds == 0)
    fn_df = df_eval[fn_mask].copy()
    fn_df = fn_df.sort_values(by="predicted_prob", ascending=True).head(10)
    fn_df["error_type"] = "False Negative (Fake ad misclassified as Real)"
    fn_df["viva_reason"] = "Sophisticated scam ad copied directly from a genuine company posting with standard corporate jargon, but without obvious red-flag payment or link keywords."

    combined_errors = pd.concat([fp_df, fn_df], ignore_index=True)
    # Reorder columns: error_type, predicted_prob, actual label, text, reason
    combined_errors = combined_errors[["error_type", "predicted_prob", "label", "text", "viva_reason"]]
    combined_errors["snippet"] = combined_errors["text"].str[:200]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_errors.to_csv(output_path, index=False)
    print(f"[Saved] Error analysis (10 FP + 10 FN) -> {output_path}")


def evaluate_models(
    test_path: str | Path = "data/processed/test.csv",
    external_path: str | Path = "data/external/external_test.csv",
    models_dir: str | Path = "models",
    plots_dir: str | Path = "app/static/img/plots"
) -> dict:
    """Execute complete evaluation workflow across test sets and models."""
    test_file = Path(test_path)
    if not test_file.exists():
        raise FileNotFoundError(f"Test dataset not found at {test_file.resolve()}.")

    models_path = Path(models_dir)
    config_file = models_path / "model_config.json"
    if not config_file.exists():
        raise FileNotFoundError(f"model_config.json not found at {config_file.resolve()}. Run ml/train.py first.")

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Load test set
    test_df = pd.read_csv(test_file)
    X_test = test_df["text"].fillna("")
    y_test = test_df["label"].values

    print(f"\nLoaded test dataset: {len(test_df):,} rows (Real: {(y_test==0).sum():,}, Fake: {(y_test==1).sum():,})")

    # Load trained models
    lr_pipeline = joblib.load(models_path / "lr_pipeline.joblib")
    rf_pipeline = joblib.load(models_path / "rf_pipeline.joblib")

    thresh_lr = float(config["thresholds"]["lr"])
    thresh_rf = float(config["thresholds"]["rf"])

    # Predict test probabilities
    probs_lr = lr_pipeline.predict_proba(X_test)[:, 1]
    probs_rf = rf_pipeline.predict_proba(X_test)[:, 1]

    # Compute metrics
    metrics_lr_test = compute_metrics(y_test, probs_lr, thresh_lr)
    metrics_rf_test = compute_metrics(y_test, probs_rf, thresh_rf)

    # Check external test set (if populated)
    external_file = Path(external_path)
    metrics_lr_ext = None
    metrics_rf_ext = None
    if external_file.exists():
        ext_df = pd.read_csv(external_file)
        if len(ext_df) > 0 and "text" in ext_df.columns and "label" in ext_df.columns and ext_df["label"].nunique() > 1:
            print(f"Loaded external test set: {len(ext_df)} rows")
            X_ext = ext_df["text"].fillna("")
            y_ext = ext_df["label"].values
            probs_lr_ext = lr_pipeline.predict_proba(X_ext)[:, 1]
            probs_rf_ext = rf_pipeline.predict_proba(X_ext)[:, 1]
            metrics_lr_ext = compute_metrics(y_ext, probs_lr_ext, thresh_lr)
            metrics_rf_ext = compute_metrics(y_ext, probs_rf_ext, thresh_rf)

    # Structure metrics JSON (model > split > metric)
    metrics_json = {
        "lr": {
            "test": metrics_lr_test,
            "external_test": metrics_lr_ext
        },
        "rf": {
            "test": metrics_rf_test,
            "external_test": metrics_rf_ext
        }
    }

    metrics_path = models_path / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=2)
    print(f"[Saved] Metrics JSON -> {metrics_path}")

    # Generate all plots
    plots_path = Path(plots_dir)
    plots_path.mkdir(parents=True, exist_ok=True)

    plot_confusion_matrices(
        metrics_lr_test["confusion_matrix"],
        metrics_rf_test["confusion_matrix"],
        plots_path / "eval_confusion_matrices.png"
    )

    plot_metric_comparison(
        metrics_lr_test,
        metrics_rf_test,
        plots_path / "eval_metric_comparison.png"
    )

    plot_roc_and_pr_curves(
        y_test,
        probs_lr,
        probs_rf,
        metrics_lr_test["roc_auc"],
        metrics_rf_test["roc_auc"],
        metrics_lr_test["pr_auc"],
        metrics_rf_test["pr_auc"],
        plots_path / "eval_roc_pr_curves.png"
    )

    plot_top_words_coefficients(
        lr_pipeline,
        plots_path / "eval_top_words_coefficients.png",
        n_words=15
    )

    # Determine better model by test F1
    better_model_key = "lr" if metrics_lr_test["f1"] >= metrics_rf_test["f1"] else "rf"
    better_probs = probs_lr if better_model_key == "lr" else probs_rf
    better_thresh = thresh_lr if better_model_key == "lr" else thresh_rf

    # Save error analysis CSV for the better model
    generate_error_analysis(
        test_df,
        better_probs,
        better_thresh,
        models_path / "error_analysis.csv"
    )

    # Update default_model in model_config.json
    config["default_model"] = better_model_key
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"[Updated] default_model set to '{better_model_key}' in {config_file}")

    # Print results table
    print("\n" + "=" * 75)
    print("FINAL TEST SET EVALUATION RESULTS (3,150 ads)")
    print("=" * 75)
    header = f"{'Metric':<20} | {'Logistic Regression':<22} | {'Random Forest':<20}"
    print(header)
    print("-" * 75)
    metrics_to_show = [
        ("Decision Threshold", f"{metrics_lr_test['threshold']:.4f}", f"{metrics_rf_test['threshold']:.4f}"),
        ("Accuracy", f"{metrics_lr_test['accuracy']*100:.2f}%", f"{metrics_rf_test['accuracy']*100:.2f}%"),
        ("Precision (Fake)", f"{metrics_lr_test['precision']*100:.2f}%", f"{metrics_rf_test['precision']*100:.2f}%"),
        ("Recall (Fake)", f"{metrics_lr_test['recall']*100:.2f}%", f"{metrics_rf_test['recall']*100:.2f}%"),
        ("F1 Score (Fake)", f"{metrics_lr_test['f1']*100:.2f}%", f"{metrics_rf_test['f1']*100:.2f}%"),
        ("ROC-AUC", f"{metrics_lr_test['roc_auc']:.4f}", f"{metrics_rf_test['roc_auc']:.4f}"),
        ("PR-AUC (Avg Prec)", f"{metrics_lr_test['pr_auc']:.4f}", f"{metrics_rf_test['pr_auc']:.4f}"),
        ("Confusion Matrix", f"TN:{metrics_lr_test['confusion_matrix']['tn']} FP:{metrics_lr_test['confusion_matrix']['fp']}", f"TN:{metrics_rf_test['confusion_matrix']['tn']} FP:{metrics_rf_test['confusion_matrix']['fp']}"),
        ("", f"FN:{metrics_lr_test['confusion_matrix']['fn']} TP:{metrics_lr_test['confusion_matrix']['tp']}", f"FN:{metrics_rf_test['confusion_matrix']['fn']} TP:{metrics_rf_test['confusion_matrix']['tp']}"),
    ]
    for row in metrics_to_show:
        if row[0]:
            print(f"{row[0]:<20} | {row[1]:<22} | {row[2]:<20}")
        else:
            print(f"{'':<20} | {row[1]:<22} | {row[2]:<20}")
    print("=" * 75)
    print(f"Higher Test F1: {better_model_key.upper()} (default_model = '{better_model_key}')\n")

    return metrics_json


if __name__ == "__main__":
    evaluate_models()
