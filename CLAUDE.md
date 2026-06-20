# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Server

```bash
cd "/Users/niranjan/my project -2/AI-Legal-Document-Analyzer"
GEMINI_API_KEY=<your-key> python main.py
```

The server runs at `http://localhost:8000` with hot-reload enabled (`uvicorn reload=True`).

To test the Gemini connection in isolation:

```bash
GEMINI_API_KEY=<your-key> python scratch/test_gemini.py
```

## Environment

`GEMINI_API_KEY` must be set in the environment. The app does **not** read a `.env` file — pass it as a shell variable or export it before starting the server.

The SSL env vars at the top of `main.py` (`CURL_CA_BUNDLE`, `REQUESTS_CA_BUNDLE`, `HF_HUB_DISABLE_CERT_VERIFICATION`) disable certificate verification — they exist to work around a local network proxy and must stay.

## Architecture

```
main.py          — FastAPI app: two endpoints (/upload, /translate-kannada)
ai_engine.py     — LegalDocumentAnalyzer class: PDF extraction, chunked Gemini prompting, chart generation
static/
  index.html     — Single-page app shell; all sections exist in DOM simultaneously, shown/hidden by JS
  script.js      — All client logic: upload, display, language switching, state management
  style.css      — All styles; glassmorphism design system with CSS custom properties
```

### Request Flow

1. **`POST /upload`** — Receives PDF → `ai_engine.analyze_document()` → returns JSON with `summary`, `risks`, `obligations`, `financial_terms`, `clauses`, `complex_terms`, `metadata`, `chart` (base64 PNG), `severity_chart` (base64 PNG).

2. **`POST /translate-kannada`** — Receives a JSON body with all text fields → single Gemini call translating all values at once → returns same JSON structure with Kannada values. Badge prefixes like `[High]`, `[Payment]` are intentionally kept in English so JS badge/filter logic still works.

### `ai_engine.py` — Key Details

- **Lazy model loading**: `self.llm` starts as `None`. Call `_load_model()` before using `self.llm` (the `/translate-kannada` endpoint does this; `analyze_document` does too internally).
- **Chunked analysis**: Long PDFs are split into ~4000-char chunks via `langchain_text_splitters.RecursiveCharacterTextSplitter`. Each chunk is analyzed separately; results are aggregated.
- **Parser**: The Gemini output is parsed with a section-header state machine (looks for `Summary:`, `Risks:`, `Obligations:`, etc.). Badged items like `[High] risk text` have special regex handling that fires before the normal parser.
- **Model**: `gemini-2.5-flash` via the `google.generativeai` package (deprecated — migration to `google.genai` is pending; see the FutureWarning at import time).

### `script.js` — State & Language System

Four module-level variables carry all runtime state:
- `englishData` — raw JSON from `/upload`; never mutated after assignment
- `kannadaData` — cached JSON from `/translate-kannada`; `null` until first KN click; set to `null` on new analysis
- `currentLang` — `'en'` or `'kn'`
- `emptyFields` — `Set` of list element IDs that had no content at analysis time; used by `populateList` so empty-state rendering works in both languages

Key functions:
- `displayResults(data)` — first display only; calls `trackEmptyFields`, `applyData`, sets chart `src`s, resets nav to Summary
- `applyData(data, animate?)` — updates all text fields and lists without touching charts; called on every language switch
- `applyLanguageLabels(lang)` — swaps `.nav-label` text nodes and `.page-title` text (re-prepending `<i>` icons after `textContent` wipe), toggles `.lang-active` on lang buttons
- `populateList(elementId, items)` — renders a list; uses `emptyFields.has(elementId)` rather than English string matching for empty-state detection

### `index.html` — DOM Structure

The app has two top-level views: `#initial-view` (upload + loading) and `#app-view` (analysis results). Both exist in the DOM; visibility is toggled via `.hidden` class.

Inside `#app-view`, seven `.page-section` elements are shown one at a time via the nav. The active section gets class `active`; others get `display:none` + `hidden`.

Nav buttons carry `data-page` attributes matching section IDs. Language-switchable text lives in `<span class="nav-label" data-en="..." data-kn="...">` inside each button. Page titles carry `data-en`/`data-kn` attributes on the `<h2>`.

## Backup Files

`static/index_backup.html`, `static/index_working.html`, `static/script_working.js`, `main_working.py`, `ai_engine_working.py`, `ai_engine_phi_working.py` are historical snapshots. The `*_phi_working` variants used a local Phi-3 GGUF model (via `llama_cpp`) before the project switched to Gemini. Do not delete them — they serve as rollback points.

## Known Issues / Debt

- `requirements.txt` is outdated: it lists `PyPDF2`, `transformers`, `torch`, `reportlab` which are no longer used. Actual runtime deps are `fastapi`, `uvicorn`, `python-multipart`, `pdfplumber`, `langchain-text-splitters`, `google-generativeai`, `matplotlib`.
- `google.generativeai` package is deprecated; future migration target is `google.genai`.
- The `test_prompt.py` file in the root still references `llama_cpp` and the local Phi-3 model — it is from the pre-Gemini era and will fail if run.
