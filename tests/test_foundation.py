"""tests/test_foundation.py
Unit tests for Flask application foundation, design system pages, health check, and error handlers.
"""

import pytest
from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = "test-secret-key-12345"


@pytest.fixture
def client():
    """Create Flask test client."""
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Verify that GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok"}


def test_all_ten_page_routes(client):
    """Verify that all user-facing routes return 200 OK."""
    routes = [
        ("/", "Is this job real? Check before you apply."),
        ("/analyze", "Analyze a job ad"),
        ("/result/test_hash_123456", "Analysis Result"),
        ("/community", "Community Verified Jobs"),
        ("/awareness", "Job Scam Awareness"),
        ("/performance", "Model Performance & Metrics"),
        ("/faq", "Frequently Asked Questions"),
        ("/about", "About DAR"),
        ("/auth", "Welcome to DAR"),
    ]

    for route, expected_text in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Route {route} failed with status {response.status_code}"
        assert expected_text.encode("utf-8") in response.data, f"Route {route} missing expected text: {expected_text}"


def test_header_and_footer_structure(client):
    """Verify that header brand, descriptor, and dark footer are present on pages."""
    response = client.get("/")
    assert response.status_code == 200
    html_text = response.data.decode("utf-8")

    # Header brand and descriptor (UI spec section 3)
    assert "dar-logo.svg" in html_text
    assert "Fake Job Detector" in html_text

    # Navigation links
    assert "Analyze Job" in html_text
    assert "Community" in html_text
    assert "Scam Awareness" in html_text
    assert "Model Performance" in html_text
    assert "FAQ" in html_text
    assert "About" in html_text

    # Dark footer content (UI spec section 5.2)
    assert "dar-logo-white.svg" in html_text
    assert "Check before you apply." in html_text
    assert "Your safety is our priority." in html_text
    assert "devanshmittal051@gmail.com" in html_text
    assert "9412494909" in html_text
    assert "Chandigarh, India" in html_text
    assert "© 2026 DAR. Created by Devansh Mittal." in html_text


def test_csrf_token_meta_tag(client):
    """Verify CSRF token meta tag is rendered in base HTML."""
    response = client.get("/")
    html_text = response.data.decode("utf-8")
    assert 'name="csrf-token"' in html_text


def test_404_error_handler(client):
    """Verify custom branded 404 page is rendered for unknown URLs."""
    response = client.get("/this-route-definitely-does-not-exist")
    assert response.status_code == 404
    html_text = response.data.decode("utf-8")
    assert "Page Not Found" in html_text
    assert "dar-logo.svg" in html_text
    assert "Return to Home" in html_text
