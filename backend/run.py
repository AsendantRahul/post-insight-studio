"""
Entry point for the Post Insight Studio backend.

Run with:
    python run.py

The frontend (static HTML/CSS/JS, no build step) is served from the
same Flask process, so one process is all you need locally.
"""
from server import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=8000)
