"""
Post Insight Studio backend package.

Structured as a small Flask application factory + blueprints, rather than
one flat app.py, so each concern (serving the static frontend, running the
extract-and-score pipeline, and the history log) lives in its own module.
"""
from flask import Flask
from flask_cors import CORS

from .blueprints.pages import pages_bp
from .blueprints.pipeline import pipeline_bp
from .blueprints.logbook import logbook_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)  # frontend may be opened from a different origin/port during dev

    app.register_blueprint(pipeline_bp)
    app.register_blueprint(logbook_bp)
    app.register_blueprint(pages_bp)  # catch-all static routes registered last

    return app
