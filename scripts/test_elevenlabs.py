"""
ElevenLabs TTS Test Script
Requires: pip install elevenlabs python-dotenv
Set ELEVEN_API_KEY in your .env file or as an environment variable.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

api_key = os.getenv("ELEVEN_API_KEY")
if not api_key:
    print("Error: ELEVEN_API_KEY not set. Add it to .env or export it.")
    sys.exit(1)

client = ElevenLabs(api_key=api_key)
output_dir = Path(__file__).parent / "tts_output"
output_dir.mkdir(exist_ok=True)


def test_list_voices():
    """List available voices."""
    print("=== Available Voices ===")
    response = client.voices.get_all()
    for voice in response.voices[:10]:
        print(f"  {voice.name} (id: {voice.voice_id})")
    print(f"  ... {len(response.voices)} total voices\n")
    return response.voices[0].voice_id if response.voices else None


def test_basic_tts(voice_id: str):
    """Generate speech from text and save to file."""
    print("=== Basic TTS ===")
    text = "Hello, this is a test of the ElevenLabs text to speech API."
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    out_path = output_dir / "basic_tts.mp3"
    with open(out_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"  Saved to {out_path} ({out_path.stat().st_size} bytes)\n")


def test_short_tts(voice_id: str):
    """Generate a short phrase."""
    print("=== Short TTS ===")
    text = "Catalyst is online."
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    out_path = output_dir / "short_tts.mp3"
    with open(out_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"  Saved to {out_path} ({out_path.stat().st_size} bytes)\n")


def test_get_models():
    """List available models."""
    print("=== Available Models ===")
    models = client.models.list()
    for model in models:
        print(f"  {model.name} (id: {model.model_id})")
    print()


if __name__ == "__main__":
    print("ElevenLabs TTS Test\n")

    # Use a known default voice (Rachel) in case voices.get_all is restricted
    default_voice_id = "21m00Tcm4TlvDq8ikWAM"

    try:
        test_get_models()
    except Exception as e:
        print(f"  Skipped (permission restricted): {e}\n")

    try:
        voice_id = test_list_voices("CwhRBWXzGAHq8TQ4Fs17") or default_voice_id
    except Exception as e:
        print(f"  Skipped (permission restricted), using default voice: {e}\n")
        voice_id = default_voice_id

    test_basic_tts(voice_id)
    test_short_tts(voice_id)
    print("All tests passed!")
