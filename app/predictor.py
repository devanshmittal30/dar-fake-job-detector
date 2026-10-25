"""app/predictor.py
Inference engine and explainability module for DAR Fake Job Detector.

Following docs/03_TECHNICAL_DESIGN.md (sections 5.7 and 5.8) and prompt P7:
1. Loads both trained pipelines (LR and RF) and model_config.json once at startup.
2. predict(text, model_key) returns:
   - ad_id: SHA-256 hash of normalized text
   - verdict: 'Likely Fake' (p >= T + 0.10), 'Likely Real' (p <= T - 0.10), or 'Uncertain'
   - probability: float probability that the ad is fake (class 1)
   - threshold: decision threshold T from model_config.json
   - model: model key ('lr' or 'rf')
   - model_name: human-readable name ('Logistic Regression' or 'Random Forest')
   - top_fake_words: up to 8 words pushing towards Fake (coefficient x TF-IDF, always from LR)
   - top_real_words: up to 5 words pushing towards Real (coefficient x TF-IDF, always from LR)
   - flags: warning flags from app/rules.py (flags never alter the verdict)
   - highlighted_html: safe HTML with matched words highlighted (<mark>)
3. make_ad_id(text): Computes the SHA-256 hash of normalized text.
"""

import hashlib
import html
import json
from pathlib import Path
import re
import sys
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from app.rules import check_rules
from ml.preprocess import clean_text


# Global model cache (loaded once at module import)
_MODELS_DIR = PROJECT_ROOT / "models"
_CONFIG_PATH = _MODELS_DIR / "model_config.json"
_LR_PATH = _MODELS_DIR / "lr_pipeline.joblib"
_RF_PATH = _MODELS_DIR / "rf_pipeline.joblib"

_PIPELINES: dict[str, Pipeline] = {}
_CONFIG: dict[str, Any] = {}
_LR_FEATURE_NAMES: np.ndarray | None = None
_LR_COEFFICIENTS: np.ndarray | None = None


def load_models_and_config() -> None:
    """Load model pipelines, feature vocabulary, coefficients, and configuration into memory."""
    global _PIPELINES, _CONFIG, _LR_FEATURE_NAMES, _LR_COEFFICIENTS

    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found at {_CONFIG_PATH}. Run ml/train.py first.")

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        _CONFIG = json.load(f)

    if not _LR_PATH.exists() or not _RF_PATH.exists():
        raise FileNotFoundError(f"Model pipelines not found in {_MODELS_DIR}. Run ml/train.py first.")

    _PIPELINES["lr"] = joblib.load(_LR_PATH)
    _PIPELINES["rf"] = joblib.load(_RF_PATH)

    # Pre-extract Logistic Regression feature names and coefficients for fast word-level explainability
    lr_pipe = _PIPELINES["lr"]
    _LR_FEATURE_NAMES = lr_pipe.named_steps["tfidf"].get_feature_names_out()
    _LR_COEFFICIENTS = lr_pipe.named_steps["clf"].coef_[0]


# Initialize on import
load_models_and_config()


def make_ad_id(text: str) -> str:
    """Compute unique 64-character SHA-256 hash of normalised text.

    Following 03_TECHNICAL_DESIGN.md section 5.4:
    Clean and normalise text first, then take SHA-256.
    """
    normalized = clean_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_verdict(p: float, threshold: float, uncertain_band: float = 0.10) -> str:
    """Determine verdict string based on probability, threshold, and uncertain band.

    Following 01_PRD.md section 6.1 and 03_TECHNICAL_DESIGN.md section 5.7:
    - Likely Fake if p >= threshold + 0.10
    - Likely Real if p <= threshold - 0.10
    - Uncertain otherwise
    """
    if p >= threshold + uncertain_band:
        return "Likely Fake"
    elif p <= threshold - uncertain_band:
        return "Likely Real"
    else:
        return "Uncertain"


def extract_top_words(cleaned_text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Calculate the specific contribution of each word in this text using the LR pipeline.

    Following 03_TECHNICAL_DESIGN.md section 5.8:
    Contribution of a word = coefficient x TF-IDF value of that word in THIS ad.
    Always computed from the Logistic Regression model, even if Random Forest is selected.

    Returns:
        (top_fake_words, top_real_words)
        top_fake_words: up to 8 words pushing towards Fake (sorted by highest positive weight)
        top_real_words: up to 5 words pushing towards Real (sorted by highest negative weight)
    """
    if not cleaned_text or _LR_FEATURE_NAMES is None or _LR_COEFFICIENTS is None:
        return [], []

    lr_pipe = _PIPELINES["lr"]
    tfidf = lr_pipe.named_steps["tfidf"]

    # Transform text to sparse TF-IDF vector
    vec = tfidf.transform([cleaned_text])
    non_zero_indices = vec.nonzero()[1]

    fake_contributions = []
    real_contributions = []

    for idx in non_zero_indices:
        tfidf_val = vec[0, idx]
        coef = _LR_COEFFICIENTS[idx]
        word = _LR_FEATURE_NAMES[idx]
        weight = float(coef * tfidf_val)

        if weight > 0:
            fake_contributions.append({"word": word, "weight": round(weight, 4)})
        elif weight < 0:
            real_contributions.append({"word": word, "weight": round(abs(weight), 4)})

    # Sort fake contributions descending (highest positive impact first)
    fake_contributions.sort(key=lambda x: x["weight"], reverse=True)
    top_fake_words = fake_contributions[:8]

    # Sort real contributions descending (highest negative impact first)
    real_contributions.sort(key=lambda x: x["weight"], reverse=True)
    top_real_words = real_contributions[:5]

    return top_fake_words, top_real_words


def highlight_text(
    raw_text: str,
    fake_words: list[str] | None = None,
    warn_matches: list[str] | None = None
) -> str:
    """Highlight matched fake words and warning phrases safely in HTML.

    Security Rule:
    Escape raw text first to prevent XSS, then wrap matched tokens in <mark>.
    - Red-soft highlight: fake-leaning words (<mark class="highlight-fake">)
    - Amber-soft highlight: warning signs (<mark class="highlight-warn">)
    """
    if not raw_text:
        return ""

    # 1. Escape original text to guarantee safe HTML output
    escaped = html.escape(str(raw_text))

    term_class: dict[str, str] = {}

    # Register warning matches (amber-soft)
    if warn_matches:
        for match in warn_matches:
            if match and str(match).strip():
                clean_term = str(match).strip().lower()
                term_class[clean_term] = "highlight-warn"

    # Register fake words (red-soft)
    if fake_words:
        for word in fake_words:
            if word and str(word).strip():
                clean_word = str(word).strip().lower()
                # If term wasn't already assigned a warning highlight, assign fake highlight
                if clean_word not in term_class:
                    term_class[clean_word] = "highlight-fake"

    if not term_class:
        return escaped

    # Sort by length descending so multi-word bigrams match before individual words
    sorted_terms = sorted(term_class.keys(), key=len, reverse=True)
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in sorted_terms) + r")\b",
        re.IGNORECASE
    )

    def _replace_tag(match: re.Match) -> str:
        matched_str = match.group(1)
        css_class = term_class.get(matched_str.lower(), "highlight-fake")
        return f'<mark class="{css_class}">{matched_str}</mark>'

    return pattern.sub(_replace_tag, escaped)


def predict(text: str, model_key: str | None = None) -> dict[str, Any]:
    """Analyze a job posting text and return full detection output and explanations.

    Args:
        text: Raw job posting text (from textarea, OCR, or URL fetcher).
        model_key: 'lr' for Logistic Regression, 'rf' for Random Forest (defaults to default_model).

    Returns:
        Dict matching Section 7 POST /api/analyze spec:
        {
            "ad_id": str,
            "verdict": str,
            "probability": float,
            "threshold": float,
            "model": str,
            "model_name": str,
            "top_fake_words": list[dict],
            "top_real_words": list[dict],
            "flags": list[dict],
            "highlighted_html": str
        }
    """
    # Fallback to default model from config
    default_key = _CONFIG.get("default_model") or "lr"
    active_key = model_key.lower() if model_key and model_key.lower() in ("lr", "rf") else default_key

    model = _PIPELINES.get(active_key)
    if model is None:
        raise ValueError(f"Unknown model key: {active_key}. Choose 'lr' or 'rf'.")

    # 1. Normalise text and calculate unique ad_id
    ad_id = make_ad_id(text)
    cleaned = clean_text(text)

    # 2. Get decision threshold and uncertain band
    threshold = float(_CONFIG["thresholds"].get(active_key, 0.50))
    uncertain_band = float(_CONFIG.get("uncertain_band", 0.10))

    # 3. Model prediction
    if not cleaned.strip():
        # Edge case: text contains no words
        prob = 0.50
        verdict = "Uncertain"
    else:
        # Predict probability for fake class (1)
        prob = float(model.predict_proba([cleaned])[0, 1])
        verdict = compute_verdict(prob, threshold, uncertain_band)

    # 4. Word-level explainability (always from LR coefficients)
    top_fake_words, top_real_words = extract_top_words(cleaned)

    # 5. Rule-based warning flags (flags never alter verdict)
    flags = check_rules(text)

    # 6. Safe HTML highlighting
    fake_terms = [item["word"] for item in top_fake_words]
    warn_terms = [m for flag in flags for m in flag.get("matches", [])]
    highlighted_html = highlight_text(text, fake_words=fake_terms, warn_matches=warn_terms)

    model_display_names = {
        "lr": "Logistic Regression",
        "rf": "Random Forest"
    }

    return {
        "ad_id": ad_id,
        "verdict": verdict,
        "probability": round(prob, 4),
        "threshold": round(threshold, 4),
        "model": active_key,
        "model_name": model_display_names.get(active_key, active_key.upper()),
        "top_fake_words": top_fake_words,
        "top_real_words": top_real_words,
        "flags": flags,
        "highlighted_html": highlighted_html
    }
