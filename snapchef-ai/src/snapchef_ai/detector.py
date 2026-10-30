"""Pretrained ingredient detector (SSDLite320, COCO weights).

This module never trains or fine-tunes. The model output is a raw
**Detection Score**, not a calibrated probability. Thresholds live in
taxonomy.json and are selected on a calibration split (see B3).
"""

from dataclasses import asdict, dataclass
from typing import Any

from PIL import Image
import torch
from torchvision.models.detection import (
    SSDLite320_MobileNet_V3_Large_Weights,
    ssdlite320_mobilenet_v3_large,
)

from snapchef_ai.taxonomy import Label, detector_labels, load_taxonomy

# Keep low-recall candidates so the calibration step can pick thresholds.
MIN_DETECTION_SCORE = 0.05


@dataclass(frozen=True)
class Detection:
    label: str
    display_name: str
    detection_score: float
    box: tuple[float, float, float, float]
    experimental: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "display_name": self.display_name,
            "detection_score": round(self.detection_score, 4),
            "box": [round(value, 4) for value in self.box],
            "experimental": self.experimental,
        }


class IngredientDetector:
    def __init__(self, labels: dict[str, Label] | None = None):
        self.labels = labels or load_taxonomy()
        self.by_coco_name = detector_labels(self.labels)
        self.weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
        self.model = ssdlite320_mobilenet_v3_large(weights=self.weights).eval()
        self.transforms = self.weights.transforms()

    def detect(
        self, image: Image.Image, min_score: float = MIN_DETECTION_SCORE
    ) -> list[Detection]:
        rgb = image.convert("RGB")
        tensor = self.transforms(rgb)
        with torch.inference_mode():
            output = self.model([tensor])[0]

        categories = self.weights.meta["categories"]
        detections: list[Detection] = []
        size_h = float(tensor.shape[-2])
        size_w = float(tensor.shape[-1])
        for box, score, category in zip(
            output["boxes"].tolist(),
            output["scores"].tolist(),
            output["labels"].tolist(),
        ):
            if score < min_score:
                continue
            label = self.by_coco_name.get(categories[category])
            if label is None:
                continue
            normalized = (
                min(max(box[0] / size_w, 0.0), 1.0),
                min(max(box[1] / size_h, 0.0), 1.0),
                min(max(box[2] / size_w, 0.0), 1.0),
                min(max(box[3] / size_h, 0.0), 1.0),
            )
            detections.append(
                Detection(
                    label=label.name,
                    display_name=label.display_name,
                    detection_score=float(score),
                    box=normalized,
                    experimental=label.experimental,
                )
            )
        detections.sort(key=lambda item: (-item.detection_score, item.label))
        return detections

    def items(self, image: Image.Image) -> list[dict[str, Any]]:
        """One entry per ingredient label, with status from taxonomy thresholds."""
        best: dict[str, Detection] = {}
        for detection in self.detect(image):
            best.setdefault(detection.label, detection)
        items = []
        for label_name, detection in best.items():
            label = self.labels[label_name]
            if detection.detection_score >= label.score_threshold:
                status = "detected"
            elif detection.detection_score >= label.low_threshold:
                status = "uncertain"
            else:
                status = "ignored"
            payload = asdict(detection)
            payload["status"] = status
            payload["type"] = label.type
            payload["display_name"] = label.display_name
            payload["detection_score"] = round(detection.detection_score, 4)
            payload["box"] = [round(value, 4) for value in detection.box]
            items.append(payload)
        items.sort(key=lambda item: (-item["detection_score"], item["label"]))
        return [item for item in items if item["status"] != "ignored"]


if __name__ == "__main__":
    from pathlib import Path

    sample = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "raw"
        / "imagefood_dataset"
        / "224"
        / "test"
    )
    images = sorted(sample.glob("*/*.jpg"))[:1] + sorted(sample.glob("*/*.png"))[:1]
    detector = IngredientDetector()
    for path in images:
        with Image.open(path) as image:
            print(path.name, detector.items(image))
