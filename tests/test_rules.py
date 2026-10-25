"""tests/test_rules.py
Unit tests for rule-based warning flags in app/rules.py.
"""

import pytest
from app.rules import check_rules


def test_money_fee_flag():
    """Verify detection of fee, money, or deposit requests."""
    text = "Candidate must deposit a refundable registration fee of 500 rupees before onboarding."
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "money_fee" in codes


def test_sensitive_data_flag():
    """Verify detection of sensitive personal data requests (Aadhaar, PAN, OTP, bank account)."""
    text = "Please share your Aadhaar number, PAN card copy, and bank account details for verification."
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "sensitive_data" in codes


def test_social_messaging_flag():
    """Verify detection of WhatsApp or Telegram exclusive contact requests."""
    text = "Do not apply via email; contact our HR manager directly on WhatsApp at 9876543210."
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "social_messaging" in codes


def test_free_email_flag():
    """Verify detection of free webmail addresses used for hiring."""
    text = "Interested candidates should forward resume to company_careers2024@gmail.com."
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "free_email" in codes


def test_no_interview_flag():
    """Verify detection of 'no interview', 'direct selection', or 'instant joining'."""
    text = "Great opportunity: Instant joining and direct selection with spot offer for all applicants!"
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "no_interview" in codes


def test_unrealistic_pay_flag():
    """Verify detection of unrealistic pay or daily earning schemes."""
    text = "Work from home for 2 hours and earn 3000 daily with guaranteed income!"
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "unrealistic_pay" in codes


def test_urgency_flag():
    """Verify detection of high-pressure urgency keywords."""
    text = "Limited slots available! Hurry up and apply immediately before offer expires today."
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "urgency" in codes


def test_no_company_info_flag():
    """Verify detection of vague anonymous companies."""
    text = "A leading MNC is hiring for various profiles across India. Submit details."
    flags = check_rules(text)
    codes = [f["code"] for f in flags]
    assert "no_company_info" in codes


def test_clean_ad_triggers_no_flags():
    """Verify legitimate corporate job postings trigger no warning flags."""
    text = (
        "Infosys Technologies Ltd is hiring a Senior Software Engineer for Bangalore office. "
        "Candidates should hold a B.Tech degree with 4 years experience in Python and cloud services. "
        "Apply through our corporate portal at careers.infosys.com."
    )
    flags = check_rules(text)
    assert len(flags) == 0


def test_empty_input_handling():
    """Verify empty or None text inputs return empty flag list gracefully."""
    assert check_rules("") == []
    assert check_rules("   ") == []
    assert check_rules(None) == []


def test_multiple_flags_simultaneous():
    """Verify multi-flag scam postings trigger all relevant indicators."""
    text = (
        "Hurry up! Earn 5000 daily with instant joining. Send 500 registration fee to "
        "recruiter@gmail.com or message on Telegram."
    )
    flags = check_rules(text)
    codes = {f["code"] for f in flags}
    expected = {"urgency", "unrealistic_pay", "no_interview", "money_fee", "free_email", "social_messaging"}
    assert expected.issubset(codes)
