"""app/config.py
Configuration settings for DAR Fake Job Detector.

Loads configuration from environment variables (.env) with sensible development fallbacks.
Following docs/03_TECHNICAL_DESIGN.md (section 8).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present
load_dotenv(BASE_DIR / ".env")


from sqlalchemy.engine import make_url


def _normalize_database_url(raw_url: str | None, default_url: str) -> str:
    """Sanitize and normalize the database connection URL for SQLAlchemy.
    Handles quotes, psql command prefixes, postgres:// schemes, and empty env vars.
    Safely validates with make_url and falls back to default_url on any parse error.
    """
    if not raw_url:
        return default_url
    url = raw_url.strip()
    # Strip key name if accidentally pasted in Render Value field
    if url.startswith("DATABASE_URL="):
        url = url[len("DATABASE_URL="):].strip()
    # Strip psql CLI command prefix if copied from Neon psql tab
    if url.startswith("psql "):
        url = url[5:].strip()
    # Strip outer quotes
    if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
        url = url[1:-1].strip()
    # Handle postgres:// vs postgresql:// protocol in Render/Heroku URLs
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    # Must be postgresql or sqlite scheme
    if not (url.startswith("postgresql://") or url.startswith("sqlite:///")):
        return default_url
    try:
        make_url(url)
        return url
    except Exception:
        return default_url


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dar-dev-secret-key-change-in-production-1234567890")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Database: SQLite in instance folder for local development, Neon PostgreSQL in production
    _default_db = f"sqlite:///{BASE_DIR / 'instance' / 'dar.db'}"
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.getenv("DATABASE_URL"), _default_db)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Engine options for Neon serverless PostgreSQL:
    # pool_pre_ping checks connections before use so suspended Neon compute doesn't cause 502/500 errors
    # pool_recycle recycles idle connections before Neon's 5-minute timeout drops them
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # CSRF protection enabled
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Token valid for session duration

    # Session and Cookie security (docs/03_TECHNICAL_DESIGN.md section 9)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (FLASK_ENV == "production")
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = (FLASK_ENV == "production")

    # Tesseract OCR path configuration (optional override)
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
