from __future__ import annotations

from typing import Optional, Tuple

from .base_scraper import (
    _root_domain,
    _detect_platform,
    _parse_title_for_company,
    _strip_platform_branding,
    _company_domain_from_links,
    _select_company_email,
    _external_domain,
)


# ---------------------------------------------------------------------------
# Platform-specific title patterns  (Priority 4)
# ---------------------------------------------------------------------------

def _platform_specific_extract(
    platform_name: Optional[str],
    og_title: str,
    h1_text: str,
    page_title: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Apply platform-specific regex patterns before falling back to the
    generic parser.  Returns (job_title, company_name); either may be None.

    Supported platforms and their typical title formats
    ---------------------------------------------------
    internshala : "Software Engineer Intern at Google - Internshala"
                  "Google is hiring for Software Engineer Intern"
    unstop       : "Software Engineer Intern - Google | Unstop"
    naukri       : "Google hiring for Software Engineer Intern in Bengaluru"
    indeed       : "Software Engineer Intern - Google - Bengaluru"
    foundit      : "Software Engineer Intern Jobs in Bengaluru - Google"
    glassdoor    : "Google Software Engineer Intern Reviews"
    """
    if not platform_name:
        return None, None

    text = _strip_platform_branding(og_title or h1_text or page_title or '')
    if not text:
        return None, None

    import re
    name_chars = r"[A-Za-z0-9&.'\- ]+?"

    patterns: dict[str, list[str]] = {
        'internshala': [
            rf'^(?P<company>{name_chars})\s+(?:is\s+)?hiring\s+for\s+(?P<title>.+)$',
            rf'^(?P<title>.+?)\s+at\s+(?P<company>{name_chars})$',
        ],
        'unstop': [
            rf'^(?P<title>.+?)\s*-\s*(?P<company>{name_chars})$',
        ],
        'naukri': [
            rf'^(?P<company>{name_chars})\s+hiring\s+for\s+(?P<title>.+?)(?:\s+in\s+.+)?$',
        ],
        'indeed': [
            rf'^(?P<title>.+?)\s*-\s*(?P<company>{name_chars})\s*-\s*.+$',
        ],
        'foundit': [
            rf'^(?P<title>.+?)\s+[Jj]obs\s+in\s+.+?-\s*(?P<company>{name_chars})$',
        ],
        'glassdoor': [
            rf'^(?P<company>{name_chars})\s+(?P<title>.+?)\s+[Rr]eviews$',
        ],
    }

    for pattern in patterns.get(platform_name, []):
        m = re.match(pattern, text)
        if m:
            gd = m.groupdict()
            company = (gd.get('company') or '').strip() or None
            title   = (gd.get('title')   or '').strip() or None
            if company or title:
                return title, company

    return None, None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def extract_job_metadata(scrape_data: dict, url: str) -> dict:
    """
    Resolve hiring-company metadata from the signals collected by
    scrape_url(), following the five-priority chain:

        Priority 1  JSON-LD JobPosting → title + hiringOrganization.name
        Priority 2  hiringOrganization.sameAs / .url → company_domain
        Priority 3  OpenGraph metadata (og:site_name, og:title)
        Priority 4  Platform-specific title patterns
        Priority 5  Generic title-parsing fallback

    Parameters
    ----------
    scrape_data : dict  — output of base_scraper.scrape_url()
    url         : str   — the original URL being analysed

    Returns
    -------
    dict with keys:
        company_name, job_title, company_email,
        company_domain, platform_domain
    Each value is a non-empty str or None (caller renders None as "Unknown").
    """
    platform_domain = _root_domain(url)
    platform_name   = _detect_platform(url)

    job_posting    = scrape_data.get('json_ld_jobposting') or {}
    company_name: Optional[str] = None
    job_title:    Optional[str] = None
    company_domain: Optional[str] = None

    # ------------------------------------------------------------------
    # Priority 1 & 2 — JSON-LD JobPosting schema
    # ------------------------------------------------------------------
    if isinstance(job_posting, dict):
        # Job title
        title_val = job_posting.get('title')
        if isinstance(title_val, str) and title_val.strip():
            job_title = title_val.strip()

        # Hiring organisation name + domain
        org = job_posting.get('hiringOrganization')
        if isinstance(org, dict):
            name_val = org.get('name')
            if isinstance(name_val, str) and name_val.strip():
                company_name = name_val.strip()

            for key in ('sameAs', 'url'):
                link_val = org.get(key)
                if isinstance(link_val, list):
                    link_val = next(
                        (v for v in link_val if isinstance(v, str)), None
                    )
                if isinstance(link_val, str) and link_val.strip():
                    domain = _external_domain(link_val, platform_domain)
                    if domain:
                        company_domain = domain
                        break

    # Convenience aliases
    og_title     = scrape_data.get('og_title', '') or ''
    og_site_name = scrape_data.get('og_site_name', '') or ''
    h1_text      = scrape_data.get('h1_text', '') or ''
    page_title   = scrape_data.get('page_title', '') or ''

    # ------------------------------------------------------------------
    # Priority 3 — OpenGraph metadata
    # ------------------------------------------------------------------
    if not company_name and og_site_name and (
        not platform_name or platform_name not in og_site_name.lower()
    ):
        company_name = og_site_name.strip()

    if not job_title and og_title:
        parsed_title, _ = _parse_title_for_company(og_title)
        job_title = parsed_title or job_title

    # ------------------------------------------------------------------
    # Priority 4 — Platform-specific title extraction
    # ------------------------------------------------------------------
    if platform_name and (not company_name or not job_title):
        platform_title, platform_company = _platform_specific_extract(
            platform_name, og_title, h1_text, page_title
        )
        company_name = company_name or platform_company
        job_title    = job_title    or platform_title

    # ------------------------------------------------------------------
    # Priority 5 — Generic title-parsing fallback
    # ------------------------------------------------------------------
    if not company_name or not job_title:
        for candidate in (og_title, h1_text, page_title):
            if not candidate:
                continue
            parsed_title, parsed_company = _parse_title_for_company(candidate)
            job_title    = job_title    or parsed_title
            company_name = company_name or parsed_company
            if company_name and job_title:
                break

    # ------------------------------------------------------------------
    # Task 4 / Priority 2 (continued) — company website links on page
    # ------------------------------------------------------------------
    if not company_domain:
        company_domain = _company_domain_from_links(
            scrape_data.get('all_links', []), platform_domain
        )

    # ------------------------------------------------------------------
    # Task 3 — company email (filtered, domain-aware)
    # ------------------------------------------------------------------
    company_email = _select_company_email(
        scrape_data.get('emails', []), platform_domain, company_domain
    )

    # ------------------------------------------------------------------
    # Task 4 / Priority 3 — company domain from the selected email
    # ------------------------------------------------------------------
    if not company_domain and company_email and '@' in company_email:
        company_domain = company_email.split('@', 1)[1].lower()

    return {
        'company_name'   : company_name    or None,
        'job_title'      : job_title       or None,
        'company_email'  : company_email   or None,
        'company_domain' : company_domain  or None,
        'platform_domain': platform_domain or None,
    }