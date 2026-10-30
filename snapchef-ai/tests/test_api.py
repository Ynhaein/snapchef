import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from snapchef_ai.api import app

from tests.test_recipes import make_parquet

client = TestClient(app)


class RecommendationEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()
        root = Path(cls.tmp.name)
        make_parquet(root / "recipes.parquet")
        from scripts.build_recipe_index import build

        build(root / "recipes.parquet", root / "artifact")
        from snapchef_ai.recipes import RecipeEngine

        cls.engine = RecipeEngine(
            artifact_dir=root / "artifact", recipe_path=root / "recipes.parquet"
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_recommend_returns_ranked_recipes(self):
        with patch("snapchef_ai.api.get_engine", return_value=self.engine):
            response = client.post(
                "/api/recommend", json={"ingredients": ["apple"], "limit": 3}
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["recommendations"])
        self.assertGreaterEqual(payload["recommendations"][0]["match_score"], 0)

    def test_recommend_rejects_empty_basket(self):
        response = client.post("/api/recommend", json={"ingredients": []})
        self.assertEqual(response.status_code, 422)

    def test_recommend_rejects_blank_ingredient(self):
        with patch("snapchef_ai.api.get_engine", return_value=self.engine):
            response = client.post("/api/recommend", json={"ingredients": ["   "]})
        self.assertEqual(response.status_code, 400)

    def test_recommend_does_not_load_the_classifier(self):
        with (
            patch("snapchef_ai.api.get_engine", return_value=self.engine),
            patch(
                "snapchef_ai.api.get_recommender",
                side_effect=AssertionError("classifier loaded"),
            ),
        ):
            response = client.post("/api/recommend", json={"ingredients": ["banana"]})
        self.assertEqual(response.status_code, 200)

    def test_classes_endpoint_keeps_legacy_field(self):
        class Stub:
            class_names = ["apple", "banana"]

        with patch("snapchef_ai.api.get_recommender", return_value=Stub()):
            response = client.get("/api/classes")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["classes"], ["apple", "banana"])
        self.assertEqual(len(payload["items"]), 15)

    def test_predict_keeps_legacy_validation(self):
        response = client.post(
            "/api/predict", files={"file": ("notes.txt", b"hello", "text/plain")}
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
