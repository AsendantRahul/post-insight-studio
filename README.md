# Post Insight Studio — Social Media Content Analyzer (Flask + Plain HTML/CSS/JS)

Upload a social post as a **PDF** or **image**, extract the text, and walk through a
3-step flow — **Upload → Read → Improve** — to get:

- **Readiness score** (0–100) with a transparent point breakdown
- **Rewritten caption** (auto-rewrite with a CTA, question hook, and hashtags)
- **Hashtag ideas** (keyword-extracted + tone-based boosters)
- **Copy buttons** everywhere (caption, hashtags, extracted text)
- **Metrics grid** (words, hashtags, mentions, emojis, readability, tone, CTA, hook)
- **Staged OCR/PDF loading experience** with a progress bar and stage-specific messages
- **PDF OCR fallback** — scanned/image-only PDFs are auto-rendered and OCR'd
- **Readability score** — Flesch Reading Ease
- **Tone detection** — lexicon-based polarity (Positive / Neutral / Negative)
- **Past analyses drawer** — history saved locally, browsable from any step

## Stack

| Part             | Technology                                    |
|------------------|------------------------------------------------|
| Frontend         | Plain HTML + CSS + JavaScript (no build step, no framework) |
| Backend          | Python + Flask (application factory + blueprints) |
| PDF extraction   | pdfplumber                                     |
| OCR              | Tesseract + pytesseract                        |
| Image processing | Pillow                                         |
| PDF → image      | pdf2image                                      |
| Storage          | JSON file                                      |

No `npm install`, no bundler, nothing to compile on the frontend.

## Project Structure

```
backend/
  run.py                          # entry point (python run.py)
  requirements.txt
  server/
    __init__.py                   # create_app() factory, registers blueprints
    config.py                     # shared constants (paths, upload limits, mime types)
    blueprints/
      pages.py                    # serves the static frontend
      pipeline.py                 # POST /api/extract, GET /api/health
      logbook.py                  # GET/DELETE /api/history
    services/
      text_extraction.py          # TextExtractor: PDF parsing + OCR + scanned-PDF fallback
      insight_engine.py           # InsightEngine: readiness score, tone, readability, caption rewrite
      logbook_store.py            # Logbook: JSON-file-backed history
    data/                         # logbook.json lives here (created automatically)
frontend/
  index.html                      # 3-step wizard markup + history drawer
  style.css                       # editorial/light theme, stepper, meter, cards
  script.js                       # wizard state machine, fetch calls, DOM rendering
  config.js                       # one line: the backend URL
```

## 1. Backend Setup

**System dependencies (install these first — they are NOT pip packages):**

- **Tesseract OCR engine**
  - Mac: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`
  - Windows: [installer here](https://github.com/UB-Mannheim/tesseract/wiki)
- **Poppler** (only needed for OCR-ing scanned PDFs)
  - Mac: `brew install poppler`
  - Linux: `sudo apt install poppler-utils`
  - Windows: [download here](https://github.com/oschwartz10612/poppler-windows/releases), add the `bin` folder to PATH

**Then, in a terminal:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
python run.py
```

Flask starts on `http://localhost:8000`. Visit `http://localhost:8000/api/health` —
you should see `{"status": "ok"}`. Leave this terminal running.

## 2. Frontend

The Flask server also serves the frontend, so just open `http://localhost:8000` in your
browser — no separate server needed. If you ever run the backend on a different host or
port, update the single `API_URL` line in `frontend/config.js`.

## How Scoring Works

The readiness score is a transparent, rule-based composite out of 100 (see
`InsightEngine._readiness_score()` in `backend/server/services/insight_engine.py`): length
appropriateness (20pts), hashtag count (15), call-to-action presence (15), a question hook
(10), emoji use (10), readability (15), and tone (15). Every point is explainable — no
black-box model, so it runs with zero API keys and no rate limits.

**Extension point:** `InsightEngine._rewrite_caption()` is a template rewrite by design. To
get smarter, more natural rewrites, swap that method's body for a call to an LLM (e.g. the
Claude API) — the rest of the pipeline doesn't need to change.

## Approach Write-up (for submission)

I built the backend as a small Flask application factory with three blueprints —
`pipeline` (extract + score), `logbook` (history), and `pages` (serving the static
frontend) — instead of one flat file, so each concern stays easy to find. `pdfplumber`
extracts text from PDFs directly; if a PDF has no real text layer (a scanned document), it
falls back to `pdf2image` + `pytesseract` for OCR. Standalone images always go through
OCR. Analysis — readiness score, tone, readability (Flesch), hashtag ideas, and caption
rewrite — is deliberately rule-based and explainable rather than an LLM call, so it's
instant and needs no API keys, with one clearly marked extension point to plug an LLM in
later. The frontend is a 3-step wizard (Upload → Read → Improve) with a staged progress
bar during OCR/parsing, so users get feedback instead of a blank spinner, plus a slide-out
drawer for past analyses. History is a local JSON file — no database needed. Given the
scope, I prioritized a working, explainable pipeline with zero setup friction over a paid
AI service.

## Known Simplifications

- The rewritten caption and hashtag ideas are rule-based, not AI-generated (see extension point above).
- The progress bar is a UX simulation (estimated durations), not literal OCR progress streamed from the server.
- History has no per-user login; it's a single shared local JSON file, intended for local/demo use.
