"""app/temp_store.py
TEMPORARY server-side in-memory cache for job ad analysis results.
Will be replaced by the SQLAlchemy Ad model in Stage 5 (docs/04_DEVELOPMENT_ROADMAP.md prompt P12).
"""

# TEMPORARY dictionary storing analysis results by ad_id (SHA-256 hash)
TEMPORARY_RESULTS: dict[str, dict] = {}


def get_demo_ad_result(ad_id: str = "demo_ad_hash_123456") -> dict:
    """Return a realistic demo result for testing and direct URL visits."""
    sample_text = (
        "URGENT HIRING: Data Entry Operator needed immediately. Work from home and earn 45,000 rupees "
        "weekly with flexible hours. Instant joining without any interview needed. Selected candidates "
        "must pay a refundable registration fee of 1500 rupees for training kit and verification before start. "
        "Contact our HR manager strictly on WhatsApp at 9876543210 or join our Telegram channel t.me/fastjobs today. "
        "Please send your Aadhaar card and PAN card copies to confirm your seat immediately. Limited vacancies available!"
    )
    return {
        "ad_id": ad_id,
        "raw_text": sample_text,
        "verdict": "Likely Fake",
        "probability": 0.94,
        "threshold": 0.62,
        "model_key": "lr",
        "model_name": "Logistic Regression",
        "word_count": len(sample_text.split()),
        "source": "text",
        "top_fake_words": [
            {"word": "registration fee", "weight": 2.45},
            {"word": "whatsapp", "weight": 2.15},
            {"word": "telegram", "weight": 1.95},
            {"word": "instant joining", "weight": 1.80},
            {"word": "aadhaar", "weight": 1.65},
            {"word": "pan card", "weight": 1.55},
            {"word": "refundable", "weight": 1.40},
            {"word": "data entry", "weight": 1.25}
        ],
        "top_real_words": [
            {"word": "flexible", "weight": 0.45},
            {"word": "weekly", "weight": 0.35},
            {"word": "operator", "weight": 0.25}
        ],
        "flags": [
            {"code": "money_fee", "message": "Asks for money, registration fee, security deposit or laptop charge."},
            {"code": "sensitive_data", "message": "Asks for sensitive personal details like bank account, Aadhaar, PAN or OTP."},
            {"code": "social_messaging", "message": "Directs communication exclusively to WhatsApp or Telegram instead of official channels."},
            {"code": "no_interview", "message": "Promises instant joining or job offers without any formal interview process."}
        ],
        "highlighted_html": (
            "URGENT HIRING: Data Entry Operator needed immediately. Work from home and earn 45,000 rupees "
            "weekly with flexible hours. <mark class=\"highlight-warn\">Instant joining without any interview</mark> needed. "
            "Selected candidates must pay a <mark class=\"highlight-fake\">refundable registration fee</mark> of 1500 rupees "
            "for training kit and verification before start. Contact our HR manager strictly on "
            "<mark class=\"highlight-warn\">WhatsApp at 9876543210</mark> or join our "
            "<mark class=\"highlight-warn\">Telegram channel</mark> today. Please send your "
            "<mark class=\"highlight-warn\">Aadhaar card and PAN card</mark> copies to confirm your seat immediately. "
            "Limited vacancies available!"
        )
    }
