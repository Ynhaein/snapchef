import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import torch
from PIL import Image
import polars as pl

from snapchef_ai.recommend import RecipeRecommender, _as_list, decide_known


class FixedLogitModel(torch.nn.Module):
    def forward(self, inputs):
        return torch.tensor([[4.0, 1.0, 0.0]], device=inputs.device)


class DecideKnownTests(unittest.TestCase):
    @patch("snapchef_ai.recommend.MIN_MARGIN", 0.20)
    @patch("snapchef_ai.recommend.MIN_CONFIDENCE", 0.70)
    def test_accepts_confident_prediction_with_clear_margin(self):
        self.assertTrue(decide_known(0.90, 0.60))

    @patch("snapchef_ai.recommend.MIN_MARGIN", 0.20)
    @patch("snapchef_ai.recommend.MIN_CONFIDENCE", 0.70)
    def test_rejects_low_confidence_prediction(self):
        self.assertFalse(decide_known(0.60, 0.40))

    @patch("snapchef_ai.recommend.MIN_MARGIN", 0.20)
    @patch("snapchef_ai.recommend.MIN_CONFIDENCE", 0.70)
    def test_rejects_ambiguous_prediction(self):
        self.assertFalse(decide_known(0.75, 0.10))

    @patch("snapchef_ai.recommend.MIN_MARGIN", 0.20)
    @patch("snapchef_ai.recommend.MIN_CONFIDENCE", 0.70)
    def test_classification_returns_ranked_candidates(self):
        recommender = RecipeRecommender.__new__(RecipeRecommender)
        recommender.device = "cpu"
        recommender.model = FixedLogitModel()
        recommender.class_names = ["first", "second", "third"]

        with TemporaryDirectory() as directory:
            image_path = Path(directory) / "food.png"
            Image.new("RGB", (32, 32), color="white").save(image_path)
            prediction = recommender.classify_image(image_path)

        self.assertTrue(prediction.is_known)
        self.assertEqual(prediction.label, "first")
        self.assertEqual(
            [candidate.label for candidate in prediction.candidates],
            ["first", "second", "third"],
        )

    def test_parses_food_com_vector_strings(self):
        self.assertEqual(_as_list('c("1", "2")'), ["1", "2"])

    def test_recipe_results_are_ranked_limited_and_normalized(self):
        recommender = RecipeRecommender.__new__(RecipeRecommender)
        recommender.recipes = pl.DataFrame([
            {
                "recipeid": 1,
                "name": "Simple Gnocchi",
                "aggregatedrating": 4.0,
                "reviewcount": 10,
                "recipeingredientquantities": ["1"],
                "recipeingredientparts": ["potato"],
                "recipeinstructions": ["Cook it."],
                "images": [],
            },
            {
                "recipeid": 2,
                "name": "Best Gnocchi",
                "aggregatedrating": 5.0,
                "reviewcount": 20,
                "recipeingredientquantities": ["2"],
                "recipeingredientparts": ["potatoes"],
                "recipeinstructions": ["Boil them."],
                "images": ["https://example.com/gnocchi.jpg"],
            },
        ]).lazy()

        recipes = recommender.get_recipes("gnocchi", limit=1)

        self.assertEqual(recipes[0]["id"], 2)
        self.assertEqual(recipes[0]["ingredients"], [{"quantity": "2", "name": "potatoes"}])


if __name__ == "__main__":
    unittest.main()
