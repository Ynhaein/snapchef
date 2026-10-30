"""Label taxonomy shared by the classifier, detector, and recipe engine."""

from dataclasses import dataclass
import json
from pathlib import Path

TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")
VALID_TYPES = {"prepared", "ingredient"}


@dataclass(frozen=True)
class Label:
    name: str
    display_name: str
    type: str
    category: str
    aliases: tuple[str, ...]
    classifier: bool
    detector_label: str | None
    score_threshold: float
    low_threshold: float
    margin_threshold: float
    experimental: bool

    @property
    def is_ingredient(self) -> bool:
        return self.type == "ingredient"


def _to_label(name: str, payload: dict) -> Label:
    label = Label(
        name=name,
        display_name=payload["display_name"],
        type=payload["type"],
        category=payload["category"],
        aliases=tuple(payload.get("aliases", ())),
        classifier=bool(payload.get("classifier", False)),
        detector_label=payload.get("detector_label"),
        score_threshold=float(payload.get("score_threshold", 0.6)),
        low_threshold=float(payload.get("low_threshold", 0.3)),
        margin_threshold=float(payload.get("margin_threshold", 0.0)),
        experimental=bool(payload.get("experimental", False)),
    )
    if label.type not in VALID_TYPES:
        raise ValueError(f"{name}: unknown type {label.type!r}")
    if not 0.0 <= label.low_threshold < label.score_threshold <= 1.0:
        raise ValueError(f"{name}: thresholds must satisfy 0 <= low < score <= 1")
    return label


def load_taxonomy(path: Path = TAXONOMY_PATH) -> dict[str, Label]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {name: _to_label(name, item) for name, item in payload["labels"].items()}


def classifier_labels(labels: dict[str, Label]) -> list[str]:
    return [name for name, label in labels.items() if label.classifier]


def detector_labels(labels: dict[str, Label]) -> dict[str, Label]:
    """Map COCO category name -> taxonomy label."""
    return {
        label.detector_label: label for label in labels.values() if label.detector_label
    }


def ingredient_names(labels: dict[str, Label]) -> list[str]:
    return [name for name, label in labels.items() if label.is_ingredient]
