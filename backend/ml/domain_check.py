# ============================================================
# ml/domain_check.py - Domain Reputation Checker
# Analyzes domain age, SSL, naming patterns, and blacklists
# ============================================================

import re
import socket
import ssl
import datetime
import httpx
from typing import Optional, Tuple
from dataclasses import dataclass


# Known legitimate job platform domains (trust by default)
TRUSTED_DOMAINS = {
    "linkedin.com", "internshala.com", "naukri.com", "indeed.com",
    "monster.com", "glassdoor.com", "shine.com", "timesjobs.com",
    "foundit.in", "freshersworld.com", "wisdomjobs.com", "apna.co",
    "unstop.com", "hirist.com", "iimjobs.com",
    # Company official domains
    "infosys.com", "tcs.com", "wipro.com", "hcltech.com",
    "accenture.com", "ibm.com", "microsoft.com", "google.com",
    "amazon.in", "amazon.com", "flipkart.com", "myntra.com",
}

# Suspicious TLD list (commonly used in scam domains)
SUSPICIOUS_TLDS = {
    ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".work", ".click", ".buzz", ".top", ".icu",
    ".club", ".online", ".site", ".website"
}

# Patterns that suggest domain impersonation
IMPERSONATION_PATTERNS = [
    r"google.+job", r"amazon.+job", r"microsoft.+job",
    r"infosys.+hiring", r"tcs.+recruit", r"wipro.+career",
    r"flipkart.+job", r"reliance.+job", r"hdfc.+recruit",
    r"sbi.+job", r"government.+job.+free", r"railway.+job.+free",
]

# Keywords in domain name that are suspicious
SUSPICIOUS_DOMAIN_KEYWORDS = [
    "free", "earn", "instant", "guaranteed", "unlimited",
    "daily-income", "work-home", "registration", "fee",
    "lucky", "selected", "hired", "job4u", "jobs4free"
]


@dataclass
class DomainResult:
    """Result of domain reputation analysis."""
    domain: str
    trust_score: float          # 0-1 (1 = fully trusted)
    risk_level: str             # LOW / MEDIUM / HIGH
    domain_age_days: Optional[int]
    ssl_valid: bool
    blacklisted: bool
    suspicious_pattern: bool
    is_trusted: bool            # known legitimate platform
    signals: list               # list of detected issues
    recommendation: str


class DomainChecker:
    """
    Analyzes a domain for fraud risk signals.
    
    Usage:
        checker = DomainChecker()
        result = checker.check("careers-google-jobs.xyz")
    """

    def __init__(self, blacklisted_domains: set = None):
        """
        blacklisted_domains: set of known bad domains from the database.
        """
        self.blacklisted_domains = blacklisted_domains or set()

    def check(self, domain: str) -> DomainResult:
        """Main check function. Returns DomainResult."""
        if not domain:
            return self._unknown_result("")

        domain = self._clean_domain(domain)
        signals = []
        trust_score = 0.7          # Start neutral-positive

        # --- 1. Check trusted list ---
        is_trusted = self._is_trusted(domain)
        if is_trusted:
            return DomainResult(
                domain=domain,
                trust_score=0.95,
                risk_level="LOW",
                domain_age_days=None,
                ssl_valid=True,
                blacklisted=False,
                suspicious_pattern=False,
                is_trusted=True,
                signals=[],
                recommendation="✅ This is a known legitimate platform."
            )

        # --- 2. Check blacklist ---
        blacklisted = self._is_blacklisted(domain)
        if blacklisted:
            trust_score = 0.0
            signals.append({
                "type": "blacklist",
                "message": "⛔ Domain is on the blacklist",
                "severity": "critical"
            })

        # --- 3. Check suspicious TLD ---
        suspicious_tld = self._check_suspicious_tld(domain)
        if suspicious_tld:
            trust_score -= 0.3
            signals.append({
                "type": "tld",
                "message": f"⚠️ Suspicious domain extension detected",
                "severity": "high"
            })

        # --- 4. Check impersonation patterns ---
        suspicious_pattern = self._check_impersonation(domain)
        if suspicious_pattern:
            trust_score -= 0.35
            signals.append({
                "type": "impersonation",
                "message": "🚨 Domain appears to impersonate a known brand",
                "severity": "critical"
            })

        # --- 5. Check suspicious keywords in domain ---
        suspicious_keyword = self._check_domain_keywords(domain)
        if suspicious_keyword:
            trust_score -= 0.2
            signals.append({
                "type": "keyword",
                "message": f"⚠️ Suspicious keyword '{suspicious_keyword}' in domain name",
                "severity": "medium"
            })

        # --- 6. Check SSL certificate ---
        ssl_valid = self._check_ssl(domain)
        if not ssl_valid:
            trust_score -= 0.15
            signals.append({
                "type": "ssl",
                "message": "🔒 No valid SSL certificate (not HTTPS)",
                "severity": "medium"
            })

        # --- 7. Check domain resolution (does it even exist?) ---
        resolves = self._resolves(domain)
        if not resolves:
            trust_score -= 0.1
            signals.append({
                "type": "dns",
                "message": "Domain does not resolve to any IP address",
                "severity": "low"
            })

        # Clamp trust_score
        trust_score = max(0.0, min(1.0, trust_score))

        # Determine risk level from trust score
        if trust_score >= 0.7:
            risk_level = "LOW"
        elif trust_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        recommendation = self._build_recommendation(trust_score, blacklisted, suspicious_pattern)

        return DomainResult(
            domain=domain,
            trust_score=trust_score,
            risk_level=risk_level,
            domain_age_days=None,       # Requires WHOIS API (see _check_whois)
            ssl_valid=ssl_valid,
            blacklisted=blacklisted,
            suspicious_pattern=suspicious_pattern,
            is_trusted=False,
            signals=signals,
            recommendation=recommendation
        )

    def _clean_domain(self, domain: str) -> str:
        """Extract clean domain from URL or domain string."""
        domain = domain.strip().lower()
        # Remove protocol
        domain = re.sub(r'^https?://', '', domain)
        # Remove path
        domain = domain.split('/')[0]
        # Remove port
        domain = domain.split(':')[0]
        # Remove 'www.'
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    def _is_trusted(self, domain: str) -> bool:
        """Check if domain is in the trusted list."""
        for trusted in TRUSTED_DOMAINS:
            if domain == trusted or domain.endswith('.' + trusted):
                return True
        return False

    def _is_blacklisted(self, domain: str) -> bool:
        """Check if domain is in the blacklist."""
        return domain in self.blacklisted_domains

    def _check_suspicious_tld(self, domain: str) -> bool:
        """Check if domain has a suspicious TLD."""
        for tld in SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                return True
        return False

    def _check_impersonation(self, domain: str) -> bool:
        """Check if domain impersonates a known brand."""
        for pattern in IMPERSONATION_PATTERNS:
            if re.search(pattern, domain, re.IGNORECASE):
                return True
        return False

    def _check_domain_keywords(self, domain: str) -> Optional[str]:
        """Check for suspicious keywords embedded in domain name."""
        for keyword in SUSPICIOUS_DOMAIN_KEYWORDS:
            if keyword in domain.replace("-", "").replace(".", ""):
                return keyword
        return None

    def _check_ssl(self, domain: str) -> bool:
        """
        Check if domain has a valid SSL certificate.
        Returns False if check fails (treat as no SSL).
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return bool(cert)
        except Exception:
            return False

    def _resolves(self, domain: str) -> bool:
        """Check if domain has a DNS record."""
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False

    def _build_recommendation(self, trust_score: float, blacklisted: bool, impersonation: bool) -> str:
        """Build a human-readable recommendation."""
        if blacklisted:
            return "⛔ DO NOT APPLY. This domain is blacklisted for scam activity."
        if impersonation:
            return "🚨 DO NOT APPLY. This domain is impersonating a legitimate company."
        if trust_score < 0.3:
            return "❌ High Risk. This domain shows multiple fraud signals. Avoid applying."
        if trust_score < 0.6:
            return "⚠️ Proceed with caution. Verify company through official channels."
        return "✅ Domain appears legitimate, but always verify independently."

    def _unknown_result(self, domain: str) -> DomainResult:
        return DomainResult(
            domain=domain,
            trust_score=0.5,
            risk_level="UNKNOWN",
            domain_age_days=None,
            ssl_valid=False,
            blacklisted=False,
            suspicious_pattern=False,
            is_trusted=False,
            signals=[],
            recommendation="No domain provided for analysis."
        )
