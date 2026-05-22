from __future__ import annotations

import re
from dataclasses import dataclass


DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")


@dataclass(frozen=True)
class NormalizedQuery:
    original_query: str
    normalized_query: str
    language_detected: str
    multilingual_detected: bool
    normalized_for_workflow: bool
    matched_shortcuts: list[str]
    smalltalk_detected: bool


class QueryNormalizer:
    """Lightweight multilingual normalizer for English/Hindi/Hinglish support queries."""

    SHORTCUTS: list[tuple[str, tuple[str, ...], str]] = [
        ("dashboard_help", ("dashboard", "login", "log in", "cannot login", "can't login", "password", "portal issue", "forgot password", "dashboard access"), "Dashboard access help"),
        ("royalty", ("royalty", "royalties", "payment", "payout", "milegi", "kab milegi"), "When will I receive my royalty payment?"),
        ("book_status", ("book live", "book status", "publishing status", "publication", "live yet", "publish", "published"), "What is my current publishing status and live date?"),
        ("author_copy", ("author copy", "copies", "dispatch", "shipping", "delivery"), "What is the status of my author copy delivery?"),
        ("addon_status", ("add-on", "addon", "service status", "campaign status", "promotion status"), "What is the status of my add-on service?"),
    ]

    HINGLISH_HINTS = (
        "meri",
        "mujhe",
        "kab",
        "kaise",
        "nahi",
        "nhi",
        "milegi",
        "milega",
        "issue hai",
        "karna hai",
        "hona chahiye",
        "aur btao",
        "acha",
    )

    SMALLTALK_MARKERS = {
        "hi",
        "hello",
        "hey",
        "hii",
        "thanks",
        "thank you",
        "thx",
        "ok",
        "okay",
        "acha",
        "accha",
        "hmm",
        "hmmm",
        "aur btao",
        "aur batao",
        "good morning",
        "good evening",
    }

    def normalize(self, query: str) -> NormalizedQuery:
        text = (query or "").strip()
        lowered = text.lower()
        has_devanagari = bool(DEVANAGARI_PATTERN.search(text))
        has_hinglish = any(token in lowered for token in self.HINGLISH_HINTS)

        language = "english"
        if has_devanagari:
            language = "hindi"
        elif has_hinglish:
            language = "hinglish"

        normalized = self._cleanup_spacing(lowered)
        smalltalk_detected = self.is_smalltalk(normalized)

        matched_shortcuts: list[str] = []
        rewritten = ""
        if not smalltalk_detected:
            for shortcut, markers, canonical in self.SHORTCUTS:
                if any(marker in normalized for marker in markers):
                    matched_shortcuts.append(shortcut)
                    rewritten = canonical
                    break

            if not rewritten:
                rewritten = self._phrase_level_normalize(text)
        else:
            rewritten = text

        rewritten = rewritten.strip() or text
        normalized_for_workflow = rewritten.lower() != text.lower()
        multilingual_detected = has_devanagari or has_hinglish

        return NormalizedQuery(
            original_query=text,
            normalized_query=rewritten,
            language_detected=language,
            multilingual_detected=multilingual_detected,
            normalized_for_workflow=normalized_for_workflow,
            matched_shortcuts=matched_shortcuts,
            smalltalk_detected=smalltalk_detected,
        )

    def is_smalltalk(self, normalized_text: str) -> bool:
        compact = normalized_text.strip(" .!?")
        if compact in self.SMALLTALK_MARKERS:
            return True

        # Keep this strict to avoid swallowing real support questions.
        word_count = len(compact.split())
        if word_count <= 3 and any(token in compact for token in self.SMALLTALK_MARKERS):
            support_keywords = ("royalty", "book", "dashboard", "login", "copy", "addon", "payment", "status")
            if not any(keyword in compact for keyword in support_keywords):
                return True
        return False

    def _cleanup_spacing(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _phrase_level_normalize(self, text: str) -> str:
        lowered = self._cleanup_spacing(text.lower())
        replacements = {
            "meri royalty kab milegi": "When will I receive my royalty payment?",
            "royalty kab milegi": "When will I receive my royalty payment?",
            "mera dashboard nahi chal raha": "I cannot access my dashboard. Please help with login troubleshooting.",
            "dashboard login issue hai": "I am facing a dashboard login issue.",
            "meri book live hui kya": "Is my book live yet?",
            "book live kab hogi": "When will my book go live?",
            "author copy kab milegi": "When will I receive my author copy?",
            "addon status batao": "What is the status of my add-on service?",
        }
        for source, target in replacements.items():
            if source in lowered:
                return target
        return text


query_normalizer = QueryNormalizer()

