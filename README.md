# EDI 210 AI Summarizer — Local Setup

## Architecture

```
edi-ai-demo/
├── backend/
│   ├── app.py              FastAPI server: parses EDI, calls Claude
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html          Upload UI
│   ├── style.css
│   └── script.js           Calls backend over HTTP (fetch)
└── sample_210.edi          Test file
```

**Flow:** Browser (frontend) → HTTP POST `/api/summarize` → FastAPI backend
parses the EDI text into segments → backend sends the parsed structure to
Claude via the Anthropic API → backend returns `{segments, summary}` as JSON
→ frontend renders the table + AI summary.

The backend holds your API key (never exposed to the browser). The
frontend is plain HTML/CSS/JS — no build step, no framework — so it's easy
to read and modify for a demo.

## Setup

### 1. Get a free Gemini API key

Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey), sign in
with any Google account, and click **Create API key** — no credit card needed.
The app defaults to `gemini-3.1-flash-lite`, which is on Google's free tier.

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env with your real key
```

Load the `.env` file (FastAPI/uvicorn don't do this automatically) — either:
- `pip install python-dotenv` (already in requirements.txt) and add
  `from dotenv import load_dotenv; load_dotenv()` at the top of `app.py`, or
- just export it directly in your shell instead of using `.env`:
  ```bash
  export GEMINI_API_KEY=your_key_here
  ```

Run the server:
```bash
uvicorn app:app --reload --port 8000
```

Confirm it's up: open `http://localhost:8000/api/health` — should return `{"status":"ok"}`.

### 3. Frontend

No build tools needed. From the `frontend/` folder, just open `index.html`
directly in a browser, **or** serve it (recommended, avoids CORS quirks):

```bash
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500`.

### 4. Use it

Upload `sample_210.edi` (or paste EDI text) and click **Parse & Summarize**.

## VS Code tips

- Install the "Python" extension for backend debugging (set breakpoints in `app.py`).
- Install "Live Server" extension as an alternative to `http.server` for the frontend.
- The two processes (backend on :8000, frontend on :5500) run in separate terminals — use VS Code's split terminal.

## Extending it

- Swap `parse_edi_210` in `app.py` for a real library (`pyx12`, `bots`) to
  handle more transaction types than just the 210.
- Add an `/api/validate` endpoint that checks against a trading partner's
  implementation guide.
- Point the parser at your own IBM i job's output files instead of a flat
  `.edi` file.
