"""app/__init__.py
Flask application factory for DAR Fake Job Detector.

Following docs/03_TECHNICAL_DESIGN.md (sections 1, 6, 7) and prompt P8:
- create_app() factory pattern
- CSRF protection with Flask-WTF
- Configuration loaded from app.config.Config
- Health check route: GET /health -> {"status": "ok"}
- Global 404 and 500 error handlers
- Blueprint registration for page routes
"""

from pathlib import Path
from flask import Flask, jsonify, render_template
from flask_wtf.csrf import CSRFProtect

from app.config import Config

csrf = CSRFProtect()


def create_app(config_class: type = Config) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance directory exists for SQLite database
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    csrf.init_app(app)

    # Register blueprints
    from app.routes_pages import bp_pages
    app.register_blueprint(bp_pages)

    # Health check route (used by Render uptime checks and tests)
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

    return app
