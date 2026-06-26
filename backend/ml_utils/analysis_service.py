from fastapi import HTTPException

from backend.ml_utils.extractor import extract_text_from_pdf, extract_text_from_image, extract_metadata

from backend.ml.detection_engine import analyze_job
from backend.ml.url_engine import analyze_url

from backend.supabase_client import supabase

## This module provides the main analysis service for the application.
# analyze_content function handles the extraction of text from various sources (URL, TEXT, PDF, IMAGE),
# performs analysis using the detection engine, and saves the results to the database.
# All paths produce a unified frontend card shape:
#   risk_score, risk_label, trust_score, trust_label, metrics, display_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _risk_label(score: int) -> str:
    """Convert a numeric risk score (0-100) to a human-readable label."""
    if score < 30:
        return "LOW"
    if score < 70:
        return "MEDIUM"
    return "HIGH"


def _trust_label(trust_score: int) -> str:
    """Convert a numeric trust score (0-100) to a human-readable label."""
    if trust_score >= 70:
        return "HIGH"
    if trust_score >= 30:
        return "MEDIUM"
    return "LOW"


def _build_job_metrics(raw: dict) -> dict:
    """
    Build the frontend metrics dict from an analyze_job() result.

    analyze_job() is expected to return keys such as:
      - risk_score          (int, 0-100)
      - fraud_reasons       (list[str])
      - signal_scores       (dict[str, int], optional)  e.g. {"Urgency": 80, ...}
      - recommended_action  (str, optional)

    Adjust the key names below if your detection engine uses different ones.
    """
    signal_scores: dict = raw.get("signal_scores") or {}

    metrics = {
        "Urgency Language":     signal_scores.get("urgency", 0),
        "Vague Job Details":    signal_scores.get("vague_details", 0),
        "Unrealistic Pay":      signal_scores.get("unrealistic_pay", 0),
        "Contact Red Flags":    signal_scores.get("contact_flags", 0),
        "Credential Requests":  signal_scores.get("credential_requests", 0),
    }
    return metrics


def _build_job_display_data(raw: dict, metadata: dict, source_type: str) -> dict:
    """
    Build the display_data block shown on the frontend card for TEXT/PDF/IMAGE.
    """
    return {
        "source_type":        source_type,
        "job_title":          metadata.get("job_title"),
        "company":            metadata.get("company"),
        "location":           metadata.get("location"),
        "fraud_reasons":      raw.get("fraud_reasons") or [],
        "recommended_action": raw.get("recommended_action", "Review carefully before proceeding."),
    }


def _domain_age_score(domain_age_days: int) -> int:
    """Convert domain age in days to a 0-100 score."""
    if domain_age_days > 365:
        return 100
    if domain_age_days > 0:
        return int((domain_age_days / 365) * 100)
    return 0


def _company_verification_label(verification_status: str | None) -> str:
    """
    Map a raw verification_status string from the URL engine to a
    frontend-friendly label.

    Expected raw values (case-insensitive): "verified", "unverified",
    "partial", "unknown". Any unrecognised value maps to "Unknown".
    """
    if not verification_status:
        return "Unknown"
    mapping = {
        "verified":   "Verified",
        "unverified": "Unverified",
        "partial":    "Partially Verified",
        "unknown":    "Unknown",
    }
    return mapping.get(verification_status.lower(), verification_status.title())


def _build_url_metrics(url_result: dict) -> dict:
    """
    Build the frontend metrics dict from an analyze_url() result.

    Signals (all expressed as 0-100 trust/quality scores so that higher = safer,
    consistent with how the job-analysis metrics work):

      Domain Risk         – inverse of domain_risk_score
      Content Risk        – inverse of content_risk_score
      Company Verification– derived from company_verification_score when
                            present, otherwise from verification_adjustment
      Domain Reputation   – domain_reputation_score (already 0-100 trust score)
      HTTPS               – 100 if https_enabled else 0
      Domain Age          – proportional to domain_age_days (capped at 1 year)

    "Domain Security" and "Content Safety" from the old model are replaced by
    "Domain Risk" and "Content Risk" respectively, which map to the same
    underlying fields but use the updated naming convention.
    """
    # --- Company Verification ---
    # Prefer an explicit 0-100 score from the engine; fall back to
    # verification_adjustment (a signed int offset, e.g. +10 / -20) mapped
    # to a 0-100 scale, or 50 (neutral) when nothing is available.
    company_verification_score: int | None = url_result.get("company_verification_score")
    if company_verification_score is None:
        adjustment: int = url_result.get("verification_adjustment", 0) or 0
        # adjustment range assumed ±30; shift to 0-100 centred on 50
        company_verification_score = max(0, min(100, 50 + adjustment))

    # --- Domain Reputation ---
    # domain_reputation_score is expected to already be a 0-100 trust score.
    domain_reputation_score: int = int(
        url_result.get("domain_reputation_score", 50) or 50
    )

    return {
        "Domain Risk":          max(0, 100 - int(url_result.get("domain_risk_score",  100))),
        "Content Risk":         max(0, 100 - int(url_result.get("content_risk_score", 100))),
        "Company Verification": max(0, min(100, int(company_verification_score))),
        "Domain Reputation":    max(0, min(100, domain_reputation_score)),
        "HTTPS":                100 if url_result.get("https_enabled") else 0,
        "Domain Age":           _domain_age_score(int(url_result.get("domain_age_days", 0) or 0)),
    }


def _build_url_display_data(url_result: dict) -> dict:
    """
    Build the display_data block for URL analysis.

    Exposes all frontend-useful fields so the card layer never has to reach
    into raw_url_analysis to assemble UI state.
    """
    risk_score:  int = int(url_result.get("final_url_risk_score", 0))
    trust_score: int = max(0, 100 - risk_score)

    # Company verification
    verification_status: str | None = url_result.get("verification_status")
    verification_label:  str        = _company_verification_label(verification_status)
    verification_adjustment: int | None = url_result.get("verification_adjustment")

    # Domain reputation
    domain_reputation_score: int | None = url_result.get("domain_reputation_score")
    domain_reputation_label: str | None = url_result.get("domain_reputation_label")  # engine may supply this

    return {
        # --- identification ---
        "source_type":               "URL",

        # --- risk summary ---
        "fraud_reasons":             url_result.get("url_risk_reasons") or [],
        "recommended_action":        url_result.get("recommended_action", "Review carefully before proceeding."),
        "risk_label":                _risk_label(risk_score),
        "trust_label":               _trust_label(trust_score),

        # --- company verification ---
        "verification_status":       verification_status,
        "verification_label":        verification_label,
        "verification_adjustment":   verification_adjustment,

        # --- domain reputation ---
        "domain_reputation_score":   domain_reputation_score,
        "domain_reputation_label":   domain_reputation_label,

        # --- passthrough for any extra fields the engine may add ---
        "raw_url_analysis":          url_result,
    }


def _normalize_job_result(raw: dict, metadata: dict, source_type: str) -> dict:
    """
    Combine raw analyze_job() output + metadata into the unified frontend shape.
    """
    risk_score:  int = int(raw.get("risk_score", 0))
    trust_score: int = max(0, 100 - risk_score)

    return {
        # --- core scores (also persisted to DB) ---
        "risk_score":   risk_score,
        "risk_label":   _risk_label(risk_score),
        "trust_score":  trust_score,
        "trust_label":  _trust_label(trust_score),
        # kept for DB compatibility (save_analysis reads "fraud_reasons")
        "fraud_reasons": raw.get("fraud_reasons") or [],
        # --- frontend card data ---
        "metrics":      _build_job_metrics(raw),
        "display_data": _build_job_display_data(raw, metadata, source_type),
    }


def _normalize_url_result(url_result: dict) -> dict:
    """
    Transform raw analyze_url() output into the unified frontend shape.
    """
    risk_score:  int = int(url_result.get("final_url_risk_score", 0))
    trust_score: int = max(0, 100 - risk_score)

    return {
        # --- core scores (also persisted to DB) ---
        "risk_score":   risk_score,
        "risk_label":   _risk_label(risk_score),
        "trust_score":  trust_score,
        "trust_label":  _trust_label(trust_score),
        # kept for DB compatibility (save_analysis reads "fraud_reasons")
        "fraud_reasons": url_result.get("url_risk_reasons") or [],
        # --- frontend card data ---
        "metrics":      _build_url_metrics(url_result),
        "display_data": _build_url_display_data(url_result),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_content(
    source_type: str,
    user_id: str | None = None,
    content: str = None,
    file_bytes: bytes = None,
    url: str = None,
) -> dict:
    """
    Extract text from the given source, run analysis, and return a unified
    frontend card dict.

    Returns:
        {
            "risk_score":   int,        # 0-100
            "risk_label":   str,        # LOW | MEDIUM | HIGH
            "trust_score":  int,        # 0-100
            "trust_label":  str,        # LOW | MEDIUM | HIGH
            "fraud_reasons": list[str], # kept for DB / legacy consumers
            "metrics":      dict,       # per-signal scores for card gauges
            "display_data": dict,       # rich card display fields
        }
    """
    if source_type == "TEXT":
        metadata = extract_metadata(content, source_type="Text")
        raw      = analyze_job(content)
        raw.update(metadata)
        result   = _normalize_job_result(raw, metadata, source_type)

    elif source_type == "PDF":
        text = extract_text_from_pdf(file_bytes)
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. The PDF may contain only images.",
            )
        metadata = extract_metadata(text, source_type="PDF")
        raw      = analyze_job(text)
        raw.update(metadata)
        result   = _normalize_job_result(raw, metadata, source_type)

    elif source_type == "IMAGE":
        text     = extract_text_from_image(file_bytes)
        metadata = extract_metadata(text, source_type="Image")
        raw      = analyze_job(text)
        raw.update(metadata)
        result   = _normalize_job_result(raw, metadata, source_type)

    elif source_type == "URL":
        url_result = analyze_url(url)
        result     = _normalize_url_result(url_result)

    else:
        raise ValueError(f"Unsupported source type: {source_type}")

    # Persist to DB then return the full frontend shape
    await save_analysis(
        user_id=user_id,
        source_type=source_type,
        result=result,
    )

    return result


async def save_analysis(user_id, source_type, result) -> dict | None:
    """Persist core analysis fields to the 'analysis' table."""
    analysis_data = {
        "user_id":      user_id,
        "input_source": source_type,
        "risk_score":   result["risk_score"],
        "risk_level":   result["risk_label"],   # DB column stays "risk_level"
        "trust_score":  result["trust_score"],
        "trust_level":  result["trust_label"],  # DB column stays "trust_level"
        "summary":      result["fraud_reasons"],
    }

    response = (
        supabase.table("analysis")
        .insert(analysis_data)
        .execute()
    )

    return response.data[0] if response.data else None