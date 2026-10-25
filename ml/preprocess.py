"""ml/preprocess.py
Text cleaning and preparation module for DAR Fake Job Detector.

Shared module used both during offline training (ml/build_dataset.py, ml/train.py)
and online inference in the Flask web application (app/predictor.py).

Implements the exact cleaning pipeline specified in:
- docs/03_TECHNICAL_DESIGN.md (section 5.3)
- docs/04_DEVELOPMENT_ROADMAP.md (prompt P4)

Cleaning steps in order:
1. Handle missing/None values (treat as empty string)
2. Convert to lowercase
3. Remove HTML tags and entities
4. Replace URLs with 'urltoken'
5. Replace email addresses with 'emailtoken'
6. Replace telephone numbers with 'phonetoken'
7. Keep letters, digits, and basic currency/percent symbols ($, €, £, ₹, %)
8. Collapse consecutive whitespace characters into a single space

Note: No stemming or lemmatisation is applied (per 03_TECHNICAL_DESIGN.md).
"""

import re
from typing import Any, Mapping

# Regular expressions compiled once for performance
RE_HTML_TAGS = re.compile(r"<[^>]+>")
RE_HTML_ENTITIES = re.compile(r"&(?:[a-zA-Z\d]+|#\d+|#x[a-fA-F\d]+);")
RE_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
RE_EMAIL = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
# Phone regex: matches domestic & international formats (e.g. +1-800-555-1234, (555) 123-4567, +91 9876543210)
RE_PHONE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
)
# Retain lowercase letters, digits, basic currency symbols, percent, and whitespace
RE_KEEP_CHARS = re.compile(r"[^a-z0-9$€£₹%\s]")
RE_SPACES = re.compile(r"\s+")

# Ordered list of text fields used for job posting representation
TEXT_FIELDS = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits"
]


def clean_text(text: Any) -> str:
    """Clean a raw job description string following the project specification.

    Args:
        text: Input string or value (handles None, float NaN, int, etc.).

    Returns:
        Cleaned, normalised text string.
    """
    if text is None:
        return ""

    # Convert to string and handle pandas NaN or other types
    text_str = str(text)
    if text_str.lower() == "nan":
        return ""

    if not text_str.strip():
        return ""

    # 1. Lowercase
    cleaned = text_str.lower()

    # 2. Remove HTML tags and HTML entities
    cleaned = RE_HTML_TAGS.sub(" ", cleaned)
    cleaned = RE_HTML_ENTITIES.sub(" ", cleaned)

    # 3. Replace URLs with urltoken
    cleaned = RE_URL.sub(" urltoken ", cleaned)

    # 4. Replace email addresses with emailtoken
    cleaned = RE_EMAIL.sub(" emailtoken ", cleaned)

    # 5. Replace telephone numbers with phonetoken
    cleaned = RE_PHONE.sub(" phonetoken ", cleaned)

    # 6. Keep letters, digits, and basic currency/percent symbols ($, €, £, ₹, %)
    cleaned = RE_KEEP_CHARS.sub(" ", cleaned)

    # 7. Collapse consecutive whitespace and strip edges
    cleaned = RE_SPACES.sub(" ", cleaned).strip()

    return cleaned


def build_text(row: Mapping[str, Any]) -> str:
    """Extract and join the 5 relevant text columns from a job posting row.

    Fields joined in order (per 03_TECHNICAL_DESIGN.md section 5.3):
    - title
    - company_profile
    - description
    - requirements
    - benefits

    Args:
        row: Dict-like mapping (dict or pandas Series) containing column keys.

    Returns:
        Single concatenated string separated by spaces.
    """
    parts = []
    for field in TEXT_FIELDS:
        # Retrieve field if present, otherwise default to empty string
        val = row.get(field, "") if hasattr(row, "get") else (row[field] if field in row else "")
        if val is not None:
            val_str = str(val).strip()
            if val_str and val_str.lower() != "nan":
                parts.append(val_str)

    # Join non-empty parts with a single space
    return " ".join(parts)
