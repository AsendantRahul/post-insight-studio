"""
Endpoints:
    GET  /api/health   -> uptime check
    POST /api/extract  -> upload a PDF/image, extract text and analyze it

Runs each upload through:

validate -> extract text -> score -> log
"""

from flask import Blueprint, request, jsonify

from ..config import (
    MAX_UPLOAD_BYTES,
    ACCEPTED_PDF_TYPES,
    ACCEPTED_IMAGE_TYPES
)

from ..services.text_extraction import (
    TextExtractor,
    ExtractionFailure
)

from ..services.insight_engine import InsightEngine
from ..services.logbook_store import Logbook


pipeline_bp = Blueprint(
    "pipeline",
    __name__,
    url_prefix="/api"
)


_extractor = TextExtractor()
_engine = InsightEngine()
_logbook = Logbook()


# Supported platforms
ALLOWED_PLATFORMS = {
    "Instagram",
    "LinkedIn",
    "X",
    "Facebook"
}


@pipeline_bp.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "ok"
    })


@pipeline_bp.route(
    "/extract",
    methods=["POST"]
)
def run_pipeline():

    # -----------------------------------------
    # FILE VALIDATION
    # -----------------------------------------

    upload = request.files.get("file")


    if upload is None or upload.filename == "":

        return jsonify({
            "error": "No file selected."
        }), 400


    mime = upload.content_type


    if mime not in (
        ACCEPTED_PDF_TYPES |
        ACCEPTED_IMAGE_TYPES
    ):

        return jsonify({
            "error":
                "Unsupported file type. "
                "Please upload a PDF, PNG, JPEG, or WEBP file."
        }), 400


    payload = upload.read()


    if not payload:

        return jsonify({
            "error":
                "Uploaded file is empty."
        }), 400


    if len(payload) > MAX_UPLOAD_BYTES:

        return jsonify({
            "error":
                "File too large. Max size is 10MB."
        }), 400


    # -----------------------------------------
    # PLATFORM
    # -----------------------------------------

    platform = request.form.get(
        "platform",
        "Instagram"
    )


    if platform not in ALLOWED_PLATFORMS:

        platform = "Instagram"


    # -----------------------------------------
    # TEXT EXTRACTION
    # -----------------------------------------

    try:

        if mime in ACCEPTED_PDF_TYPES:

            outcome = _extractor.from_pdf(
                payload
            )

        else:

            outcome = _extractor.from_image(
                payload
            )

    except ExtractionFailure as err:

        return jsonify({
            "error": str(err)
        }), 422


    # -----------------------------------------
    # EMPTY TEXT CHECK
    # -----------------------------------------

    if not outcome.text.strip():

        return jsonify({
            "error":
                "No readable text could be extracted "
                "from this file. Try a clearer scan "
                "or a text-based PDF."
        }), 422


    # -----------------------------------------
    # ANALYSIS
    # -----------------------------------------

    insight = _engine.evaluate(
        outcome.text,
        platform
    )


    # -----------------------------------------
    # SAVE HISTORY
    # -----------------------------------------

    _logbook.record(
        upload.filename,
        outcome.method,
        outcome.text,
        insight
    )


    # -----------------------------------------
    # RESPONSE
    # -----------------------------------------

    return jsonify({

        "success": True,

        "file_name":
            upload.filename,

        "method":
            outcome.method,

        "extracted_text":
            outcome.text,

        "analysis":
            insight

    })