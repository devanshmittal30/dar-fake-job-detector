"""tests/test_p15_pages.py
Tests for P15 deliverables:
1. /api/stats and india_stats.json content
2. /api/metrics endpoint
3. Awareness page (/awareness)
4. Model Performance page (/performance)
5. FAQ page (/faq)
6. About page (/about)
"""

import json
from pathlib import Path
import pytest
from app import create_app
from app.config import Config


class P15TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "p15-test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def client():
    app = create_app(P15TestConfig)
    with app.test_client() as c:
        yield c


def test_api_stats_endpoint(client):
    """Test that GET /api/stats serves the exact 9 statistics from UI spec section 14."""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()

    # 1. Yearly losses
    assert "yearly_losses" in data
    assert len(data["yearly_losses"]) == 4
    years = [item["year"] for item in data["yearly_losses"]]
    assert "2023" in years
    assert "2024" in years
    assert "2025" in years
    assert "2026 (H1)" in years

    # Verify 2023, 2024, 2025 values
    loss_map = {item["year"]: item for item in data["yearly_losses"]}
    assert loss_map["2023"]["amount_crore"] == 7465
    assert loss_map["2024"]["amount_crore"] == 22845
    assert loss_map["2025"]["amount_crore"] == 22495
    assert loss_map["2026 (H1)"]["amount_crore"] == 10178

    # 2. Six year total
    assert data["total_six_years"]["amount_crore"] == 52976

    # 3. Share of 2025 losses from fake investment schemes
    assert data["fake_investment_share_2025"]["percentage"] == 76

    # 4. Recovery rate 2025
    assert data["recovery_rate_2025"]["percentage"] == 24

    # 5. NCRB police cases
    assert data["ncrb_police_cases"]["cases_by_year"]["2021"] == 52974
    assert data["ncrb_police_cases"]["cases_by_year"]["2022"] == 65893
    assert data["ncrb_police_cases"]["cases_by_year"]["2023"] == 86420

    # 6. Rescued Indians from Southeast Asia job scams
    assert data["rescued_indians_southeast_asia"]["count"] == 6700
    assert data["rescued_indians_southeast_asia"]["scope"] == "job scams"

    # All entries have checked_on and source
    for item in data["yearly_losses"]:
        assert "source" in item and "checked_on" in item
    assert "source" in data["total_six_years"] and "checked_on" in data["total_six_years"]
    assert "source" in data["fake_investment_share_2025"] and "checked_on" in data["fake_investment_share_2025"]
    assert "source" in data["recovery_rate_2025"] and "checked_on" in data["recovery_rate_2025"]
    assert "source" in data["ncrb_police_cases"] and "checked_on" in data["ncrb_police_cases"]
    assert "source" in data["rescued_indians_southeast_asia"] and "checked_on" in data["rescued_indians_southeast_asia"]


def test_api_metrics_endpoint(client):
    """Test that GET /api/metrics returns sanitized metrics and config."""
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    data = resp.get_json()

    assert "metrics" in data
    assert "config" in data

    metrics = data["metrics"]
    assert "lr" in metrics
    assert "rf" in metrics

    lr_test = metrics["lr"]["test"]
    assert lr_test["accuracy"] == 0.9848
    assert lr_test["precision"] == 0.873
    assert lr_test["recall"] == 0.7746
    assert lr_test["f1"] == 0.8209
    assert lr_test["roc_auc"] == 0.986
    assert lr_test["pr_auc"] == 0.9004

    # Config sanitization: ensure no internal filesystem paths are exposed
    for k in data["config"].keys():
        assert not k.endswith("_path")


def test_awareness_page(client):
    """Test that /awareness renders the expected sections, scope note, and scripts."""
    resp = client.get("/awareness")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "Job Scam Awareness" in html
    assert "Scope note:" in html
    assert "These figures cover all online financial fraud in India" in html
    assert "Where the Money Goes" in html
    assert "10 Safety Rules for Job Seekers" in html
    assert "If You Have Been Scammed" in html
    assert "Job Scam Stories" in html
    assert "No verified stories yet" in html
    assert "chart.umd.min.js" in html
    assert "awareness.js" in html


def test_performance_page(client):
    """Test that /performance renders the metrics table, plots, notes, and datasets."""
    resp = client.get("/performance")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "Model Performance & Metrics" in html
    assert "How well does DAR work?" in html
    assert "Why accuracy alone is misleading:" in html
    assert "Only about 5% of ads in the training data are fake" in html
    assert "Logistic Regression (Default)" in html
    assert "Random Forest" in html
    assert "eval_confusion_matrices.png" in html
    assert "eval_metric_comparison.png" in html
    assert "eval_top_words_coefficients.png" in html
    assert "eval_roc_pr_curves.png" in html
    assert "D1 Raw (Kaggle EMSCAD)" in html
    assert "17,880" in html
    assert "3,150" in html
    assert "performance.js" in html


def test_faq_page(client):
    """Test that /faq renders all 13 questions from UI spec section 12 in an accordion."""
    resp = client.get("/faq")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "Frequently Asked Questions" in html
    assert "Frequently asked questions" in html

    expected_questions = [
        "1. Is DAR 100% accurate?",
        "2. What does \"Uncertain\" mean?",
        "3. How does DAR decide?",
        "4. Which data was the model trained on?",
        "5. Do you store my screenshots or photos?",
        "6. How do thumbs up and thumbs down work?",
        "7. Does the community vote change DAR's verdict?",
        "8. Why do I need an account?",
        "9. Why is the first page load slow sometimes?",
        "10. Can DAR read ads in Hindi?",
        "11. What should I do if I already paid a scammer?",
        "12. How are ratings shown on the home page?",
        "13. Who made DAR?",
    ]

    for q in expected_questions:
        assert q in html, f"Missing question: {q}"

    assert "Created by Devansh Mittal" in html or "created by Devansh Mittal" in html
    assert "faq.js" in html


def test_about_page(client):
    """Test that /about renders what DAR is, 7 steps, data sources, 9 limitations, and creator."""
    resp = client.get("/about")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "About DAR" in html
    assert "What DAR is" in html
    assert "120" in html  # 120px logo dimensions
    assert "Input" in html
    assert "Read Text" in html
    assert "Clean Text" in html
    assert "TF-IDF Features" in html
    assert "Model Scoring" in html
    assert "Explanation" in html
    assert "Community Verification" in html

    # Data sources
    assert "D1 (Primary)" in html
    assert "17,880" in html
    assert "E1 (External)" in html

    # Limitations
    assert "Class Imbalance:" in html
    assert "Domain Shift:" in html
    assert "OCR Noise:" in html
    assert "Language Support:" in html
    assert "Dataset Errors:" in html
    assert "Decision Support Only:" in html
    assert "Ad Matching Thresholds:" in html
    assert "Cold Starts:" in html
    assert "Community Voting Independence:" in html

    # Name and creator
    assert "The Name \"DAR\"" in html
    assert "Created by Devansh Mittal" in html
