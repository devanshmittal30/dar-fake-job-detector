# wsgi.py
# Entry point for gunicorn in production.
# Usage: gunicorn wsgi:app

from app import create_app

app = create_app()
