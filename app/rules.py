"""app/rules.py
Rule-based warning flags for DAR Fake Job Detector.

Implements the 8 warning flags defined in docs/03_TECHNICAL_DESIGN.md (section 5.8)
and docs/02_UI_UX_SPEC.md (section 8.1).

Critical Project Rule:
Warning flags are explanatory warnings only — flags NEVER alter the ML model's verdict.
"""

import re
from typing import Any

# 1. Asks for money, fee or deposit
RE_MONEY_FEE = re.compile(
    r"\b(?:"
    r"registration\s*fee|security\s*deposit|processing\s*fee|application\s*fee|"
    r"training\s*fee|refundable\s*deposit|pay\s*(?:money|amount|cash|fee|deposit)|"
    r"deposit\s*(?:required|needed|amount)|send\s*money|transfer\s*fee|"
    r"courier\s*charges?|equipment\s*deposit|laptop\s*deposit"
    r")\b",
    re.IGNORECASE
)

# 2. Asks for bank, Aadhaar, PAN or OTP
RE_SENSITIVE_DATA = re.compile(
    r"\b(?:"
    r"aadhaar|pan\s*card|bank\s*account(?:\s*number)?|ifsc|otp|one\s*time\s*password|"
    r"credit\s*card|debit\s*card|cvv|pin\s*number|net\s*banking|"
    r"share\s*your\s*otp|bank\s*details|passport\s*copy"
    r")\b",
    re.IGNORECASE
)

# 3. Contact only through WhatsApp or Telegram
RE_SOCIAL_MESSAGING = re.compile(
    r"\b(?:"
    r"whatsapp|telegram|wa\.me|t\.me|"
    r"(?:contact|message|dm|text|ping)\s*(?:us|me|hr)?\s*on\s*(?:whatsapp|telegram)|"
    r"whatsapp\s*only|telegram\s*only"
    r")\b",
    re.IGNORECASE
)

# 4. Free email domain as contact
RE_FREE_EMAIL = re.compile(
    r"\b[a-zA-Z0-9._%+-]+@(?:gmail|yahoo|hotmail|outlook|rediffmail|yopmail|icloud|live)\.com\b",
    re.IGNORECASE
)

# 5. "No interview" or "instant joining"
RE_NO_INTERVIEW = re.compile(
    r"\b(?:"
    r"no\s*interview|without\s*interview|instant\s*joining|immediate\s*joining|"
    r"direct\s*(?:selection|joining|hiring|placement)|spot\s*offer|"
    r"guaranteed\s*selection|100%\s*selection"
    r")\b",
    re.IGNORECASE
)

# 6. Unrealistic pay words
RE_UNREALISTIC_PAY = re.compile(
    r"\b(?:"
    r"earn\s*(?:up\s*to\s*)?(?:[$€£₹]\s*)?\d{3,}\s*(?:daily|per\s*day|hourly|per\s*hour)|"
    r"daily\s*(?:income|payout|payment|earnings)|earn\s*(?:easy\s*money|quick\s*cash)|"
    r"make\s*money\s*fast|guaranteed\s*daily\s*income|earn\s*from\s*home\s*daily|"
    r"unlimited\s*earning\s*potential|simple\s*copy\s*paste\s*work|"
    r"earn\s*lakhs|daily\s*salary"
    r")\b",
    re.IGNORECASE
)

# 7. Urgency words
RE_URGENCY = re.compile(
    r"\b(?:"
    r"apply\s*immediately|hurry\s*up|limited\s*(?:seats|slots|openings|vacancies)|"
    r"only\s*\d+\s*(?:seats|slots|vacancies)\s*left|offer\s*expires\s*today|"
    r"urgent\s*requirement|rush\s*your\s*(?:resume|cv)|act\s*fast|last\s*chance|"
    r"apply\s*today\s*only"
    r")\b",
    re.IGNORECASE
)

# 8. No company name or details
# Check for vague generic designations with no identifiable corporate structure
RE_VAGUE_COMPANY = re.compile(
    r"\b(?:"
    r"leading\s*mnc|reputed\s*company|confidential\s*company|top\s*client|"
    r"undisclosed\s*client|anonymous\s*employer|genuine\s*company"
    r")\b",
    re.IGNORECASE
)

RE_GENUINE_COMPANY_INDICATORS = re.compile(
    r"\b(?:"
    r"ltd|limited|pvt|private\s*limited|inc|incorporated|corp|corporation|"
    r"technologies|solutions|services|group|llc|gmbh|co\."
    r")\b",
    re.IGNORECASE
)


RULES_DEFINITIONS = [
    {
        "code": "money_fee",
        "message": "Asks for money, registration fee, or security deposit.",
        "pattern": RE_MONEY_FEE,
    },
    {
        "code": "sensitive_data",
        "message": "Asks for sensitive personal details (bank account, Aadhaar, PAN card, or OTP).",
        "pattern": RE_SENSITIVE_DATA,
    },
    {
        "code": "social_messaging",
        "message": "Contact only through WhatsApp or Telegram rather than official email/portal.",
        "pattern": RE_SOCIAL_MESSAGING,
    },
    {
        "code": "free_email",
        "message": "Uses a free public email address (Gmail, Yahoo, Outlook) as company contact.",
        "pattern": RE_FREE_EMAIL,
    },
    {
        "code": "no_interview",
        "message": "Offers 'no interview', 'direct selection', or 'instant joining'.",
        "pattern": RE_NO_INTERVIEW,
    },
    {
        "code": "unrealistic_pay",
        "message": "Promises unrealistic pay or daily income for minimal work.",
        "pattern": RE_UNREALISTIC_PAY,
    },
    {
        "code": "urgency",
        "message": "Uses high-pressure urgency words (e.g. 'limited slots', 'hurry', 'apply immediately').",
        "pattern": RE_URGENCY,
    },
]


def check_rules(text: str) -> list[dict[str, Any]]:
    """Scan job ad text against all 8 rule-based warning patterns.

    Args:
        text: Raw or clean job description text.

    Returns:
        List of triggered warning flag dictionaries:
        [{"code": str, "message": str, "matches": list[str]}]
    """
    if not text or not str(text).strip():
        return []

    text_str = str(text)
    flags = []

    # 1-7. Standard regex patterns
    for rule in RULES_DEFINITIONS:
        pattern: re.Pattern = rule["pattern"]
        matches = pattern.findall(text_str)
        if matches:
            # Flatten or format matches cleanly
            unique_matches = sorted(list({m.strip() for m in matches if isinstance(m, str) and m.strip()}))
            flags.append({
                "code": rule["code"],
                "message": rule["message"],
                "matches": unique_matches
            })

    # 8. Check for lack of identifiable company name / details
    # Triggers if explicit vague placeholder phrases are present, or text has substantial length
    # but lacks any company structure or website mentions
    has_vague = bool(RE_VAGUE_COMPANY.search(text_str))
    has_indicators = bool(RE_GENUINE_COMPANY_INDICATORS.search(text_str))

    if has_vague or (len(text_str.split()) >= 50 and not has_indicators):
        vague_matches = RE_VAGUE_COMPANY.findall(text_str)
        flags.append({
            "code": "no_company_info",
            "message": "No verifiable company name, official website, or registered entity details provided.",
            "matches": sorted(list({m.strip() for m in vague_matches})) if vague_matches else ["no company details"]
        })

    return flags
