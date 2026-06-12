import re
import spacy
import textstat

class NLPFraudDetector:

    def __init__(self):

        self.nlp = spacy.load("en_core_web_sm")

        self.scam_keywords = [

            "registration fee",
            "processing fee",
            "security deposit",
            "telegram",
            "whatsapp",
            "immediate joining",
            "instant joining",
            "limited seats",
            "earn money fast",
            "guaranteed placement",
            "investment required",
            "training fee",
            "easy money",
            "work from home income"

        ]

        self.skills = [

            "python",
            "java",
            "sql",
            "react",
            "node",
            "aws",
            "docker",
            "kubernetes",
            "excel",
            "power bi",
            "machine learning",
            "data science"

        ]

        self.urgency_words = [

            "urgent",
            "immediate",
            "instant",
            "limited",
            "hurry"

        ]

        self.contact_words = [

            "telegram",
            "whatsapp"

        ]

    # ----------------------
    # CLEAN TEXT
    # ----------------------

    def clean_text(self, text):

        if text is None:
            return ""

        text = str(text).lower()

        text = re.sub(r"http\S+", " ", text)

        text = re.sub(r"[^a-zA-Z ]", " ", text)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ----------------------
    # LEMMATIZATION
    # ----------------------

    def lemmatize_text(self, text):

        doc = self.nlp(text)

        tokens = [

            token.lemma_

            for token in doc

            if not token.is_stop
            and not token.is_punct

        ]

        return " ".join(tokens)

    # ----------------------
    # KEYWORD SCORE
    # ----------------------

    def keyword_score(self, text):

        score = 0
        matched = []

        for keyword in self.scam_keywords:

            if keyword in text:

                score += 1
                matched.append(keyword)

        return score, matched

    # ----------------------
    # SKILLS
    # ----------------------

    def skill_count(self, text):

        count = 0
        found = []

        for skill in self.skills:

            if skill in text:

                count += 1
                found.append(skill)

        return count, found

    # ----------------------
    # URGENCY SCORE
    # ----------------------

    def urgency_score(self, text):

        score = 0

        for word in self.urgency_words:

            if word in text:
                score += 1

        return score

    # ----------------------
    # CONTACT SCORE
    # ----------------------

    def contact_channel_score(self, text):

        score = 0

        for word in self.contact_words:

            if word in text:
                score += 1

        return score

    # ----------------------
    # MAIN ANALYSIS
    # ----------------------

    def analyze(self, text):

        clean_text = self.clean_text(text)

        lemmatized_text = self.lemmatize_text(
            clean_text
        )

        keyword_score, matched_keywords = (

            self.keyword_score(clean_text)

        )

        skill_count, found_skills = (

            self.skill_count(clean_text)

        )

        description_length = len(
            clean_text.split()
        )

        readability_score = round(

            textstat.flesch_reading_ease(
                clean_text
            ),

            2

        )

        urgency_score = self.urgency_score(
            clean_text
        )

        contact_score = (

            self.contact_channel_score(
                clean_text
            )

        )

        has_description = (

            1 if description_length > 0 else 0

        )

        missing_info_score = (

            1 if description_length < 20 else 0

        )

        scam_density = round(

            keyword_score / max(
                description_length,
                1
            ),

            3

        )

        # ----------------------
        # RISK SCORE
        # ----------------------

        risk_score = 0

        risk_score += keyword_score * 15

        risk_score += urgency_score * 5

        risk_score += contact_score * 10

        risk_score += missing_info_score * 10

        risk_score = min(
            risk_score,
            100
        )

        prediction = (

            "SCAM"

            if risk_score >= 40

            else "GENUINE"

        )

        return {

            "clean_text": clean_text,

            "lemmatized_text": lemmatized_text,

            "description_length": description_length,

            "readability_score": readability_score,

            "keyword_score": keyword_score,

            "matched_keywords": matched_keywords,

            "skill_count": skill_count,

            "found_skills": found_skills,

            "urgency_score": urgency_score,

            "contact_score": contact_score,

            "has_description": has_description,

            "missing_info_score": missing_info_score,

            "scam_density": scam_density,

            "risk_score": risk_score,

            "prediction": prediction

        }