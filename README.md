# CATalyst Inspect

Backend-only workspace.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.api.server
```

Notes:
- Backend code lives under `src/`.
- Frontend files were removed so a new UI can be generated from scratch.
- Copy `.env.example` to `.env` for secrets.
- CI uses `pytest` and includes a Supermemory integration test. To enable it in GitHub Actions,
  set repository secrets `SUPERMEMORY_API_KEY` (required) and `SUPERMEMORY_BASE_URL` (optional).
