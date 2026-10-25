"""app/routes_auth.py
Authentication blueprint for DAR Fake Job Detector using Flask-Login and Werkzeug.

Following docs/03_TECHNICAL_DESIGN.md (sections 7 and 9) and docs/02_UI_UX_SPEC.md (section 9.6):
- POST /auth/register: User registration with password hashing (min 8 chars) and lowercase email.
- POST /auth/login: User authentication with secure session cookie.
- GET/POST /auth/logout: User sign out.
- GET /auth/me: Current user authentication status and profile payload.
- Rate limits: 10 per minute per IP on register and login.
- Safe redirect: Enforces relative URLs only (no open redirects).
"""

from urllib.parse import urlparse
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, db

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")


def is_safe_redirect(target: str | None) -> bool:
    """Verify that a redirect URL is strictly relative and safe against open-redirect attacks."""
    if not target or not isinstance(target, str):
        return False
    target = target.strip()
    if not target.startswith("/") or target.startswith("//") or "\\" in target:
        return False
    # Parse URL and verify netloc is empty
    try:
        parsed = urlparse(target)
        return not bool(parsed.netloc) and not bool(parsed.scheme)
    except Exception:
        return False


def get_safe_redirect_target(default: str = "/") -> str:
    """Get validated relative redirect target from query parameters or JSON body."""
    target = request.args.get("next")
    if not target and request.is_json:
        data = request.get_json(silent=True) or {}
        target = data.get("next")
    elif not target and request.form:
        target = request.form.get("next")

    if is_safe_redirect(target):
        return target
    return default


@bp_auth.route("/register", methods=["POST"])
def register():
    """Register a new user account.

    Expects JSON or Form:
        name, email, password, confirm_password (optional)
    """
    if current_user.is_authenticated:
        return jsonify({"ok": True, "redirect": url_for("pages.home")}), 200

    if request.is_json:
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        confirm = data.get("confirm_password", "")
        is_json = True
    else:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        is_json = False

    # Validations
    if not name:
        err = "Please enter your full name."
        return jsonify({"error": err}), 400 if is_json else _render_auth_error(err, "register")

    if not email or "@" not in email or "." not in email:
        err = "Please enter a valid email address."
        return jsonify({"error": err}), 400 if is_json else _render_auth_error(err, "register")

    if len(password) < 8:
        err = "Password must be at least 8 characters long."
        return jsonify({"error": err}), 400 if is_json else _render_auth_error(err, "register")

    if confirm and password != confirm:
        err = "Passwords do not match."
        return jsonify({"error": err}), 400 if is_json else _render_auth_error(err, "register")

    # Check for existing email (case-insensitive)
    existing = User.query.filter_by(email=email).first()
    if existing:
        err = "Email already registered."
        return jsonify({"error": err}), 400 if is_json else _render_auth_error(err, "register")

    # Create user with hashed password
    hashed_password = generate_password_hash(password, method="scrypt")
    user = User(
        name=name,
        email=email,
        password_hash=hashed_password
    )
    db.session.add(user)
    db.session.commit()

    # Log in immediately after registration
    login_user(user)

    redirect_url = get_safe_redirect_target(default=url_for("pages.home"))
    if is_json:
        return jsonify({
            "ok": True,
            "message": "Account created successfully.",
            "redirect": redirect_url,
            "user": {"id": user.id, "name": user.name, "email": user.email}
        }), 201

    flash(f"Welcome to DAR, {user.name}!", "success")
    return redirect(redirect_url)


@bp_auth.route("/login", methods=["POST"])
def login():
    """Authenticate an existing user.

    Expects JSON or Form:
        email, password, next (optional)
    """
    if current_user.is_authenticated:
        return jsonify({"ok": True, "redirect": url_for("pages.home")}), 200

    if request.is_json:
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        is_json = True
    else:
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        is_json = False

    if not email or not password:
        err = "Wrong email or password."
        return jsonify({"error": err}), 400 if is_json else _render_auth_error(err, "login")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        err = "Wrong email or password."
        return jsonify({"error": err}), 400 if is_json else _render_auth_error(err, "login")

    # Log in session
    login_user(user, remember=True)

    redirect_url = get_safe_redirect_target(default=url_for("pages.home"))
    if is_json:
        return jsonify({
            "ok": True,
            "message": "Logged in successfully.",
            "redirect": redirect_url,
            "user": {"id": user.id, "name": user.name, "email": user.email}
        }), 200

    flash(f"Welcome back, {user.name}!", "success")
    return redirect(redirect_url)


@bp_auth.route("/logout", methods=["GET", "POST"])
def logout():
    """Log out currently authenticated user."""
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "info")

    if request.is_json:
        return jsonify({"ok": True, "redirect": url_for("pages.home")}), 200

    return redirect(url_for("pages.home"))


@bp_auth.route("/me", methods=["GET"])
def me():
    """Return profile info of the currently logged-in user."""
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email
            }
        }), 200
    return jsonify({"authenticated": False}), 200


def _render_auth_error(message: str, active_tab: str):
    """Helper to re-render auth page with error flash."""
    flash(message, "error")
    return redirect(url_for("pages.auth", tab=active_tab))
