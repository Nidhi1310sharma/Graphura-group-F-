import re
#  STEP 12 : Explainability Layer

# Pattern detectors
_PHONE_PATTERN = re.compile(r'(\+?\d[\d\s\-]{8,}\d)')
_PERSONAL_EMAIL_PATTERN = re.compile(
    r'\b[\w.+-]+@(gmail|yahoo|hotmail|rediffmail|outlook|ymail)\.com\b',
    re.IGNORECASE
)
_NO_WEBSITE_INDICATORS = [
    "no website", "visit us at", "contact directly",
    "no official site", "personal recruiter"
]
_ANON_RECRUITER_INDICATORS = [
    "company name not disclosed", "client of ours",
    "undisclosed company", "anonymous client",
    "confidential company", "our client"
]

# Specific phrase → human label mapping for top fraud phrases
_FRAUD_PHRASE_LABELS = {
    "registration fee"   : "Registration fee mentioned",
    "security deposit"   : "Security deposit required",
    "processing fee"     : "Processing fee detected",
    "training fee"       : "Training fee required",
    "joining fee"        : "Joining fee mentioned",
    "investment required": "Investment required from applicant",
    "earn money fast"    : "'Earn money fast' language detected",
    "guaranteed income"  : "Guaranteed income promise detected",
    "pay upfront"        : "Upfront payment requested",
    "advance payment"    : "Advance payment mentioned",
    "pay to work"        : "Pay-to-work scheme detected",
    "get rich"           : "Get-rich-quick language detected",
    "100% profit"        : "Unrealistic profit guarantee found",
    "wire transfer"      : "Wire transfer payment requested",
    "data entry work"    : "Data entry scam pattern detected",
    "typing work from home": "Typing-job scam pattern detected",
}

_CONTACT_LABELS = {
    "telegram"           : "Telegram contact used (no official channel)",
    "whatsapp"           : "WhatsApp communication detected",
    "gmail.com"          : "Personal Gmail address used for recruitment",
    "yahoo.com"          : "Personal Yahoo address used for recruitment",
    "hotmail.com"        : "Personal Hotmail address used for recruitment",
    "call now"           : "'Call now' pressure tactic detected",
    "wechat"             : "WeChat contact used (no official channel)",
}

_URGENCY_LABELS = {
    "apply now"          : "High-pressure 'Apply Now' language",
    "urgent hiring"      : "Urgent hiring claim detected",
    "limited seats"      : "False scarcity tactic: 'Limited seats'",
    "immediate joining"  : "Immediate joining demanded",
    "instant selection"  : "Instant selection promise detected",
    "deadline today"     : "Same-day deadline pressure",
}


def generate_fraud_reasons(text: str, risk_score: float) -> list:
    """
    Build a human-readable list of fraud indicators found in the text.

    Parameters
    ----------
    text       : str    Raw input text.
    risk_score : float  Final hybrid risk score.

    Returns
    -------
    list of str
        Explanation strings for the frontend.
    """
    reasons    = []
    text_lower = text.lower()

    # ── Check fraud phrases ──
    for phrase, label in _FRAUD_PHRASE_LABELS.items():
        if phrase in text_lower:
            reasons.append(label)

    # ── Check risky contact terms ──
    for term, label in _CONTACT_LABELS.items():
        if term in text_lower:
            reasons.append(label)

    # ── Check urgency words ──
    for word, label in _URGENCY_LABELS.items():
        if word in text_lower:
            reasons.append(label)

    # ── Anonymous recruiter ──
    if any(ind in text_lower for ind in _ANON_RECRUITER_INDICATORS):
        reasons.append("Anonymous/undisclosed recruiter")

    # ── Short posting ──
    if len(re.findall(r'\b\w+\b', text)) < 50:
        reasons.append("Very short job posting — low information content")

    # ── Personal email ──
    if _PERSONAL_EMAIL_PATTERN.search(text):
        reasons.append("Personal email address used for hiring")

    # ── ML-driven catch-all if model flagged it but no specific reason ──
    if risk_score >= 70 and not reasons:
        reasons.append(
            "ML model detected statistical patterns consistent with scam postings"
        )

    # ── If genuinely clean ──
    if not reasons:
        reasons.append("No significant fraud indicators detected")

    return reasons
