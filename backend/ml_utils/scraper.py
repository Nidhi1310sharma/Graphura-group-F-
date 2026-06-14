import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict


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
        'page_title'      : '',
        'meta_description': '',
        'body_text'       : '',
        'all_links'       : [],
        'emails'          : [],
        'phone_numbers'   : [],
        'scrape_success'  : False
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
            'page_title'      : page_title,
            'meta_description': meta_desc,
            'body_text'       : body_text,
            'all_links'       : all_links,
            'emails'          : emails,
            'phone_numbers'   : phone_numbers,
            'scrape_success'  : True
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

