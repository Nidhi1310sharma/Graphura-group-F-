from fastapi import HTTPException

from backend.ml_utils.extractor import extract_text_from_pdf, extract_text_from_image, extract_metadata

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

        metadata = extract_metadata(content, source_type="Text")
        result = analyze_job(content)
        result.update(metadata)

    elif source_type == "PDF":

        text = extract_text_from_pdf(file_bytes)
        if not text or not text.strip():
            raise HTTPException(
        status_code=400,
        detail="Could not extract text from PDF. The PDF may contain only images."
    )
        metadata = extract_metadata(text, source_type="PDF")
        result = analyze_job(text)
        result.update(metadata)

    elif source_type == "IMAGE":

        text = extract_text_from_image(file_bytes)
        metadata = extract_metadata(text, source_type="Image")
        result = analyze_job(text)
        result.update(metadata)

    elif source_type == "URL":

        url_result = analyze_url(url)

        result = {
            "risk_score": url_result["final_url_risk_score"],
            "risk_level": url_result["final_risk_level"],
            "trust_score":max(0, 100 - url_result["final_url_risk_score"]),
            "trust_level":
                "HIGH"
                if url_result["final_url_risk_score"] < 30
                else "MEDIUM"
                if url_result["final_url_risk_score"] < 70
                else "LOW",
            "fraud_reasons":url_result["url_risk_reasons"],
            "recommended_action":url_result["recommended_action"],
            "raw_url_analysis":url_result,
            "raw_url_analysis": url_result,
            "url_card_metrics": {
                "Domain Security":max( 0, 100 - url_result["domain_risk_score"]),
                "HTTPS":100 if url_result["https_enabled"] 
                            else 0,
                "Domain Age":100 if url_result["domain_age_days"] > 365
                    else int(
                        (url_result["domain_age_days"] / 365) * 100 )
                            if url_result["domain_age_days"] > 0
                            else 0,
                "Content Safety":max(0,100 - url_result["content_risk_score"])
            }
        }
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