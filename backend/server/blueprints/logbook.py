"""
Endpoints:
    GET    /api/history -> list past analyses, most recent first
    DELETE /api/history -> clear past analyses
"""
from flask import Blueprint, jsonify

from ..services.logbook_store import Logbook

logbook_bp = Blueprint("logbook", __name__, url_prefix="/api")

_logbook = Logbook()


@logbook_bp.route("/history", methods=["GET"])
def list_entries():
    return jsonify({"items": _logbook.all_entries()})


@logbook_bp.route("/history", methods=["DELETE"])
def clear_entries():
    _logbook.clear()
    return jsonify({"success": True})
