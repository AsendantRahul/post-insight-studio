"""Serves the static single-page frontend from the same Flask process."""
from flask import Blueprint, send_from_directory

from ..config import FRONTEND_DIR

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/", methods=["GET"])
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@pages_bp.route("/<path:filename>", methods=["GET"])
def static_asset(filename):
    return send_from_directory(FRONTEND_DIR, filename)
