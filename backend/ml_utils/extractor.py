#pip install pymupdf pytesseract pillow opencv-python
import fitz
from io import BytesIO
import cv2
import numpy as np
import pytesseract
from PIL import Image

# pytesseract.pytesseract.tesseract_cmd = (r"C:\Program Files\Tesseract-OCR\tesseract.exe")

import os
import shutil
import pytesseract

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
else:
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
print("Tesseract path:", shutil.which("tesseract"))
print("Configured path:", pytesseract.pytesseract.tesseract_cmd)

#pdf extractor
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF.
    Falls back to OCR for scanned/image-based pages.
    """

    extracted_text = []

    try:
        pdf = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        for page_num in range(len(pdf)):

            page = pdf[page_num]

            # Attempt normal extraction
            page_text = page.get_text("text").strip()

            # If enough text exists, use it
            if len(page_text) > 30:
                extracted_text.append(page_text)
                continue

            # OCR fallback
            pix = page.get_pixmap(
                matrix=fitz.Matrix(4, 4),  # higher resolution
                alpha=False
            )
            img = np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,11)
            ocr_text = pytesseract.image_to_string(thresh, lang="eng", config="--oem 3 --psm 6")
            print(f"Page {page_num+1}: OCR chars = {len(ocr_text)}")
            if ocr_text.strip():
                extracted_text.append(ocr_text)

        pdf.close()

        return "\n".join(extracted_text)

    except Exception as e:
        raise Exception(
            f"PDF extraction failed: {str(e)}"
        )

#image extractor        
def extract_text_from_image(
    image_bytes: bytes
) -> str:
    """
    Extract text from image using OCR.
    """

    try:
        np_img = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        text = pytesseract.image_to_string(thresh, lang="eng")
        return text.strip()

    except Exception as e:
        raise Exception(f"Image OCR failed: {str(e)}")

# ──────────────────────────────────────────────────────────────────────────
# METADATA EXTRACTION (additive — does not alter extract_text_from_pdf /
# extract_text_from_image above). Used for PDF, IMAGE and TEXT analysis only.
# URL metadata extraction (ml_utils/url_computation.py) is untouched.
# ──────────────────────────────────────────────────────────────────────────
import re

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

PREFERRED_EMAIL_PREFIXES = (
    "careers", "career", "hr", "jobs", "recruitment", "recruit",
    "talent", "hiring", "hello", "contact", "info"
)

GENERIC_EMAIL_PROVIDERS = {
    "gmail", "yahoo", "outlook", "hotmail", "rediffmail", "icloud", "protonmail", "live", "aol"
}

# Domain pattern: a label.label(.label) sequence not immediately preceded by
# "@" (so we don't pick up the domain half of an email address here).
DOMAIN_PATTERN = re.compile(
    r"(?<![\w.\-@])(?:https?://)?(?:www\.)?"
    r"([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,24}){1,3})"
)

GENERIC_SUBDOMAINS = {"www", "careers", "career", "jobs", "hr", "apply", "m", "mail", "recruit", "recruitment"}
CC_SECOND_LEVEL = {"co.in", "co.uk", "com.au", "co.za", "org.in", "net.in", "gov.in", "ac.in", "co.nz"}

PHONE_PATTERN = re.compile(
    r"(?:\+91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b"                       # Indian mobile (10 digits, optional 5+5 grouping)
    r"|\+\d{1,3}[\-\s]?\(?\d{2,4}\)?(?:[\-\s]?\d{2,4}){2,4}"          # international format
)

COMPANY_LABEL_PATTERN = re.compile(
    r"(?:Hiring\s*Company|Company|Employer|Organization|Organisation)\s*[:\-]\s*([^\n]{2,60})",
    re.IGNORECASE
)

TITLE_AT_COMPANY_PATTERN = re.compile(
    r"(?:Intern(?:ship)?|Engineer|Developer|Analyst|Designer|Manager|Executive)\s+(?:at|@|with|in)\s+"
    r"([A-Z][A-Za-z0-9&.\-' ]{1,40})"
)

COMPANY_HIRING_PATTERN = re.compile(
    r"\b(?!We\b|Now\b|This\b|Join\b|Apply\b|Currently\b|Urgently\b)"
    r"([A-Z][A-Za-z0-9&.\-' ]{1,40}?)\s+(?:is\s+)?[Hh]iring\b"
)

COMPANY_SUFFIX_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9&.\-' ]{1,40}\s+(?:Pvt\.?\s*Ltd\.?|Private\s+Limited|LLC|Inc\.?|Technologies|Solutions|Systems|Labs|Limited))\b"
)

JOB_ROLE_KEYWORDS = (
    "Intern", "Internship", "Engineer", "Developer", "Analyst",
    "Designer", "Manager", "Executive", "Specialist", "Associate"
)

JOB_TITLE_STOPWORDS = ("Hiring", "For", "Now", "Urgent", "Urgently", "Apply", "Join", "We", "Are", "Is", "The")

JOB_TITLE_PATTERN = re.compile(
    r"\b(?!(?:" + "|".join(JOB_TITLE_STOPWORDS) + r")\b)"
    r"([A-Z][A-Za-z\+\#/]*"
    r"(?:\s+(?!(?:" + "|".join(JOB_TITLE_STOPWORDS) + r")\b)[A-Z][A-Za-z\+\#/]*){0,4}"
    r"\s+(?:" + "|".join(JOB_ROLE_KEYWORDS) + r"))\b"
)

LABELLED_TITLE_PATTERN = re.compile(
    r"(?:Job\s*Title|Position|Role|Designation)\s*[:\-]\s*([^\n]{2,60})",
    re.IGNORECASE
)


def normalize_domain(raw: str) -> str:
    """Normalize a raw domain/URL fragment (e.g. 'https://careers.google.com/x')
    down to a clean root domain (e.g. 'google.com')."""
    d = raw.lower().strip()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0].split("?")[0].split("#")[0].strip(".")
    parts = [p for p in d.split(".") if p]
    if parts and parts[0] in GENERIC_SUBDOMAINS and len(parts) > 2:
        parts = parts[1:]
    if len(parts) > 2:
        last_two = ".".join(parts[-2:])
        if last_two in CC_SECOND_LEVEL:
            return ".".join(parts[-3:])
        return last_two
    return ".".join(parts)


def extract_emails(text: str) -> list:
    """Find every email address in the full text (not just lines labelled 'Email:')."""
    if not text:
        return []
    seen, emails = set(), []
    for m in EMAIL_PATTERN.finditer(text):
        e = m.group(0)
        key = e.lower()
        if key not in seen:
            seen.add(key)
            emails.append(e)
    return emails


def pick_company_email(emails: list) -> str:
    """Prefer recruiter-style addresses (careers@, hr@, jobs@, recruitment@...)."""
    if not emails:
        return None
    for e in emails:
        local = e.split("@")[0].lower()
        if any(local.startswith(p) for p in PREFERRED_EMAIL_PREFIXES):
            return e
    return emails[0]


def extract_domains(text: str) -> list:
    """Find every standalone domain/website mention in the full text (watermarks,
    headers, footers, banners — not just lines labelled 'Website:')."""
    if not text:
        return []
    seen, domains = set(), []
    for m in DOMAIN_PATTERN.finditer(text):
        end = m.end()
        if end < len(text) and text[end] == "@":
            continue  # this was the local-part of an email address, not a domain
        d = normalize_domain(m.group(0))
        if "." in d and d not in seen:
            seen.add(d)
            domains.append(d)
    return domains


def extract_phone(text: str):
    if not text:
        return None
    for m in PHONE_PATTERN.finditer(text):
        candidate = m.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        if 7 <= len(digits) <= 15:
            return candidate
    return None


def extract_job_title(text: str):
    if not text:
        return None
    # Priority: explicit "Job Title:" / "Position:" / "Role:" / "Designation:" label
    m = LABELLED_TITLE_PATTERN.search(text)
    if m:
        return m.group(1).strip(" .:-")
    # Scan lines top-down (OCR text has no font-size info, so earlier lines are
    # treated as the closest approximation of "largest heading" / "main title")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:40]:
        m = JOB_TITLE_PATTERN.search(line)
        if m:
            return m.group(1).strip()
    m = JOB_TITLE_PATTERN.search(text)
    if m:
        return m.group(1).strip()
    return None


def extract_company_name(text: str, company_email: str = None, company_domain: str = None):
    if not text:
        text = ""
    # Priority 1: explicit label
    m = COMPANY_LABEL_PATTERN.search(text)
    if m:
        return m.group(1).strip(" .:-")
    # Priority 2: job posting title patterns ("X Intern at Company" / "Company Hiring X")
    m = TITLE_AT_COMPANY_PATTERN.search(text)
    if m:
        return m.group(1).strip(" .:-")
    m = COMPANY_HIRING_PATTERN.search(text)
    if m:
        return m.group(1).strip(" .:-")
    # Priority 3: recruitment footer info (legal-suffix company mentions)
    m = COMPANY_SUFFIX_PATTERN.search(text)
    if m:
        return m.group(1).strip(" .:-")
    # Priority 4: infer from email domain (skip generic providers like gmail)
    if company_email:
        local_provider = company_email.split("@")[-1].split(".")[0].lower()
        if local_provider not in GENERIC_EMAIL_PROVIDERS:
            return local_provider.capitalize()
    # Priority 5: infer from website domain
    if company_domain:
        name = company_domain.split(".")[0]
        if name:
            return name.capitalize()
    # Priority 4 fallback: use the email anyway if no domain was found
    if company_email:
        name = company_email.split("@")[-1].split(".")[0]
        if name:
            return name.capitalize()
    # Priority 6: large OCR heading / logo / banner text — best effort using the
    # first short, title-cased line of the extracted text
    for line in text.splitlines():
        line = line.strip()
        if line:
            words = line.split()
            if 1 <= len(words) <= 5 and line[0].isupper():
                return line
        break
    return None


def extract_metadata(raw_text: str, source_type: str = "Text") -> dict:
    """
    Extract recruiter/company metadata from raw extracted text for PDF,
    IMAGE and TEXT analysis. Searches the FULL text (not just labelled
    lines) so values inside watermarks, headers, footers, logos, posters,
    flyers and banners are still picked up.

    Returns: company_name, job_title, company_email, company_domain,
    phone_number, source_type. Any field that can't be determined is
    returned as None (the frontend renders missing values as "Unknown").
    """
    text = raw_text or ""

    emails = extract_emails(text)
    company_email = pick_company_email(emails)

    domains = extract_domains(text)
    company_domain = None
    if company_email:
        email_domain = normalize_domain(company_email.split("@")[-1])
        local_provider = email_domain.split(".")[0]
        if local_provider not in GENERIC_EMAIL_PROVIDERS:
            company_domain = email_domain
    if not company_domain and domains:
        company_domain = domains[0]

    phone_number = extract_phone(text)
    company_name = extract_company_name(text, company_email=company_email, company_domain=company_domain)
    job_title = extract_job_title(text)

    return {
        "company_name": company_name,
        "job_title": job_title,
        "company_email": company_email,
        "company_domain": company_domain,
        "phone_number": phone_number,
        "source_type": source_type,
    }
