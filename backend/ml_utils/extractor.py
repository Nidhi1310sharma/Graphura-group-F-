#pip install pymupdf pytesseract pillow opencv-python
import fitz
from io import BytesIO
import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (r"C:\Program Files\Tesseract-OCR\tesseract.exe")

#pdf extractor
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from uploaded PDF.
    Args:
        pdf_bytes: PDF file content
    Returns:
        Extracted text
    """

    text = []
    try:
        pdf = fitz.open(
            stream=BytesIO(pdf_bytes), filetype="pdf"
        )
        for page in pdf:
            page_text = page.get_text()

            if page_text:
                text.append(page_text)

        pdf.close()

        return "\n".join(text)

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