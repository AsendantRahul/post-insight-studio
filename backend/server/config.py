"""Central configuration constants shared across the backend package."""
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
DATA_DIR = Path(__file__).resolve().parent / "data"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB

ACCEPTED_PDF_TYPES = {"application/pdf"}
ACCEPTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
