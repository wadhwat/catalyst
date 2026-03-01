"""
ElevenLabs TTS proxy. Keeps API key server-side.
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tts"])


class TTSRequest(BaseModel):
    text: str


def _get_api_key() -> str | None:
    return os.getenv("ELEVENLABS_API_KEY")


def _get_voice_id() -> str:
    return os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel


@router.post("/tts")
async def tts(req: TTSRequest) -> Response:
    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="TTS not configured (missing ELEVENLABS_API_KEY)")
    text = (req.text or "").strip()
    if not text or len(text) > 500:
        raise HTTPException(status_code=400, detail="Text must be 1-500 characters")
    voice_id = _get_voice_id()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={"text": text, "model_id": "eleven_flash_v2_5"},
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
            )
        if resp.status_code != 200:
            logger.warning("ElevenLabs TTS error %d: %s", resp.status_code, resp.text[:200])
            raise HTTPException(status_code=502, detail="TTS service error")
        return Response(content=resp.content, media_type="audio/mpeg")
    except httpx.RequestError as e:
        logger.warning("ElevenLabs request failed: %s", e)
        raise HTTPException(status_code=502, detail="TTS service unreachable")
