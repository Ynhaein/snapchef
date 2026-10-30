"""Food classification and recipe recommendation services."""

from dataclasses import asdict, dataclass
import csv
import os
from pathlib import Path
from typing import Any

import polars as pl
from PIL import Image
import torch
from torchvision import transforms

from snapchef_ai.model import get_model

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "best_food_model.pth"
RECIPE_DATA_DIR = BASE_DIR / "data" / "raw" / "receiptfood_dataset"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MIN_CONFIDENCE = float(os.getenv("SNAPCHEF_MIN_CONFIDENCE", "0.70"))
MIN_MARGIN = float(os.getenv("SNAPCHEF_MIN_MARGIN", "0.20"))
TOP_K = 3

inference_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


@dataclass(frozen=True)
class PredictionCandidate:
    label: str
    confidence: float


@dataclass(frozen=True)
class PredictionResult:
    label: str
    is_known: bool
    confidence: float
    margin: float
    candidates: list[PredictionCandidate]

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "is_known": self.is_known,
            "confidence": self.confidence,
            "margin": self.margin,
            "top_candidates": [asdict(candidate) for candidate in self.candidates],
        }


def decide_known(confidence: float, margin: float) -> bool:
    return confidence >= MIN_CONFIDENCE and margin >= MIN_MARGIN


DETECTION_NOTE = (
    "detection_score is the raw detector output, not a calibrated probability. "
    "Thresholds are selected on a calibration split."
)


def route_prediction(
    detected_items: list[dict[str, Any]],
    prediction: PredictionResult,
    labels: dict[str, Any],
) -> dict[str, Any]:
    """Decide whether recipes come from ingredients, a prepared dish, or nothing."""
    ingredients = sorted(
        {
            item["label"]
            for item in detected_items
            if item.get("type") == "ingredient" and item.get("status") == "detected"
        }
    )
    if ingredients:
        return {
            "path": "ingredient",
            "ingredient_labels": ingredients,
            "needs_confirmation": [],
        }

    uncertain = sorted(
        {
            item["label"]
            for item in detected_items
            if item.get("type") == "ingredient" and item.get("status") == "uncertain"
        }
    )
    if uncertain:
        return {
            "path": "uncertain",
            "ingredient_labels": [],
            "needs_confirmation": uncertain,
        }

    prediction_label = (
        prediction.get("label")
        if isinstance(prediction, dict)
        else getattr(prediction, "label")
    )
    prediction_is_known = (
        prediction.get("is_known")
        if isinstance(prediction, dict)
        else getattr(prediction, "is_known")
    )
    label = labels.get(prediction_label)
    if prediction_is_known and label is not None and label.type == "prepared":
        return {"path": "dish", "ingredient_labels": [], "needs_confirmation": []}

    return {"path": "unknown", "ingredient_labels": [], "needs_confirmation": []}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return [value]
    value = value.strip()
    if not value or value == "NA":
        return []
    if value.startswith("c(") and value.endswith(")"):
        return [
            item
            for item in next(csv.reader([value[2:-1]], skipinitialspace=True))
            if item and item != "NA"
        ]
    return [value]


class RecipeRecommender:
    def __init__(
        self, model_path: Path = MODEL_PATH, recipe_dir: Path = RECIPE_DATA_DIR
    ):
        self.device = DEVICE
        self.model, self.class_names = self._load_model(model_path)
        self.recipes = self._load_recipes(recipe_dir)

    def _load_model(self, model_path: Path):
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}.")
        checkpoint = torch.load(model_path, map_location=self.device)
        model = get_model(checkpoint["num_classes"], pretrained=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(self.device).eval()
        return model, checkpoint["class_names"]

    @staticmethod
    def _load_recipes(recipe_dir: Path) -> pl.LazyFrame | None:
        parquet_path = recipe_dir / "recipes.parquet"
        csv_path = recipe_dir / "recipes.csv"
        if parquet_path.exists():
            frame = pl.scan_parquet(parquet_path)
        elif csv_path.exists():
            frame = pl.scan_csv(csv_path, infer_schema_length=10_000)
        else:
            return None
        return frame.rename(
            {name: name.lower() for name in frame.collect_schema().names()}
        )

    def classify_image(self, image_path: Path) -> PredictionResult:
        with Image.open(image_path) as source:
            image = source.convert("RGB")
        input_tensor = inference_transform(image).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            probabilities = torch.softmax(self.model(input_tensor), dim=1)[0]

        count = min(TOP_K, len(self.class_names))
        confidences, indices = torch.topk(probabilities, k=count)
        candidates = [
            PredictionCandidate(self.class_names[index.item()], confidence.item())
            for confidence, index in zip(confidences, indices)
        ]
        confidence = candidates[0].confidence
        margin = confidence - (candidates[1].confidence if len(candidates) > 1 else 0.0)
        is_known = decide_known(confidence, margin)
        return PredictionResult(
            label=candidates[0].label if is_known else "unknown",
            is_known=is_known,
            confidence=confidence,
            margin=margin,
            candidates=candidates,
        )

    def predict_image(self, image_path: Path):
        prediction = self.classify_image(image_path)
        return prediction.label, prediction.confidence * 100

    def get_recipe(self, food_name: str, limit: int = 5) -> pl.DataFrame:
        if self.recipes is None:
            return pl.DataFrame()
        query = food_name.replace("_", " ").lower()
        frame = self.recipes.filter(
            pl.col("name")
            .cast(pl.String)
            .str.to_lowercase()
            .str.contains(query, literal=True)
        )
        schema = frame.collect_schema().names()
        sorting = [
            name for name in ("aggregatedrating", "reviewcount") if name in schema
        ]
        if sorting:
            frame = frame.sort(sorting, descending=True, nulls_last=True)
        response_columns = [
            "recipeid",
            "name",
            "description",
            "images",
            "preptime",
            "cooktime",
            "totaltime",
            "recipeservings",
            "aggregatedrating",
            "reviewcount",
            "recipeingredientquantities",
            "recipeingredientparts",
            "recipeinstructions",
        ]
        return (
            frame.select([name for name in response_columns if name in schema])
            .limit(limit)
            .collect()
        )

    def get_recipes(self, food_name: str, limit: int = 5) -> list[dict[str, Any]]:
        rows = self.get_recipe(food_name, limit).to_dicts()
        recipes = []
        for row in rows:
            quantities = _as_list(row.get("recipeingredientquantities"))
            parts = _as_list(row.get("recipeingredientparts"))
            images = _as_list(row.get("images"))
            recipes.append(
                {
                    "id": int(row["recipeid"])
                    if row.get("recipeid") is not None
                    else None,
                    "name": row.get("name"),
                    "description": row.get("description"),
                    "image_url": images[0] if images else None,
                    "prep_time": row.get("preptime"),
                    "cook_time": row.get("cooktime"),
                    "total_time": row.get("totaltime"),
                    "servings": row.get("recipeservings"),
                    "rating": row.get("aggregatedrating"),
                    "review_count": row.get("reviewcount"),
                    "ingredients": [
                        {
                            "quantity": quantities[index]
                            if index < len(quantities)
                            else None,
                            "name": name,
                        }
                        for index, name in enumerate(parts)
                    ],
                    "instructions": _as_list(row.get("recipeinstructions")),
                }
            )
        return recipes

    def recommend(self, image_path: Path) -> dict[str, Any]:
        prediction = self.classify_image(image_path)
        return {
            "prediction": prediction.to_dict(),
            "recipes": self.get_recipes(prediction.label)
            if prediction.is_known
            else [],
        }


if __name__ == "__main__":
    recommender = RecipeRecommender()
    sample_dir = BASE_DIR / "data" / "raw" / "imagefood_dataset" / "224" / "test"
    sample_images = list(sample_dir.glob("*/*.jpg")) + list(sample_dir.glob("*/*.png"))
    if sample_images:
        print(recommender.recommend(sample_images[0]))
    else:
        print("Sample image file not found for testing.")
