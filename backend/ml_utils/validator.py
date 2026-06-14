from urllib.parse import urlparse
import tldextract
import datetime, time
import requests
import whois

# --- Request settings ---
REQUEST_TIMEOUT = 10   # seconds
REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

# STEP 2: URL VALIDATION

def validate_url(url: str) -> bool:
    """
    Validate that the input string is a well-formed HTTP/HTTPS URL.

    Parameters
    ----------
    url : str
        Raw URL string to validate.

    Returns
    -------
    bool
        True if the URL is structurally valid, False otherwise.
    """
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        parsed = urlparse(url.strip())
        # Scheme must be http or https
        if parsed.scheme not in ('http', 'https'):
            return False
        # Network location (domain) must be present
        if not parsed.netloc:
            return False
        # Domain must contain at least one dot
        if '.' not in parsed.netloc:
            return False
        return True
    except Exception:
        return False

# STEP 3: EXTRACT DOMAIN INFORMATION

def extract_domain_info(url: str) -> dict:
    """
    Decompose a URL into subdomain, domain, suffix and full_domain.

    Returns a dict with keys: subdomain, domain, suffix, full_domain.
    Returns empty strings on failure.
    """
    try:
        extracted   = tldextract.extract(url)
        subdomain   = extracted.subdomain  or ''
        domain      = extracted.domain    or ''
        suffix      = extracted.suffix    or ''
        # Build clean full_domain — omit empty subdomain
        parts       = [p for p in [subdomain, domain, suffix] if p]
        full_domain = '.'.join(parts)
        return {
            'subdomain'  : subdomain,
            'domain'     : domain,
            'suffix'     : suffix,
            'full_domain': full_domain
        }
    except Exception as e:
        return {'subdomain': '', 'domain': '', 'suffix': '', 'full_domain': ''}

# STEP 4: HTTPS ANALYSIS

def check_https(url: str) -> bool:
    """
    Return True if the URL uses HTTPS, False if HTTP.
    """
    try:
        return urlparse(url.strip()).scheme.lower() == 'https'
    except Exception:
        return False

# STEP 5: DOMAIN AGE ANALYSIS (WHOIS)

def get_domain_age(url: str) -> dict:
    """
    Perform WHOIS lookup and return domain registration metadata.

    Returns
    -------
    dict with keys:
        creation_date    : str  (ISO format) or 'Unknown'
        domain_age_days  : int  or -1 if lookup failed
        domain_age_risk  : str  'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN'
    """
    domain_info = extract_domain_info(url)
    root_domain = f"{domain_info['domain']}.{domain_info['suffix']}"

    try:
        w = whois.whois(root_domain)
        creation = w.creation_date

        # creation_date can be a list — take the earliest
        if isinstance(creation, list):
            creation = min(
                [d for d in creation if isinstance(d, datetime)],
                default=None
            )

        if creation is None or not isinstance(creation, datetime):
            return {'creation_date': 'Unknown',
                    'domain_age_days': -1,
                    'domain_age_risk': 'UNKNOWN'}

        # Normalise timezone — strip tz info for naive comparison
        now = datetime.now()
        if creation.tzinfo is not None:
            creation = creation.replace(tzinfo=None)

        age_days = (now - creation).days

        if age_days < 30:
            risk = 'HIGH'
        elif age_days < 180:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'

        return {
            'creation_date'  : creation.strftime('%Y-%m-%d'),
            'domain_age_days': age_days,
            'domain_age_risk': risk
        }

    except Exception as e:
        return {'creation_date': 'Unknown',
                'domain_age_days': -1,
                'domain_age_risk': 'UNKNOWN'}

# STEP 6: SUSPICIOUS TLD DETECTION

SUSPICIOUS_TLDS = {
    'xyz', 'top', 'click', 'online', 'site', 'live',
    'shop', 'buzz', 'work', 'loan', 'win', 'gq',
    'ml', 'cf', 'tk', 'ga', 'pw', 'cc', 'biz',
    'info', 'mobi', 'name', 'pro', 'link', 'space',
    'website', 'press', 'rocks', 'fun', 'icu'
}

def check_suspicious_tld(url: str) -> dict:
    """
    Check whether the URL's TLD appears in the suspicious TLD list.

    Returns
    -------
    dict with keys:
        suffix          : str  — actual TLD found
        suspicious_tld  : int  — 1 if suspicious, 0 if safe
    """
    domain_info = extract_domain_info(url)
    # Take only the final component for multi-part TLDs (e.g. 'co.uk' → 'uk')
    suffix      = domain_info.get('suffix', '').lower()
    final_tld   = suffix.split('.')[-1] if suffix else ''
    is_suspicious = 1 if final_tld in SUSPICIOUS_TLDS else 0
    return {
        'suffix'        : suffix,
        'suspicious_tld': is_suspicious
    }
    
# STEP 7: WEBSITE AVAILABILITY CHECK

def check_website_availability(url: str) -> dict:
    """
    Attempt an HTTP GET to the URL and return availability info.

    Returns
    -------
    dict with keys:
        status_code       : int   — HTTP status or -1 on failure
        website_reachable : bool  — True if status 200-399
        response_time_ms  : float — round-trip time in ms
        error_message     : str   — '' on success, error text on failure
    """
    try:
        start    = time.time()
        response = requests.get(
            url,
            headers = REQUEST_HEADERS,
            timeout = REQUEST_TIMEOUT,
            allow_redirects = True
        )
        elapsed  = round((time.time() - start) * 1000, 2)
        reachable = 200 <= response.status_code < 400
        return {
            'status_code'      : response.status_code,
            'website_reachable': reachable,
            'response_time_ms' : elapsed,
            'error_message'    : ''
        }
    except requests.exceptions.SSLError:
        return {'status_code': -1, 'website_reachable': False,
                'response_time_ms': 0, 'error_message': 'SSL certificate error'}
    except requests.exceptions.ConnectionError:
        return {'status_code': -1, 'website_reachable': False,
                'response_time_ms': 0, 'error_message': 'Connection refused or DNS failure'}
    except requests.exceptions.Timeout:
        return {'status_code': -1, 'website_reachable': False,
                'response_time_ms': 0, 'error_message': f'Request timed out after {REQUEST_TIMEOUT}s'}
    except Exception as e:
        return {'status_code': -1, 'website_reachable': False,
                'response_time_ms': 0, 'error_message': str(e)}

