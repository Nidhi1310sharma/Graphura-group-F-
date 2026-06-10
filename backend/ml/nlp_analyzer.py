# ============================================================
# ml/nlp_analyzer.py - NLP-Based Fraud Text Analysis
# Uses keyword matching, TF-IDF, and pattern detection
# to score job descriptions for fraud signals
# ============================================================

import re
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass

# ---------------------------------------------------------------
# Built-in fraud keyword dictionary
# (Also loaded from database at runtime - this is the fallback)
# ---------------------------------------------------------------
FRAUD_KEYWORDS: Dict[str, float] = {
    # Fee-related (highest risk)
    "registration fee": 0.95,
    "training fee": 0.93,
    "security deposit": 0.90,
    "refundable deposit": 0.88,
    "pay to work": 0.97,
    "joining fee": 0.92,
    "application fee": 0.85,
    "kit fee": 0.91,
    "laptop deposit": 0.89,
    "background check fee": 0.87,
    "id card fee": 0.91,
    "uniform fee": 0.89,

    # Urgency / fake scarcity
    "limited seats": 0.69,
    "apply immediately": 0.65,
    "urgent hiring": 0.60,
    "last 2 seats": 0.75,
    "offer expires today": 0.78,
    "immediate joining": 0.82,
    "instant joining": 0.80,
    "joining in 24 hours": 0.76,
    "limited time offer": 0.70,
    "hurry up": 0.65,

    # Unrealistic offers
    "earn daily": 0.77,
    "work from home unlimited": 0.85,
    "no experience needed": 0.55,
    "no skills required": 0.65,
    "part time 1 hour": 0.72,
    "work 2 hours daily": 0.70,
    "guaranteed income": 0.80,
    "100% placement guarantee": 0.75,
    "earn while you sleep": 0.88,
    "passive income": 0.70,
    "be your own boss": 0.65,
    "unlimited earning": 0.78,

    # Phishing / personal data
    "aadhar card required": 0.85,
    "pan card required": 0.80,
    "bank account details": 0.92,
    "send your photo": 0.70,
    "send your documents": 0.72,
    "otp verification": 0.68,

    # Communication red flags
    "whatsapp hr": 0.91,
    "contact on whatsapp": 0.85,
    "telegram only": 0.83,
    "no interview": 0.75,
    "direct selection": 0.72,
    "selected without interview": 0.80,

    # Suspicious email domains in text
    "@gmail.com hr": 0.78,
    "@yahoo.com hr": 0.75,
    "@rediffmail.com": 0.80,
    "@hotmail.com recruiter": 0.72,
}

# Suspicious domain TLD patterns
SUSPICIOUS_TLDS = [".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".work", ".click", ".buzz"]

# Patterns that impersonate legitimate companies
IMPERSONATION_PATTERNS = [
    r"google[-.]?(job|hiring|career|intern|recruit)",
    r"amazon[-.]?(job|hiring|career|intern|recruit)",
    r"microsoft[-.]?(job|hiring|career|intern|recruit)",
    r"infosys[-.]?(job|hiring|career|intern|recruit)",
    r"tcs[-.]?(job|hiring|career|intern|recruit)",
    r"wipro[-.]?(job|hiring|career|intern|recruit)",
    r"flipkart[-.]?(job|hiring|career|intern|recruit)",
]

# Salary regex patterns (Indian rupee format)
SALARY_PATTERNS = [
    r"₹?\s*(\d+)[,.]?(\d*)\s*(?:k|thousand|lakh|l)?\s*(?:per\s*)?(?:month|/month|/mo|pm|monthly)",
    r"rs\.?\s*(\d+)[,.]?(\d*)\s*(?:k|thousand|lakh)?\s*(?:per\s*)?(?:month|/month|pm)",
    r"(\d+)[,.]?(\d*)\s*(?:k|thousand|lakh)?\s*(?:rupees|inr)\s*(?:per\s*)?(?:month|/month|pm)",
]


@dataclass
class NLPResult:
    """Result from NLP analysis of job text."""
    keyword_score: float            # 0-100
    suspicious_keywords: List[str]
    matched_patterns: List[str]
    salary_anomaly: bool
    detected_salary: float          # in INR per month
    grammar_score: float            # 0-100 (higher = better grammar = less suspicious)
    impersonation_detected: bool
    fraud_signals: List[dict]


class NLPAnalyzer:
    """
    Analyzes job posting text for fraud indicators.
    
    Usage:
        analyzer = NLPAnalyzer()
        result = analyzer.analyze("Job description text here", salary_text="₹80,000/month")
    """

    def __init__(self, custom_keywords: Dict[str, float] = None):
        """
        Initialize with built-in keywords.
        custom_keywords: additional keywords from the database.
        """
        self.keywords = FRAUD_KEYWORDS.copy()
        if custom_keywords:
            self.keywords.update(custom_keywords)

    def analyze(self, text: str, salary_text: str = None, domain: str = None) -> NLPResult:
        """Main analysis function - runs all checks and returns NLPResult."""
        if not text:
            return self._empty_result()

        text_lower = text.lower().strip()
        signals = []
        matched_keywords = []

        # --- 1. Keyword Scanning ---
        keyword_score, found_keywords = self._scan_keywords(text_lower)
        matched_keywords.extend(found_keywords)

        for kw in found_keywords:
            weight = self.keywords.get(kw, 0.5)
            signals.append({
                "signal_type": "keyword",
                "description": f"Suspicious phrase detected: '{kw}'",
                "severity": "high" if weight > 0.80 else "medium" if weight > 0.60 else "low",
                "score_contribution": weight * 15
            })

        # --- 2. Salary Anomaly Detection ---
        salary_anomaly, detected_salary = self._check_salary_anomaly(
            salary_text or text_lower
        )
        if salary_anomaly:
            signals.append({
                "signal_type": "salary",
                "description": f"Unrealistic salary offer detected: ₹{detected_salary:,.0f}/month",
                "severity": "high",
                "score_contribution": 20
            })

        # --- 3. Impersonation Detection ---
        impersonation = self._detect_impersonation(text_lower, domain or "")
        if impersonation:
            signals.append({
                "signal_type": "impersonation",
                "description": "Possible brand impersonation detected (fake Google/Amazon/TCS etc.)",
                "severity": "high",
                "score_contribution": 25
            })

        # --- 4. Grammar Quality Check ---
        grammar_score = self._analyze_grammar(text)
        if grammar_score < 40:
            signals.append({
                "signal_type": "grammar",
                "description": "Poor grammar detected - often a sign of fraudulent postings",
                "severity": "medium",
                "score_contribution": 10
            })

        # --- 5. Suspicious Domain Pattern in Text ---
        for tld in SUSPICIOUS_TLDS:
            if tld in text_lower:
                signals.append({
                    "signal_type": "domain",
                    "description": f"Suspicious domain extension '{tld}' found in posting",
                    "severity": "medium",
                    "score_contribution": 12
                })
                break

        return NLPResult(
            keyword_score=min(keyword_score, 100),
            suspicious_keywords=matched_keywords,
            matched_patterns=[s["description"] for s in signals],
            salary_anomaly=salary_anomaly,
            detected_salary=detected_salary,
            grammar_score=grammar_score,
            impersonation_detected=impersonation,
            fraud_signals=signals
        )

    def _scan_keywords(self, text: str) -> Tuple[float, List[str]]:
        """Scan text for fraud keywords. Returns (score 0-100, matched keywords)."""
        found = []
        total_weight = 0.0

        for keyword, weight in self.keywords.items():
            if keyword in text:
                found.append(keyword)
                total_weight += weight

        # Use log scale to prevent score saturation from many low-weight keywords
        if total_weight > 0:
            score = min(100, total_weight * 40 * (1 + math.log(1 + len(found) * 0.1)))
        else:
            score = 0.0

        return score, found

    def _check_salary_anomaly(self, text: str) -> Tuple[bool, float]:
        """
        Detect unrealistically high salary offers.
        Returns (is_anomaly, salary_amount)
        Thresholds for Indian market:
        - Internship > ₹40,000/month = suspicious
        - Fresher job > ₹150,000/month = suspicious
        """
        for pattern in SALARY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        amount_str = "".join(match).replace(",", "")
                    else:
                        amount_str = str(match).replace(",", "")

                    amount = float(amount_str)

                    # Handle 'k' suffix (e.g., "50k" = 50,000)
                    if "k" in text[text.find(amount_str):text.find(amount_str)+10].lower():
                        amount *= 1000
                    # Handle lakh
                    if "lakh" in text[text.find(amount_str):text.find(amount_str)+15].lower():
                        amount *= 100000

                    # Flag if internship/freshers salary > ₹40,000/month
                    if amount > 40000 and ("intern" in text or "fresher" in text or "no experience" in text):
                        return True, amount
                    # Flag if any job > ₹200,000/month for unspecified role
                    if amount > 200000:
                        return True, amount

                except (ValueError, IndexError):
                    continue

        return False, 0.0

    def _detect_impersonation(self, text: str, domain: str) -> bool:
        """Check if the posting impersonates a known company brand."""
        combined = (text + " " + domain).lower()
        for pattern in IMPERSONATION_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
        return False

    def _analyze_grammar(self, text: str) -> float:
        """
        Simple grammar quality heuristic.
        Returns score 0-100 (higher = better grammar).
        Checks: ALL CAPS usage, repeated punctuation, excessive exclamation marks.
        """
        if not text or len(text) < 20:
            return 50.0

        score = 100.0

        # Penalize ALL CAPS words (scammers often use excessive caps)
        words = text.split()
        caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / max(len(words), 1)
        score -= caps_ratio * 40

        # Penalize excessive exclamation marks
        exclamation_count = text.count("!")
        score -= min(exclamation_count * 5, 30)

        # Penalize repeated punctuation like "!!!" or "..."
        if re.search(r"[!?]{2,}", text):
            score -= 15

        # Penalize very short descriptions (less than 100 chars - too vague)
        if len(text) < 100:
            score -= 20

        return max(0.0, min(100.0, score))

    def _empty_result(self) -> NLPResult:
        """Return empty result when no text provided."""
        return NLPResult(
            keyword_score=0,
            suspicious_keywords=[],
            matched_patterns=[],
            salary_anomaly=False,
            detected_salary=0,
            grammar_score=50,
            impersonation_detected=False,
            fraud_signals=[]
        )
