import fitz
import cv2
import numpy as np
import pytesseract
import os
import shutil
import re

# --- Configuration & Setup ---
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

# --- 1. Hybrid PDF Extraction (Per Section 4 of Spec) ---

def extract_pdf_text_pymupdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text

def extract_pdf_text_ocr(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        text += pytesseract.image_to_string(img) + "\n"
    return text

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_native = extract_pdf_text_pymupdf(pdf_bytes)
    text_ocr = extract_pdf_text_ocr(pdf_bytes)
    # Merge and simple deduplication
    combined = text_native + "\n" + text_ocr
    lines = list(dict.fromkeys(combined.splitlines()))
    return "\n".join(lines)

# --- 2. OCR Cleanup (Per Section 3 of Spec) ---

def clean_ocr_text(text: str) -> str:
    # Normalize common mistakes
    replacements = {"Go0gle": "Google", "Micr0soft": "Microsoft", "lnternship": "Internship"}
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove random symbols/broken lines
    text = re.sub(r'[^\w\s@\.\-]', '', text)
    return text

# --- 3. Unified Entity Extractor & Validation (Per Section 5 & 6) ---

def validate_field(value: str) -> str:
    """Reject dummy data."""
    if not value or value in ["1", "123", "N/A", "Unknown"] or len(value) < 3 or value.isdigit():
        return None
    return value

def extract_metadata(raw_text: str, source_type: str = "Text") -> dict:
    text = clean_ocr_text(raw_text)
    
    # ... (Keep existing extraction logic for company_name, job_title, etc.) ...
    
    # New requirements from spec:
    company_name = validate_field(extract_company_name(text))
    job_description = extract_job_description(text) # New function needed here
    
    metadata = {
        "company_name": company_name,
        "job_title": extract_job_title(text),
        "company_email": pick_company_email(extract_emails(text)),
        "company_website": None, # Extract using domain logic
        "company_domain": extract_domains(text)[0] if extract_domains(text) else None,
        "platform_domain": None,
        "phone_number": extract_phone(text),
        "job_description": job_description,
        "extraction_confidence": 0.8, # Placeholder for your model confidence
        "completeness_score": 0
    }
    return metadata
    def calculate_internal_completeness(meta: dict) -> int:

    weights = {
        "company_name": 25, 
        "job_title": 20, 
        "job_description": 20, 
        "company_email": 10, 
        "company_domain": 10, 
        "phone_number": 10,
        "extraction_confidence": 5
    }
    
    total_score = 0
    for field, weight in weights.items():
        if meta.get(field): 
            total_score += weight
            
    return total_score


