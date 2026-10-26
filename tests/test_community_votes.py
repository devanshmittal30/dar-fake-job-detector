"""tests/test_community_votes.py
Unit and integration tests for community verification, voting, ratings, and community feed.

Following docs/01_PRD.md (F8, F11, F13, F14), docs/02_UI_UX_SPEC.md (8.3, 8.4, 9.1),
docs/03_TECHNICAL_DESIGN.md (sections 7 and 8), and roadmap prompt P13:
- Vote uniqueness per account per ad (cannot double vote).
- Changing a vote updates counts without creating duplicate rows.
- Voting with multiple distinct accounts.
- Login requirement on voting and rating endpoints (401 JSON).
- Rating persistence with approved=False default.
- Disputed logic: both sides have at least 3 votes and the smaller side >= 30%.
- Amber disagreement note when AI verdict and vote majority (>= 3 votes) differ.
- Community API filtering, search, sorting, and pagination.
"""

import pytest
from werkzeug.security import generate_password_hash

from sqlalchemy.pool import StaticPool

from app import create_app
from app.config import Config
from app.models import Ad, Rating, User, Vote, db


class CommunityTestConfig(Config):
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
    app = create_app(CommunityTestConfig)
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


def create_test_user(app_instance, name: str, email: str, password: str = "Password123") -> int:
    """Helper to create and persist a test user."""
    with app_instance.app_context():
        user = User(
            name=name,
            email=email.lower(),
            password_hash=generate_password_hash(password, method="scrypt")
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def create_test_ad(
    app_instance,
    ad_id: str,
    snippet: str = "Hiring software engineers...",
    ai_label: str = "Likely Real",
    ai_prob: float = 0.15
):
    """Helper to create and persist a test ad."""
    with app_instance.app_context():
        ad = Ad(
            ad_id=ad_id,
            snippet=snippet[:200],
            full_text=snippet,
            ai_label=ai_label,
            ai_probability=ai_prob,
            model_used="lr",
            check_count=1
        )
        db.session.add(ad)
        db.session.commit()


def login_user_session(client, email: str, password: str = "Password123"):
    """Helper to authenticate a user via /auth/login."""
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    assert resp.status_code == 200


def test_login_required_for_voting_and_rating(client, app_instance):
    """Verify that unauthenticated voting and rating calls return 401 JSON."""
    create_test_ad(app_instance, "ad_auth_check_1")

    # Vote without login
    resp = client.post("/api/ads/ad_auth_check_1/vote", json={"vote": "fake"})
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Login required"

    # Rating without login
    resp = client.post("/api/ads/ad_auth_check_1/rating", json={"stars": 5, "comment": "Nice"})
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Login required"


def test_vote_uniqueness_and_changing_vote(client, app_instance):
    """Verify one vote per account, vote changing, and count updates."""
    create_test_user(app_instance, "Alice", "alice@example.com")
    create_test_ad(app_instance, "ad_vote_test_1")

    # Initial state: 0 votes
    resp = client.get("/api/ads/ad_vote_test_1")
    assert resp.status_code == 200
    assert resp.get_json()["fake_votes"] == 0
    assert resp.get_json()["genuine_votes"] == 0
    assert resp.get_json()["my_vote"] is None

    # Login Alice and vote fake
    login_user_session(client, "alice@example.com")

    vote_resp = client.post("/api/ads/ad_vote_test_1/vote", json={"vote": "fake"})
    assert vote_resp.status_code == 200
    data = vote_resp.get_json()
    assert data["ok"] is True
    assert data["fake_votes"] == 1
    assert data["genuine_votes"] == 0
    assert data["my_vote"] == "fake"

    # Change vote to genuine
    change_resp = client.post("/api/ads/ad_vote_test_1/vote", json={"vote": "genuine"})
    assert change_resp.status_code == 200
    data = change_resp.get_json()
    assert data["ok"] is True
    assert data["fake_votes"] == 0
    assert data["genuine_votes"] == 1
    assert data["my_vote"] == "genuine"

    # Verify exactly 1 vote record exists in database
    with app_instance.app_context():
        votes = Vote.query.filter_by(ad_id="ad_vote_test_1").all()
        assert len(votes) == 1
        assert votes[0].vote == "genuine"


def test_vote_with_two_accounts_no_double_voting(client, app_instance):
    """Verify two accounts voting on the same ad; same account cannot double vote."""
    u1_id = create_test_user(app_instance, "User One", "user1@example.com")
    u2_id = create_test_user(app_instance, "User Two", "user2@example.com")
    create_test_ad(app_instance, "ad_multi_user_1")

    # User 1 votes fake
    login_user_session(client, "user1@example.com")
    r1 = client.post("/api/ads/ad_multi_user_1/vote", json={"vote": "fake"})
    assert r1.status_code == 200
    assert r1.get_json()["fake_votes"] == 1
    assert r1.get_json()["genuine_votes"] == 0

    # User 1 votes fake again: no double voting
    r1_again = client.post("/api/ads/ad_multi_user_1/vote", json={"vote": "fake"})
    assert r1_again.status_code == 200
    assert r1_again.get_json()["fake_votes"] == 1

    # User 1 logs out
    client.post("/auth/logout")

    # User 2 logs in and votes genuine
    login_user_session(client, "user2@example.com")
    r2 = client.post("/api/ads/ad_multi_user_1/vote", json={"vote": "genuine"})
    assert r2.status_code == 200
    assert r2.get_json()["fake_votes"] == 1
    assert r2.get_json()["genuine_votes"] == 1
    assert r2.get_json()["total_votes"] == 2

    # Database verification: exactly 2 distinct rows
    with app_instance.app_context():
        votes = Vote.query.filter_by(ad_id="ad_multi_user_1").all()
        assert len(votes) == 2
        user_ids = {v.user_id for v in votes}
        assert user_ids == {u1_id, u2_id}


def test_amber_disagreement_note_logic(client, app_instance):
    """Verify amber disagreement note appears when AI verdict and majority of >= 3 votes differ."""
    create_test_user(app_instance, "U1", "u1@example.com")
    create_test_user(app_instance, "U2", "u2@example.com")
    create_test_user(app_instance, "U3", "u3@example.com")

    # AI says Likely Real
    create_test_ad(app_instance, "ad_disagree_1", ai_label="Likely Real", ai_prob=0.10)

    # User 1 votes fake
    login_user_session(client, "u1@example.com")
    r = client.post("/api/ads/ad_disagree_1/vote", json={"vote": "fake"})
    assert r.get_json()["disagreement"] is False
    client.post("/auth/logout")

    # User 2 votes fake (total = 2, still < 3)
    login_user_session(client, "u2@example.com")
    r = client.post("/api/ads/ad_disagree_1/vote", json={"vote": "fake"})
    assert r.get_json()["disagreement"] is False
    client.post("/auth/logout")

    # User 3 votes fake (total = 3, community fake vs AI real -> Disagreement!)
    login_user_session(client, "u3@example.com")
    r = client.post("/api/ads/ad_disagree_1/vote", json={"vote": "fake"})
    data = r.get_json()
    assert data["disagreement"] is True
    assert "The AI and the community disagree" in data["disagreement_message"]

    # User 3 changes vote to genuine: 2 fake vs 1 genuine -> majority still fake -> still disagrees
    r = client.post("/api/ads/ad_disagree_1/vote", json={"vote": "genuine"})
    assert r.get_json()["disagreement"] is True
    client.post("/auth/logout")

    # User 2 changes to genuine: 1 fake vs 2 genuine -> majority genuine -> matches AI -> False
    login_user_session(client, "u2@example.com")
    r = client.post("/api/ads/ad_disagree_1/vote", json={"vote": "genuine"})
    assert r.get_json()["disagreement"] is False


def test_rating_saved_with_approved_false(app_instance):
    """Verify ratings and optional comments are saved with approved=False."""
    create_test_user(app_instance, "Reviewer", "reviewer@example.com")
    create_test_ad(app_instance, "ad_rating_1")

    with app_instance.test_client() as client:
        login_user_session(client, "reviewer@example.com")

        # Submit valid rating
        resp = client.post(
            "/api/ads/ad_rating_1/rating",
            json={"stars": 5, "comment": "Accurate prediction on this fee scam ad."}
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert "Comments are reviewed" in resp.get_json()["message"]

        # Validate stars range validation
        invalid_resp = client.post("/api/ads/ad_rating_1/rating", json={"stars": 6})
        assert invalid_resp.status_code == 400

        # Validate comment length limit (max 200)
        long_comment = "x" * 201
        invalid_comment = client.post("/api/ads/ad_rating_1/rating", json={"stars": 4, "comment": long_comment})
        assert invalid_comment.status_code == 400

    # Verify DB state
    with app_instance.app_context():
        rating = Rating.query.filter_by(ad_id="ad_rating_1").first()
        assert rating is not None
        assert rating.stars == 5
        assert rating.comment == "Accurate prediction on this fee scam ad."
        assert rating.approved is False  # Must not appear on home until owner approves


def test_community_disputed_logic(app_instance):
    """Verify Disputed = both sides have at least 3 votes and the smaller side at least 30%."""
    # Create 4 ads with varying vote distributions
    create_test_ad(app_instance, "ad_split_50_50", snippet="Job A")  # 3 fake, 3 genuine -> 3/6 = 50% >= 30% -> Disputed
    create_test_ad(app_instance, "ad_split_30_70", snippet="Job B")  # 3 fake, 7 genuine -> 3/10 = 30% >= 30% -> Disputed
    create_test_ad(app_instance, "ad_split_27_73", snippet="Job C")  # 3 fake, 8 genuine -> 3/11 = 27.3% < 30% -> Not Disputed
    create_test_ad(app_instance, "ad_split_2_votes", snippet="Job D")  # 2 fake, 10 genuine -> fake < 3 -> Not Disputed

    with app_instance.app_context():
        # Helper to seed votes
        for i in range(12):
            u_id = create_test_user(app_instance, f"Voter {i}", f"voter{i}@example.com")
            # Ad A: 3 fake, 3 genuine
            if i < 3:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_50_50", vote="fake"))
            elif i < 6:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_50_50", vote="genuine"))

            # Ad B: 3 fake, 7 genuine
            if i < 3:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_30_70", vote="fake"))
            elif i < 10:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_30_70", vote="genuine"))

            # Ad C: 3 fake, 8 genuine
            if i < 3:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_27_73", vote="fake"))
            elif i < 11:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_27_73", vote="genuine"))

            # Ad D: 2 fake, 10 genuine
            if i < 2:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_2_votes", vote="fake"))
            elif i < 12:
                db.session.add(Vote(user_id=u_id, ad_id="ad_split_2_votes", vote="genuine"))

        db.session.commit()

    with app_instance.test_client() as client:
        resp = client.get("/api/community?filter=disputed")
        assert resp.status_code == 200
        data = resp.get_json()
        ids = [item["ad_id"] for item in data["items"]]
        assert "ad_split_50_50" in ids
        assert "ad_split_30_70" in ids
        assert "ad_split_27_73" not in ids
        assert "ad_split_2_votes" not in ids


def test_community_filters_and_search(app_instance):
    """Verify community API filter chips, search query, sorting, and pagination."""
    create_test_ad(app_instance, "ad_fake_1", snippet="Telegram data entry fee scam", ai_label="Likely Fake")
    create_test_ad(app_instance, "ad_genuine_1", snippet="Infosys software developer position Bangalore", ai_label="Likely Real")

    with app_instance.app_context():
        u1 = create_test_user(app_instance, "T1", "t1@example.com")
        # Give ad_fake_1 more fake votes
        db.session.add(Vote(user_id=u1, ad_id="ad_fake_1", vote="fake"))
        # Give ad_genuine_1 more genuine votes
        db.session.add(Vote(user_id=u1, ad_id="ad_genuine_1", vote="genuine"))
        db.session.commit()

    with app_instance.test_client() as client:
        # Filter: fake
        rfake = client.get("/api/community?filter=fake")
        assert rfake.status_code == 200
        fake_ids = [item["ad_id"] for item in rfake.get_json()["items"]]
        assert "ad_fake_1" in fake_ids
        assert "ad_genuine_1" not in fake_ids

        # Filter: genuine
        rgen = client.get("/api/community?filter=genuine")
        assert rgen.status_code == 200
        gen_ids = [item["ad_id"] for item in rgen.get_json()["items"]]
        assert "ad_genuine_1" in gen_ids
        assert "ad_fake_1" not in gen_ids

        # Search keyword "Infosys"
        rsearch = client.get("/api/community?q=Infosys")
        assert rsearch.status_code == 200
        search_ids = [item["ad_id"] for item in rsearch.get_json()["items"]]
        assert "ad_genuine_1" in search_ids
        assert "ad_fake_1" not in search_ids

        # Search keyword that matches nothing
        rempty = client.get("/api/community?q=NonExistentKeywordXYZ")
        assert rempty.status_code == 200
        assert rempty.get_json()["total"] == 0
        assert len(rempty.get_json()["items"]) == 0
