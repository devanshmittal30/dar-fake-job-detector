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


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dar-dev-secret-key-change-in-production-1234567890")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Database: SQLite in instance folder for local development, Neon PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'dar.db'}")
    # Handle postgres:// vs postgresql:// protocol in Render/Heroku URLs
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
