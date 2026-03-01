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
- The `POST /inspect/infer` endpoint calls an external GPU inference service (YOLO + Qwen). Set `INFERENCE_SERVICE_URL` to your deployed service (e.g. `http://your-gpu-ip:9000`).
- CI uses `pytest` and includes a Supermemory integration test. To enable it in GitHub Actions,
  set repository secrets `SUPERMEMORY_API_KEY` (required) and `SUPERMEMORY_BASE_URL` (optional).
