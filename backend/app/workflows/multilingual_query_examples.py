from __future__ import annotations

from app.ai.query_normalizer import query_normalizer


EXAMPLES = [
    "aur btao",
    "thanks",
    "Meri royalty kab milegi?",
    "Mera dashboard login nahi ho raha.",
    "Is my book live yet?",
    "Author copy kab dispatch hogi?",
    "Mujhe add-on service ka status chahiye",
    "डैशबोर्ड पासवर्ड रीसेट कैसे करूं?",
]


def run_examples() -> None:
    print("Multilingual query normalization examples:\n")
    for idx, query in enumerate(EXAMPLES, start=1):
        result = query_normalizer.normalize(query)
        print(
            f"{idx}. {query}\n"
            f"   language={result.language_detected}, multilingual={result.multilingual_detected}, "
            f"normalized={result.normalized_for_workflow}\n"
            f"   -> {result.normalized_query}\n"
        )


if __name__ == "__main__":
    run_examples()
