"""FastAPI entry point for SnapChef inference."""

from functools import lru_cache
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import asyncio

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from snapchef_ai.detector import IngredientDetector
from snapchef_ai.recipes import RecipeEngine
from snapchef_ai.recommend import RecipeRecommender, route_prediction
from snapchef_ai.taxonomy import load_taxonomy

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@lru_cache(maxsize=1)
def get_recommender() -> RecipeRecommender:
    return RecipeRecommender()


@lru_cache(maxsize=1)
def get_detector() -> IngredientDetector:
    return IngredientDetector()


@lru_cache(maxsize=1)
def get_engine() -> RecipeEngine:
    return RecipeEngine()


class RecommendationRequest(BaseModel):
    ingredients: list[str] = Field(min_length=1, max_length=10)
    limit: int = Field(default=5, ge=1, le=10)


def _cors_origins() -> list[str]:
    configured = os.getenv("SNAPCHEF_CORS_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


app = FastAPI(
    title="SnapChef AI API",
    description=(
        "Food classification and ingredient-aware recipe recommendations. "
        "Detector scores are raw Detection Scores, not calibrated probabilities."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/classes")
def supported_classes():
    labels = load_taxonomy()
    return {
        "classes": get_recommender().class_names,
        "items": [
            {
                "name": name,
                "display_name": label.display_name,
                "type": label.type,
                "category": label.category,
                "experimental": label.experimental,
            }
            for name, label in labels.items()
        ],
    }


@app.post("/api/recommend")
def recommend_recipes(payload: RecommendationRequest):
    seen: set[str] = set()
    ingredients: list[str] = []
    for raw in payload.ingredients:
        value = raw.strip()
        if value and value.lower() not in seen:
            seen.add(value.lower())
            ingredients.append(value)
    if not ingredients:
        raise HTTPException(400, "Add at least one ingredient.")
    return {
        "status": "success",
        "path": "ingredient",
        **get_engine().recommend(ingredients, payload.limit),
    }


@app.post("/api/predict")
async def predict_recipe(file: UploadFile = File(...)):
    """Classify a dish photo and detect ingredient candidates.

    detected_items[].detection_score is a raw Detection Score, not a probability.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Choose a JPEG, PNG, or WebP image.")
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if not payload:
        raise HTTPException(400, "The uploaded image is empty.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Choose an image smaller than 5 MB.")

    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            delete=False, suffix=ALLOWED_IMAGE_TYPES[file.content_type]
        ) as temp:
            temp.write(payload)
            temporary_path = Path(temp.name)
        try:
            with Image.open(temporary_path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as error:
            raise HTTPException(400, "Choose a valid image and try again.") from error

        with Image.open(temporary_path) as image:
            rgb = image.convert("RGB")

        detected_items, result = await asyncio.gather(
            asyncio.to_thread(get_detector().items, rgb),
            asyncio.to_thread(get_recommender().recommend, temporary_path),
        )
        labels = load_taxonomy()
        route = route_prediction(detected_items, result["prediction"], labels)

        recipes = result["recipes"] if route["path"] == "dish" else []
        recommendations: list[
            dict[str, Any]
        ] = []  # candidate suggester: never auto-recommend unconfirmed visual predictions

        return {
            "status": "success",
            "prediction": result["prediction"],
            "recipes": recipes,
            "detected_items": detected_items,
            "recommendations": recommendations,
            "path": route["path"],
            "needs_confirmation": route["needs_confirmation"],
        }
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
