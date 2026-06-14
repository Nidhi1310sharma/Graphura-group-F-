import numpy as np
import re
import backend.ml.nlp_analyzer as nlp
import backend.ml.feature_engineering as fe
import joblib

MODEL_PATH        = "backend/models/best_scam_detector.pkl"
FEATURE_NAMES_PATH = "backend/models/feature_names.pkl"
model = joblib.load(MODEL_PATH)
feature_names = joblib.load(FEATURE_NAMES_PATH)

# model features generator, ML predictor, hybrid analysis engine
#Risk classifier and trust classifier 

#  STEP 6 : Model Input Generator

def build_model_input(text: str) -> np.ndarray:
    """
    Convert raw text into a feature array aligned with training.

    Parameters
    ----------
    text : str
        Raw input text from any source.

    Returns
    -------
    np.ndarray, shape (1, n_features)
        Feature vector ready for model.predict / predict_proba.
    """
    # Gather all computed features
    nlp_feats = nlp.generate_nlp_features(text)
    eng_feats = fe.generate_engineered_features(text)

    all_features = {**nlp_feats, **eng_feats}

    # Align to training feature order — missing keys → 0
    ordered_values = [
        all_features.get(fname, 0) for fname in feature_names
    ]

    return np.array(ordered_values).reshape(1, -1)


#  STEP 7 : ML Prediction Generator

def get_ml_prediction(text: str) -> dict:
    """
    Run ML inference on raw input text.

    Parameters
    ----------
    text : str
        Raw input text.

    Returns
    -------
    dict
        ml_prediction (int) and ml_probability (float).
    """
    X = build_model_input(text)

    ml_prediction   = int(model.predict(X)[0])

    # predict_proba returns [[prob_class_0, prob_class_1]]
    proba_array     = model.predict_proba(X)[0]
    ml_probability  = round(float(proba_array[1]), 4)   # scam probability

    return {
        "ml_prediction" : ml_prediction,
        "ml_probability": ml_probability,
    }
    
#  STEP 9 : Hybrid Risk Engine    
def compute_hybrid_risk(rule_score: float, ml_probability: float) -> float:
    """
    Compute the blended final risk score.

    Parameters
    ----------
    rule_score     : float  Rule-based score (0–100)
    ml_probability : float  ML scam probability (0–1)

    Returns
    -------
    float
        final_risk_score in [0, 100], rounded to 2 dp.
    """
    raw_score = (
        0.6 * rule_score
        + 0.4 * (ml_probability * 100)
    )
    return round(min(raw_score, 100), 2)

#  STEP 10 : Risk Classification

def classify_risk(risk_score: float) -> str:
    """
    Return a categorical risk level for a given numeric risk score.

    Parameters
    ----------
    risk_score : float  Final hybrid risk score (0–100)

    Returns
    -------
    str
        'LOW', 'MEDIUM', or 'HIGH'
    """
    if risk_score < 40:
        return "LOW"
    elif risk_score < 70:
        return "MEDIUM"
    else:
        return "HIGH"
    
#  STEP 11 : Trust Classification

def compute_trust(risk_score: float) -> dict:
    """
    Derive trust score and human-readable trust level.

    Parameters
    ----------
    risk_score : float  Final hybrid risk score (0–100)

    Returns
    -------
    dict
        trust_score (float) and trust_level (str).
    """
    trust_score = round(100 - risk_score, 2)

    if trust_score > 60:
        trust_level = "High Trust"
    elif trust_score > 30:
        trust_level = "Moderate Trust"
    else:
        trust_level = "Low Trust"

    return {
        "trust_score": trust_score,
        "trust_level": trust_level,
    }