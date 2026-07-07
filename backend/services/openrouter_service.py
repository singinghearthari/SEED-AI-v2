import os
import time
import json
import base64
import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger("OpenRouterService")

VISION_MODEL = "google/gemma-4-26b-a4b-it:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterService:
    _instance = None

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self._available = bool(self.api_key)
        if not self._available:
            logger.warning("OPENROUTER_API_KEY not set — OpenRouter unavailable")

    @classmethod
    def get_instance(cls) -> "OpenRouterService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def available(self) -> bool:
        return self._available

    @property
    def model(self) -> str:
        return VISION_MODEL

    def analyze_plant_disease(
        self,
        image_bytes: bytes,
        crop: str = "crop",
        detections: Optional[list] = None,
    ) -> Dict[str, Any]:
        if not self._available:
            return {"status": "error", "message": "OpenRouter API key not configured"}

        detection_summary = ""
        if detections:
            confs = [f"{d['label']} ({d['confidence']:.1%})" for d in detections]
            detection_summary = "YOLO detection results: " + ", ".join(confs)

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            f"You are an expert plant pathologist and agricultural scientist. "
            f"Analyze this {crop} leaf image carefully.\n\n"
            f"{detection_summary}\n\n"
            "Provide a detailed expert analysis in the following JSON format (ONLY valid JSON, no markdown):\n"
            "{\n"
            '  "disease": "name of the disease or Healthy",\n'
            '  "severity": "Low/Medium/High/Critical",\n'
            '  "confidence": <overall confidence 0-100>,\n'
            '  "causes": "detailed explanation of what caused this condition",\n'
            '  "affected_area_percent": <estimated percentage>,\n'
            '  "symptoms": "visible symptoms observed",\n'
            '  "treatment": "recommended treatment plan",\n'
            '  "prevention": "prevention measures for future",\n'
            '  "organic_remedies": "organic/biological treatment options if available",\n'
            '  "immediate_action": "what the farmer should do right now",\n'
            '  "visual_explanation": "detailed visual description of what is seen"\n'
            "}"
        )

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.1,
        }

        try:
            start = time.time()
            resp = requests.post(
                url=OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            latency_ms = (time.time() - start) * 1000

            if resp.status_code != 200:
                logger.error(f"OpenRouter API error: {resp.status_code} {resp.text[:200]}")
                return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}

            data = resp.json()
            result_text = data["choices"][0]["message"]["content"].strip().strip("` \n")
            if result_text.startswith("json\n"):
                result_text = result_text[5:]

            try:
                parsed = json.loads(result_text)
            except json.JSONDecodeError:
                parsed = {"raw_response": result_text}

            return {
                "status": "success",
                "analysis": parsed,
                "model": VISION_MODEL,
                "latency_ms": round(latency_ms, 1),
            }

        except requests.Timeout:
            logger.error("OpenRouter request timed out after 60s")
            return {"status": "error", "message": "Request timed out"}
        except Exception as e:
            logger.error(f"OpenRouter vision analysis failed: {e}")
            return {"status": "error", "message": str(e)}
