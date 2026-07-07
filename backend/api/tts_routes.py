"""
SEED AI — TTS API Routes (edge-tts)
Multilingual voice narration with auto-detection, generation, and caching.
"""
import logging
from fastapi import APIRouter, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from services.tts_service import TTSService

logger = logging.getLogger("TTSRoutes")
router = APIRouter(prefix="/tts", tags=["TTS"])
tts = TTSService.get_instance()


class TTSGenerateRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    rate: str = "+0%"
    language: Optional[str] = None


@router.get("/languages")
def list_languages():
    """List supported languages with native names and voice counts."""
    langs = tts.get_languages()
    enriched = []
    for l in langs:
        voices = tts.get_voices(language=l["code"])
        enriched.append({**l, "voices": len(voices)})
    return {
        "languages": enriched,
        "default": "en",
        "auto_detect": True,
    }


@router.get("/voices")
def list_voices(language: Optional[str] = Query(None, description="Filter by language code (e.g. hi, ta, en)")):
    """List available TTS voices, optionally filtered by language."""
    return {
        "voices": tts.get_voices(language=language),
        "total": len(tts.get_voices()),
        "available": tts.is_available(),
    }


@router.post("/detect")
def detect_text_language(text: str = Body(..., embed=True)):
    """Detect the language of the given text using Unicode script analysis."""
    detected = tts.detect_language(text)
    recommended_voice = tts.get_voice_for_language(detected)
    return {
        "detected_language": detected,
        "recommended_voice": recommended_voice,
        "available_voices": len(tts.get_voices(language=detected)),
    }


@router.post("/generate")
async def generate_speech(request: TTSGenerateRequest):
    """
    Generate TTS audio from text with auto-language detection.
    If voice is specified, uses that voice.
    If language is specified, picks best voice for that language.
    Otherwise auto-detects from text.
    """
    if not request.text.strip():
        return JSONResponse({"status": "error", "message": "Text cannot be empty"}, status_code=400)

    voice = request.voice
    if not voice and request.language:
        voice = tts.get_voice_for_language(request.language)

    result = await tts.generate_async(
        text=request.text,
        voice=voice,
        rate=request.rate,
    )

    if result["status"] != "success":
        return JSONResponse(result, status_code=502)

    return result


@router.get("/audio/{cache_key}")
def serve_audio(cache_key: str):
    """Serve a cached TTS audio file with long-term caching headers."""
    from pathlib import Path
    from services.tts_service import CACHE_DIR

    audio_file = CACHE_DIR / f"{cache_key}.mp3"
    if not audio_file.exists():
        return JSONResponse({"status": "error", "message": "Audio not found"}, status_code=404)

    return FileResponse(
        path=str(audio_file),
        media_type="audio/mpeg",
        filename="seed-ai-narration.mp3",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@router.post("/cache/clear")
def clear_cache(days: int = Query(7, description="Max age in days")):
    """Clear expired TTS cache entries."""
    removed = tts.clear_cache(max_age_days=days)
    return {"status": "ok", "removed": removed}
