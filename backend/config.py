# ============================================================
# config.py - Application Settings
# Reads from .env file using pydantic-settings
# ============================================================

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    All app settings are read from environment variables.
    Pydantic automatically validates types and raises errors
    if required variables are missing.
    """

    # --- App Info ---
    APP_NAME: str = "Fake Job Scam Detector API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- Database ---
    # PostgreSQL connection string
    DATABASE_URL: str

    # --- JWT Auth ---
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- CORS ---
    # Allow requests from these frontend origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ]

    # --- External APIs (optional) ---
    WHOIS_API_KEY: str = ""           # whoisxmlapi.com
    VIRUSTOTAL_API_KEY: str = ""      # virustotal.com

    # --- Fraud Score Thresholds ---
    LOW_RISK_THRESHOLD: float = 30.0
    MEDIUM_RISK_THRESHOLD: float = 60.0
    HIGH_RISK_THRESHOLD: float = 80.0

    # --- Risk Score Weights (must sum to 1.0) ---
    KEYWORD_WEIGHT: float = 0.40      # NLP keyword fraud score
    DOMAIN_WEIGHT: float = 0.30       # Domain reputation score
    SALARY_WEIGHT: float = 0.20       # Salary anomaly score
    REPORT_WEIGHT: float = 0.10       # User reports score

    class Config:
        env_file = ".env"             # Load from .env file
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a single settings instance to import across the app
settings = Settings()


def get_risk_level(score: float) -> str:
    """
    Convert numeric scam score to risk level label.
    Score range: 0-100
    """
    if score <= settings.LOW_RISK_THRESHOLD:
        return "LOW"
    elif score <= settings.MEDIUM_RISK_THRESHOLD:
        return "MEDIUM"
    elif score <= settings.HIGH_RISK_THRESHOLD:
        return "HIGH"
    else:
        return "CONFIRMED_SCAM"
