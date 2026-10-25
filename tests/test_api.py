"""tests/test_api.py
Comprehensive test suite for DAR API endpoints:
- POST /api/analyze
- POST /api/fetch
- CSRF validation
- Rate limiting (Flask-Limiter)

Following docs/03_TECHNICAL_DESIGN.md (sections 7 and 9), docs/02_UI_UX_SPEC.md (section 7),
and roadmap prompt P9.
"""

import re
from unittest.mock import MagicMock, patch
import pytest

from app import create_app
from app.config import Config


class ApiTestConfig(Config):
    """Test configuration for API testing."""
    TESTING = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = "test-secret-key-dar-fake-job-detector"


@pytest.fixture
def app_instance():
    """Create a fresh Flask application instance for tests."""
    app = create_app(ApiTestConfig)
    return app


@pytest.fixture
def client(app_instance):
    """Create Flask test client."""
    with app_instance.test_client() as test_client:
        yield test_client


@pytest.fixture
def csrf_token(client):
    """Retrieve a valid CSRF token from a GET page request."""
    response = client.get("/analyze")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    assert match is not None, "CSRF token meta tag not found in /analyze"
    return match.group(1)


def test_csrf_protection_enforced(client):
    """Verify that POST /api/analyze without CSRF token is rejected with 400."""
    response = client.post("/api/analyze", json={"text": "Test ad text"})
    assert response.status_code == 400


def test_analyze_empty_input(client, csrf_token):
    """Verify empty text validation message exactly as in UI spec."""
    headers = {"X-CSRFToken": csrf_token}

    # Empty string
    response = client.post("/api/analyze", json={"text": ""}, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Please paste the job ad text to analyze."

    # Whitespace only
    response = client.post("/api/analyze", json={"text": "   \n\t  "}, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Please paste the job ad text to analyze."

    # Missing text key
    response = client.post("/api/analyze", json={}, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Please paste the job ad text to analyze."


def test_analyze_fewer_than_50_words(client, csrf_token):
    """Verify validation message for ad text under 50 words."""
    headers = {"X-CSRFToken": csrf_token}
    short_text = "We are hiring software developers for immediate joining. Good salary and benefits. Send resume."
    assert len(short_text.split()) < 50

    response = client.post("/api/analyze", json={"text": short_text}, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Please paste the full ad (at least 50 words)."
    assert "word_count" in data
    assert data["word_count"] == len(short_text.split())


def test_analyze_valid_job_posting_lr(client, csrf_token):
    """Verify successful prediction with Logistic Regression on a realistic posting."""
    headers = {"X-CSRFToken": csrf_token}

    # Realistic 60-word job posting
    valid_posting = (
        "Senior Software Engineer wanted at TechCorp India Pvt Ltd. We are looking for an experienced "
        "Python backend engineer with 4+ years developing microservices using Flask, FastAPI and PostgreSQL. "
        "The ideal candidate must possess strong communication skills, design patterns knowledge, Docker, "
        "and cloud deployment experience on AWS. Competitive compensation package including health insurance, "
        "annual bonus, flexible working hours, and generous stock options. Apply today with your portfolio "
        "and resume through our official website careers portal at https://techcorp.example.com/careers."
    )
    words = valid_posting.split()
    assert len(words) >= 50

    response = client.post(
        "/api/analyze",
        json={"text": valid_posting, "model": "lr", "source": "text"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.get_json()

    # Required response keys from docs/03_TECHNICAL_DESIGN.md section 7
    required_keys = [
        "ad_id", "verdict", "probability", "threshold", "model_name",
        "top_fake_words", "top_real_words", "flags", "highlighted_html",
        "word_count", "source"
    ]
    for key in required_keys:
        assert key in data, f"Missing key in API response: {key}"

    assert len(data["ad_id"]) == 64
    assert data["verdict"] in ("Likely Fake", "Likely Real", "Uncertain")
    assert 0.0 <= data["probability"] <= 1.0
    assert 0.0 <= data["threshold"] <= 1.0
    assert data["model_name"] == "Logistic Regression"
    assert data["source"] == "text"
    assert data["word_count"] == len(words)
    assert isinstance(data["top_fake_words"], list)
    assert isinstance(data["top_real_words"], list)
    assert isinstance(data["flags"], list)
    assert "<mark" in data["highlighted_html"] or valid_posting[:20] in data["highlighted_html"]


def test_analyze_model_switch_to_rf(client, csrf_token):
    """Verify model switching parameter works with Random Forest."""
    headers = {"X-CSRFToken": csrf_token}
    valid_posting = (
        "Customer Support Associate needed urgently for leading e-commerce enterprise. "
        "Responsibilities include handling inbound phone calls, resolving billing inquiries, "
        "chat support, and ensuring customer satisfaction. Must have excellent English verbal and "
        "written communication skills, basic computer literacy, and willingness to work rotating shifts. "
        "We offer comprehensive training, competitive starting salary, transport facility, and medical "
        "cover. Candidates with 6 months customer service experience preferred but freshers may also apply."
    )
    assert len(valid_posting.split()) >= 50

    response = client.post(
        "/api/analyze",
        json={"text": valid_posting, "model": "rf"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["model_name"] == "Random Forest"
    assert data["verdict"] in ("Likely Fake", "Likely Real", "Uncertain")


def test_analyze_warning_flags_detection(client, csrf_token):
    """Verify rule warning flags are returned when scam indicators are present."""
    headers = {"X-CSRFToken": csrf_token}
    scam_posting = (
        "Urgent job opening for Data Entry Specialist! Work from home and earn 50,000 rupees weekly. "
        "Instant joining without any interview needed. Selected candidates must pay a refundable registration "
        "fee of 2000 rupees for training kit and background check before start date. Contact our HR manager "
        "strictly on WhatsApp at 9876543210 or join our Telegram channel t.me/fastjobs today. Please send "
        "your Aadhaar card and PAN card copies to confirm your seat immediately. Limited vacancies available!"
    )
    assert len(scam_posting.split()) >= 50

    response = client.post(
        "/api/analyze",
        json={"text": scam_posting, "model": "lr"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.get_json()

    flag_codes = [f["code"] for f in data["flags"]]
    # Should flag money fee, WhatsApp/Telegram, sensitive data, no interview
    assert "money_fee" in flag_codes
    assert "social_messaging" in flag_codes
    assert "sensitive_data" in flag_codes
    assert "no_interview" in flag_codes


def test_fetch_unsafe_urls_rejected(client, csrf_token):
    """Verify POST /api/fetch rejects unsafe URLs as per prompt P9."""
    headers = {"X-CSRFToken": csrf_token}
    unsafe_urls = [
        "http://localhost:5000",
        "http://localhost",
        "http://127.0.0.1",
        "http://169.254.169.254",
        "file:///etc/passwd",
        "http://10.0.0.1",
        "http://192.168.1.1",
        "ftp://example.com/job.txt"
    ]

    for url in unsafe_urls:
        response = client.post("/api/fetch", json={"url": url}, headers=headers)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data, f"No error key returned for unsafe URL {url}"


def test_fetch_empty_url(client, csrf_token):
    """Verify POST /api/fetch validates empty URL."""
    headers = {"X-CSRFToken": csrf_token}
    response = client.post("/api/fetch", json={"url": ""}, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Please enter a valid job URL."


def test_fetch_mocked_success(client, csrf_token):
    """Verify POST /api/fetch extracts clean text from a simulated web page."""
    headers = {"X-CSRFToken": csrf_token}
    fake_html = """
    <html>
      <head><title>Job Title</title><script>var x = 1;</script></head>
      <body>
        <h1>Lead Mobile Developer</h1>
        <p>Acme Corp is seeking an iOS and Android developer with React Native experience.</p>
        <p>You will collaborate with design teams and ship production mobile applications.</p>
      </body>
    </html>
    """

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_resp.encoding = "utf-8"
    mock_resp.iter_content = MagicMock(return_value=[fake_html.encode("utf-8")])

    with patch("app.fetcher.validate_url_safety"):
        with patch("requests.Session.get", return_value=mock_resp):
            response = client.post(
                "/api/fetch",
                json={"url": "https://example.com/jobs/lead-dev"},
                headers=headers
            )
            assert response.status_code == 200
            data = response.get_json()
            assert "text" in data
            assert "Lead Mobile Developer" in data["text"]
            assert "Acme Corp is seeking" in data["text"]
            assert "var x = 1;" not in data["text"]


def test_rate_limiting_enforced():
    """Verify rate limit returns 429 after exceeding 30 requests per minute."""
    rate_app = create_app(ApiTestConfig)
    with rate_app.test_client() as rate_client:
        # Get CSRF token
        resp = rate_client.get("/analyze")
        token = re.search(r'name="csrf-token" content="([^"]+)"', resp.data.decode("utf-8")).group(1)
        headers = {"X-CSRFToken": token}

        hit_429 = False
        for i in range(35):
            res = rate_client.post("/api/fetch", json={"url": ""}, headers=headers)
            if res.status_code == 429:
                hit_429 = True
                data = res.get_json()
                assert "Rate limit exceeded" in data["error"]
                break

        assert hit_429, "Rate limiter did not trigger 429 after 30+ requests"
