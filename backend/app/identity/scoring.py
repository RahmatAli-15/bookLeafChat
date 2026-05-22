from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SignalScore:
    email: float = 0.0
    phone: float = 0.0
    whatsapp: float = 0.0
    name: float = 0.0
    instagram: float = 0.0


WEIGHTS = {
    "email": 0.35,
    "phone": 0.30,
    "whatsapp": 0.25,
    "name": 0.20,
    "instagram": 0.20,
}


def weighted_confidence(score: SignalScore, used_signals: list[str]) -> float:
    if not used_signals:
        return 0.0
    total_weight = sum(WEIGHTS[s] for s in used_signals)
    weighted_sum = sum(getattr(score, s) * WEIGHTS[s] for s in used_signals)
    return weighted_sum / total_weight if total_weight > 0 else 0.0
