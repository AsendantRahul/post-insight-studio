"""
Turns an uploaded document into plain text.

Uses pdfplumber for normal PDFs and Tesseract OCR for
images/scanned PDFs while keeping memory usage low.
"""

import io
from dataclasses import dataclass

from PIL import Image
import pytesseract
import pdfplumber

MIN_CHARS_BEFORE_OCR_FALLBACK = 20

# Keep images reasonably small for Render's free memory limit.
MAX_IMAGE_SIZE = 1800


class ExtractionFailure(Exception):
    """Raised when a document can't be opened or read at all."""


@dataclass
class ExtractionOutcome:
    text: str
    method: str
    page_count: int = 1


class TextExtractor:
    """Helper for extracting text from PDFs and images."""

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
            raise ExtractionFailure(
                f"Could not read PDF: {err}"
            ) from err

        joined = "\n\n".join(pages_text).strip()

        # Normal text-based PDF
        if len(joined) >= MIN_CHARS_BEFORE_OCR_FALLBACK:
            return ExtractionOutcome(
                text=joined,
                method="PDF text layer",
                page_count=page_count,
            )

        # Scanned/image-only PDF
        rescued = self._ocr_pdf_pages(raw_bytes, page_count)

        if rescued.strip():
            return ExtractionOutcome(
                text=rescued.strip(),
                method="PDF OCR fallback (scanned PDF)",
                page_count=page_count,
            )

        return ExtractionOutcome(
            text=joined,
            method="PDF text layer",
            page_count=page_count,
        )

    def from_image(self, raw_bytes: bytes) -> ExtractionOutcome:
        try:
            picture = Image.open(io.BytesIO(raw_bytes))

            # Convert to RGB
            picture = picture.convert("RGB")

            # Reduce very large images before OCR.
            picture.thumbnail(
                (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE),
                Image.Resampling.LANCZOS,
            )

        except Exception as err:
            raise ExtractionFailure(
                f"Could not read image: {err}"
            ) from err

        try:
            text = pytesseract.image_to_string(picture)

        except pytesseract.TesseractNotFoundError as err:
            raise ExtractionFailure(
                "Tesseract OCR engine is not installed."
            ) from err

        except Exception as err:
            raise ExtractionFailure(
                f"OCR failed: {err}"
            ) from err

        finally:
            # Release image memory.
            try:
                picture.close()
            except Exception:
                pass

        return ExtractionOutcome(
            text=text.strip(),
            method="OCR (pytesseract)",
        )

    def _ocr_pdf_pages(
        self,
        raw_bytes: bytes,
        page_count: int,
    ) -> str:
        """
        OCR scanned PDF one page at a time.

        This is intentionally done page-by-page instead of rendering
        the entire PDF into memory.
        """

        try:
            from pdf2image import convert_from_bytes

        except ImportError:
            return ""

        recovered = []

        # Process one page at a time to keep RAM usage low.
        for page_number in range(1, page_count + 1):

            try:
                rendered_pages = convert_from_bytes(
                    raw_bytes,
                    dpi=120,
                    first_page=page_number,
                    last_page=page_number,
                    fmt="jpeg",
                    thread_count=1,
                )

                if not rendered_pages:
                    continue

                page_image = rendered_pages[0]

                # Reduce image size before OCR.
                page_image.thumbnail(
                    (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE),
                    Image.Resampling.LANCZOS,
                )

                try:
                    text = pytesseract.image_to_string(
                        page_image
                    )

                    if text.strip():
                        recovered.append(text.strip())

                finally:
                    page_image.close()

                # Remove references to the rendered image.
                del rendered_pages

            except Exception:
                # Continue with the next page if one page fails.
                continue

        return "\n\n".join(recovered)