# VLM Pipeline & PDF Test Guide

How to test the full inspection pipeline (VLM + report + PDF) using a **single image**.

## Prerequisites

1. **Backend** – API server running
2. **EC2 inference** – GPU server with Qwen VLM (or mocked for unit tests)
3. **Environment** – `.env` with `INFERENCE_SERVICE_URL` and `OPENAI_API_KEY`

## Quick test (single frame → PDF)

### 1. Start the backend

```bash
cd /path/to/catalyst
python3 -m src.api.server
# or: uvicorn src.api.server:app --reload --host 0.0.0.0
```

### 2. Run a single-image inspection

```bash
curl -X POST http://localhost:8000/inspect \
  -F "file=@/path/to/your/image.jpg" \
  -F "machine_type=loader" \
  -F "niche=construction" \
  -F "client_trace_id=test-single-frame-001" \
  -F "vin=VIN12345"
```

**Form fields:**

| Field | Required | Example |
|-------|----------|---------|
| `file` | Yes | Image (jpg, png) or video |
| `machine_type` | Yes | `loader` |
| `niche` | Yes | `construction` |
| `client_trace_id` | Yes | Unique id (used as inspection_id) |
| `vin` | Yes | Serial/VIN |
| `engineer_notes` | No | Optional text |

If auth is enabled, add a Bearer token:

```bash
curl -X POST http://localhost:8000/inspect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.jpg" \
  ...
```

### 3. Inspect the response

The response JSON includes:

- `inspection_id` – same as `client_trace_id` (sanitized)
- `report_pdf_url` – e.g. `/media/inspections/test-single-frame-001/report.pdf`
- `evidence_frames` – frame filenames
- `evidence_urls` – URLs for frames
- `findings` – VLM defect findings
- `report` – structured report (items, summary)

### 4. Download or open the PDF

```bash
# Using the inspection_id from the response
curl -o report.pdf "http://localhost:8000/media/inspections/test-single-frame-001/report.pdf"
open report.pdf   # macOS
```

Or open in browser:  
`http://localhost:8000/media/inspections/test-single-frame-001/report.pdf`

## EC2 inference requirements

The `/inspect` endpoint calls `check_inference_health()` first. If the EC2 service is unreachable, you get `503`.

Ensure:

1. `INFERENCE_SERVICE_URL` in `.env` points to the EC2 endpoint (e.g. `http://<EC2_IP>:8000`)
2. EC2 inference server is running (`ec2_inference/server.py` or equivalent)
3. Network/firewall allows access from your machine

## Unit test (mocked pipeline)

For CI or local runs without EC2, use the existing test that mocks inference:

```bash
pytest tests/test_inspect_media.py -v
```

This mocks:

- `check_inference_health` → OK
- `classify_frames` → no VLM findings
- `generate_report_via_llm` → fallback report
- Frame extraction → blank frame for invalid image

The test asserts `report_pdf_url` is in the response and the PDF is created.

## PDF format

The generated PDF matches **Caterpillar EN_Mini_HEX_Safety & Maint. Inspection**:

- Header: HYDRAULIC EXCAVATOR, Safety & Maintenance Inspection (300.9-308)
- Meta: Operator, Date, Time, Serial Number (VIN), Machine Hours
- Sections: **FROM THE GROUND**, **ENGINE COMPARTMENT OR PLATFORMS**, **INSIDE THE CAB**
- Table columns: What are you inspecting? | √ | What are you looking for? | √ | Evaluator Comments
- Footer: Inspected by, Caterpillar legal text

## Troubleshooting

| Issue | Cause |
|-------|--------|
| `503` on `/inspect` | EC2 inference unreachable; check `INFERENCE_SERVICE_URL` |
| No `report_pdf_url` in response | PDF generation failed; check logs for `PDF generation failed` |
| `401` | Auth required; pass valid Bearer token |
| PDF 404 | Inspection directory or `report.pdf` missing; verify `data/inspections/{id}/` exists |
