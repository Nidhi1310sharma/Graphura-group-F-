# ============================================================
# STEP 11: DOMAIN RISK SCORE
# Combine the four domain-level signals into a single numeric
# domain_risk_score on a 0–100 scale.
#
# Weighted components:
#
#   Signal               Max Points  Rationale
#   ─────────────────    ──────────  ──────────────────────────────
#   Domain age           40 pts      Newly registered = highest risk
#   HTTPS                20 pts      HTTP-only in 2024 is suspicious
#   Suspicious TLD       25 pts      .xyz/.work/.buzz etc.
#   Website reachability 15 pts      Offline sites are red flags
#
# Domain age scoring:
#   < 30 days    → 40 pts (HIGH)
#   30–180 days  → 20 pts (MEDIUM)
#   > 180 days   →  0 pts (LOW)
#   UNKNOWN      → 15 pts (partial penalty)
#
# Extended signals from domain_check.py (optional, additive):
#   Domain reputation    up to +20 pts   Low trust_score from DomainChecker
#   Blacklist hit              +25 pts   Domain is on the blacklist
#   Brand impersonation        +20 pts   Impersonation pattern detected
#   Trusted platform           −20 pts   Known legitimate job board (bonus)
# ============================================================

def compute_domain_risk_score(https_enabled: bool,
                               domain_age_days: int,
                               domain_age_risk: str,
                               suspicious_tld: int,
                               website_reachable: bool,
                               domain_checker_result=None) -> dict:
    """
    Compute a weighted domain risk score from signal inputs.

    Parameters
    ----------
    https_enabled        : bool — True if the URL uses HTTPS
    domain_age_days      : int  — age of the domain in days
    domain_age_risk      : str  — 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN'
    suspicious_tld       : int  — truthy if TLD is suspicious
    website_reachable    : bool — True if the domain resolves/responds
    domain_checker_result: DomainResult (optional) — output of
                           DomainChecker.check() from domain_check.py.
                           When supplied, four additional signals are
                           incorporated. When None, the function behaves
                           exactly as before (backward compatible).

    Returns
    -------
    dict with keys:
        domain_risk_score     : int  (0–100)
        domain_risk_level     : str  'LOW' | 'MEDIUM' | 'HIGH'
        domain_risk_breakdown : dict of component scores
    """
    breakdown = {}

    # --- Domain age component (max 40) ---
    if domain_age_risk == 'HIGH':
        breakdown['domain_age_score'] = 40
    elif domain_age_risk == 'MEDIUM':
        breakdown['domain_age_score'] = 20
    elif domain_age_risk == 'LOW':
        breakdown['domain_age_score'] = 0
    else:  # UNKNOWN
        breakdown['domain_age_score'] = 15

    # --- HTTPS component (max 20) ---
    breakdown['https_score'] = 0 if https_enabled else 20

    # --- Suspicious TLD component (max 25) ---
    breakdown['tld_score'] = 25 if suspicious_tld else 0

    # --- Website availability component (max 15) ---
    breakdown['availability_score'] = 0 if website_reachable else 15

    # --- Domain reputation signals from domain_check.py (optional) ---
    # All default to 0 so callers that omit domain_checker_result are unaffected.
    breakdown['reputation_score']    = 0
    breakdown['blacklist_score']     = 0
    breakdown['impersonation_score'] = 0
    breakdown['trusted_bonus']       = 0

    if domain_checker_result is not None:
        # Convert trust_score (0–1, higher = safer) to a risk contribution.
        # trust_score 0.0 → +20 pts risk; 1.0 → 0 pts risk.
        trust_score = getattr(domain_checker_result, 'trust_score', 0.7)
        breakdown['reputation_score'] = int(round((1.0 - trust_score) * 20))

        # Blacklisted domain — hard penalty
        if getattr(domain_checker_result, 'blacklisted', False):
            breakdown['blacklist_score'] = 25

        # Brand impersonation — hard penalty
        if getattr(domain_checker_result, 'suspicious_pattern', False):
            breakdown['impersonation_score'] = 20

        # Known trusted platform — negative risk (small bonus)
        if getattr(domain_checker_result, 'is_trusted', False):
            breakdown['trusted_bonus'] = -20

    domain_risk_score = sum(breakdown.values())
    domain_risk_score = min(max(domain_risk_score, 0), 100)   # clamp 0–100

    if domain_risk_score >= 60:
        domain_risk_level = 'HIGH'
    elif domain_risk_score >= 30:
        domain_risk_level = 'MEDIUM'
    else:
        domain_risk_level = 'LOW'

    return {
        'domain_risk_score'    : domain_risk_score,
        'domain_risk_level'    : domain_risk_level,
        'domain_risk_breakdown': breakdown
    }
    
# ============================================================
# STEP 11b: COMPANY VERIFICATION ADJUSTMENT
# Translate the output of the company verification module into
# a numeric adjustment applied to the domain risk score before
# it is fed into the final blended score.
#
# Verification outcomes → risk adjustment:
#   VERIFIED            → −15 pts  (confirmed legitimate company)
#   PARTIALLY_VERIFIED  →   0 pts  (neutral — inconclusive)
#   UNVERIFIED          → +10 pts  (could not confirm existence)
#   SUSPICIOUS          → +20 pts  (active red flags found)
#
# The adjusted score is clamped to 0–100 before use.
# ============================================================

# Adjustment table keyed on the verification_status string
# produced by the company verification module.
_COMPANY_VERIFICATION_ADJUSTMENTS = {
    'VERIFIED'           : -15,
    'PARTIALLY_VERIFIED' :   0,
    'UNVERIFIED'         :  10,
    'SUSPICIOUS'         :  20,
}


def apply_company_verification_adjustment(domain_risk_score: int,
                                           company_verification_result=None) -> int:
    """
    Apply a company-verification adjustment to the raw domain risk score.

    Parameters
    ----------
    domain_risk_score          : int — output of compute_domain_risk_score()
    company_verification_result: dict or object (optional) — must expose a
                                  'verification_status' key/attribute whose
                                  value is one of VERIFIED | PARTIALLY_VERIFIED
                                  | UNVERIFIED | SUSPICIOUS.
                                  When None the original score is returned
                                  unchanged (backward compatible).

    Returns
    -------
    int — adjusted domain risk score, clamped to 0–100.
    """
    if company_verification_result is None:
        return domain_risk_score

    # Support both dict and object (dataclass / namedtuple) access patterns
    if isinstance(company_verification_result, dict):
        status = company_verification_result.get('verification_status', 'PARTIALLY_VERIFIED')
    else:
        status = getattr(company_verification_result, 'verification_status', 'PARTIALLY_VERIFIED')

    adjustment = _COMPANY_VERIFICATION_ADJUSTMENTS.get(status, 0)
    return min(max(domain_risk_score + adjustment, 0), 100)


# ============================================================
# STEP 12: FINAL URL RISK SCORE
# Combine the domain-level risk score (Step 11) and the
# content-level risk score (Step 10) into a single unified
# final_url_risk_score on a 0–100 scale.
#
# Weighting rationale:
#   Domain risk  — 40% weight
#     Structural signals (age, TLD, HTTPS) are objective
#     and harder to fake than page content.
#
#   Content risk — 60% weight
#     The actual language of the job posting is the most
#     direct indicator of fraudulent intent.
#
# Formula:
#   final = (domain_risk_score × 0.4) + (content_risk_score × 0.6)
#   capped at 100.
#
# Final risk bands:
#   0–24   → LOW
#   25–49  → MEDIUM
#   50–74  → HIGH
#   75–100 → CRITICAL
#
# Extended (domain_check.py integration):
#   When domain_checker_result is supplied, domain reputation is blended
#   in as a third component and weights are redistributed to:
#       Domain risk        — 30%
#       Content risk       — 50%
#       Domain reputation  — 20%
# ============================================================

DOMAIN_WEIGHT  = 0.40
CONTENT_WEIGHT = 0.60

# Weights used when domain reputation is available as a third signal
_DOMAIN_WEIGHT_EXT     = 0.30
_CONTENT_WEIGHT_EXT    = 0.50
_REPUTATION_WEIGHT_EXT = 0.20


def compute_final_risk_score(domain_risk_score: int,
                              content_risk_score: int,
                              domain_checker_result=None,
                              company_verification_result=None) -> dict:
    """
    Compute the final blended URL risk score.

    Parameters
    ----------
    domain_risk_score          : int — output of compute_domain_risk_score()
    content_risk_score         : int — output of the content analysis module
    domain_checker_result      : DomainResult (optional) — when supplied,
                                  domain reputation is blended in as a third
                                  component and weights are redistributed.
    company_verification_result: dict or object (optional) — when supplied,
                                  a verification adjustment is applied to the
                                  domain risk score before blending.

    Returns
    -------
    dict with keys:
        final_url_risk_score      : int  (0–100)
        final_risk_level          : str  'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
        domain_reputation_score   : int  (0–100) — 0 when not available
        company_verification_adj  : int  — pts added/subtracted for company
                                    verification; 0 when not available
    """
    # Apply company verification adjustment to domain risk before blending
    adjusted_domain_risk = apply_company_verification_adjustment(
        domain_risk_score, company_verification_result
    )
    company_adj = adjusted_domain_risk - domain_risk_score  # record delta for transparency

    domain_reputation_score = 0

    if domain_checker_result is not None:
        # Convert trust_score (0–1, higher = safer) to a 0–100 risk score
        # (higher = riskier) so it blends naturally with the other scores.
        trust_score = getattr(domain_checker_result, 'trust_score', 0.7)
        domain_reputation_score = int(round((1.0 - trust_score) * 100))

        # Three-component blend when reputation is available
        raw = (adjusted_domain_risk     * _DOMAIN_WEIGHT_EXT +
               content_risk_score       * _CONTENT_WEIGHT_EXT +
               domain_reputation_score  * _REPUTATION_WEIGHT_EXT)
    else:
        # Original two-component formula — fully backward compatible
        raw = (adjusted_domain_risk * DOMAIN_WEIGHT +
               content_risk_score   * CONTENT_WEIGHT)

    final_score = min(int(round(raw)), 100)

    if final_score >= 75:
        level = 'CRITICAL'
    elif final_score >= 50:
        level = 'HIGH'
    elif final_score >= 25:
        level = 'MEDIUM'
    else:
        level = 'LOW'

    return {
        'final_url_risk_score'    : final_score,
        'final_risk_level'        : level,
        'domain_reputation_score' : domain_reputation_score,
        'company_verification_adj': company_adj,
    }


# ============================================================
# STEP 13: EXPLAINABILITY LAYER
# Generate a consolidated, human-readable list of risk reasons
# combining domain-level and content-level signals.
#
# This layer is what makes the system actionable — instead of
# just a number, the user sees exactly WHY the URL was flagged.
#
# Domain-level reason triggers:
#   • Newly registered domain (< 30 days)
#   • Recently registered domain (30–180 days)
#   • Suspicious TLD detected
#   • Website unavailable or unreachable
#   • HTTP-only website (no HTTPS)
#   • Domain age unknown (WHOIS lookup failed)
#
# Extended reason triggers (domain_check.py / company verification):
#   • Domain blacklisted
#   • Brand impersonation detected
#   • Domain reputation low (trust_score < 0.4)
#   • SSL certificate expiring soon
#   • Company unverified or flagged as suspicious
#
# Content-level reasons come directly from analyze_job_text()
# (fraud phrases, urgency cues, risky contact channels).
# ============================================================

def build_risk_reasons(domain_age_days: int,
                        domain_age_risk: str,
                        suspicious_tld: int,
                        suffix: str,
                        https_enabled: bool,
                        website_reachable: bool,
                        content_fraud_reasons: list,
                        emails: list,
                        phone_numbers: list,
                        domain_checker_result=None,
                        company_verification_result=None) -> list:
    """
    Consolidate all risk signals into a single url_risk_reasons list.

    Parameters
    ----------
    domain_age_days            : int
    domain_age_risk            : str  — 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN'
    suspicious_tld             : int  — truthy if TLD is suspicious
    suffix                     : str  — TLD string e.g. 'xyz'
    https_enabled              : bool
    website_reachable          : bool
    content_fraud_reasons      : list of str — from content analysis module
    emails                     : list of str — emails found on the page
    phone_numbers              : list of str — phone numbers found on page
    domain_checker_result      : DomainResult (optional) — from domain_check.py
    company_verification_result: dict or object (optional) — from company
                                  verification module

    Returns
    -------
    list of str — ordered from highest-severity to lowest
    """
    reasons = []

    # --- Domain blacklist / impersonation (highest severity — prepended first) ---
    if domain_checker_result is not None:
        if getattr(domain_checker_result, 'blacklisted', False):
            reasons.append("⛔ Domain is blacklisted — known scam or fraud site")

        if getattr(domain_checker_result, 'suspicious_pattern', False):
            reasons.append("🚨 Domain impersonates a well-known brand — likely phishing")

        # Low trust score warrants a general reputation warning
        trust_score = getattr(domain_checker_result, 'trust_score', None)
        if trust_score is not None and trust_score < 0.4:
            reasons.append(
                f"Domain reputation is very low (trust score: {trust_score:.2f}) "
                "— multiple fraud signals detected"
            )

        # SSL expiry warning surfaced from ssl_info when available
        ssl_info = getattr(domain_checker_result, 'ssl_info', None)
        if ssl_info is not None:
            days_left = getattr(ssl_info, 'days_until_expiry', None)
            if days_left is not None and 0 <= days_left < 14:
                reasons.append(
                    f"⚠️ SSL certificate expires in {days_left} day(s) — site may become unsafe soon"
                )

    # --- Company verification ---
    if company_verification_result is not None:
        if isinstance(company_verification_result, dict):
            status      = company_verification_result.get('verification_status')
            reason_text = company_verification_result.get('reason', '')
        else:
            status      = getattr(company_verification_result, 'verification_status', None)
            reason_text = getattr(company_verification_result, 'reason', '')

        if status == 'SUSPICIOUS':
            reasons.append(
                "🚨 Company flagged as suspicious during verification"
                + (f": {reason_text}" if reason_text else "")
            )
        elif status == 'UNVERIFIED':
            reasons.append(
                "⚠️ Company could not be verified — no credible online presence found"
            )

    # --- Domain age ---
    if domain_age_risk == 'HIGH' and domain_age_days >= 0:
        reasons.append(f"Newly registered domain — only {domain_age_days} days old (HIGH RISK)")
    elif domain_age_risk == 'MEDIUM' and domain_age_days >= 0:
        reasons.append(f"Recently registered domain — {domain_age_days} days old (MEDIUM RISK)")
    elif domain_age_risk == 'UNKNOWN':
        reasons.append("Domain age unknown — WHOIS lookup failed or domain is privacy-protected")

    # --- HTTPS ---
    if not https_enabled:
        reasons.append("Website uses HTTP only — no SSL/TLS encryption (suspicious in 2024)")

    # --- Suspicious TLD ---
    if suspicious_tld:
        reasons.append(f"Suspicious TLD detected: .{suffix} — commonly used by fraudulent sites")

    # --- Availability ---
    if not website_reachable:
        reasons.append("Website is currently unreachable — may have been taken down")

    # --- Contact channels ---
    if emails:
        free_email_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'rediffmail.com']
        suspicious_emails  = [e for e in emails if any(d in e for d in free_email_domains)]
        if suspicious_emails:
            reasons.append(f"Recruiter uses free email service(s): {suspicious_emails[:3]}")

    if len(phone_numbers) > 2:
        reasons.append(f"Multiple phone numbers found ({len(phone_numbers)}) — unusual for legitimate postings")

    # --- Append content-level reasons from Detection Engine ---
    reasons.extend(content_fraud_reasons)

    return reasons