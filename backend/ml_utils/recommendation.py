
#  STEP 13 : Recommendation Engine

def get_recommendation(risk_level: str, risk_score: float) -> str:
    """
    Generate an actionable recommendation string.

    Parameters
    ----------
    risk_level : str    'LOW', 'MEDIUM', or 'HIGH'
    risk_score : float  Numeric risk score (0–100)

    Returns
    -------
    str
        Human-readable recommended action.
    """
    if risk_level == "LOW":
        return "Safe to Proceed"

    elif risk_level == "MEDIUM":
        if risk_score < 55:
            return "Review Before Applying"
        else:
            return "Manual Verification Required"

    else:  # HIGH
        return "Potential Scam Detected — Do Not Apply"