from __future__ import annotations

from app.schemas.intent import IntentType
from app.services.intent_classification_service import intent_classifier_service


EXAMPLES: list[tuple[str, IntentType]] = [
    ("What is the print status of my book Stars of Velora?", IntentType.BOOK_STATUS),
    ("My April royalty payment is missing. When is payout?", IntentType.ROYALTY),
    ("Please send me 20 author copies to my address.", IntentType.AUTHOR_COPY),
    ("Is the Launch Campaign Automation add-on still active?", IntentType.ADDON_STATUS),
    ("I cannot log in to the dashboard, OTP is failing.", IntentType.DASHBOARD_ACCESS),
    ("What is your policy for turnaround time on support tickets?", IntentType.GENERAL_POLICY),
    ("Hello there", IntentType.UNKNOWN),
]


def run_examples() -> None:
    print("Intent classification examples:\n")
    for text, expected in EXAMPLES:
        result = intent_classifier_service.classify(text)
        print(f"query: {text}")
        print(f"expected: {expected.value}")
        print(
            "actual: "
            f"{result.intent.value}, confidence={result.confidence}, entities={result.entities}"
        )
        print("-")


if __name__ == "__main__":
    run_examples()
