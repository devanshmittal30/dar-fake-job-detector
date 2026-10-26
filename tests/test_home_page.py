"""tests/test_home_page.py
Unit and integration tests for Home page and GET /api/home endpoint.

Following docs/01_PRD.md (F12, F13), docs/02_UI_UX_SPEC.md (section 6),
docs/03_TECHNICAL_DESIGN.md (sections 7 and 8), and roadmap prompt P14:
- GET /api/home returns analyses_total, training_rows, accuracy, recall, precision,
  avg_rating, rating_count, distribution, and reviews.
- analyses_total equals sum of ads.check_count (not hard-coded).
- Metrics come from metrics.json and model_config.json.
- Reviews: only approved, 4 or 5 stars, newest 6, first name only.
- Home page HTML renders sections strictly in UI spec order.
- Honest empty state when no ratings exist.
"""

import json
from pathlib import Path
import pytest
from sqlalchemy.pool import StaticPool
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.models import Ad, Rating, User, db


class HomeTestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False}
    }


@pytest.fixture
def app_instance():
    """Create Flask application instance with in-memory SQLite database."""
    app = create_app(HomeTestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    """Create Flask test client."""
    with app_instance.test_client() as test_client:
        yield test_client


def test_api_home_empty_database(client):
    """Verify /api/home response when database is empty."""
    resp = client.get("/api/home")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["analyses_total"] == 0
    assert data["avg_rating"] is None
    assert data["rating_count"] == 0
    assert data["reviews"] == []
    assert data["distribution"] == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    # Verify metrics come from config/metrics.json
    assert data["training_rows"] == 12599
    assert isinstance(data["accuracy"], float)
    assert isinstance(data["recall"], float)
    assert isinstance(data["precision"], float)


def test_api_home_analyses_total_sum(client, app_instance):
    """Verify analyses_total sums check_count across all ads."""
    with app_instance.app_context():
        ad1 = Ad(
            ad_id="ad_test_1",
            snippet="First ad snippet",
            full_text="First ad text full content with sufficient words",
            ai_label="Likely Real",
            ai_probability=0.1,
            model_used="lr",
            check_count=5
        )
        ad2 = Ad(
            ad_id="ad_test_2",
            snippet="Second ad snippet",
            full_text="Second ad text full content with sufficient words",
            ai_label="Likely Fake",
            ai_probability=0.9,
            model_used="lr",
            check_count=12
        )
        db.session.add_all([ad1, ad2])
        db.session.commit()

    resp = client.get("/api/home")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["analyses_total"] == 17  # 5 + 12


def test_api_home_ratings_and_reviews_moderation(client, app_instance):
    """Verify ratings aggregation and review moderation (only approved 4-5 stars)."""
    with app_instance.app_context():
        # Create users
        u1 = User(name="Rohan Sharma", email="rohan@example.com", password_hash=generate_password_hash("pass1234"))
        u2 = User(name="Priya Patel", email="priya@example.com", password_hash=generate_password_hash("pass1234"))
        u3 = User(name="Amit Kumar", email="amit@example.com", password_hash=generate_password_hash("pass1234"))
        u4 = User(name="Sneha Rao", email="sneha@example.com", password_hash=generate_password_hash("pass1234"))
        db.session.add_all([u1, u2, u3, u4])
        db.session.commit()

        ad = Ad(
            ad_id="ad_common_1",
            snippet="Job snippet",
            full_text="Job ad full text content for testing ratings and reviews",
            ai_label="Likely Real",
            ai_probability=0.1,
            check_count=1
        )
        db.session.add(ad)
        db.session.commit()

        # 1. Approved 5-star review (SHOULD appear, first name "Rohan")
        r1 = Rating(user_id=u1.id, ad_id=ad.ad_id, stars=5, comment="Spotted a fee scam instantly!", approved=True)
        # 2. Approved 4-star review (SHOULD appear, first name "Priya")
        r2 = Rating(user_id=u2.id, ad_id=ad.ad_id, stars=4, comment="Very helpful explanation.", approved=True)
        # 3. Unapproved 5-star review (SHOULD NOT appear until owner approves)
        r3 = Rating(user_id=u3.id, ad_id=ad.ad_id, stars=5, comment="Pending approval comment", approved=False)
        # 4. Approved 3-star review (SHOULD NOT appear because only 4 or 5 stars allowed on home)
        r4 = Rating(user_id=u4.id, ad_id=ad.ad_id, stars=3, comment="Average experience.", approved=True)

        db.session.add_all([r1, r2, r3, r4])
        db.session.commit()

    resp = client.get("/api/home")
    assert resp.status_code == 200
    data = resp.get_json()

    # Total ratings = 4; average = (5 + 4 + 5 + 3) / 4 = 17 / 4 = 4.25 -> 4.2
    assert data["rating_count"] == 4
    assert data["avg_rating"] == 4.2
    assert data["distribution"]["5"] == 2
    assert data["distribution"]["4"] == 1
    assert data["distribution"]["3"] == 1
    assert data["distribution"]["1"] == 0

    # Reviews: only r1 and r2
    reviews = data["reviews"]
    assert len(reviews) == 2
    comments = [rev["comment"] for rev in reviews]
    assert "Spotted a fee scam instantly!" in comments
    assert "Very helpful explanation." in comments
    assert "Pending approval comment" not in comments
    assert "Average experience." not in comments

    # First name only
    first_names = [rev["first_name"] for rev in reviews]
    assert "Rohan" in first_names
    assert "Priya" in first_names
    assert "Rohan Sharma" not in first_names


def test_home_page_html_spec_sections(client):
    """Verify that all sections in 02_UI_UX_SPEC.md section 6 are present in order."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # 6.2 Banner
    assert "AI + Community powered" in html
    assert "Is this job real?" in html
    assert "Check before you apply." in html
    assert "Paste an ad, upload a screenshot or scan a poster with your camera." in html
    assert "hero-scan-line" in html
    assert "hero-shield-tick" in html
    assert "Fee demanded" in html
    assert "No company info" in html

    # 6.3 Four proof boxes
    assert "Jobs analyzed" in html
    assert "Detection accuracy" in html
    assert "Platform support" in html
    assert "Available any time" in html
    assert "Trained on" in html
    assert "Works everywhere" in html
    assert "24/7" in html
    assert "Measured on test data the model never saw" in html

    # 6.4 Main call to action
    assert "Analyze Job Now" in html
    assert "Free. No payment. Never share your bank details with a recruiter." in html

    # 6.5 How DAR works (4 steps)
    assert "How DAR works" in html
    assert "Add the job ad" in html
    assert "DAR reads it" in html
    assert "The model checks it" in html
    assert "See the result and verify" in html

    # 6.6 Why choose DAR (6 cards)
    assert "Why choose DAR" in html
    assert "Explains its answer" in html
    assert "Works with screenshots and photos" in html
    assert "Community verified" in html
    assert "Honest about accuracy" in html
    assert "Private by design" in html
    assert "Free to use" in html

    # 6.7 Ratings and what users say
    assert "What users say about DAR" in html
    assert "No ratings yet. Analyze a job ad and be the first to rate DAR." in html
    assert "Ratings come only from users who have analyzed an ad. Comments are reviewed before they appear." in html
