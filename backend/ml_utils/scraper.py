import re
import json
import requests
import tldextract
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple


# --- Request settings ---
REQUEST_TIMEOUT = 10   # seconds
REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

# STEP 8: WEB SCRAPING

def _extract_json_ld_jobposting(soup: BeautifulSoup) -> Optional[dict]:
    """
    Scan all <script type="application/ld+json"> blocks on the page and
    return the first object whose @type is "JobPosting" (schema.org).
    Handles JSON-LD blocks that are a single object, a list of objects,
    or wrapped in an "@graph" array. Returns None if no JobPosting schema
    is found or the JSON cannot be parsed.
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
        expanded = []
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
        all_links, emails, phone_numbers, scrape_success
    """
    default = {
        'page_title'        : '',
        'meta_description'  : '',
        'body_text'         : '',
        'all_links'         : [],
        'emails'            : [],
        'phone_numbers'     : [],
        'scrape_success'    : False,
        # --- job-metadata signals (used for company/title resolution) ---
        'json_ld_jobposting': None,
        'og_title'          : '',
        'og_site_name'      : '',
        'h1_text'           : ''
    }

    try:
        response = requests.get(
            url,
            headers = REQUEST_HEADERS,
            timeout = REQUEST_TIMEOUT,
            allow_redirects = True
        )
        if response.status_code != 200:
            default['scrape_success'] = False
            return default

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Page title ---
        title_tag  = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else ''

        # --- Meta description ---
        meta_tag   = soup.find('meta', attrs={'name': re.compile('description', re.I)})
        meta_desc  = meta_tag.get('content', '') if meta_tag else ''

        # --- OpenGraph metadata (company-name / job-title signals) ---
        og_title_tag = soup.find('meta', attrs={'property': re.compile(r'^og:title$', re.I)})
        og_site_tag  = soup.find('meta', attrs={'property': re.compile(r'^og:site_name$', re.I)})
        og_title     = og_title_tag.get('content', '').strip() if og_title_tag else ''
        og_site_name = og_site_tag.get('content', '').strip() if og_site_tag else ''

        # --- H1 heading (job title / company often rendered here) ---
        h1_tag  = soup.find('h1')
        h1_text = h1_tag.get_text(strip=True) if h1_tag else ''

        # --- JSON-LD JobPosting schema — must run BEFORE <script> tags
        #     are stripped below, since the JSON-LD lives in a <script> tag.
        json_ld_jobposting = _extract_json_ld_jobposting(soup)

        # --- Body text (remove scripts and styles first) ---
        for tag in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav']):
            tag.decompose()
        body_text  = soup.get_text(separator=' ', strip=True)

        # --- All hyperlinks ---
        all_links  = list(set(
            a.get('href', '') for a in soup.find_all('a', href=True)
            if a.get('href', '').startswith('http')
        ))

        # --- Email addresses ---
        email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        emails        = list(set(re.findall(email_pattern, response.text)))

        # --- Phone numbers (Indian + international formats) ---
        phone_pattern  = r'(?:\+91[\-\s]?)?[6-9]\d{9}|\b\d{7,12}\b'
        phone_numbers  = list(set(re.findall(phone_pattern, body_text)))

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
            'h1_text'           : h1_text
        }

    except Exception as e:
        default['scrape_success'] = False
        return default

# STEP 9: CONTENT CLEANING

MAX_CLEAN_CHARS = 5000

def clean_scraped_text(raw_text: str) -> str:
    """
    Normalise raw scraped body text for Detection Engine input.

    Parameters
    ----------
    raw_text : str  — raw body_text from scrape_url()

    Returns
    -------
    str — cleaned, lowercase, truncated text
    """
    if not raw_text or not isinstance(raw_text, str):
        return ''
    text = raw_text.lower()
    text = re.sub(r'https?://\S+|www\.\S+',        ' ', text)   # URLs
    text = re.sub(r'\S+@\S+\.\S+',                 ' ', text)   # Emails
    text = re.sub(r'[^a-z\s]',                     ' ', text)   # Non-alpha
    text = re.sub(r'\s+',                           ' ', text)   # Whitespace
    text = text.strip()
    return text[:MAX_CLEAN_CHARS]

# STEP 10: HIRING-COMPANY / JOB-TITLE / EMAIL / DOMAIN RESOLUTION
#
# Job-board listings (Internshala, Unstop, LinkedIn, Indeed, Naukri,
# Foundit, Apna, Glassdoor, ...) expose the *platform* domain in the URL,
# but the trust card needs the *hiring company's* identity. This section
# resolves that identity from the signals captured in scrape_url(),
# using the priority order:
#
#   1. JSON-LD JobPosting schema (hiringOrganization.name)
#   2. hiringOrganization.sameAs / .url            -> company_domain
#   3. OpenGraph metadata (og:site_name / og:title)
#   4. Platform-specific title patterns
#   5. Generic title-parsing fallback ("X at Company", "Company Hiring X", "X | Company")

# Known job-board platforms -> their own root domain (used to tell the
# platform apart from the hiring company, and to exclude platform/social
# links when looking for a company website on the page).
PLATFORM_DOMAINS = {
    'internshala': 'internshala.com',
    'unstop'     : 'unstop.com',
    'linkedin'   : 'linkedin.com',
    'indeed'     : 'indeed.com',
    'naukri'     : 'naukri.com',
    'foundit'    : 'foundit.in',
    'apna'       : 'apna.co',
    'glassdoor'  : 'glassdoor.com',
}

# Domains that are never the hiring company, even if linked from the page
_NON_COMPANY_LINK_DOMAINS = {
    'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'youtube.com',
    'play.google.com', 'apps.apple.com', 'wa.me', 'whatsapp.com',
    'telegram.org', 't.me', 'g.co', 'goo.gl', 'bit.ly', 'pinterest.com',
} | set(PLATFORM_DOMAINS.values())

# Email local-parts that indicate an automated/non-company mailbox (Task 3)
_EMAIL_IGNORE_TOKENS = (
    'noreply', 'no-reply', 'support', 'help',
    'notifications', 'admin', 'contact'
)

# Suffix appended by a platform's own branding to <title>/og:title text,
# e.g. "... | Internshala", "... - Naukri.com" — stripped before parsing.
_PLATFORM_BRANDING_RE = re.compile(
    r'\s*[\|\-–—:]\s*(internshala|unstop|linkedin|indeed|naukri(?:\.com)?|'
    r'foundit|apna|glassdoor)\b.*$',
    re.I
)


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
    return _PLATFORM_BRANDING_RE.sub('', text or '').strip()


def _parse_title_for_company(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Generic title-parsing fallback (Task 5 / Priority 5).
    Recognises patterns such as:
        "Software Engineer Intern at Google"
        "Google Hiring Software Engineer"
        "Frontend Developer | Microsoft"
    Returns (job_title, company_name); either may be None.
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
        cleaned, re.I
    )
    if m:
        return m.group('title').strip(), m.group('company').strip()

    # "<title> | <Company>"  (also accept '-' / '–' / '—' as separator)
    parts = re.split(r'\s*[\|–—]\s*', cleaned)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()

    return None, None


def _platform_specific_extract(
    platform_name: Optional[str],
    og_title: str,
    h1_text: str,
    page_title: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Platform-specific title patterns (Task 1 / Priority 4) for the job
    boards named in the project spec. Falls back to (None, None) if no
    platform pattern matches — the generic parser (Priority 5) then runs.
    """
    if not platform_name:
        return None, None

    text = _strip_platform_branding(og_title or h1_text or page_title or '')
    if not text:
        return None, None

    name_chars = r"[A-Za-z0-9&.'\- ]+?"
    patterns = {
        # "Software Engineer Intern at Google - Internshala"
        # "Google is hiring for Software Engineer Intern"
        'internshala': [
            rf'^(?P<company>{name_chars})\s+(?:is\s+)?hiring\s+for\s+(?P<title>.+)$',
            rf'^(?P<title>.+?)\s+at\s+(?P<company>{name_chars})$',
        ],
        # "Software Engineer Intern - Google | Unstop"
        'unstop': [
            rf'^(?P<title>.+?)\s*-\s*(?P<company>{name_chars})$',
        ],
        # "Google hiring for Software Engineer Intern in Bengaluru"
        'naukri': [
            rf'^(?P<company>{name_chars})\s+hiring\s+for\s+(?P<title>.+?)(?:\s+in\s+.+)?$',
        ],
        # "Software Engineer Intern - Google - Bengaluru"
        'indeed': [
            rf'^(?P<title>.+?)\s*-\s*(?P<company>{name_chars})\s*-\s*.+$',
        ],
        # "Software Engineer Intern Jobs in Bengaluru - Google"
        'foundit': [
            rf'^(?P<title>.+?)\s+[Jj]obs\s+in\s+.+?-\s*(?P<company>{name_chars})$',
        ],
        # "Google Software Engineer Intern Reviews"
        'glassdoor': [
            rf'^(?P<company>{name_chars})\s+(?P<title>.+?)\s+[Rr]eviews$',
        ],
    }

    for pattern in patterns.get(platform_name, []):
        m = re.match(pattern, text)
        if m:
            gd = m.groupdict()
            company = (gd.get('company') or '').strip() or None
            title   = (gd.get('title') or '').strip() or None
            if company or title:
                return title, company

    return None, None


def _company_domain_from_links(all_links: List[str], platform_domain: Optional[str]) -> Optional[str]:
    """Task 4 / Priority 2 — find a company website among the page's outbound links."""
    for link in all_links:
        domain = _external_domain(link, platform_domain)
        if domain and domain not in _NON_COMPANY_LINK_DOMAINS:
            return domain
    return None


def _select_company_email(
    emails: List[str],
    platform_domain: Optional[str],
    company_domain: Optional[str]
) -> Optional[str]:
    """Task 3 — pick the best company-related email, ignoring automated mailboxes."""
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
        off_platform = [e for e in candidates if not e.lower().endswith('@' + platform_domain.lower())]
        if off_platform:
            return off_platform[0]

    return candidates[0]


def extract_job_metadata(scrape_data: dict, url: str) -> dict:
    """
    Resolve hiring-company metadata from the signals collected by
    scrape_url(), following the priority order described in the project
    spec (JSON-LD -> hiringOrganization links -> OpenGraph ->
    platform-specific patterns -> generic title parsing).

    Parameters
    ----------
    scrape_data : dict — output of scrape_url()
    url         : str  — the original URL being analysed

    Returns
    -------
    dict with keys:
        company_name, job_title, company_email,
        company_domain, platform_domain
    (each value is either a non-empty str, or None if it could not be
    resolved — callers/UI are responsible for rendering None as "Unknown")
    """
    platform_domain = _root_domain(url)
    platform_name    = _detect_platform(url)

    job_posting    = scrape_data.get('json_ld_jobposting') or {}
    company_name   = None
    job_title      = None
    company_domain = None

    # --- Priority 1 & 2: JSON-LD JobPosting schema ---
    if isinstance(job_posting, dict):
        title_val = job_posting.get('title')
        if isinstance(title_val, str) and title_val.strip():
            job_title = title_val.strip()

        org = job_posting.get('hiringOrganization')
        if isinstance(org, dict):
            name_val = org.get('name')
            if isinstance(name_val, str) and name_val.strip():
                company_name = name_val.strip()

            for key in ('sameAs', 'url'):
                link_val = org.get(key)
                if isinstance(link_val, list):
                    link_val = next((v for v in link_val if isinstance(v, str)), None)
                if isinstance(link_val, str) and link_val.strip():
                    domain = _external_domain(link_val, platform_domain)
                    if domain:
                        company_domain = domain
                        break

    og_title     = scrape_data.get('og_title', '') or ''
    og_site_name = scrape_data.get('og_site_name', '') or ''
    h1_text      = scrape_data.get('h1_text', '') or ''
    page_title   = scrape_data.get('page_title', '') or ''

    # --- Priority 3: OpenGraph metadata ---
    if not company_name and og_site_name and (
        not platform_name or platform_name not in og_site_name.lower()
    ):
        company_name = og_site_name.strip()

    if not job_title and og_title:
        parsed_title, _ = _parse_title_for_company(og_title)
        job_title = parsed_title or job_title

    # --- Priority 4: platform-specific extraction ---
    if platform_name and (not company_name or not job_title):
        platform_title, platform_company = _platform_specific_extract(
            platform_name, og_title, h1_text, page_title
        )
        company_name = company_name or platform_company
        job_title    = job_title or platform_title

    # --- Priority 5: generic title-parsing fallback ---
    if not company_name or not job_title:
        for candidate in (og_title, h1_text, page_title):
            if not candidate:
                continue
            parsed_title, parsed_company = _parse_title_for_company(candidate)
            job_title    = job_title or parsed_title
            company_name = company_name or parsed_company
            if company_name and job_title:
                break

    # --- Task 4 / Priority 2 (continued): company website links on page ---
    if not company_domain:
        company_domain = _company_domain_from_links(
            scrape_data.get('all_links', []), platform_domain
        )

    # --- Task 3: company email (filtered, domain-aware) ---
    company_email = _select_company_email(
        scrape_data.get('emails', []), platform_domain, company_domain
    )

    # --- Task 4 / Priority 3: company domain from the selected email ---
    if not company_domain and company_email and '@' in company_email:
        company_domain = company_email.split('@', 1)[1].lower()

    return {
        'company_name'   : company_name or None,
        'job_title'      : job_title or None,
        'company_email'  : company_email or None,
        'company_domain' : company_domain or None,
        'platform_domain': platform_domain or None
    }

