# FitBuddy — AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite application that follows the supplied project documentation: it accepts a user's name, ID, age, weight, goal, and workout intensity; generates a 7-day plan and nutrition/recovery tip with Gemini; stores the data; and supports feedback-based plan revisions plus an admin dashboard.

## Architecture

- `app/main.py` — FastAPI application and static assets
- `app/routes.py` — HTML and API-facing route handlers
- `app/ai.py` — Google Gemini integration and structured-output validation
- `app/database.py` — SQLAlchemy ORM + SQLite persistence
- `app/schemas.py` — Pydantic validation and Gemini response schemas
- `app/config.py` — environment configuration
- `templates/` — Jinja2 pages
- `static/styles.css` — responsive UI
- `tests/` — smoke tests

The original documentation specifies Gemini 1.5 Pro and Gemini Flash and the legacy `google-generativeai` package. This implementation keeps the same Pro/Flash architectural split but uses Google's current `google-genai` SDK and configurable current model IDs. Google now recommends `google-genai` over the legacy Python SDK and supports Pydantic-based structured outputs. See the setup notes in the answer that accompanied this project.

## Quick start

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `GEMINI_API_KEY` plus a non-default `ADMIN_PASSWORD`.

Start:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` and API docs at `http://127.0.0.1:8000/docs`.

Admin dashboard: `http://127.0.0.1:8000/view-all-users` and enter the `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `.env` when prompted.

## Tests

```bash
pytest -q
```

The smoke tests do not call Gemini. To test the full AI flow, configure a valid `GEMINI_API_KEY` and submit a plan through the browser.

## Notes

- SQLite database is created at `data/fitbuddy.db` on first startup.
- Do not commit `.env` or the SQLite database to Git.
- This app is a wellness/fitness planning demo, not a medical device or medical-advice service.
