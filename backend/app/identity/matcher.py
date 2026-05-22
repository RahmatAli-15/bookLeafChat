from __future__ import annotations

from rapidfuzz import fuzz


def exact_match(a: str, b: str) -> float:
    return 1.0 if a and b and a == b else 0.0


def fuzzy_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return fuzz.ratio(a, b) / 100.0
