"""
Turns an uploaded document into plain text.

Strategy:
- Text-based PDFs are parsed directly with pdfplumber, which keeps the
  original reading order without needing OCR at all.
- If a PDF turns out to have little or no extractable text (i.e. it's a
  scanned/image-only PDF), each page is rendered to an image and OCR'd.
- Standalone images always go through OCR (pytesseract + the Tesseract
  engine).
"""
import io
from dataclasses import dataclass

from PIL import Image
import pytesseract
import pdfplumber

MIN_CHARS_BEFORE_OCR_FALLBACK = 20


class ExtractionFailure(Exception):
    """Raised when a document can't be opened or read at all."""


@dataclass
class ExtractionOutcome:
    text: str
    method: str
    page_count: int = 1


class TextExtractor:
    """Stateless helper that knows how to pull text out of PDFs and images."""

    def from_pdf(self, raw_bytes: bytes) -> ExtractionOutcome:
        pages_text = []
        page_count = 0
        try:
            with pdfplumber.open(io.BytesIO(raw_bytes)) as document:
                page_count = len(document.pages)
                for page in document.pages:
                    chunk = (page.extract_text() or "").strip()
                    if chunk:
                        pages_text.append(chunk)
        except Exception as err:
            raise ExtractionFailure(f"Could not read PDF: {err}") from err

        joined = "\n\n".join(pages_text).strip()
        if len(joined) >= MIN_CHARS_BEFORE_OCR_FALLBACK:
            return ExtractionOutcome(text=joined, method="PDF text layer", page_count=page_count)

        # Scanned / image-only PDF: fall back to OCR-per-page.
        rescued = self._ocr_pdf_pages(raw_bytes)
        if rescued.strip():
            return ExtractionOutcome(
                text=rescued.strip(), method="PDF OCR fallback (scanned PDF)", page_count=page_count
            )

        return ExtractionOutcome(text=joined, method="PDF text layer", page_count=page_count)

    def from_image(self, raw_bytes: bytes) -> ExtractionOutcome:
        try:
            picture = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        except Exception as err:
            raise ExtractionFailure(f"Could not read image: {err}") from err

        try:
            text = pytesseract.image_to_string(picture)
        except pytesseract.TesseractNotFoundError as err:
            raise ExtractionFailure(
                "Tesseract OCR engine is not installed on this machine. "
                "Install it via 'brew install tesseract' (Mac) or "
                "'sudo apt install tesseract-ocr' (Linux)."
            ) from err
        except Exception as err:
            raise ExtractionFailure(f"OCR failed: {err}") from err

        return ExtractionOutcome(text=text.strip(), method="OCR (pytesseract)")

    def _ocr_pdf_pages(self, raw_bytes: bytes) -> str:
        """Render PDF pages to images and OCR them. Requires poppler installed."""
        try:
            from pdf2image import convert_from_bytes
        except ImportError:
            return ""

        try:
            rendered_pages = convert_from_bytes(raw_bytes, dpi=200)
        except Exception:
            # poppler missing, or conversion failed -- fail gracefully and let
            # the caller fall back to whatever (possibly empty) text it found.
            return ""

        recovered = []
        for page_image in rendered_pages:
            try:
                recovered.append(pytesseract.image_to_string(page_image))
            except Exception:
                continue
        return "\n\n".join(part.strip() for part in recovered if part.strip())
