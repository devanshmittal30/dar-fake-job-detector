"""tests/test_predictor.py
Unit tests for app/predictor.py (ML inference, explainability, verdicts, and highlighting).
"""

import html
import pytest
from app.predictor import (
    compute_verdict,
    extract_top_words,
    highlight_text,
    make_ad_id,
    predict,
)


def test_make_ad_id_properties_and_stability():
    """Verify ad_id generation: 64-char hex SHA-256, invariant to whitespace and casing."""
    text1 = "Senior Python Engineer at Microsoft Corporation."
    text2 = "  senior python engineer at microsoft corporation.  \n"
    text3 = "Different Job Title at Another Company."

    id1 = make_ad_id(text1)
    id2 = make_ad_id(text2)
    id3 = make_ad_id(text3)

    assert len(id1) == 64
    assert id1 == id2  # Normalization ensures identical ID for equivalent text
    assert id1 != id3


def test_compute_verdict_threshold_logic():
    """Verify verdict decision bands: Likely Fake (p >= T + 0.10), Likely Real (p <= T - 0.10), Uncertain."""
    T = 0.60
    band = 0.10

    # Above T + band (>= 0.70)
    assert compute_verdict(0.70, T, band) == "Likely Fake"
    assert compute_verdict(0.95, T, band) == "Likely Fake"

    # Below T - band (<= 0.50)
    assert compute_verdict(0.50, T, band) == "Likely Real"
    assert compute_verdict(0.20, T, band) == "Likely Real"

    # Uncertain band (0.50 < p < 0.70)
    assert compute_verdict(0.60, T, band) == "Uncertain"
    assert compute_verdict(0.55, T, band) == "Uncertain"
    assert compute_verdict(0.65, T, band) == "Uncertain"


def test_predict_real_posting():
    """Verify inference on a legitimate corporate posting yields Likely Real."""
    real_text = (
        "Senior Software Engineer at Oracle Technologies India Ltd. "
        "We are looking for an experienced Java developer with 5+ years of experience "
        "building distributed enterprise backend systems. Requirements: B.Tech in Computer Science, "
        "strong SQL database skills, and cloud knowledge. Comprehensive benefits package included."
    )
    result = predict(real_text, model_key="lr")

    assert result["verdict"] == "Likely Real"
    assert result["probability"] < 0.50
    assert result["model"] == "lr"
    assert len(result["top_real_words"]) > 0
    assert isinstance(result["ad_id"], str) and len(result["ad_id"]) == 64


def test_predict_fake_posting():
    """Verify inference on a scam posting yields Likely Fake with warning flags."""
    fake_text = (
        "URGENT REQUIREMENT: Earn $5000 weekly from home! Immediate joining for Receptionist / Data Entry. "
        "No interview required. Apply using link url and deposit 500 registration fee. "
        "Contact immediately on WhatsApp at 9876543210 or email recruiter@gmail.com."
    )
    result = predict(fake_text, model_key="lr")

    assert result["verdict"] == "Likely Fake"
    assert result["probability"] >= 0.70
    assert len(result["top_fake_words"]) > 0
    assert len(result["flags"]) > 0
    assert "<mark" in result["highlighted_html"]


def test_predict_model_switching():
    """Verify prediction works with both LR and RF pipelines."""
    sample = "Software engineer building mobile web applications with React and Python."

    result_lr = predict(sample, model_key="lr")
    assert result_lr["model"] == "lr"
    assert result_lr["model_name"] == "Logistic Regression"

    result_rf = predict(sample, model_key="rf")
    assert result_rf["model"] == "rf"
    assert result_rf["model_name"] == "Random Forest"


def test_predict_empty_input():
    """Verify empty input does not crash and returns Uncertain verdict."""
    result = predict("")
    assert result["verdict"] == "Uncertain"
    assert result["probability"] == 0.50
    assert result["flags"] == []


def test_highlight_text_security_and_wrapping():
    """Verify that dangerous HTML is escaped before highlighting to prevent XSS."""
    malicious = "<script>alert('hack')</script> Apply for Receptionist position via WhatsApp."
    fake_words = ["receptionist"]
    warn_phrases = ["whatsapp"]

    highlighted = highlight_text(malicious, fake_words=fake_words, warn_matches=warn_phrases)

    # Raw script tags must NEVER appear in output
    assert "<script>" not in highlighted
    assert "&lt;script&gt;" in highlighted
    # Matched terms wrapped in mark tags
    assert '<mark class="highlight-fake">Receptionist</mark>' in highlighted
    assert '<mark class="highlight-warn">WhatsApp</mark>' in highlighted


def test_explainability_word_limits():
    """Verify that top_fake_words has at most 8 items and top_real_words has at most 5 items."""
    long_ad = (
        "Urgent receptionist required! High school diploma needed. Call phone now. "
        "Apply using link url for timejob. English language client recruitment software digital startup."
    )
    result = predict(long_ad, model_key="lr")

    assert len(result["top_fake_words"]) <= 8
    assert len(result["top_real_words"]) <= 5

    for item in result["top_fake_words"]:
        assert "word" in item
        assert "weight" in item
        assert item["weight"] > 0
