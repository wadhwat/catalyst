# Supermemory Setup for Inspection Reports

When configured, `/inspect/infer` stores each inspection report (including findings and recommended parts) in Supermemory.

## 1. Get Supermemory credentials

**Option A — Supermemory Cloud**
- Sign up at [console.supermemory.ai](https://console.supermemory.ai)
- Create an API key
- Use:
  - `SUPERMEMORY_BASE_URL=https://api.supermemory.ai` (or the URL shown in the console)
  - `SUPERMEMORY_API_KEY=your_key`
  - `SUPERMEMORY_WORKSPACE=your_workspace` (if required)

**Option B — Self-hosted Supermemory**
- Deploy Supermemory on your infrastructure
- Set `SUPERMEMORY_BASE_URL` to your instance (e.g. `http://localhost:8080`)
- Set `SUPERMEMORY_API_KEY` if your deployment requires auth

## 2. Configure your `.env`

```bash
SUPERMEMORY_API_KEY=sk-...
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
SUPERMEMORY_WORKSPACE=your_workspace   # optional
```

## 3. API expectations

The Catalyst backend sends:

- **POST** to `{SUPERMEMORY_BASE_URL}/memories` (or `SUPERMEMORY_CREATE_PATH`)
- Body: `{ "type": "inspection_report", "content": {...}, "tags": [...], "metadata": {...} }`
- `content` includes: `inspection_id`, `vin`, `findings`, `report` (with `recommended_parts` per item), `processing_stats`, `errors`

If your Supermemory API uses different paths or payload fields, set:

- `SUPERMEMORY_CREATE_PATH` — override the create endpoint
- `SUPERMEMORY_SEARCH_PATH` — override the search endpoint

## 4. Search later

Use Supermemory search (via its API or dashboard) with tags:

- `inspection:{inspection_id}` — one inspection
- `vin:{vin}` — all inspections for a vehicle
- `user:{user_id}` — all inspections for a user
- `kind:inspection_report` — all inspection reports

## 5. Verify

After running an inspection:

1. Check logs for `Stored inspection ... in Supermemory`
2. Query Supermemory for `kind:inspection_report` to confirm the record
