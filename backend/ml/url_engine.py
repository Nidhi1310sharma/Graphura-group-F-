
import pandas as pd
import numpy as np
import re
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
import requests
import tldextract
import whois
from bs4 import BeautifulSoup
import backend.ml_utils.scraper as scraper
import backend.ml_utils.validator as validator  
import backend.ml_utils.url_computation as url_comp

# --- Request settings ---
REQUEST_TIMEOUT = 10   # seconds
REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

# STEP 10: DETECTION ENGINE INTEGRATION

from textstat import flesch_reading_ease

# --- Weighted fraud phrase dictionary (Notebook 3 source) ---
ENGINE_FRAUD_PHRASES = {
    'registration fee' : 15, 'security deposit' : 15,
    'processing fee'   : 12, 'training fee'     : 12,
    'pay to work'      : 15, 'investment'       : 12,
    'earn online'      : 10, 'earn money fast'  : 12,
    'daily payment'    : 10, 'income source'    :  8,
    'form filling'     :  8, 'typing job'       :  8,
    'data entry'       :  6, 'copy paste'       : 10,
    'captcha'          :  8, 'ad posting'       : 10,
    'refer and earn'   : 10, 'multi level'      : 12,
    'refundable deposit': 14,'no experience needed': 6,
}

ENGINE_URGENCY_PHRASES = [
    'urgent', 'immediately', 'limited seats', 'limited openings',
    'hurry', 'apply now', 'last date', 'closing soon',
    'act fast', 'do not miss', 'first come first', 'fast track'
]

ENGINE_CONTACT_RISKS = {
    'whatsapp': 10, 'telegram': 10, 'gmail.com': 6,
    'yahoo.com': 6, 'call now': 8,  'call us': 5,
    'dm us': 6,     'direct message': 6, 'ping us': 5,
}


def analyze_job_text(text: str) -> dict:
    """
    Run the Detection Engine on a cleaned job description text.

    Returns
    -------
    dict with keys:
        content_risk_score, risk_level, fraud_reasons,
        recommended_action, fraud_phrase_score,
        urgency_score, contact_risk_score, readability_score
    """
    reasons = []
    t       = text.lower()

    # --- Fraud phrase scoring ---
    phrase_score = sum(
        w for p, w in ENGINE_FRAUD_PHRASES.items() if p in t
    )
    for p, w in ENGINE_FRAUD_PHRASES.items():
        if p in t:
            reasons.append(f"Fraud phrase detected: '{p}' (weight {w})")

    # --- Urgency scoring ---
    urgency_score = sum(1 for p in ENGINE_URGENCY_PHRASES if p in t)
    if urgency_score > 0:
        reasons.append(f"Urgency language detected ({urgency_score} cues)")

    # --- Contact risk scoring ---
    contact_score = sum(
        w for c, w in ENGINE_CONTACT_RISKS.items() if c in t
    )
    for c, w in ENGINE_CONTACT_RISKS.items():
        if c in t:
            reasons.append(f"Risky contact channel: '{c}' (weight {w})")

    # --- Readability scoring ---
    try:
        readability = flesch_reading_ease(text)
        if readability > 85:
            reasons.append(f"Very high readability score ({readability:.1f}) — unusually simple language")
    except Exception:
        readability = 50.0

    # --- Composite content risk score (cap at 100) ---
    raw_score = phrase_score + (urgency_score * 5) + contact_score
    content_risk_score = min(int(raw_score), 100)

    # --- Risk level bands ---
    if content_risk_score >= 60:
        risk_level = 'CRITICAL'
        action     = 'DO NOT APPLY — High probability scam. Report immediately.'
    elif content_risk_score >= 35:
        risk_level = 'HIGH'
        action     = 'Proceed with extreme caution. Verify company independently.'
    elif content_risk_score >= 15:
        risk_level = 'MEDIUM'
        action     = 'Exercise caution. Research the company before applying.'
    else:
        risk_level = 'LOW'
        action     = 'Appears relatively safe. Standard due diligence recommended.'

    return {
        'content_risk_score' : content_risk_score,
        'risk_level'         : risk_level,
        'fraud_reasons'      : reasons,
        'recommended_action' : action,
        'fraud_phrase_score' : phrase_score,
        'urgency_score'      : urgency_score,
        'contact_risk_score' : contact_score,
        'readability_score'  : round(readability, 2)
    }


# ============================================================
# STEP 14: MASTER FUNCTION — analyze_url()
# This is the single entry point for the entire URL Analysis
# Engine.  It chains all 13 preceding steps into one call and
# returns a fully structured JSON-serialisable report.
#
# Input  : A raw URL string
# Output : A dict (JSON report) containing:
#   • url, is_valid
#   • Domain info (subdomain, domain, suffix, full_domain)
#   • HTTPS, domain_age_days, creation_date
#   • suspicious_tld, status_code, website_reachable
#   • page_title, meta_description, emails, phone_numbers
#   • content_risk_score, domain_risk_score
#   • final_url_risk_score, final_risk_level
#   • url_risk_reasons (consolidated list)
#   • recommended_action
#   • analysis_timestamp
# ============================================================

def analyze_url(url: str,
                run_whois: bool = True,
                verbose: bool   = True) -> dict:
    """
    Full URL analysis pipeline — single entry point.

    Parameters
    ----------
    url       : str  — raw URL to analyse
    run_whois : bool — set False to skip WHOIS (faster, no domain age)
    verbose   : bool — print progress steps if True

    Returns
    -------
    dict — full JSON-serialisable risk report
    """

    if verbose: print(f"\n{'='*60}")
    if verbose: print(f"  Analysing: {url}")
    if verbose: print(f"{'='*60}")

    # ── Step 2: Validate ──────────────────────────────────────
    is_valid = validator.validate_url(url)
    if not is_valid:
        if verbose: print("  [INVALID URL] Returning error report.")
        return {
            'url'                  : url,
            'is_valid'             : False,
            'final_url_risk_score' : 100,
            'final_risk_level'     : 'INVALID',
            'url_risk_reasons'     : ['URL is malformed or uses an unsupported scheme'],
            'recommended_action'   : 'This URL is not a valid HTTP/HTTPS address.',
            'analysis_timestamp'   : datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    # ── Step 3: Domain extraction ─────────────────────────────
    if verbose: print("  [1/7] Extracting domain info...")
    domain_info = validator.extract_domain_info(url)

    # ── Step 4: HTTPS ─────────────────────────────────────────
    https_enabled = validator.check_https(url)

    # ── Step 5: WHOIS ─────────────────────────────────────────
    if verbose: print("  [2/7] WHOIS domain age lookup...")
    if run_whois:
        age_info = validator.get_domain_age(url)
    else:
        age_info = {'creation_date': 'Skipped', 'domain_age_days': -1, 'domain_age_risk': 'UNKNOWN'}

    # ── Step 6: TLD check ─────────────────────────────────────
    if verbose: print("  [3/7] Checking TLD...")
    tld_info = validator.check_suspicious_tld(url)

    # ── Step 7: Availability ──────────────────────────────────
    if verbose: print("  [4/7] Checking website availability...")
    avail_info = validator.check_website_availability(url)

    # ── Steps 8 & 9: Scrape + Clean ───────────────────────────
    if verbose: print("  [5/7] Scraping page content...")
    if avail_info['website_reachable']:
        scrape_data = scraper.scrape_url(url)
        clean_text  = scraper.clean_scraped_text(scrape_data['body_text'])
    else:
        scrape_data = {
            'page_title': '', 'meta_description': '', 'body_text': '',
            'all_links': [], 'emails': [], 'phone_numbers': [],
            'scrape_success': False,
            'json_ld_jobposting': None, 'og_title': '', 'og_site_name': '', 'h1_text': ''
        }
        clean_text = ''

    # ── Step 9b: Hiring-company / job-title / email / domain resolution ──
    job_meta = scraper.extract_job_metadata(scrape_data, url)

    # ── Step 10: Detection Engine ─────────────────────────────
    if verbose: print("  [6/7] Running Detection Engine...")
    engine_result = analyze_job_text(clean_text)

    # ── Step 11: Domain risk score ────────────────────────────
    domain_risk = url_comp.compute_domain_risk_score(
        https_enabled     = https_enabled,
        domain_age_days   = age_info['domain_age_days'],
        domain_age_risk   = age_info['domain_age_risk'],
        suspicious_tld    = tld_info['suspicious_tld'],
        website_reachable = avail_info['website_reachable']
    )

    # ── Step 12: Final URL risk score ─────────────────────────
    final_risk = url_comp.compute_final_risk_score(
        domain_risk_score  = domain_risk['domain_risk_score'],
        content_risk_score = engine_result['content_risk_score']
    )

    # ── Step 13: Explainability ───────────────────────────────
    if verbose: print("  [7/7] Building risk reasons...")
    url_risk_reasons = url_comp.build_risk_reasons(
        domain_age_days       = age_info['domain_age_days'],
        domain_age_risk       = age_info['domain_age_risk'],
        suspicious_tld        = tld_info['suspicious_tld'],
        suffix                = tld_info['suffix'],
        https_enabled         = https_enabled,
        website_reachable     = avail_info['website_reachable'],
        content_fraud_reasons = engine_result['fraud_reasons'],
        emails                = scrape_data['emails'],
        phone_numbers         = scrape_data['phone_numbers']
    )

    # ── Assemble final report ──────────────────────────────────
    report = {
        'url'                    : url,
        'is_valid'               : True,
        # Domain metadata
        'subdomain'              : domain_info['subdomain'],
        'domain'                 : domain_info['domain'],
        'suffix'                 : domain_info['suffix'],
        'full_domain'            : domain_info['full_domain'],
        # Security signals
        'https_enabled'          : https_enabled,
        'creation_date'          : age_info['creation_date'],
        'domain_age_days'        : age_info['domain_age_days'],
        'domain_age_risk'        : age_info['domain_age_risk'],
        'suspicious_tld'         : bool(tld_info['suspicious_tld']),
        # Availability
        'status_code'            : avail_info['status_code'],
        'website_reachable'      : avail_info['website_reachable'],
        'response_time_ms'       : avail_info['response_time_ms'],
        # Scraped content
        'page_title'             : scrape_data['page_title'],
        'meta_description'       : scrape_data['meta_description'],
        'emails_found'           : scrape_data['emails'],
        'phone_numbers_found'    : scrape_data['phone_numbers'],
        'links_found'            : len(scrape_data['all_links']),
        # Hiring-company metadata (URL trust card)
        'company_name'           : job_meta['company_name'],
        'job_title'              : job_meta['job_title'],
        'company_email'          : job_meta['company_email'],
        'company_domain'         : job_meta['company_domain'],
        'platform_domain'        : job_meta['platform_domain'],
        # Scores
        'fraud_phrase_score'     : engine_result['fraud_phrase_score'],
        'urgency_score'          : engine_result['urgency_score'],
        'contact_risk_score'     : engine_result['contact_risk_score'],
        'readability_score'      : engine_result['readability_score'],
        'content_risk_score'     : engine_result['content_risk_score'],
        'domain_risk_score'      : domain_risk['domain_risk_score'],
        'domain_risk_breakdown'  : domain_risk['domain_risk_breakdown'],
        'final_url_risk_score'   : final_risk['final_url_risk_score'],
        'final_risk_level'       : final_risk['final_risk_level'],
        # Explainability
        'url_risk_reasons'       : url_risk_reasons,
        'recommended_action'     : engine_result['recommended_action'],
        'analysis_timestamp'     : datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    if verbose:
        print(f"\n  ✓ Analysis complete")
        print(f"  Final Risk Score : {report['final_url_risk_score']} / 100")
        print(f"  Risk Level       : {report['final_risk_level']}")
        print(f"  Reasons found    : {len(url_risk_reasons)}")

    return report
