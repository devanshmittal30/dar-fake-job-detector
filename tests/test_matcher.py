"""tests/test_matcher.py
Unit tests for duplicate and near-duplicate job advertisement matching in app/matcher.py.

Following docs/03_TECHNICAL_DESIGN.md (section 5.4) and roadmap prompt P12:
- Exact copy matches (SHA-256).
- Near-duplicate with small OCR-like errors matches (threshold 0.85).
- Distinct job ad does not match (< 0.85).
"""

import pytest
from app import create_app
from app.config import Config
from app.matcher import (
    clear_cache,
    find_matching_ad,
    index_ad
)
from app.models import Ad, db
from app.predictor import make_ad_id


class MatcherTestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def app_ctx():
    """Create test application context with in-memory database."""
    app = create_app(MatcherTestConfig)
    with app.app_context():
        clear_cache()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        clear_cache()


def test_exact_ad_copy_matches(app_ctx):
    """Verify that an exact copy matches and returns the original ad_id."""
    original_text = (
        "Senior Cloud Architect wanted at Infosys Limited Bangalore. Candidates must have 7+ years "
        "experience with AWS, Kubernetes, Terraform, Python backend services, and distributed systems. "
        "Competitive salary package including annual bonus, health cover, and stock options. "
        "Apply via official career portal."
    )
    ad_id = make_ad_id(original_text)

    # Insert into DB and index in matcher cache
    ad = Ad(
        ad_id=ad_id,
        snippet=original_text[:200],
        full_text=original_text,
        ai_label="Likely Real",
        ai_probability=0.08,
        model_used="lr",
        check_count=1
    )
    db.session.add(ad)
    db.session.commit()
    index_ad(ad_id, original_text)

    # Query with exact text
    matched_id = find_matching_ad(original_text)
    assert matched_id == ad_id


def test_near_duplicate_ocr_typos_matches(app_ctx):
    """Verify that small OCR-like imperfections match the original ad (similarity >= 0.85)."""
    original_text = (
        "URGENT HIRING: Remote Data Entry Operator needed immediately. Work from home and earn "
        "forty-five thousand rupees weekly with flexible hours. Instant joining without any interview. "
        "Selected candidates must pay a refundable registration fee of 1500 rupees for training kit. "
        "Contact our HR manager strictly on WhatsApp at 9876543210 or join our Telegram channel today. "
        "Please send your Aadhaar card and PAN card copies to confirm seat."
    )
    ad_id = make_ad_id(original_text)
    index_ad(ad_id, original_text)

    # Simulated OCR screenshot extraction with minor typos, punctuation shifts, and casing
    ocr_extracted_text = (
        "URGENT HIRING: Rem0te Data Entry 0perator needed immediately. Work from home and earn "
        "forty-five th0usand rupees weekly with flexible hours! lnstant joining without any interview. "
        "Selected candidates must pay a refundable registrati0n fee of 1500 rupees for training kit. "
        "C0ntact our HR manager strictly on WhatsApp at 9876543210 or join our Telegram channe1 today. "
        "Please send your Aadhaar card and PAN card c0pies to confirm seat."
    )

    matched_id = find_matching_ad(ocr_extracted_text)
    assert matched_id == ad_id, "Matcher failed to recognize near-duplicate OCR text with typos"


def test_distinct_job_ad_does_not_match(app_ctx):
    """Verify that a completely different job posting returns None."""
    ad_text_1 = (
        "Lead Frontend Engineer needed at Swiggy Bangalore for React, Redux, Next.js, and TypeScript. "
        "Build customer-facing mobile-first consumer applications with micro-frontend architectures. "
        "Offers competitive salary, flexible leave policy, and medical insurance."
    )
    ad_id_1 = make_ad_id(ad_text_1)
    index_ad(ad_id_1, ad_text_1)

    distinct_ad_text = (
        "Hiring Registered Nursing Staff for Max Super Speciality Hospital Saket New Delhi. "
        "Requires BSc Nursing or GNM with 2+ years ICU/emergency room experience. Day and night shifts. "
        "Submit documents at HR reception counter between 10 AM and 4 PM."
    )

    matched_id = find_matching_ad(distinct_ad_text)
    assert matched_id is None, "Matcher falsely matched a distinct job ad"
