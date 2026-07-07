"""
SEED AI — Qwen2.5-VL Expert Explanation Service
Uses Hugging Face Inference API to run Qwen/Qwen2.5-VL-7B-Instruct for
expert-level plant disease analysis, waste classification insights,
treatment recommendations, and prevention advice.
Falls back gracefully if the model is unavailable.
"""
import os
import time
import base64
import logging
import json
from typing import Optional, Dict, Any, List
from huggingface_hub import InferenceClient
from io import BytesIO
from PIL import Image

logger = logging.getLogger("QwenVisionService")

QWEN_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"


class QwenVisionService:
    _instance = None

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("HUGGING_FACE_API", "")
        self.client = None
        self._available = False

        if not self.api_key:
            logger.warning("HUGGING_FACE_API not set — Qwen Vision unavailable")
            return

        try:
            self.client = InferenceClient(token=self.api_key)
            self._available = True
            logger.info(f"Qwen Vision client initialized ({QWEN_MODEL})")
        except Exception as e:
            logger.warning(f"Qwen Vision init failed: {e}")
            self._available = False

    @classmethod
    def get_instance(cls) -> "QwenVisionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def available(self) -> bool:
        return self._available and self.client is not None

    def analyze_plant_disease(
        self,
        image_bytes: bytes,
        crop: str = "crop",
        detections: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        return self._analyze(image_bytes, mode="disease", crop=crop, detections=detections)

    def analyze_waste(
        self,
        image_bytes: bytes,
        detections: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        return self._analyze(image_bytes, mode="waste", detections=detections)

    def _analyze(
        self,
        image_bytes: bytes,
        mode: str = "disease",
        crop: str = "crop",
        detections: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        if not self.available:
            return {"status": "error", "message": "Qwen Vision client not available"}

        detection_summary = ""
        if detections:
            labels = [d["label"] for d in detections]
            confs = [f"{d['label']} ({d['confidence']:.1%})" for d in detections]
            detection_summary = "Detection results: " + ", ".join(confs)

        if mode == "disease":
            prompt = (
                "You are an expert plant pathologist and agricultural scientist. "
                "Analyze this crop leaf image carefully.\n\n"
                f"Crop type: {crop}\n"
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
        else:
            prompt = (
                "You are an expert in waste management and recycling. "
                "Analyze this waste image carefully.\n\n"
                f"{detection_summary}\n\n"
                "Provide a detailed expert analysis in the following JSON format (ONLY valid JSON, no markdown):\n"
                "{\n"
                '  "waste_type": "classification of waste",\n'
                '  "material": "specific material identified",\n'
                '  "confidence": <overall confidence 0-100>,\n'
                '  "recyclable": true/false,\n'
                '  "disposal_method": "recommended disposal or recycling method",\n'
                '  "environmental_impact": "assessment of environmental impact",\n'
                '  "value_recovery": "potential value recovery or upcycling options",\n'
                '  "visual_explanation": "detailed visual description"\n'
                "}"
            )

        try:
            pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
            start = time.time()

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": pil_image},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            response = self.client.chat.completions.create(
                model=QWEN_MODEL,
                messages=messages,
                max_tokens=1024,
                temperature=0.1,
            )

            latency_ms = (time.time() - start) * 1000
            result_text = response.choices[0].message.content.strip()
            result_text = result_text.strip("` \n")
            if result_text.startswith("json"):
                result_text = result_text[4:]

            try:
                parsed = json.loads(result_text)
            except json.JSONDecodeError:
                parsed = {"raw_response": result_text}

            return {
                "status": "success",
                "analysis": parsed,
                "model": QWEN_MODEL,
                "latency_ms": round(latency_ms, 1),
            }

        except Exception as e:
            error_str = str(e)
            logger.error(f"Qwen Vision analysis failed ({mode}): {error_str}")
            return {"status": "error", "message": error_str}
