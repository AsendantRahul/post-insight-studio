"""
File-backed log of past analyses (a JSON file on disk -- no database setup
needed for this project's scope).
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from ..config import DATA_DIR

_LOG_FILE: Path = DATA_DIR / "logbook.json"
_lock = Lock()

DATA_DIR.mkdir(parents=True, exist_ok=True)
if not _LOG_FILE.exists():
    _LOG_FILE.write_text("[]")


class Logbook:
    """Thin, mostly-stateless facade around the on-disk JSON log."""

    MAX_ENTRIES = 50

    def record(self, file_name: str, method: str, text: str, insight: dict) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_name": file_name,
            "method": method,
            "text_preview": text[:180] + ("…" if len(text) > 180 else ""),
            "text": text,
            "readiness_score": insight["readiness"]["score"],
            "readiness_band": insight["readiness"]["band"],
            "tone": insight["tone"]["label"],
        }
        with _lock:
            entries = self._read_all()
            entries.insert(0, entry)
            entries = entries[: self.MAX_ENTRIES]
            self._write_all(entries)
        return entry

    def all_entries(self) -> list:
        with _lock:
            return self._read_all()

    def clear(self) -> None:
        with _lock:
            self._write_all([])

    @staticmethod
    def _read_all() -> list:
        try:
            return json.loads(_LOG_FILE.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    @staticmethod
    def _write_all(entries: list) -> None:
        _LOG_FILE.write_text(json.dumps(entries, indent=2))
