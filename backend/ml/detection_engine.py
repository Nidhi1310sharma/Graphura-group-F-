import joblib
import numpy as np
import re
import backend.ml_utils.helpers as helpers
import backend.ml_utils.explain as explain
import backend.ml_utils.recommendation as rec
import backend.ml.feature_engineering as fe
import backend.ml.nlp_analyzer as nlp

MODEL_PATH        = "backend/models/best_scam_detector.pkl"
FEATURE_NAMES_PATH = "backend/models/feature_names.pkl"
model = joblib.load(MODEL_PATH)
feature_names = joblib.load(FEATURE_NAMES_PATH)


#  STEP 14 : JSON Response Generator

def analyze_job(raw_text: str) -> dict:
    """
    Full pipeline: raw text → structured JSON fraud analysis.

    Parameters
    ----------
    raw_text : str
        Any text input — job description, URL content,
        OCR output, or offer letter text.

    Returns
    -------
    dict
        Complete fraud analysis response.
    """
    # ── 1. ML Prediction ──────────────────────────────────────
    ml_result = helpers.get_ml_prediction(raw_text)

    # ── 2. Rule-Based Scoring ─────────────────────────────────
    rule_result = fe.compute_rule_score(raw_text)

    # ── 3. Hybrid Risk Score ──────────────────────────────────
    final_risk = helpers.compute_hybrid_risk(
        rule_score     = rule_result["rule_score"],
        ml_probability = ml_result["ml_probability"]
    )

    # ── 4. Risk Level ─────────────────────────────────────────
    risk_level = helpers.classify_risk(final_risk)

    # ── 5. Trust Score ────────────────────────────────────────
    trust = helpers.compute_trust(final_risk)

    # ── 6. Explainability ─────────────────────────────────────
    reasons = explain.generate_fraud_reasons(raw_text, final_risk)

    # ── 7. Recommendation ─────────────────────────────────────
    recommendation = rec.get_recommendation(risk_level, final_risk)

    # ── 8. Trust Card Metrics ──────────────────────────────────
    try:
        card_metrics = build_trust_card_metrics(raw_text)
    except Exception as e:
        print("CARD METRICS ERROR:", e)
        card_metrics = {}
    # ── 9. Assemble Response ──────────────────────────────────
    return {
        "risk_score"        : final_risk,
        "risk_level"        : risk_level,
        "trust_score"       : trust["trust_score"],
        "trust_level"       : trust["trust_level"],
        "ml_prediction"     : ml_result["ml_prediction"],
        "ml_probability"    : ml_result["ml_probability"],
        "rule_score"        : rule_result["rule_score"],
        "fraud_reasons"     : reasons,
        "recommended_action": recommendation,
        "card_metrics"      : card_metrics
    }

def build_trust_card_metrics(raw_text: str) -> dict:
    """
    Build UI metrics for trust card display.
    Does not affect ML prediction.
    """
    fe_features = fe.generate_engineered_features(raw_text)
    nlp_features = nlp.generate_nlp_features(raw_text)
    return {
        "Fraud Phrases": min(fe_features["fraud_phrase_score"] * 10, 100),
        "Urgency":min(fe_features["urgency_score"] * 15, 100),
        "Contact Risk":min(fe_features["contact_risk_score"] * 20, 100),
        "Readability":max(0,min(int(nlp_features["readability_score"]),100)),
        "Language Quality":min(int(nlp_features["lexical_diversity"] * 100),100)
    }