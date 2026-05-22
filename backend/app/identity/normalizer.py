from __future__ import annotations

import re


def normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def normalize_phone(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\D+", "", value)


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_handle(value: str | None) -> str:
    if not value:
        return ""
    return value.lower().strip().lstrip("@")
