from fastapi import HTTPException

from backend.ml_utils.extractor import extract_text_from_pdf, extract_text_from_image

from backend.ml.detection_engine import analyze_job
from backend.ml.url_engine import analyze_url

from backend.supabase_client import supabase

## This module provides the main analysis service for the application.
# analyze_content function handles the extraction of text from various sources (URL, TEXT, PDF, IMAGE), 
# performs analysis using the detection engine, and saves the results to the database.

async def analyze_content(
    source_type: str,
    user_id: str | None = None,
    content: str = None,
    file_bytes: bytes = None,
    url: str = None
):
    if source_type == "TEXT":

        result = analyze_job(content)

    elif source_type == "PDF":

        text = extract_text_from_pdf(file_bytes)
        if not text or not text.strip():
            raise HTTPException(
        status_code=400,
        detail="Could not extract text from PDF. The PDF may contain only images."
    )
        result = analyze_job(text)

    elif source_type == "IMAGE":

        text = extract_text_from_image(file_bytes)
        result = analyze_job(text)

    elif source_type == "URL":

        result = analyze_url(url)


    else:
        raise ValueError(f"Unsupported source type: {source_type}")
    # save
    await save_analysis(
        user_id=user_id,
        source_type=source_type,
        result=result
    )

    return result


async def save_analysis( user_id, source_type, result):
    analysis_data = {
    "user_id": user_id,
    "input_source": source_type,
    "risk_score": result["risk_score"],
    "risk_level": result["risk_level"],
    "trust_score": result["trust_score"],
    "trust_level": result["trust_level"],
    "summary": result["fraud_reasons"]
}       
    response=( supabase.table("analysis") 
    .insert(analysis_data) 
    .execute())
    
    return response.data[0] if response.data else None