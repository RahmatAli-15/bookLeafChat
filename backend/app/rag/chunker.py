from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    chunk_size: int = 800
    overlap: int = 120


class TextChunker:
    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()

    def chunk(self, text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n").strip()
        if not normalized:
            return []

        sections = self._split_sections(normalized)
        chunks: list[str] = []

        for section in sections:
            chunks.extend(self._chunk_section(section))

        return chunks

    def _split_sections(self, text: str) -> list[str]:
        parts: list[str] = []
        current: list[str] = []

        for line in text.split("\n"):
            if line.strip().startswith("#") and current:
                parts.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)

        if current:
            parts.append("\n".join(current).strip())

        return [p for p in parts if p]

    def _chunk_section(self, section: str) -> list[str]:
        if len(section) <= self.config.chunk_size:
            return [section]

        words = section.split()
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for word in words:
            projected = current_len + len(word) + (1 if current else 0)
            if projected > self.config.chunk_size and current:
                chunks.append(" ".join(current))
                overlap_words = self._take_overlap_words(current)
                current = overlap_words + [word]
                current_len = len(" ".join(current))
            else:
                current.append(word)
                current_len = projected

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _take_overlap_words(self, words: list[str]) -> list[str]:
        if self.config.overlap <= 0:
            return []

        overlap_words: list[str] = []
        size = 0
        for word in reversed(words):
            size += len(word) + (1 if overlap_words else 0)
            if size > self.config.overlap:
                break
            overlap_words.insert(0, word)
        return overlap_words


text_chunker = TextChunker()
