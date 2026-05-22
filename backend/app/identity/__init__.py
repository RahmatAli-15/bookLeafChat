from app.identity.matcher import exact_match, fuzzy_similarity
from app.identity.normalizer import normalize_email, normalize_handle, normalize_name, normalize_phone
from app.identity.resolver import identity_resolver
from app.identity.scoring import SignalScore, weighted_confidence

__all__ = [
    "identity_resolver",
    "normalize_email",
    "normalize_phone",
    "normalize_name",
    "normalize_handle",
    "exact_match",
    "fuzzy_similarity",
    "SignalScore",
    "weighted_confidence",
]
