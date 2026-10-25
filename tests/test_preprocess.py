"""tests/test_preprocess.py
Unit tests for text preprocessing, field joining, and dataset splitting.

Requirements from prompt P4 and docs/03_TECHNICAL_DESIGN.md (section 5.3):
- At least 6 test cases for text cleaning and preparation.
- A test asserting that train.csv and test.csv share no overlapping text.
- Note: This file is finalised in P4 and never touched afterwards.
"""

from pathlib import Path
import pandas as pd
import pytest

from ml.preprocess import build_text, clean_text


def test_clean_text_lowercase():
    """Verify that all uppercase characters are converted to lowercase."""
    raw = "URGENT HIRING: Senior Python Developer Needed Immediately!"
    cleaned = clean_text(raw)
    assert cleaned == cleaned.lower()
    assert "urgent hiring" in cleaned
    assert "senior python developer" in cleaned


def test_clean_text_html_removal():
    """Verify that HTML tags and HTML entities are removed."""
    raw = "<div><h1>Job Description</h1><p>We need a coder &amp; designer.&nbsp;</p><br/></div>"
    cleaned = clean_text(raw)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "&amp;" not in cleaned
    assert "&nbsp;" not in cleaned
    assert "job description" in cleaned
    assert "we need a coder" in cleaned
    assert "designer" in cleaned


def test_clean_text_url_replacement():
    """Verify that HTTP, HTTPS, and WWW URLs are replaced with 'urltoken'."""
    raw = "Apply at https://careers.example.com/job1 or visit http://site.org or www.applyhere.co.uk now."
    cleaned = clean_text(raw)
    assert "https://" not in cleaned
    assert "http://" not in cleaned
    assert "www." not in cleaned
    assert cleaned.count("urltoken") == 3


def test_clean_text_email_replacement():
    """Verify that email addresses are replaced with 'emailtoken'."""
    raw = "Send your CV to jobs.fake_corp@domain.com or hr-department@company.org."
    cleaned = clean_text(raw)
    assert "@" not in cleaned
    assert cleaned.count("emailtoken") == 2


def test_clean_text_phone_replacement():
    """Verify that telephone numbers in multiple standard formats are replaced with 'phonetoken'."""
    raw = "Call us at +1-800-555-0199 or (555) 234-5678 or 9876543210 for quick interview."
    cleaned = clean_text(raw)
    assert "+1-800" not in cleaned
    assert "phonetoken" in cleaned
    assert "quick interview" in cleaned


def test_clean_text_character_filtering_and_currency():
    """Verify that letters, digits, basic currency symbols ($, €, £, ₹), and % are preserved,
    while punctuation marks and special symbols are stripped.
    """
    raw = "Salary: $5,000 to €4,500 / £3,800 / ₹3,00,000 per month! (100% remote work) ***apply***"
    cleaned = clean_text(raw)
    # Currency symbols and percent must be preserved
    assert "$" in cleaned
    assert "€" in cleaned
    assert "£" in cleaned
    assert "₹" in cleaned
    assert "%" in cleaned
    # Punctuation like exclamation marks, asterisks, commas, and parentheses must be removed
    assert "!" not in cleaned
    assert "*" not in cleaned
    assert "," not in cleaned
    assert "(" not in cleaned
    assert ")" not in cleaned


def test_clean_text_whitespace_and_edge_cases():
    """Verify handling of None, NaN, empty strings, and collapsing multiple spaces."""
    assert clean_text(None) == ""
    assert clean_text("") == ""
    assert clean_text("   \n\t  ") == ""
    assert clean_text("nan") == ""
    assert clean_text(float("nan")) == ""

    # Collapse multiple consecutive whitespaces
    multiple_spaces = "Data    Scientist   \n\n\t  Position   available   "
    assert clean_text(multiple_spaces) == "data scientist position available"


def test_build_text_field_concatenation():
    """Verify that build_text joins title, company_profile, description, requirements, benefits in order."""
    row = {
        "title": "Software Engineer",
        "company_profile": "Top Tech Innovator",
        "description": "Building next-gen AI systems.",
        "requirements": "Python, SQL, PyTorch",
        "benefits": "Competitive pay and equity"
    }
    result = build_text(row)
    expected = (
        "Software Engineer Top Tech Innovator Building next-gen AI systems. "
        "Python, SQL, PyTorch Competitive pay and equity"
    )
    assert result == expected

    # Verify that missing/None/empty fields are skipped gracefully
    row_with_nones = {
        "title": "Data Analyst",
        "company_profile": None,
        "description": "Analyze queries.",
        "requirements": "",
        "benefits": None
    }
    result_nones = build_text(row_with_nones)
    assert result_nones == "Data Analyst Analyze queries."


def test_train_and_test_are_disjoint_and_stratified():
    """Verify that:
    1. Both train.csv and test.csv exist.
    2. Exactly columns ['text', 'label'] are present.
    3. Train and test sets share ZERO text (completely disjoint).
    4. Fake percentages in both sets are balanced (~4.5% fraud rate).
    """
    train_path = Path("data/processed/train.csv")
    test_path = Path("data/processed/test.csv")

    assert train_path.exists(), f"Missing processed file: {train_path}"
    assert test_path.exists(), f"Missing processed file: {test_path}"

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Check columns
    assert list(train_df.columns) == ["text", "label"]
    assert list(test_df.columns) == ["text", "label"]

    # Check non-empty
    assert len(train_df) > 0
    assert len(test_df) > 0

    # Total row count check (12,599 + 3,150 = 15,749)
    assert len(train_df) + len(test_df) == 15749

    # CRITICAL CHECK: Train and test must share NO text
    train_texts = set(train_df["text"])
    test_texts = set(test_df["text"])
    overlap = train_texts.intersection(test_texts)
    assert len(overlap) == 0, f"Data leakage detected! {len(overlap)} overlapping texts between train and test."

    # Check stratification: fake proportion must be approximately equal (~4.5%)
    train_fake_rate = train_df["label"].mean() * 100
    test_fake_rate = test_df["label"].mean() * 100

    assert 4.0 <= train_fake_rate <= 5.0, f"Unexpected train fake rate: {train_fake_rate:.2f}%"
    assert 4.0 <= test_fake_rate <= 5.0, f"Unexpected test fake rate: {test_fake_rate:.2f}%"
    assert abs(train_fake_rate - test_fake_rate) < 0.2, (
        f"Train and test fake rates diverge: train={train_fake_rate:.2f}%, test={test_fake_rate:.2f}%"
    )
