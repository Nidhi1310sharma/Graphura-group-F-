# ============================================================
# utils/helpers.py - Common Helper Functions
# ============================================================
import re
from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """Extract clean domain from a URL."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except Exception:
        return url.replace("https://", "").replace("http://", "").split("/")[0]


def clean_text(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_salary(salary_text: str) -> float:
    """Extract numeric salary value from text string."""
    if not salary_text:
        return 0.0
    nums = re.findall(r"\d[\d,]*", salary_text.replace(" ", ""))
    if not nums:
        return 0.0
    try:
        val = float(nums[0].replace(",", ""))
        if "lakh" in salary_text.lower():
            val *= 100000
        elif "k" in salary_text.lower():
            val *= 1000
        return val
    except ValueError:
        return 0.0
