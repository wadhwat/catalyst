# CATalyst Inspect

Backend-first setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.api.server
```

Notes:
- The backend will live under `src/` and expose a FastAPI server.
- The Expo app will live under `app/`.
- Copy `.env.example` to `.env` for secrets.
- CI uses `pytest` and includes a Supermemory integration test. To enable it in GitHub Actions,
  set repository secrets `SUPERMEMORY_API_KEY` (required) and `SUPERMEMORY_BASE_URL` (optional).
