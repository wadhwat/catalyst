# CATalyst Inspect

Backend-first setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.api.server
```

The backend binds to `0.0.0.0:8000` so it's reachable from your LAN (e.g. `http://YOUR_LAN_IP:8000`).

## Expo app on your phone

```bash
cd app
cp .env.example .env
# Edit .env: set EXPO_PUBLIC_API_BASE_URL to your backend URL (e.g. http://192.168.1.100:8000)
# localhost does not work on a physical phone — use your machine's LAN IP
npm install
npx expo start
```

Scan the QR code with Expo Go. Ensure your phone and backend are on the same network.

## Configuration

- **Backend** (`.env` at repo root): Copy `.env.example` to `.env`. Set `INFERENCE_SERVICE_URL` to your EC2 GPU endpoint (e.g. `http://your-gpu-ip:9000`).
- **Expo** (`app/.env`): Set `EXPO_PUBLIC_API_BASE_URL` to your backend URL. Use LAN IP for phone testing.
- **CI**: Set `SUPERMEMORY_API_KEY` and `SUPERMEMORY_BASE_URL` as GitHub secrets.

## AI Use in Development

This project was built with assistance from AI tools (including Cursor, Codex, and Claude Code) for code generation, refactoring, and debugging. AI was used to accelerate implementation of features such as the inspection pipeline, PDF report generation, voice commands, and integration with external APIs.
