import pandas as pd   
import numpy as np         
import joblib                
import re                    
import json                  
import textstat

#  STEP 4 : NLP Feature Generator

def generate_nlp_features(text: str) -> dict:
    """
    Compute NLP-based features from a raw text string.

    Parameters
    ----------
    text : str
        Raw input text (job description, URL content, OCR output, etc.)

    Returns
    -------
    dict
        Dictionary of NLP feature names → values.
    """
    if not text or not isinstance(text, str):
        text = ""

    text_clean = text.strip()

    # Tokenise words (alphanumeric only)
    words = re.findall(r'\b[a-zA-Z]+\b', text_clean.lower())

    # Sentence count via punctuation heuristic
    sentences = re.split(r'[.!?]+', text_clean)
    sentences = [s.strip() for s in sentences if s.strip()]

    word_count      = len(words)
    sentence_count  = max(len(sentences), 1)
    unique_words    = set(words)
    unique_word_count = len(unique_words)

    avg_word_length = (
        round(sum(len(w) for w in words) / word_count, 4)
        if word_count > 0 else 0
    )

    lexical_diversity = (
        round(unique_word_count / word_count, 4)
        if word_count > 0 else 0
    )

    # Flesch Reading Ease (textstat)
    try:
        readability_score = textstat.flesch_reading_ease(text_clean)
    except Exception:
        readability_score = 50.0   # neutral default

    return {
        "readability_score"  : readability_score,
        "word_count"         : word_count,
        "sentence_count"     : sentence_count,
        "average_word_length": avg_word_length,
        "unique_word_count"  : unique_word_count,
        "lexical_diversity"  : lexical_diversity,
    }
