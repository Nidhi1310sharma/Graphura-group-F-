#pip install pymupdf pytesseract pillow opencv-python
import fitz
from io import BytesIO
import cv2
import numpy as np
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = (r"C:\Program Files\Tesseract-OCR\tesseract.exe")

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