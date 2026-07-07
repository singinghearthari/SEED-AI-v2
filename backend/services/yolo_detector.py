"""
SEED AI — YOLO11 Detection Service
Provides object detection for plant diseases and waste classification using Ultralytics YOLO11.
Runs locally on CPU/GPU with auto-detection. Falls back gracefully if model unavailable.
Returns bounding boxes, confidence scores, and annotated images.
"""
import os
import time
import base64
import logging
import io
from typing import Optional, List, Dict, Any
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("YOLODetector")

DISEASE_CLASS_NAMES = {
    0: "healthy_leaf", 1: "early_blight", 2: "late_blight",
    3: "leaf_rust", 4: "powdery_mildew", 5: "leaf_spot",
    6: "bacterial_wilt", 7: "mosaic_virus", 8: "yellow_leaf_curl",
    9: "leaf_blight", 10: "anthracnose", 11: "downy_mildew",
    12: "leaf_miner_damage", 13: "nutrient_deficiency", 14: "herbicide_damage",
    15: "healthy", 16: "diseased_leaf",
}

WASTE_CLASS_NAMES = {
    0: "organic_waste", 1: "plastic", 2: "paper", 3: "metal",
    4: "glass", 5: "e_waste", 6: "textile", 7: "rubber",
    8: "hazardous_waste", 9: "construction_debris",
}


def _download_model(model_path: str) -> bool:
    """Trigger YOLO model download by importing and instantiating."""
    try:
        from ultralytics import YOLO
        YOLO(model_path)
        return True
    except Exception as e:
        logger.warning(f"YOLO model download failed for {model_path}: {e}")
        return False


class YOLODetector:
    _instance = None
    _model = None
    _model_path = None

    def __init__(self, model_path: str = "yolo11n.pt"):
        self._model_path = model_path
        self._model = None
        self._available = False
        self._device = "cpu"
        self._load_model()

    @classmethod
    def get_instance(cls, model_path: str = "yolo11n.pt") -> "YOLODetector":
        if cls._instance is None or cls._model_path != model_path:
            cls._instance = cls(model_path=model_path)
            cls._model_path = model_path
        return cls._instance

    def _load_model(self):
        try:
            from ultralytics import YOLO
            import torch

            if torch.cuda.is_available():
                self._device = "cuda:0"
                logger.info("YOLO11: GPU detected, using CUDA")
            elif hasattr(torch, 'backends') and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self._device = "mps"
                logger.info("YOLO11: MPS detected, using Apple Silicon")
            else:
                self._device = "cpu"
                logger.info("YOLO11: Using CPU")

            self._model = YOLO(self._model_path)
            self._available = True
            logger.info(f"YOLO11 model loaded: {self._model_path} on {self._device}")
        except ImportError:
            logger.warning("ultralytics not installed. YOLO detection disabled.")
            self._available = False
        except Exception as e:
            logger.warning(f"YOLO model load failed: {e}")
            self._available = False

    @property
    def available(self) -> bool:
        return self._available and self._model is not None

    @property
    def device(self) -> str:
        return self._device

    def detect_plant_disease(
        self,
        image_bytes: bytes,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> Dict[str, Any]:
        return self._detect(image_bytes, mode="disease", conf_threshold=conf_threshold, iou_threshold=iou_threshold)

    def detect_waste(
        self,
        image_bytes: bytes,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> Dict[str, Any]:
        return self._detect(image_bytes, mode="waste", conf_threshold=conf_threshold, iou_threshold=iou_threshold)

    def _detect(
        self,
        image_bytes: bytes,
        mode: str = "disease",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> Dict[str, Any]:
        if not self.available:
            return {"status": "error", "message": "YOLO model not available"}

        class_names = DISEASE_CLASS_NAMES if mode == "disease" else WASTE_CLASS_NAMES

        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            orig_w, orig_h = pil_image.size

            start = time.time()
            results = self._model(
                pil_image,
                conf=conf_threshold,
                iou=iou_threshold,
                device=self._device,
                verbose=False,
            )
            inference_ms = (time.time() - start) * 1000

            detections = []
            annotated_image = pil_image.copy()
            draw = ImageDraw.Draw(annotated_image)

            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            color_map = [
                "#22c55e", "#ef4444", "#f59e0b", "#3b82f6",
                "#a855f7", "#ec4899", "#14b8a6", "#f97316",
            ]

            for result in results:
                if result.boxes is None:
                    continue
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                cls_ids = result.boxes.cls.cpu().numpy().astype(int)

                for box, conf, cls_id in zip(boxes, confs, cls_ids):
                    x1, y1, x2, y2 = map(float, box)
                    label = class_names.get(cls_id, f"class_{cls_id}")
                    color = color_map[cls_id % len(color_map)]

                    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                    text = f"{label} {conf:.2%}"
                    bbox = draw.textbbox((0, 0), text, font=font) if font else (0, 0, len(text) * 6, 10)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    draw.rectangle([x1, y1 - th - 4, x1 + tw + 8, y1], fill=color)
                    draw.text((x1 + 4, y1 - th - 2), text, fill="white", font=font)

                    detections.append({
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "label": label,
                        "confidence": round(float(conf), 4),
                        "class_id": int(cls_id),
                    })

            buf = io.BytesIO()
            annotated_image.save(buf, format="JPEG", quality=85)
            annotated_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            return {
                "status": "success",
                "mode": mode,
                "detections": detections,
                "detection_count": len(detections),
                "annotated_image_b64": annotated_b64,
                "inference_time_ms": round(inference_ms, 1),
                "image_size": {"width": orig_w, "height": orig_h},
                "device": self._device,
            }

        except Exception as e:
            logger.error(f"YOLO detection failed ({mode}): {e}")
            return {"status": "error", "message": str(e)}
