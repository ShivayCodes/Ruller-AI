"""Optional OCR and image-understanding helpers.

This module is intentionally opt-in: Ruller AI stays offline-first, and image
recognition only runs when the required OCR libraries are installed and the user
asks to inspect an image.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImageTextSummary:
    """Structured OCR output for image text recognition."""

    source: str
    raw_text: str = ""
    text_segments: list[str] = field(default_factory=list)
    number_segments: list[str] = field(default_factory=list)
    mixed_segments: list[str] = field(default_factory=list)

    def to_report(self) -> str:
        lines = [f"Image source: {self.source}"]
        if self.raw_text.strip():
            lines.append(f"Detected text:\n{self.raw_text.strip()}")
        else:
            lines.append("Detected text: none")
        if self.text_segments:
            lines.append("Text-only segments: " + "; ".join(self.text_segments))
        if self.number_segments:
            lines.append("Numeric segments: " + "; ".join(self.number_segments))
        if self.mixed_segments:
            lines.append("Mixed text/number segments: " + "; ".join(self.mixed_segments))
        return "\n".join(lines)


def _split_ocr_segments(raw_text: str) -> tuple[list[str], list[str], list[str]]:
    chunks = [segment.strip() for segment in raw_text.splitlines() if segment.strip()]
    text_segments: list[str] = []
    number_segments: list[str] = []
    mixed_segments: list[str] = []
    for chunk in chunks:
        has_letters = bool(re.search(r"[A-Za-z]", chunk))
        has_digits = bool(re.search(r"\d", chunk))
        if has_letters and has_digits:
            mixed_segments.append(chunk)
        elif has_digits:
            number_segments.append(chunk)
        elif has_letters:
            text_segments.append(chunk)
    return text_segments, number_segments, mixed_segments


def extract_text_from_image(path: str | Path) -> ImageTextSummary:
    """Use OCR to read text and numbers from an image.

    The project intentionally does not force OCR dependencies at install time; if
    the libraries are missing, this raises a descriptive RuntimeError instead of
    failing silently.
    """
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise FileNotFoundError(f"Image not found: {file_path}")

    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - depends on optional deps
        raise RuntimeError(
            "Image OCR requires optional dependencies. Install 'pillow' and 'pytesseract', "
            "plus the Tesseract binary on your system."
        ) from exc

    try:
        image = Image.open(file_path)
        raw_text = pytesseract.image_to_string(image, config="--psm 6")
    except Exception as exc:  # pragma: no cover - runtime dependency issue
        raise RuntimeError(f"OCR failed for {file_path}: {exc}") from exc

    text_segments, number_segments, mixed_segments = _split_ocr_segments(raw_text)
    return ImageTextSummary(
        source=str(file_path),
        raw_text=raw_text.strip(),
        text_segments=text_segments,
        number_segments=number_segments,
        mixed_segments=mixed_segments,
    )


def summarize_image_text(path: str | Path) -> str:
    return extract_text_from_image(path).to_report()
