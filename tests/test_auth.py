"""tests/test_auth.py
Unit and integration tests for authentication system in app/routes_auth.py.

Following docs/03_TECHNICAL_DESIGN.md (sections 7, 8, 9) and roadmap prompt P12:
- User registration with password hashing (minimum 8 characters).
- Duplicate email prevention (lowercase index).
- Login with correct and incorrect credentials.
- Password not stored in plain text.
- Logout flow and /auth/me state.
- Open redirect prevention (only relative paths accepted).
"""

import pytest
from werkzeug.security import check_password_hash

from app import create_app
from app.config import Config
from app.models import User, db


class AuthTestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def app_instance():
    app = create_app(AuthTestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    with app_instance.test_client() as test_client:
        yield test_client


def test_register_new_user_success(client, app_instance):
    """Verify user registration, password hashing, and immediate login."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Devansh Mittal",
            "email": "Devansh@Example.COM",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123"
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["ok"] is True
    assert data["user"]["email"] == "devansh@example.com"

    # Verify database persistence & password hashing
    with app_instance.app_context():
        user = User.query.filter_by(email="devansh@example.com").first()
        assert user is not None
        assert user.name == "Devansh Mittal"
        # Password must NEVER be readable in plain text
        assert user.password_hash != "SecurePassword123"
        assert check_password_hash(user.password_hash, "SecurePassword123")

    # Verify session is authenticated
    me_resp = client.get("/auth/me")
    assert me_resp.status_code == 200
    me_data = me_resp.get_json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["name"] == "Devansh Mittal"


def test_register_duplicate_email_rejected(client):
    """Verify that duplicate email registration (case-insensitive) is rejected."""
    # Register first user
    r1 = client.post(
        "/auth/register",
        json={
            "name": "First User",
            "email": "user@domain.com",
            "password": "Password123"
        }
    )
    assert r1.status_code == 201

    # Log out first user so second registration can be evaluated
    client.post("/auth/logout")

    # Attempt registration with uppercase variant
    r2 = client.post(
        "/auth/register",
        json={
            "name": "Duplicate User",
            "email": "USER@DOMAIN.COM",
            "password": "AnotherPassword123"
        }
    )
    assert r2.status_code == 400
    assert "Email already registered." in r2.get_json()["error"]


def test_register_password_length_validation(client):
    """Verify that passwords under 8 characters are rejected."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Short Pass User",
            "email": "short@domain.com",
            "password": "short"
        }
    )
    assert response.status_code == 400
    assert "at least 8 characters" in response.get_json()["error"]


def test_login_flow_and_wrong_password(client):
    """Verify login authentication and rejection of incorrect passwords."""
    client.post(
        "/auth/register",
        json={
            "name": "Login Tester",
            "email": "tester@domain.com",
            "password": "CorrectPassword123"
        }
    )
    client.post("/auth/logout")

    # Wrong password
    bad_login = client.post(
        "/auth/login",
        json={
            "email": "tester@domain.com",
            "password": "WrongPassword999"
        }
    )
    assert bad_login.status_code == 400
    assert bad_login.get_json()["error"] == "Wrong email or password."

    # Correct password
    good_login = client.post(
        "/auth/login",
        json={
            "email": "tester@domain.com",
            "password": "CorrectPassword123"
        }
    )
    assert good_login.status_code == 200
    assert good_login.get_json()["ok"] is True

    # Check /auth/me
    me = client.get("/auth/me").get_json()
    assert me["authenticated"] is True


def test_logout_clears_session(client):
    """Verify that /auth/logout clears user session."""
    client.post(
        "/auth/register",
        json={
            "name": "Logout Tester",
            "email": "logout@domain.com",
            "password": "Password123"
        }
    )
    assert client.get("/auth/me").get_json()["authenticated"] is True

    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code in (200, 302)
    assert client.get("/auth/me").get_json()["authenticated"] is False


def test_safe_redirect_prevents_open_redirect(client):
    """Verify redirect after login accepts only relative paths and blocks external domains."""
    # Attempt open redirect
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "test@domain.com",
            "password": "pwd",
            "next": "https://evil.com/phishing"
        }
    )
    # Even if login fails, safe redirect helper defaults to /
    from app.routes_auth import is_safe_redirect
    assert is_safe_redirect("https://evil.com/phishing") is False
    assert is_safe_redirect("//evil.com") is False
    assert is_safe_redirect("javascript:alert(1)") is False
    assert is_safe_redirect("/result/some_hash") is True
    assert is_safe_redirect("/analyze") is True
