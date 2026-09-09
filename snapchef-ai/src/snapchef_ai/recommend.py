# %% [markdown] 
# ## 1. Import Libraries 

# %%
from dataclasses import asdict, dataclass
import os
from pathlib import Path 
from typing import Any
import torch 
import polars as pl
from PIL import Image 
from torchvision import transforms 
from snapchef_ai.model import get_model

# Set up paths 
BASE_DIR = Path(__file__).resolve().parents[2] 
MODEL_PATH = BASE_DIR / "models" / "best_food_model.pth" 
RECIPE_DATA_DIR = BASE_DIR / "data" / "raw" / "receiptfood_dataset" 

DEVICE = 'cuda' if torch.cuda.is_available() else "cpu" 
MIN_CONFIDENCE = float(os.getenv("SNAPCHEF_MIN_CONFIDENCE", "0.70"))
MIN_MARGIN = float(os.getenv("SNAPCHEF_MIN_MARGIN", "0.20"))
TOP_K = 3


@dataclass(frozen=True)
class PredictionCandidate:
    """One model candidate with a probability in the 0-1 range."""

    label: str
    confidence: float


@dataclass(frozen=True)
class PredictionResult:
    """Prediction enriched with an abstention decision and alternatives."""

    label: str
    is_known: bool
    confidence: float
    margin: float
    candidates: list[PredictionCandidate]

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "candidates": [asdict(candidate) for candidate in self.candidates],
        }


def decide_known(confidence: float, margin: float) -> bool:
    """Apply the lightweight confidence guardrails used during inference."""
    return confidence >= MIN_CONFIDENCE and margin >= MIN_MARGIN

# Transformation for inference
inference_transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Perbaikan: Standar MobileNet adalah 224x224
    transforms.ToTensor(), 
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# %% [markdown] 
# ## 2. Core Recommender System Class

# %%
class RecipeRecommender:
    def __init__(self, model_path: Path = MODEL_PATH, recipe_dir: Path = RECIPE_DATA_DIR):
        """
        Initialize the recommendation system by loading the ML model and recipe database.
        """
        self.device = DEVICE
        self.model, self.class_names = self._load_model(model_path)
        self.recipes_df = self._load_recipes(recipe_dir)

    def _load_model(self, model_path: Path):
        """Load model weights and class_names metadata from a .pth file."""
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}. Run train.py first.")

        checkpoint = torch.load(model_path, map_location=self.device)
        class_names = checkpoint['class_names']
        num_classes = checkpoint['num_classes']

        model = get_model(num_classes=num_classes, pretrained=False)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()

        return model, class_names

    def _load_recipes(self, recipe_dir: Path) -> pl.DataFrame:
        """Load the recipe dataset (supports CSV or JSON) using Polars."""
        csv_files = list(recipe_dir.glob("*.csv"))
        json_files = list(recipe_dir.glob("*.json"))

        if csv_files:
            df = pl.read_csv(csv_files[0])
        elif json_files:
            df = pl.read_json(json_files[0])
        else:
            print(f" Warning: No CSV/JSON file found in {recipe_dir}. Using mock dataset mode.")
            return pl.DataFrame()

        # Rename kolom ke lowercase
        rename_dict = {col: col.lower().strip() for col in df.columns}
        df = df.rename(rename_dict)
        return df

    def classify_image(self, image_path: Path) -> PredictionResult:
        """Return top candidates and abstain when the result is ambiguous."""
        image = Image.open(image_path).convert("RGB")
        input_tensor = inference_transform(image).unsqueeze(0).to(self.device)

        with torch.inference_mode():
            outputs = self.model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]

        count = min(TOP_K, len(self.class_names))
        confidences, indices = torch.topk(probabilities, k=count)
        candidates = [
            PredictionCandidate(self.class_names[index.item()], confidence.item())
            for confidence, index in zip(confidences, indices)
        ]
        top_confidence = candidates[0].confidence
        runner_up = candidates[1].confidence if len(candidates) > 1 else 0.0
        margin = top_confidence - runner_up
        is_known = decide_known(top_confidence, margin)

        return PredictionResult(
            label=candidates[0].label if is_known else "unknown",
            is_known=is_known,
            confidence=top_confidence,
            margin=margin,
            candidates=candidates,
        )

    def predict_image(self, image_path: Path):
        """Backward-compatible top-1 prediction returning confidence percent."""
        prediction = self.classify_image(image_path)
        return prediction.label, prediction.confidence * 100

    def get_recipe(self, food_name: str) -> pl.DataFrame:
        """Find recipe details based on the predicted food name using Polars expressions."""
        if self.recipes_df.is_empty():
            return pl.DataFrame()

        search_query = food_name.replace("_", " ").lower()

        # Filter Polars: Mencari kata kunci pada semua kolom berulang/string
        # Membuat kondisi OR untuk setiap kolom string di DataFrame
        string_cols = [col for col, dtype in zip(self.recipes_df.columns, self.recipes_df.dtypes) if dtype == pl.Utf8]
        
        if not string_cols:
            return pl.DataFrame()

        # Buat ekspresi filter
        filter_expr = pl.any_horizontal([
            pl.col(col).str.to_lowercase().str.contains(search_query) 
            for col in string_cols
        ])

        matched_recipes = self.recipes_df.filter(filter_expr)
        return matched_recipes

    def recommend(self, image_path: Path):
        """Main pipeline: Image Input -> Prediction -> Recipe Recommendation."""
        print(f"\n Analyzing image: {image_path.name}...")
        prediction = self.classify_image(image_path)
        predicted_food = prediction.label
        confidence = prediction.confidence * 100
        
        print(f" Predicted Food : {predicted_food.upper()} (Confidence: {confidence:.2f}%)")
        print("-" * 50)

        recipes = self.get_recipe(predicted_food) if prediction.is_known else pl.DataFrame()

        if not recipes.is_empty():
            print(f" Found {len(recipes)} matching recipes:")
            return {
                "food_name": predicted_food,
                "confidence": confidence,
                "is_known": prediction.is_known,
                "margin": prediction.margin,
                "top_candidates": [asdict(candidate) for candidate in prediction.candidates],
                "recipes": recipes
            }
        else:
            print(f" No recipe for '{predicted_food}' is available in the CSV/JSON database.")
            return {
                "food_name": predicted_food,
                "confidence": confidence,
                "is_known": prediction.is_known,
                "margin": prediction.margin,
                "top_candidates": [asdict(candidate) for candidate in prediction.candidates],
                "recipes": None
            }

# %% [markdown]
# ## 3. Testing & Debugging (Interactive Mode)

# %%
if __name__ == "__main__":
    recommender = RecipeRecommender()

    sample_image_dir = BASE_DIR / "data" / "raw" / "imagefood_dataset" / "224" / "test"
    sample_images = list(sample_image_dir.glob("*/*.jpg")) + list(sample_image_dir.glob("*/*.png"))
    
    if sample_images:
        test_image_path = sample_images[0]
        result = recommender.recommend(test_image_path)
        
        if result["recipes"] is not None:
            print("\nRecipe Data Preview (Polars Head):")
            print(result["recipes"].head(5))
    else:
        print("Sample image file not found for testing.")
