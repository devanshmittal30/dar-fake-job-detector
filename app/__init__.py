"""app/__init__.py
Flask application factory for DAR Fake Job Detector.

Following docs/03_TECHNICAL_DESIGN.md (sections 1, 6, 7, 8, 9) and roadmap prompt P12:
- create_app() factory pattern
- Flask-SQLAlchemy initialization and db.create_all() at startup
- Flask-Login authentication and session management
- CSRF protection with Flask-WTF
- Rate limiting with Flask-Limiter:
    * 30 per min for analyze & fetch
    * 10 per min for register & login
- Configuration loaded from app.config.Config
- Health check route: GET /health -> {"status": "ok"}
- Global 404, 500, and 429 error handlers
- Blueprint registration for pages, api, and auth
"""

from pathlib import Path
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from app.config import Config
from app.models import User, db

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["300 per hour"]
)
login_manager = LoginManager()


def create_app(config_class: type = Config) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Cookie security policy (docs/03_TECHNICAL_DESIGN.md section 9)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (app.config.get("FLASK_ENV") == "production")

    # Ensure instance directory exists for SQLite database
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "pages.auth"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "info"

    @login_manager.unauthorized_handler
    def handle_unauthorized():
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Login required"}), 401
        return redirect(url_for(login_manager.login_view, next=request.path))

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        """Load user by primary key for Flask-Login session."""
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Register blueprints
    from app.routes_pages import bp_pages
    from app.routes_api import bp_api
    from app.routes_auth import bp_auth

    app.register_blueprint(bp_pages)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_auth)

    # Apply rate limits (docs/03_TECHNICAL_DESIGN.md section 9)
    limiter.limit("30 per minute")(bp_api)
    limiter.limit("10 per minute")(bp_auth)

    # Database initialization & matcher cache preloading
    with app.app_context():
        try:
            db.create_all()
            from app.matcher import load_cache_from_db
            load_cache_from_db()
        except Exception as exc:
            app.logger.warning("Database startup note (deferred until first request): %s", exc)

    # Health check route
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok"}), 200

    # Error handlers
    @app.errorhandler(404)
    def handle_not_found(error):
        """Render branded 404 page."""
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def handle_server_error(error):
        """Render branded 500 page."""
        return render_template("500.html"), 500

    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle rate limit errors with friendly JSON."""
        return jsonify({
            "error": "Rate limit exceeded. Please slow down and try again shortly."
        }), 429

    return app
