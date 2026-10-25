"""tests/test_result_page.py
Unit and integration tests for the DAR Result page (/result/<ad_id>).

Following docs/02_UI_UX_SPEC.md (section 8) and roadmap prompt P11:
- 8.1 Result block: verdict banner, gauge, model switch, explainability chips, warning flags, highlighted text.
- 8.2 Colour legend: 7 color swatches and explanations.
- 8.3 Verify this ad: voting buttons, count line, vote bar, empty state, login modal.
- 8.4 Rating form: star rating, comments box, submission notice.
- 8.5 What to do next: checklist, analyze another ad, copy link.
- 8.6 Disclaimer: always visible decision-support notice.
"""

import re
import pytest
from app import create_app
from app.config import Config


class ResultTestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = "test-secret-key-result-page"


@pytest.fixture
def client():
    app = create_app(ResultTestConfig)
    with app.test_client() as test_client:
        yield test_client


def test_result_page_renders_all_spec_sections(client):
    """Verify that all 6 subsections of 02_UI_UX_SPEC.md Section 8 are present in order."""
    response = client.get("/result/demo_test_hash_001")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # 8.1 Result block
    assert "Likely FAKE" in html or "Likely REAL" in html or "UNCERTAIN" in html
    assert "Screen reader verdict:" in html
    assert "gauge-svg" in html
    assert "Chance this ad is fake:" in html
    assert "Model used:" in html
    assert "See the other model's result" in html
    assert "Warning signs found" in html
    assert "The ad text with highlights" in html

    # Removed per user customization
    assert "Why DAR says this" not in html
    assert "What the colours mean" not in html

    # 8.3 Verify this ad
    assert "Help others: is this ad genuine or fake?" in html
    assert "This ad is genuine" in html
    assert "This ad is fake" in html
    assert "users marked this ad as fake" in html
    assert "No community votes yet. Be the first to verify this ad." in html
    assert "Log in to verify this ad" in html

    # 8.4 Rate your experience
    assert "How was this analysis?" in html
    assert "Submit rating" in html
    assert "Thank you. Comments are reviewed before they appear on our home page." in html

    # 8.5 What to do next
    assert "What to do next" in html
    assert "Verify the company on its official website" in html
    assert "Never pay a fee for a job" in html
    assert "1930" in html
    assert "cybercrime.gov.in" in html
    assert "Analyze another ad" in html
    assert "Copy link" in html

    # 8.6 Disclaimer
    assert "DAR is a decision-support tool. It can be wrong. Never pay money to get a job." in html


def test_result_page_model_switching(client):
    """Verify model switching toggles between Logistic Regression and Random Forest."""
    # Check default (LR)
    res_lr = client.get("/result/demo_test_hash_001?model=lr")
    assert res_lr.status_code == 200
    html_lr = res_lr.data.decode("utf-8")
    assert "Logistic Regression" in html_lr
    assert "See the other model's result (Random Forest)" in html_lr

    # Switch to RF
    res_rf = client.get("/result/demo_test_hash_001?model=rf")
    assert res_rf.status_code == 200
    html_rf = res_rf.data.decode("utf-8")
    assert "Random Forest" in html_rf
    assert "See the other model's result (Logistic Regression)" in html_rf


def test_analyze_to_result_pipeline(client):
    """Verify end-to-end flow from POST /api/analyze to GET /result/<ad_id>."""
    # Retrieve CSRF token
    page_resp = client.get("/analyze")
    match = re.search(r'name="csrf-token" content="([^"]+)"', page_resp.data.decode("utf-8"))
    token = match.group(1)

    real_job_ad = (
        "Principal Systems Architect needed for cloud infrastructure engineering team at Bangalore. "
        "Candidates should have at least 8 years experience architecting high-scale distributed systems, "
        "Kubernetes clusters, Kafka streaming pipelines, and microservices design. Excellent competitive "
        "compensation including equity stock options, complete health coverage, and flexible remote work. "
        "Apply with your CV and GitHub portfolio directly through our official careers portal at acme.org."
    )
    headers = {"X-CSRFToken": token}

    analyze_resp = client.post(
        "/api/analyze",
        json={"text": real_job_ad, "model": "lr"},
        headers=headers
    )
    assert analyze_resp.status_code == 200
    data = analyze_resp.get_json()
    ad_id = data["ad_id"]

    # Open Result page with generated ad_id
    result_resp = client.get(f"/result/{ad_id}")
    assert result_resp.status_code == 200
    result_html = result_resp.data.decode("utf-8")

    assert "Principal" in result_html
    assert "Architect" in result_html
    assert data["verdict"] in result_html
    assert "Chance this ad is fake:" in result_html
