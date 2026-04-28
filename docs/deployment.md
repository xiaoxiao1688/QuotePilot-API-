# Deployment

## Rule

This project must run from the project-local `.venv`. The system Python is used only once to create `.venv`.

## Database

The backend now persists quote history through SQLAlchemy.

- Default local database: `sqlite:///./data/app.db`
- MySQL deployment database: set `DATABASE_URL` in `.env`

Example:

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/ai_quote_assistant?charset=utf8mb4
```

## Local Deployment Steps

```powershell
.\scripts\setup_venv.ps1
.\scripts\smoke_test.ps1
.\scripts\run_prod.ps1
```

You can override the port if needed:

```powershell
.\scripts\run_prod.ps1 -Port 18000
```

## What Goes Into `.venv`

- `fastapi`
- `uvicorn`
- `pydantic`
- `pydantic-settings`
- `python-multipart`
- `SQLAlchemy`
- `PyMySQL`
- `scikit-learn`
- `joblib`
- all transitive runtime dependencies

## Ports

- Default bind host: `0.0.0.0`
- Default port: `8000`

## Health Check

`GET /api/v1/health`

## Notes

- If you later add OCR or OpenAI integration, keep those Python packages installed through `.venv\Scripts\python.exe -m pip install ...`
- If you deploy behind Nginx or another reverse proxy later, keep the app process command unchanged and proxy traffic to `127.0.0.1:8000`
- The local risk model file is stored under `models/quote_risk_model.joblib` and is loaded directly by the app
- The local text model file is stored under `models/quote_text_classifier.joblib` and is loaded directly by the app
