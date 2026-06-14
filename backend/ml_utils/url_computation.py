    
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
# ============================================================

def compute_domain_risk_score(https_enabled: bool,
                               domain_age_days: int,
                               domain_age_risk: str,
                               suspicious_tld: int,
                               website_reachable: bool) -> dict:
    """
    Compute a weighted domain risk score from signal inputs.

    Returns
    -------
    dict with keys:
        domain_risk_score   : int  (0–100)
        domain_risk_level   : str  'LOW' | 'MEDIUM' | 'HIGH'
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

    domain_risk_score = sum(breakdown.values())
    domain_risk_score = min(domain_risk_score, 100)

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
# ============================================================

DOMAIN_WEIGHT  = 0.40
CONTENT_WEIGHT = 0.60

def compute_final_risk_score(domain_risk_score: int,
                              content_risk_score: int) -> dict:
    """
    Compute the final blended URL risk score.

    Returns
    -------
    dict with keys:
        final_url_risk_score : int  (0–100)
        final_risk_level     : str  'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
    """
    raw = (domain_risk_score  * DOMAIN_WEIGHT +
           content_risk_score * CONTENT_WEIGHT)
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
        'final_url_risk_score': final_score,
        'final_risk_level'    : level
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
                        phone_numbers: list) -> list:
    """
    Consolidate all risk signals into a single url_risk_reasons list.

    Returns
    -------
    list of str — ordered from highest-severity to lowest
    """
    reasons = []

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
