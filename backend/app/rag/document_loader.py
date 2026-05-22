from __future__ import annotations

from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}

    def load_text(self, path: str) -> tuple[str, str]:
        file_path = Path(path)
        extension = file_path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {extension}")

        if extension in {".md", ".markdown", ".txt"}:
            return file_path.stem, file_path.read_text(encoding="utf-8", errors="ignore")

        if extension == ".pdf":
            if PdfReader is None:
                raise RuntimeError("pypdf is required for PDF ingestion")

            reader = PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return file_path.stem, "\n\n".join(pages)

        raise ValueError(f"Unhandled document type: {extension}")


document_loader = DocumentLoader()
