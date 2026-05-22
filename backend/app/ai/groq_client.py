from __future__ import annotations

import json
import logging
import time
from typing import Any

try:
    from groq import Groq
except ImportError:  # pragma: no cover - handled by configuration checks
    Groq = None

from app.core_config import settings

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self) -> None:
        self._client = (
            Groq(api_key=settings.GROQ_API_KEY)
            if (Groq is not None and settings.GROQ_API_KEY)
            else None
        )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def chat(self, user_message: str, system_prompt: str) -> str:
        if not self._client:
            raise RuntimeError("Groq client not configured")

        completion = self._client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
        )

        return completion.choices[0].message.content or ""

    def chat_json(
        self,
        *,
        user_message: str,
        system_prompt: str,
        max_retries: int = 2,
        timeout_seconds: float = 15.0,
        initial_backoff_seconds: float = 0.5,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Groq client not configured")

        retries = max(0, max_retries)
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                completion = self._client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    timeout=timeout_seconds,
                )
                content = completion.choices[0].message.content or "{}"
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("Groq JSON response must be an object")
                return parsed
            except Exception as exc:
                last_error = exc
                logger.warning("groq_chat_json_attempt_failed", extra={"attempt": attempt + 1, "retries": retries}, exc_info=True)
                if attempt < retries:
                    time.sleep(initial_backoff_seconds * (2**attempt))

        raise RuntimeError("Groq JSON request failed after retries") from last_error


groq_client = GroqClient()
