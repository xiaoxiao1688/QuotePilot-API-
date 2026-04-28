# QuotePilot API

QuotePilot is an AI-assisted quotation parsing and supplier comparison backend for a mini-program.

## Project Goals

- Upload or paste quotation content from chat, OCR, or PDF extraction
- Convert unstructured quotation text into normalized line items
- Compare multiple suppliers on price and delivery
- Generate a concise recommendation with basic risk flags

## Stack

- FastAPI
- Pydantic v2
- SQLAlchemy
- PyMySQL
- scikit-learn local risk model
- scikit-learn local text classifier
- `.venv` for local Python isolation

## Venv-Only Workflow

This project is intended to run only from the local `.venv`. Do not install project dependencies into the system interpreter.

## Quick Start

```powershell
.\scripts\setup_venv.ps1
.\scripts\run_dev.ps1
```

Open `http://127.0.0.1:8000/docs`.

By default the app persists data to `data/app.db`. To use MySQL, set `DATABASE_URL` in `.env`, for example:

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/ai_quote_assistant?charset=utf8mb4
```

## Manual Commands

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Production Run

```powershell
.\scripts\run_prod.ps1
.\scripts\run_prod.ps1 -Port 18000
```

This starts the API with `.venv\Scripts\python.exe` and binds to `0.0.0.0:8000` by default.

## Current API

- `GET /api/v1/health`
- `POST /api/v1/auth/demo-login`
- `POST /api/v1/quotes/parse`
- `POST /api/v1/quotes/compare`
- `GET /api/v1/quotes/history`
- `GET /api/v1/ai/model-info`
- `POST /api/v1/ai/analyze-text`

## Example Parse Request

```json
{
  "supplier_name": "Shenzhen Parts Co.",
  "source_text": "MacBook stand x 10 unit_price 88 lead_time 5 shipping 20 tax included"
}
```

## Next Backend Steps

1. Add file upload.
2. Add OCR pipeline and real LLM extraction adapter.
3. Introduce JWT auth, RBAC, and company-level isolation.
4. Add async task queue for parsing large files.
