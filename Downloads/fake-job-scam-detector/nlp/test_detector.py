from nlp_detector import NLPFraudDetector

sample_job = """

Data Entry Internship

Work from Office

Instant Joining

Registration Fee Required

No Interview

Contact on WhatsApp

Limited Seats Available

Earn Money Fast

"""

detector = NLPFraudDetector()

result = detector.analyze(
    sample_job
)

print("\n===== ANALYSIS RESULT =====\n")

for key, value in result.items():

    print(
        f"{key}: {value}"
    )