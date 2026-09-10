"""FastAPI entry point for SnapChef inference."""

from functools import lru_cache
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from snapchef_ai.recommend import RecipeRecommender

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@lru_cache(maxsize=1)
def get_recommender() -> RecipeRecommender:
    return RecipeRecommender()


def _cors_origins() -> list[str]:
    configured = os.getenv("SNAPCHEF_CORS_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


app = FastAPI(title="SnapChef AI API")
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
    return {"classes": get_recommender().class_names}


@app.post("/api/predict")
async def predict_recipe(file: UploadFile = File(...)):
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
        with NamedTemporaryFile(delete=False, suffix=ALLOWED_IMAGE_TYPES[file.content_type]) as temp:
            temp.write(payload)
            temporary_path = Path(temp.name)
        try:
            with Image.open(temporary_path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as error:
            raise HTTPException(400, "Choose a valid image and try again.") from error
        return {"status": "success", **get_recommender().recommend(temporary_path)}
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
