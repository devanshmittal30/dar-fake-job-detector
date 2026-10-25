"""ml/train.py
Model training script for DAR Fake Job Detector.

Trains two scikit-learn models following docs/03_TECHNICAL_DESIGN.md (sections 5.5, 5.6, 5.9):
1. Logistic Regression pipeline ('tfidf' + 'clf') with balanced class weights and liblinear solver.
2. Random Forest pipeline ('tfidf' + 'clf') with balanced_subsample class weights.

Tuning & Decision Thresholds:
- Hyperparameters tuned with 5-fold StratifiedKFold GridSearchCV scoring for F1 (fake class).
- Optimal decision thresholds selected using out-of-fold predicted probabilities on training data.
- Models saved with joblib compression (level 3) to keep files under 50 MB.
- Metadata and thresholds written to models/model_config.json.
- Note: Does NOT touch or evaluate on the test set (per prompt P5).
"""

import json
from pathlib import Path
import sys
import time
from datetime import datetime

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline


def get_tfidf_vectorizer() -> TfidfVectorizer:
    """Create the TF-IDF vectorizer configured exactly as in 03_TECHNICAL_DESIGN.md section 5.6.

    Settings:
    - ngram_range=(1, 2): Unigrams and bigrams
    - max_features=20000: Limits vocabulary to top 20,000 features by frequency
    - min_df=3: Ignores terms appearing in fewer than 3 documents
    - sublinear_tf=True: Replaces tf with 1 + log(tf) to dampen effect of repeated words
    - stop_words="english": Standard English stopwords removed
    """
    return TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=20000,
        min_df=3,
        sublinear_tf=True,
        stop_words="english"
    )


def find_optimal_threshold(y_true: np.ndarray, y_probs: np.ndarray) -> tuple[float, float]:
    """Find the probability decision threshold that maximizes the F1 score for fake ads (class 1).

    Args:
        y_true: True binary labels (0 or 1).
        y_probs: Predicted probabilities for the fake class (class 1).

    Returns:
        (best_threshold, best_f1)
    """
    candidate_thresholds = np.linspace(0.05, 0.95, 91)
    best_f1 = -1.0
    best_threshold = 0.50

    for t in candidate_thresholds:
        preds = (y_probs >= t).astype(int)
        score = f1_score(y_true, preds, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_threshold = float(t)

    return round(best_threshold, 4), round(float(best_f1), 4)


def train_logistic_regression(
    X_train: pd.Series,
    y_train: pd.Series,
    cv: StratifiedKFold
) -> tuple[Pipeline, dict, float, float]:
    """Train and tune the Logistic Regression pipeline.

    Args:
        X_train: Training text series.
        y_train: Training binary labels.
        cv: StratifiedKFold cross-validator.

    Returns:
        (best_pipeline, best_params, optimal_threshold, cv_f1_optimal)
    """
    print("\n" + "-" * 50)
    print("1. TRAINING LOGISTIC REGRESSION PIPELINE")
    print("-" * 50)

    pipeline = Pipeline([
        ("tfidf", get_tfidf_vectorizer()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            solver="liblinear",
            random_state=42
        ))
    ])

    param_grid = {
        "clf__C": [0.1, 1.0, 10.0]
    }

    start_time = time.time()
    grid = GridSearchCV(
        pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring="f1",
        n_jobs=-1,
        refit=True
    )
    grid.fit(X_train, y_train)
    duration = time.time() - start_time

    print(f"GridSearchCV completed in {duration:.1f}s")
    print(f"Best C parameter: {grid.best_params_['clf__C']}")
    print(f"Cross-validation F1 (default threshold 0.50): {grid.best_score_:.4f}")

    # Out-of-fold predicted probabilities for optimal threshold selection
    print("Finding optimal decision threshold via out-of-fold cross-validation...")
    oof_probs = cross_val_predict(
        grid.best_estimator_,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=-1
    )[:, 1]

    best_thresh, best_f1 = find_optimal_threshold(y_train.values, oof_probs)
    print(f"Optimal decision threshold: {best_thresh:.4f} (F1 at threshold: {best_f1:.4f})")

    return grid.best_estimator_, grid.best_params_, best_thresh, best_f1


def train_random_forest(
    X_train: pd.Series,
    y_train: pd.Series,
    cv: StratifiedKFold
) -> tuple[Pipeline, dict, float, float]:
    """Train and tune the Random Forest pipeline.

    Args:
        X_train: Training text series.
        y_train: Training binary labels.
        cv: StratifiedKFold cross-validator.

    Returns:
        (best_pipeline, best_params, optimal_threshold, cv_f1_optimal)
    """
    print("\n" + "-" * 50)
    print("2. TRAINING RANDOM FOREST PIPELINE")
    print("-" * 50)

    pipeline = Pipeline([
        ("tfidf", get_tfidf_vectorizer()),
        ("clf", RandomForestClassifier(
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42
        ))
    ])

    param_grid = {
        "clf__n_estimators": [100, 200],
        "clf__max_depth": [20, 40],
        "clf__min_samples_leaf": [1, 2]
    }

    start_time = time.time()
    grid = GridSearchCV(
        pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring="f1",
        n_jobs=-1,
        refit=True
    )
    grid.fit(X_train, y_train)
    duration = time.time() - start_time

    print(f"GridSearchCV completed in {duration:.1f}s")
    print(f"Best parameters: {grid.best_params_}")
    print(f"Cross-validation F1 (default threshold 0.50): {grid.best_score_:.4f}")

    # Out-of-fold predicted probabilities for optimal threshold selection
    print("Finding optimal decision threshold via out-of-fold cross-validation...")
    oof_probs = cross_val_predict(
        grid.best_estimator_,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=-1
    )[:, 1]

    best_thresh, best_f1 = find_optimal_threshold(y_train.values, oof_probs)
    print(f"Optimal decision threshold: {best_thresh:.4f} (F1 at threshold: {best_f1:.4f})")

    return grid.best_estimator_, grid.best_params_, best_thresh, best_f1


def save_model(model: Pipeline, output_path: Path) -> float:
    """Save pipeline with joblib compression (level 3) and check file size.

    Args:
        model: Trained scikit-learn Pipeline.
        output_path: Destination file path.

    Returns:
        Size in megabytes (MB).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path, compress=3)
    size_mb = output_path.stat().st_size / (1024 * 1024)

    print(f"[Saved] {output_path.name} -> {size_mb:.2f} MB")
    if size_mb > 50.0:
        print(f"  [WARNING] File size ({size_mb:.2f} MB) exceeds 50 MB GitHub recommendation limit! See G2.")
    else:
        print(f"  [OK] File size is well within the 50 MB limit.")

    return size_mb


def main(
    train_path: str | Path = "data/processed/train.csv",
    models_dir: str | Path = "models"
) -> None:
    """Main training workflow: loads training data, fits both models, saves artifacts and config."""
    overall_start = time.time()
    train_file = Path(train_path)
    if not train_file.exists():
        raise FileNotFoundError(f"Processed training file not found at {train_file.resolve()}. Run ml/build_dataset.py first.")

    print(f"Loading training data from {train_file}...")
    train_df = pd.read_csv(train_file)
    train_df["text"] = train_df["text"].fillna("")

    X_train = train_df["text"]
    y_train = train_df["label"]

    total_rows = len(train_df)
    fake_count = int((y_train == 1).sum())
    real_count = int((y_train == 0).sum())
    print(f"Training rows: {total_rows:,} (Real: {real_count:,}, Fake: {fake_count:,})")

    # 5-fold Stratified cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # 1. Train Logistic Regression
    lr_pipeline, lr_params, lr_thresh, lr_f1 = train_logistic_regression(X_train, y_train, cv)

    # 2. Train Random Forest
    rf_pipeline, rf_params, rf_thresh, rf_f1 = train_random_forest(X_train, y_train, cv)

    # 3. Save Model Artifacts
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "-" * 50)
    print("3. SAVING MODEL ARTIFACTS (compress=3)")
    print("-" * 50)
    lr_path = models_path / "lr_pipeline.joblib"
    rf_path = models_path / "rf_pipeline.joblib"

    lr_size = save_model(lr_pipeline, lr_path)
    rf_size = save_model(rf_pipeline, rf_path)

    # 4. Save model_config.json
    config_data = {
        "thresholds": {
            "lr": lr_thresh,
            "rf": rf_thresh
        },
        "uncertain_band": 0.10,
        "default_model": None,  # Set in P6 (evaluate.py) based on test set F1
        "sklearn_version": sklearn.__version__,
        "training_date": datetime.now().strftime("%Y-%m-%d"),
        "dataset_names": ["D1 (Kaggle EMSCAD)"],
        "dataset_row_counts": {
            "raw": 17880,
            "unique_clean": 15749
        },
        "training_row_count": total_rows,
        "best_parameters": {
            "lr": {k.replace("clf__", ""): v for k, v in lr_params.items()},
            "rf": {k.replace("clf__", ""): v for k, v in rf_params.items()}
        },
        "cross_validation_f1": {
            "lr_optimal": lr_f1,
            "rf_optimal": rf_f1
        },
        "file_sizes_mb": {
            "lr_pipeline": round(lr_size, 2),
            "rf_pipeline": round(rf_size, 2)
        }
    }

    config_path = models_path / "model_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    print(f"\n[Saved] Configuration -> {config_path}")

    total_duration = time.time() - overall_start
    print(f"\nTraining pipeline completed in {total_duration:.1f}s ({total_duration/60:.1f} mins).")
    print("Models and config ready. Next step: P6 (evaluation on test set).")


if __name__ == "__main__":
    main()
