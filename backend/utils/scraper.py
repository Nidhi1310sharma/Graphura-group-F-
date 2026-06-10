# ============================================================
# utils/scraper.py - Web Scraping Utilities
# Uses requests + BeautifulSoup for basic page scraping.
# ============================================================
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from backend.utils.helpers import clean_text, extract_domain

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def scrape_job_page(url: str) -> Optional[Dict]:
    """
    Scrape basic job info from a URL.
    Works best on small company career pages.
    Major sites (LinkedIn, Internshala) require their official APIs.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        title = None
        for selector in ["h1", ".job-title", ".position-title"]:
            el = soup.select_one(selector)
            if el:
                title = el.get_text(strip=True)
                break
        desc = None
        for selector in [".job-description", ".description", "article", "main"]:
            el = soup.select_one(selector)
            if el:
                desc = clean_text(el.get_text())
                break
        if not desc:
            desc = clean_text(soup.get_text())[:3000]
        return {"title": title, "description": desc, "domain": extract_domain(url), "source_url": url}
    except Exception:
        return None
