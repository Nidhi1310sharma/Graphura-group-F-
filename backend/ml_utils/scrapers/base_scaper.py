from __future__ import annotations

import re
import json
import requests
import tldextract
from bs4 import BeautifulSoup
from typing import Optional, List, Tuple


# ---------------------------------------------------------------------------
# Request settings
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 10   # seconds
REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}


# ---------------------------------------------------------------------------
# Platform registry
# ---------------------------------------------------------------------------

# Known job-board platforms → their own root domain.
# Used to tell the platform apart from the hiring company, and to exclude
# platform/social links when looking for the company website on the page.
PLATFORM_DOMAINS: dict[str, str] = {
    'internshala': 'internshala.com',
    'unstop'     : 'unstop.com',
    'linkedin'   : 'linkedin.com',
    'indeed'     : 'indeed.com',
    'naukri'     : 'naukri.com',
    'foundit'    : 'foundit.in',
    'apna'       : 'apna.co',
    'glassdoor'  : 'glassdoor.com',
}

# Domains that are never the hiring company, even if linked from the page.
_NON_COMPANY_LINK_DOMAINS: set[str] = {
    'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'youtube.com',
    'play.google.com', 'apps.apple.com', 'wa.me', 'whatsapp.com',
    'telegram.org', 't.me', 'g.co', 'goo.gl', 'bit.ly', 'pinterest.com',
} | set(PLATFORM_DOMAINS.values())

# Email local-parts that indicate an automated/non-company mailbox.
_EMAIL_IGNORE_TOKENS: tuple[str, ...] = (
    'noreply', 'no-reply', 'support', 'help',
    'notifications', 'admin', 'contact'
)

# Platform branding appended to <title> / og:title, e.g. "… | Internshala".
_PLATFORM_BRANDING_RE = re.compile(
    r'\s*[\|\-–—:]\s*(internshala|unstop|linkedin|indeed|naukri(?:\.com)?|'
    r'foundit|apna|glassdoor)\b.*$',
    re.I
)


# ---------------------------------------------------------------------------
# STEP 8: WEB SCRAPING
# ---------------------------------------------------------------------------

def _extract_json_ld_jobposting(soup: BeautifulSoup) -> Optional[dict]:
    """
    Scan all <script type="application/ld+json"> blocks and return the first
    object whose @type is "JobPosting" (schema.org).

    Handles single objects, lists, and "@graph" arrays.
    Returns None if no JobPosting schema is found or JSON cannot be parsed.
    """
    for script in soup.find_all('script', attrs={'type': re.compile(r'ld\+json', re.I)}):
        raw = script.string or script.get_text()
        if not raw or not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]

        # Some sites nest schema objects inside an "@graph" array
        expanded: list = []
        for item in candidates:
            if isinstance(item, dict) and isinstance(item.get('@graph'), list):
                expanded.extend(item['@graph'])
            else:
                expanded.append(item)

        for obj in expanded:
            if isinstance(obj, dict) and str(obj.get('@type', '')).lower() == 'jobposting':
                return obj

    return None


def scrape_url(url: str) -> dict:
    """
    Fetch a URL and extract structured content using BeautifulSoup.

    Returns
    -------
    dict with keys:
        page_title, meta_description, body_text,
        all_links, emails, phone_numbers, scrape_success,
        json_ld_jobposting, og_title, og_site_name, h1_text
    """
    default: dict = {
        'page_title'        : '',
        'meta_description'  : '',
        'body_text'         : '',
        'all_links'         : [],
        'emails'            : [],
        'phone_numbers'     : [],
        'scrape_success'    : False,
        'json_ld_jobposting': None,
        'og_title'          : '',
        'og_site_name'      : '',
        'h1_text'           : '',
    }

    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        if response.status_code != 200:
            return default

        soup = BeautifulSoup(response.text, 'html.parser')

        # Page title
        title_tag  = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else ''

        # Meta description
        meta_tag  = soup.find('meta', attrs={'name': re.compile('description', re.I)})
        meta_desc = meta_tag.get('content', '') if meta_tag else ''

        # OpenGraph metadata
        og_title_tag = soup.find('meta', attrs={'property': re.compile(r'^og:title$', re.I)})
        og_site_tag  = soup.find('meta', attrs={'property': re.compile(r'^og:site_name$', re.I)})
        og_title     = og_title_tag.get('content', '').strip() if og_title_tag else ''
        og_site_name = og_site_tag.get('content', '').strip() if og_site_tag else ''

        # H1 heading
        h1_tag  = soup.find('h1')
        h1_text = h1_tag.get_text(strip=True) if h1_tag else ''

        # JSON-LD JobPosting — must run BEFORE <script> tags are stripped below
        json_ld_jobposting = _extract_json_ld_jobposting(soup)

        # Body text (remove noise tags first)
        for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav']):
            tag.decompose()
        body_text = soup.get_text(separator=' ', strip=True)

        # All hyperlinks
        all_links = list(set(
            a.get('href', '') for a in soup.find_all('a', href=True)
            if a.get('href', '').startswith('http')
        ))

        # Email addresses
        email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        emails        = list(set(re.findall(email_pattern, response.text)))

        # Phone numbers (Indian + international formats)
        phone_pattern = r'(?:\+91[\-\s]?)?[6-9]\d{9}|\b\d{7,12}\b'
        phone_numbers = list(set(re.findall(phone_pattern, body_text)))

        return {
            'page_title'        : page_title,
            'meta_description'  : meta_desc,
            'body_text'         : body_text,
            'all_links'         : all_links,
            'emails'            : emails,
            'phone_numbers'     : phone_numbers,
            'scrape_success'    : True,
            'json_ld_jobposting': json_ld_jobposting,
            'og_title'          : og_title,
            'og_site_name'      : og_site_name,
            'h1_text'           : h1_text,
        }

    except Exception:
        return default


# ---------------------------------------------------------------------------
# STEP 9: CONTENT CLEANING
# ---------------------------------------------------------------------------

MAX_CLEAN_CHARS = 5000


def clean_scraped_text(raw_text: str) -> str:
    """
    Normalise raw scraped body text for the Detection Engine.

    Parameters
    ----------
    raw_text : str — raw body_text from scrape_url()

    Returns
    -------
    str — cleaned, lowercase, truncated text
    """
    if not raw_text or not isinstance(raw_text, str):
        return ''
    text = raw_text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)   # URLs
    text = re.sub(r'\S+@\S+\.\S+',          ' ', text)   # Emails
    text = re.sub(r'[^a-z\s]',              ' ', text)   # Non-alpha
    text = re.sub(r'\s+',                   ' ', text)   # Whitespace
    text = text.strip()
    return text[:MAX_CLEAN_CHARS]


# ---------------------------------------------------------------------------
# STEP 10: SHARED HELPER FUNCTIONS
# (used by both generic_scraper and every platform-specific scraper)
# ---------------------------------------------------------------------------

def _root_domain(value: str) -> Optional[str]:
    """Extract a clean 'domain.suffix' root domain from a URL or domain string."""
    if not value or not isinstance(value, str):
        return None
    try:
        ext = tldextract.extract(value)
        if not ext.domain or not ext.suffix:
            return None
        return f"{ext.domain}.{ext.suffix}".lower()
    except Exception:
        return None


def _detect_platform(url: str) -> Optional[str]:
    """Identify which known job board the URL belongs to, if any."""
    root = _root_domain(url)
    if not root:
        return None
    for name, domain in PLATFORM_DOMAINS.items():
        if root == domain:
            return name
    return None


def _external_domain(link: str, platform_domain: Optional[str]) -> Optional[str]:
    """Resolve `link` to a root domain, excluding the platform's own domain."""
    root = _root_domain(link)
    if not root:
        return None
    if platform_domain and root == platform_domain:
        return None
    return root


def _strip_platform_branding(text: str) -> str:
    """Remove trailing platform branding from a title string."""
    return _PLATFORM_BRANDING_RE.sub('', text or '').strip()


def _parse_title_for_company(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Generic title-parsing fallback (Priority 5).

    Recognises patterns such as:
        "Software Engineer Intern at Google"
        "Google Hiring Software Engineer"
        "Frontend Developer | Microsoft"

    Returns
    -------
    (job_title, company_name) — either element may be None.
    """
    cleaned = _strip_platform_branding(text)
    if not cleaned:
        return None, None

    name_chars = r"[A-Za-z0-9&.'\- ]+?"

    # "<title> at <Company>"
    m = re.match(rf'^(?P<title>.+?)\s+at\s+(?P<company>{name_chars})$', cleaned, re.I)
    if m:
        return m.group('title').strip(), m.group('company').strip()

    # "<Company> Hiring <title>" / "<Company> is hiring for <title>"
    m = re.match(
        rf'^(?P<company>{name_chars})\s+(?:is\s+)?hiring\s+(?:for\s+)?(?:an?\s+)?(?P<title>.+)$',
        cleaned, re.I,
    )
    if m:
        return m.group('title').strip(), m.group('company').strip()

    # "<title> | <Company>"  (also accept '–' / '—' as separator)
    parts = re.split(r'\s*[\|–—]\s*', cleaned)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()

    return None, None


def _company_domain_from_links(
    all_links: List[str],
    platform_domain: Optional[str],
) -> Optional[str]:
    """
    Priority 2 (Task 4) — find the company website among the page's
    outbound links, skipping platform and social-media domains.
    """
    for link in all_links:
        domain = _external_domain(link, platform_domain)
        if domain and domain not in _NON_COMPANY_LINK_DOMAINS:
            return domain
    return None


def _select_company_email(
    emails: List[str],
    platform_domain: Optional[str],
    company_domain: Optional[str],
) -> Optional[str]:
    """
    Task 3 — pick the best company-related email, ignoring automated
    mailboxes (noreply, support, …).
    """
    if not emails:
        return None

    def is_automated(addr: str) -> bool:
        local = addr.split('@', 1)[0].lower()
        return any(token in local for token in _EMAIL_IGNORE_TOKENS)

    candidates = [e for e in emails if not is_automated(e)]
    if not candidates:
        return None

    # Prefer an email on the already-known company domain
    if company_domain:
        for e in candidates:
            if e.lower().endswith('@' + company_domain.lower()):
                return e

    # Otherwise prefer an email that is NOT on the platform's own domain
    if platform_domain:
        off_platform = [e for e in candidates
                        if not e.lower().endswith('@' + platform_domain.lower())]
        if off_platform:
            return off_platform[0]

    return candidates[0]