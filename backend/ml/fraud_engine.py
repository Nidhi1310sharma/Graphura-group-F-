# ============================================================
# ml/fraud_engine.py - Main Fraud Detection Engine
# Combines NLP, domain, salary, and user report signals
# into a single scam probability score (0-100)
# ============================================================

from dataclasses import dataclass
from typing import List, Optional
from backend.ml.nlp_analyzer import NLPAnalyzer, NLPResult
from backend.ml.domain_check import DomainChecker, DomainResult
from backend.config import settings, get_risk_level


@dataclass
class FraudEngineResult:
    """Final result from the full fraud analysis pipeline."""
    scam_score: float               # 0-100 final score
    risk_level: str                 # LOW / MEDIUM / HIGH / CONFIRMED_SCAM
    risk_label: str                 # Human-readable label
    risk_color: str                 # CSS color name for UI

    keyword_score: float            # 0-100 from NLP
    domain_score: float             # 0-100 from domain check
    salary_score: float             # 0-100 from salary check
    report_score: float             # 0-100 from user reports

    suspicious_keywords: List[str]
    fraud_signals: List[dict]

    domain_age_days: Optional[int]
    ssl_valid: Optional[bool]
    domain_blacklisted: bool
    salary_anomaly: bool
    impersonation_detected: bool

    recommendation: str
    confidence: str                 # LOW / MEDIUM / HIGH (based on data available)


class FraudEngine:
    """
    Main orchestrator for fraud detection.
    
    Combines all sub-analyzers and applies the weighted scoring formula:
    
    Risk Score = (Keyword Score × 0.40)
               + (Domain Risk   × 0.30)
               + (Salary Anomaly × 0.20)
               + (User Reports   × 0.10)
    
    Usage:
        engine = FraudEngine()
        result = engine.analyze(
            description="Job description text",
            domain="suspicious-jobs.xyz",
            salary_text="₹80,000/month",
            user_report_count=3
        )
    """

    def __init__(self, blacklisted_domains: set = None, custom_keywords: dict = None):
        self.nlp = NLPAnalyzer(custom_keywords=custom_keywords)
        self.domain_checker = DomainChecker(blacklisted_domains=blacklisted_domains or set())

    def analyze(
        self,
        description: str = "",
        title: str = "",
        company_name: str = "",
        domain: str = "",
        salary_text: str = "",
        recruiter_email: str = "",
        user_report_count: int = 0,
    ) -> FraudEngineResult:
        """
        Run full fraud analysis pipeline.
        All parameters are optional but more data = better accuracy.
        """

        # Combine all text for NLP analysis
        full_text = " ".join(filter(None, [title, company_name, description, salary_text]))

        # --- Run NLP Analysis ---
        nlp_result: NLPResult = self.nlp.analyze(
            text=full_text,
            salary_text=salary_text,
            domain=domain
        )

        # --- Run Domain Analysis ---
        domain_result: DomainResult = self.domain_checker.check(domain)

        # --- Email Analysis ---
        email_score = self._analyze_email(recruiter_email)

        # --- Convert sub-scores to 0-100 scale ---

        # NLP keyword score (already 0-100)
        keyword_score = nlp_result.keyword_score

        # Domain score: invert trust_score (0=trusted → 0 risk, 1=untrusted → 100 risk)
        domain_score = (1.0 - domain_result.trust_score) * 100

        # Salary score: binary but weighted
        salary_score = 85.0 if nlp_result.salary_anomaly else 0.0

        # Report score: scale by report count (capped at 100)
        report_score = min(100.0, user_report_count * 25.0)

        # --- Weighted Final Score (formula from project brief) ---
        scam_score = (
            keyword_score * settings.KEYWORD_WEIGHT +
            domain_score  * settings.DOMAIN_WEIGHT  +
            salary_score  * settings.SALARY_WEIGHT  +
            report_score  * settings.REPORT_WEIGHT
        )

        # --- Override: guaranteed high score conditions ---
        if domain_result.blacklisted:
            scam_score = max(scam_score, 85.0)
        if domain_result.suspicious_pattern and nlp_result.keyword_score > 40:
            scam_score = max(scam_score, 75.0)
        if nlp_result.impersonation_detected:
            scam_score = max(scam_score, 80.0)

        # Add email signal
        scam_score = min(100.0, scam_score + email_score)
        scam_score = max(0.0, min(100.0, scam_score))

        # --- Collect all fraud signals ---
        all_signals = list(nlp_result.fraud_signals)

        if domain_result.blacklisted:
            all_signals.append({
                "signal_type": "domain",
                "description": "Domain is on the fraud blacklist",
                "severity": "critical",
                "score_contribution": 30
            })

        if not domain_result.ssl_valid and domain:
            all_signals.append({
                "signal_type": "domain",
                "description": "No SSL certificate — website is not secure (not HTTPS)",
                "severity": "medium",
                "score_contribution": 10
            })

        if domain_result.suspicious_pattern:
            all_signals.append({
                "signal_type": "domain",
                "description": "Domain name pattern suggests impersonation",
                "severity": "high",
                "score_contribution": 20
            })

        if email_score > 0:
            all_signals.append({
                "signal_type": "email",
                "description": "Recruiter using personal email (Gmail/Yahoo) — suspicious for company HR",
                "severity": "medium",
                "score_contribution": email_score
            })

        if user_report_count > 0:
            all_signals.append({
                "signal_type": "reports",
                "description": f"This posting/company has {user_report_count} user report(s)",
                "severity": "high" if user_report_count > 2 else "medium",
                "score_contribution": report_score
            })

        # --- Risk Level ---
        risk_level = get_risk_level(scam_score)
        risk_label, risk_color = self._get_risk_display(risk_level)

        # --- Confidence Level ---
        data_points = sum([
            bool(description), bool(domain), bool(salary_text),
            bool(recruiter_email), user_report_count > 0
        ])
        confidence = "HIGH" if data_points >= 3 else "MEDIUM" if data_points >= 2 else "LOW"

        # --- Recommendation ---
        recommendation = self._build_recommendation(scam_score, risk_level, all_signals)

        # --- Domain recommendation takes precedence ---
        if domain_result.blacklisted:
            recommendation = "⛔ DO NOT APPLY. Domain is confirmed fraudulent."

        return FraudEngineResult(
            scam_score=round(scam_score, 2),
            risk_level=risk_level,
            risk_label=risk_label,
            risk_color=risk_color,
            keyword_score=round(keyword_score, 2),
            domain_score=round(domain_score, 2),
            salary_score=round(salary_score, 2),
            report_score=round(report_score, 2),
            suspicious_keywords=nlp_result.suspicious_keywords,
            fraud_signals=all_signals,
            domain_age_days=domain_result.domain_age_days,
            ssl_valid=domain_result.ssl_valid,
            domain_blacklisted=domain_result.blacklisted,
            salary_anomaly=nlp_result.salary_anomaly,
            impersonation_detected=nlp_result.impersonation_detected,
            recommendation=recommendation,
            confidence=confidence
        )

    def _analyze_email(self, email: str) -> float:
        """
        Personal email domains for recruiter are suspicious.
        Returns extra score to add (0-15).
        """
        if not email:
            return 0.0
        email_lower = email.lower()
        personal_domains = ["@gmail.com", "@yahoo.com", "@hotmail.com",
                            "@rediffmail.com", "@outlook.com", "@yahoo.in"]
        for domain in personal_domains:
            if email_lower.endswith(domain):
                return 12.0     # Company HR should use company email
        return 0.0

    def _get_risk_display(self, risk_level: str):
        """Get display label and CSS color for risk level."""
        mapping = {
            "LOW":            ("Low Risk", "#10b981"),
            "MEDIUM":         ("Medium Risk", "#f59e0b"),
            "HIGH":           ("High Risk", "#ef4444"),
            "CONFIRMED_SCAM": ("Confirmed Scam", "#7c3aed"),
            "UNKNOWN":        ("Unknown", "#6b7280"),
        }
        return mapping.get(risk_level, ("Unknown", "#6b7280"))

    def _build_recommendation(self, score: float, risk_level: str, signals: list) -> str:
        """Build a human-friendly recommendation message."""
        if risk_level == "CONFIRMED_SCAM":
            return "🚫 DO NOT APPLY. Multiple strong fraud indicators detected. Report this posting."
        elif risk_level == "HIGH":
            return "❌ Very suspicious. Avoid applying. Verify the company through official channels before proceeding."
        elif risk_level == "MEDIUM":
            return "⚠️ Proceed with caution. Research the company thoroughly before sharing personal information."
        else:
            return "✅ Appears legitimate. Always verify company details before sharing sensitive information."
