import fitz
import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
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

# --- 1. Extraction Functions (PDF & Image) ---

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
    combined = text_native + "\n" + text_ocr
    lines = list(dict.fromkeys(combined.splitlines()))
    return "\n".join(lines)

def extract_text_from_image(image_path_or_obj) -> str:
    try:
       
        if not isinstance(image_path_or_obj, str):
            img = Image.open(image_path_or_obj) 
        else:
            img = Image.open(image_path_or_obj)
        return pytesseract.image_to_string(img)
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""

# --- 2. OCR Cleanup ---

# --- Helper functions for entity extraction ---

def extract_company_name(text: str) -> str:
    
    return "Unknown" 

def extract_job_title(text: str) -> str:
   
    return "Unknown"

def extract_job_description(text: str) -> str:
   
    return text[:200] if len(text) > 200 else "Description unavailable"

def extract_emails(text: str) -> list:
    email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)

def extract_domains(text: str) -> list:
    domain_pattern = r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}'
    return re.findall(domain_pattern, text)

def extract_phone(text: str) -> str:
    phone_pattern = r'(?:\+91[\-\s]?)?[6-9]\d{9}'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else None

def pick_company_email(emails: list) -> str:
    return emails[0] if emails else None

# --- 3. Unified Entity Extractor & Validation ---

def validate_field(value: str) -> str:
    if not value or value in ["1", "123", "N/A", "Unknown"] or len(value) < 3 or value.isdigit():
        return None
    return value

def extract_metadata(raw_text: str, source_type: str = "Text") -> dict:
    text = clean_ocr_text(raw_text)
    
    # Placeholder functions (ensure these exist in your project)
    company_name = validate_field(extract_company_name(text))
    job_description = extract_job_description(text)
    
    metadata = {
        "company_name": company_name,
        "job_title": extract_job_title(text),
        "company_email": pick_company_email(extract_emails(text)),
        "company_website": None,
        "company_domain": extract_domains(text)[0] if extract_domains(text) else None,
        "platform_domain": None,
        "phone_number": extract_phone(text),
        "job_description": job_description,
        "extraction_confidence": 0.8,
        "completeness_score": 0
    }
    # Calculate score after creating dictionary
    metadata["completeness_score"] = calculate_internal_completeness(metadata)
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
