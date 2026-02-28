# TODO

## Assumptions and Defaults
- Vehicle identity is provided via `vin`.
- Memory references store only file names + hashes (no raw media).
- ElevenLabs is deferred; guidance is text-only in the UI.
- Secrets via env vars only.

## Completed
- [x] Supermemory client + schema.
- [x] `/inspect` memory read/write integration with `vin` and optional `engineer_notes`.
- [x] Baseline rubric generator + report schema.
- [x] Rubric tests + pytest config for clean imports.
- [x] Supermemory tests with live gating.
- [x] Auth system (register/login/profile), JWT, SQLite users.
- [x] User-scoped memory routes (`/memories/add`, `/memories/search`).
- [x] CI workflow for pytest.
- [x] README note about Supermemory secrets.

## Next (Backlog Order)
- [ ] 6.1 Expo scaffold + Settings + health check.
- [ ] 6.2 Camera capture + upload (include `vin`, `engineer_notes`, auth token).
- [ ] 6.3 Results UI (status chips, summary, preferred_source banner, copy JSON).
- [ ] Figma: build new Home + Machine detail based on updated spec.
- [ ] 2.1 CLIP scorer (optional heavy deps).
- [ ] 3.1 Specialized model stub + 3.2 arbitration.
- [ ] 4.1-4.3 LLM reasoning + orchestrator.
- [ ] 7.1-7.2 polish (demo mode + pitch outputs).

## Notes
- Live Supermemory tests run only if `SUPERMEMORY_RUN_LIVE_TESTS=1`.
- CI secrets: `SUPERMEMORY_API_KEY` required, `SUPERMEMORY_BASE_URL` optional.
- Auth secrets: `JWT_SECRET`, `JWT_EXPIRE_MINUTES`.
- DB path: `CATALYST_DB_PATH`.
