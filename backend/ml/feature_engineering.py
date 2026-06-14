import pandas as pd   
import numpy as np         
import re

#Feature engineering and rule-based detection engine for scam detection

#  STEP 3 : Load Fraud Dictionaries

# --- 3A. Monetary / Fee-Based Fraud Phrases ---
fraud_phrases = [
    "registration fee", "security deposit", "processing fee",
    "training fee", "joining fee", "application fee",
    "background check fee", "kit fee", "equipment fee",
    "investment required", "earn money fast", "make money online",
    "guaranteed income", "no experience needed", "work from home earn",
    "money transfer", "wire transfer", "pay upfront",
    "advance payment", "refundable deposit", "non-refundable",
    "pay to work", "data entry work", "typing work from home",
    "part time earn", "unlimited earnings", "get rich",
    "lottery winner", "inheritance", "100% profit"
]

# --- 3B. Urgency / Pressure Language ---
urgency_words = [
    "apply now", "limited seats", "hurry", "urgent hiring",
    "last chance", "immediate joining", "only today",
    "few slots left", "don't miss", "act now",
    "respond immediately", "fast response required",
    "deadline today", "interview today", "join today",
    "selected candidates only", "exclusive offer",
    "once in a lifetime", "don't wait", "instant selection"
]

# --- 3C. Risky / Anonymous Contact Channels ---
risky_contact_terms = [
    "telegram", "whatsapp", "gmail.com", "yahoo.com",
    "hotmail.com", "rediffmail.com", "outlook.com",
    "call now", "contact on whatsapp", "message on telegram",
    "wechat", "signal", "contact via sms",
    "no official website", "personal number",
    "direct contact", "private recruiter"
]

#  STEP 5 : Feature Engineering Generator

def generate_engineered_features(text: str) -> dict:
    """
    Compute keyword density and structural fraud features.

    Parameters
    ----------
    text : str
        Raw input text.

    Returns
    -------
    dict
        Dictionary of engineered feature names → values.
    """
    if not text or not isinstance(text, str):
        text = ""

    text_lower  = text.lower()
    text_length = len(text)

    # Count fraud phrase matches
    fraud_phrase_score = sum(
        1 for phrase in fraud_phrases if phrase in text_lower
    )

    # Count urgency word matches
    urgency_score = sum(
        1 for word in urgency_words if word in text_lower
    )

    # Count risky contact term matches
    contact_risk_score = sum(
        1 for term in risky_contact_terms if term in text_lower
    )

    # Total keyword hits
    keyword_count = fraud_phrase_score + urgency_score + contact_risk_score

    # ALL-CAPS word ratio — scams frequently shout at the reader
    all_words  = text.split()
    caps_words = [w for w in all_words if w.isupper() and len(w) > 1]
    all_caps_ratio = (
        round(len(caps_words) / len(all_words), 4)
        if all_words else 0
    )

    return {
        "keyword_count"      : keyword_count,
        "fraud_phrase_score" : fraud_phrase_score,
        "urgency_score"      : urgency_score,
        "contact_risk_score" : contact_risk_score,
        "all_caps_ratio"     : all_caps_ratio,
        "text_length"        : text_length,
    }

#  STEP 8 : Rule-Based Fraud Engine

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


def compute_rule_score(text: str) -> dict:
    """
    Compute a weighted rule-based fraud score.

    Parameters
    ----------
    text : str
        Raw input text.

    Returns
    -------
    dict
        rule_score (int, 0–100) and raw_rule_points (int, pre-cap).
    """
    if not text:
        return {"rule_score": 0, "raw_rule_points": 0}

    text_lower  = text.lower()
    raw_points  = 0

    # ── Signal 1 : Fraud phrases (+10 each) ──
    fp_hits = sum(1 for p in fraud_phrases if p in text_lower)
    raw_points += fp_hits * 10

    # ── Signal 2 : Urgency words (+6 each) ──
    uw_hits = sum(1 for w in urgency_words if w in text_lower)
    raw_points += uw_hits * 6

    # ── Signal 3 : Risky contact terms (+8 each) ──
    rc_hits = sum(1 for t in risky_contact_terms if t in text_lower)
    raw_points += rc_hits * 8

    # ── Signal 4 : Anonymous recruiter indicators (+15) ──
    if any(ind in text_lower for ind in _ANON_RECRUITER_INDICATORS):
        raw_points += 15

    # ── Signal 5 : Excessive ALL-CAPS ratio (+5) ──
    words_all  = text.split()
    caps_words = [w for w in words_all if w.isupper() and len(w) > 1]
    caps_ratio = len(caps_words) / len(words_all) if words_all else 0
    if caps_ratio > 0.15:
        raw_points += 5

    # ── Signal 6 : Very short posting — low information (<50 words, +10) ──
    word_count = len(re.findall(r'\b\w+\b', text))
    if word_count < 50:
        raw_points += 10

    # ── Signal 7 : Personal email address detected (+7) ──
    if _PERSONAL_EMAIL_PATTERN.search(text):
        raw_points += 7

    # Cap at 100
    rule_score = min(raw_points, 100)

    return {
        "rule_score"     : rule_score,
        "raw_rule_points": raw_points,
    }

