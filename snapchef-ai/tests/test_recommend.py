import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import torch
from PIL import Image

from snapchef_ai.recommend import RecipeRecommender, decide_known


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


if __name__ == "__main__":
    unittest.main()
