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

# Domain age thresholds (in days) used for trust scoring
_AGE_VERY_NEW_DAYS  = 90    # < 90 days  → significant trust penalty
_AGE_NEW_DAYS       = 365   # < 1 year   → mild trust penalty
_AGE_ESTABLISHED_DAYS = 730 # > 2 years  → slight trust bonus


@dataclass
class SSLInfo:
    """Detailed SSL/TLS certificate information."""
    valid: bool                         # Basic validity (matches existing ssl_valid field)
    issuer: Optional[str] = None        # e.g. "Let's Encrypt Authority X3"
    expiry_date: Optional[datetime.datetime] = None
    days_until_expiry: Optional[int] = None
    tls_version: Optional[str] = None  # e.g. "TLSv1.3"


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
    # --- New fields added below; all default to None so existing
    #     code that constructs DomainResult without them still works. ---
    registrar: Optional[str] = None          # Registrar name from WHOIS / RDAP
    ssl_info: Optional[SSLInfo] = None       # Detailed SSL certificate data


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
            # Enrich the trusted result with live SSL and WHOIS/RDAP data
            # so callers get real certificate and age info even for known platforms.
            # Trust score (0.95) and risk level (LOW) are kept unchanged.
            trusted_ssl_info = self._check_ssl(domain)
            trusted_age_days, trusted_registrar = self._check_whois_with_rdap_fallback(domain)
            return DomainResult(
                domain=domain,
                trust_score=0.95,
                risk_level="LOW",
                domain_age_days=trusted_age_days,
                ssl_valid=trusted_ssl_info.valid,
                blacklisted=False,
                suspicious_pattern=False,
                is_trusted=True,
                signals=[],
                recommendation="✅ This is a known legitimate platform.",
                registrar=trusted_registrar,
                ssl_info=trusted_ssl_info,
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

        # --- 6. Check SSL certificate (now returns rich SSLInfo) ---
        ssl_info = self._check_ssl(domain)
        ssl_valid = ssl_info.valid
        if not ssl_valid:
            trust_score -= 0.15
            signals.append({
                "type": "ssl",
                "message": "🔒 No valid SSL certificate (not HTTPS)",
                "severity": "medium"
            })
        elif ssl_info.days_until_expiry is not None and ssl_info.days_until_expiry < 14:
            # SSL exists but is about to expire — mild warning
            trust_score -= 0.05
            signals.append({
                "type": "ssl_expiry",
                "message": f"⚠️ SSL certificate expires in {ssl_info.days_until_expiry} day(s)",
                "severity": "low"
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

        # --- 8. WHOIS / RDAP: domain age + registrar (NEW) ---
        domain_age_days, registrar = self._check_whois_with_rdap_fallback(domain)

        if domain_age_days is not None:
            if domain_age_days < _AGE_VERY_NEW_DAYS:
                # Very new domain — significant red flag
                trust_score -= 0.25
                signals.append({
                    "type": "domain_age",
                    "message": f"🆕 Domain is very new ({domain_age_days} days old) — high fraud risk",
                    "severity": "high"
                })
            elif domain_age_days < _AGE_NEW_DAYS:
                # Less than a year old — mild concern
                trust_score -= 0.1
                signals.append({
                    "type": "domain_age",
                    "message": f"⚠️ Domain is relatively new ({domain_age_days} days old)",
                    "severity": "low"
                })
            elif domain_age_days >= _AGE_ESTABLISHED_DAYS:
                # Well-established domain — small positive signal
                trust_score = min(1.0, trust_score + 0.05)

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
            domain_age_days=domain_age_days,
            ssl_valid=ssl_valid,
            blacklisted=blacklisted,
            suspicious_pattern=suspicious_pattern,
            is_trusted=False,
            signals=signals,
            recommendation=recommendation,
            registrar=registrar,
            ssl_info=ssl_info,
        )

    # ------------------------------------------------------------------
    # Existing helpers (unchanged)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # SSL inspection — IMPROVED (requirement 5)
    # ------------------------------------------------------------------

    def _check_ssl(self, domain: str) -> SSLInfo:
        """
        Check SSL certificate validity and extract additional detail:
            - issuer organisation
            - expiry date + days until expiry
            - TLS protocol version

        Returns an SSLInfo dataclass. ssl_valid=False is returned on any
        error so the rest of the scoring flow is unaffected.
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    if not cert:
                        return SSLInfo(valid=False)

                    # --- Issuer ---
                    issuer = None
                    issuer_dict = dict(x[0] for x in cert.get('issuer', []))
                    issuer = issuer_dict.get('organizationName') or issuer_dict.get('commonName')

                    # --- Expiry date ---
                    expiry_date = None
                    days_until_expiry = None
                    not_after = cert.get('notAfter')
                    if not_after:
                        try:
                            expiry_date = datetime.datetime.strptime(
                                not_after, "%b %d %H:%M:%S %Y %Z"
                            )
                            days_until_expiry = (expiry_date - datetime.datetime.utcnow()).days
                        except ValueError:
                            pass  # Non-standard date format — skip gracefully

                    # --- TLS version ---
                    # ssock.version() returns a string like "TLSv1.3" or None
                    tls_version = ssock.version() if hasattr(ssock, 'version') else None

                    return SSLInfo(
                        valid=True,
                        issuer=issuer,
                        expiry_date=expiry_date,
                        days_until_expiry=days_until_expiry,
                        tls_version=tls_version,
                    )

        except Exception:
            return SSLInfo(valid=False)

    # ------------------------------------------------------------------
    # WHOIS with RDAP fallback — NEW (requirements 1, 2, 3, 4)
    # ------------------------------------------------------------------

    def _check_whois_with_rdap_fallback(
        self, domain: str
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Return (domain_age_days, registrar_name).

        Strategy
        --------
        1. Try python-whois (primary).  If it returns a usable creation_date
           and registrar, return immediately.
        2. If WHOIS fails or is missing either field, try RDAP as a fallback.
        3. If both fail, return (None, None) — the caller handles None gracefully.

        The function never raises; all exceptions are caught internally so that
        a WHOIS / RDAP failure can never break the main check() flow.
        """
        age_days, registrar = self._whois_lookup(domain)

        # Fall back to RDAP only if WHOIS could not supply both fields
        if age_days is None or registrar is None:
            rdap_age, rdap_registrar = self._rdap_lookup(domain)
            age_days  = age_days  if age_days  is not None else rdap_age
            registrar = registrar if registrar is not None else rdap_registrar

        return age_days, registrar

    def _whois_lookup(self, domain: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Primary WHOIS lookup via the `python-whois` library.

        Handles the many different shapes that `creation_date` can take:
            - datetime object
            - list / tuple of datetimes (use the earliest)
            - string (attempt to parse)
            - None / missing key

        Returns (domain_age_days, registrar) — either element may be None.
        """
        try:
            import whois  # python-whois; optional dependency
            w = whois.whois(domain)
        except Exception:
            # Library not installed, network error, or parsing error
            return None, None

        # --- creation_date: normalise to a single datetime ---
        creation_date = None
        raw_date = getattr(w, 'creation_date', None)

        if raw_date is None:
            pass  # nothing to work with
        elif isinstance(raw_date, (list, tuple)):
            # Some TLDs return multiple dates; pick the earliest valid one
            datetimes = [
                d for d in raw_date
                if isinstance(d, datetime.datetime)
            ]
            if datetimes:
                creation_date = min(datetimes)
            else:
                # Items might be strings — try parsing the first one
                for item in raw_date:
                    parsed = self._try_parse_date(item)
                    if parsed:
                        creation_date = parsed
                        break
        elif isinstance(raw_date, datetime.datetime):
            creation_date = raw_date
        elif isinstance(raw_date, str):
            creation_date = self._try_parse_date(raw_date)

        # --- domain_age_days ---
        age_days = None
        if creation_date:
            try:
                delta = datetime.datetime.utcnow() - creation_date.replace(tzinfo=None)
                age_days = max(0, delta.days)
            except Exception:
                pass  # unexpected datetime shape — skip

        # --- registrar ---
        registrar = None
        raw_reg = getattr(w, 'registrar', None)
        if isinstance(raw_reg, (list, tuple)):
            raw_reg = raw_reg[0] if raw_reg else None
        if isinstance(raw_reg, str) and raw_reg.strip():
            registrar = raw_reg.strip()

        return age_days, registrar

    def _try_parse_date(self, value) -> Optional[datetime.datetime]:
        """
        Attempt to parse a date-string into a datetime, trying several
        common formats used by WHOIS registries.  Returns None on failure.
        """
        if not isinstance(value, str):
            return None
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",     # ISO 8601 UTC
            "%Y-%m-%dT%H:%M:%S",       # ISO 8601 without Z
            "%Y-%m-%d %H:%M:%S",       # Space-separated
            "%Y-%m-%d",                # Date only
            "%d-%b-%Y",                # e.g. "15-Jan-2020"
            "%d/%m/%Y",                # e.g. "15/01/2020"
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None

    def _rdap_lookup(self, domain: str) -> Tuple[Optional[int], Optional[str]]:
        """
        RDAP fallback (requirement 2).

        Tries multiple RDAP endpoints in order so that a single server
        being down or returning bad data never causes a failure:

            1. IANA bootstrap endpoint  (follows 301/302 to the TLD server)
            2. RDAP.org universal proxy (covers most gTLDs and ccTLDs)
            3. Cloudflare RDAP proxy    (additional fallback)

        For each endpoint the function:
            - Uses a short timeout so a slow server does not stall the check.
            - Catches every possible exception independently.
            - Returns (None, None) for any field it cannot parse rather than
              raising, so the caller's logic is never disrupted.

        Returns (domain_age_days, registrar_name) — either may be None.
        """
        endpoints = [
            f"https://rdap.iana.org/domain/{domain}",
            f"https://rdap.org/domain/{domain}",
            f"https://www.rdap.cloud/domain/{domain}",
        ]

        for url in endpoints:
            try:
                response = httpx.get(url, timeout=8, follow_redirects=True)
                if response.status_code != 200:
                    continue  # Try the next endpoint

                # Guard against non-JSON responses (e.g. HTML error pages)
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type and not response.text.lstrip().startswith("{"):
                    continue

                try:
                    data = response.json()
                except Exception:
                    continue  # Unparseable body — try next endpoint

                # --- creation date from "events" array ---
                age_days = None
                for event in data.get('events', []):
                    if not isinstance(event, dict):
                        continue
                    if event.get('eventAction') == 'registration':
                        raw = event.get('eventDate', '')
                        parsed = self._try_parse_date(raw)
                        if parsed:
                            try:
                                delta = datetime.datetime.utcnow() - parsed.replace(tzinfo=None)
                                age_days = max(0, delta.days)
                            except Exception:
                                pass  # Unexpected datetime shape — skip
                        break

                # --- registrar from "entities" with role "registrar" ---
                registrar = None
                for entity in data.get('entities', []):
                    if not isinstance(entity, dict):
                        continue
                    roles = entity.get('roles', [])
                    if 'registrar' not in roles:
                        continue

                    # Try plain name fields first (fastest path)
                    name = entity.get('fn') or entity.get('name')

                    # Fall back to parsing the vCard array
                    if not name:
                        vcard = entity.get('vcardArray', [])
                        # vCard structure: ["vcard", [[field, params, type, value], ...]]
                        if isinstance(vcard, list) and len(vcard) > 1:
                            for entry in vcard[1]:
                                if isinstance(entry, list) and entry[0] == 'fn':
                                    name = entry[-1]
                                    break

                    if isinstance(name, str) and name.strip():
                        registrar = name.strip()
                    break  # Found the registrar entity; stop scanning

                # If we got at least one useful piece of data, stop trying endpoints
                if age_days is not None or registrar is not None:
                    return age_days, registrar

                # Both fields still None from this endpoint — try the next one
                continue

            except httpx.TimeoutException:
                continue  # Server too slow — try next endpoint
            except httpx.RequestError:
                continue  # Network-level error — try next endpoint
            except Exception:
                continue  # Catch-all: never let RDAP break the analysis

        # All endpoints exhausted without usable data
        return None, None