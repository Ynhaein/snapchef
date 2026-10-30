import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl

from snapchef_ai.ingredients import contains_term, normalize_text
from snapchef_ai.recipes import RecipeEngine, load_weights
from snapchef_ai.taxonomy import load_taxonomy

RECIPES = [
    (1, "Apple Pie", ["apple", "flour", "butter", "sugar"], 5.0, 100),
    (2, "Apple Juice", ["apple", "water", "sugar"], 4.0, 10),
    (3, "Fruit Fly Trap", ["apple", "water"], 5.0, 0),
    (4, "Banana Bread", ["banana", "flour", "sugar"], 4.5, 50),
    (5, "Apple Banana Smoothie", ["apple", "banana", "milk"], 4.0, 20),
    (6, "Tomato Soup", ["tomato", "onion", "garlic"], 3.0, 5),
    (7, "Pineapple Chicken", ["pineapple", "chicken", "garlic"], 4.0, 8),
    (8, "Broccoli Rabe", ["broccoli rabe", "garlic", "olive oil"], 4.0, 3),
]


def make_parquet(path: Path) -> None:
    pl.DataFrame(
        {
            "RecipeId": [row[0] for row in RECIPES],
            "Name": [row[1] for row in RECIPES],
            "RecipeIngredientParts": [row[2] for row in RECIPES],
            "RecipeIngredientQuantities": [["1"] * len(row[2]) for row in RECIPES],
            "AggregatedRating": [row[3] for row in RECIPES],
            "ReviewCount": [row[4] for row in RECIPES],
            "Description": ["desc"] * len(RECIPES),
            "Images": [[f"https://example.com/{row[0]}.jpg"] for row in RECIPES],
            "TotalTime": ["PT30M"] * len(RECIPES),
            "RecipeServings": [4] * len(RECIPES),
            "RecipeInstructions": [["Cook it."]] * len(RECIPES),
        }
    ).write_parquet(path)


class RecipeEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        make_parquet(root / "recipes.parquet")
        from scripts.build_recipe_index import build

        self.artifact = root / "artifact"
        build(root / "recipes.parquet", self.artifact)
        self.engine = RecipeEngine(
            artifact_dir=self.artifact, recipe_path=root / "recipes.parquet"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_whole_word_matching_skips_pineapple(self):
        result = self.engine.recommend(["apple"], limit=10)
        names = [item["name"] for item in result["recommendations"]]
        self.assertNotIn("Pineapple Chicken", names)
        self.assertIn("Apple Pie", names)

    def test_short_recipes_are_filtered(self):
        result = self.engine.recommend(["apple"], limit=10)
        self.assertNotIn(
            "Fruit Fly Trap", [item["name"] for item in result["recommendations"]]
        )

    def test_components_stay_in_unit_range(self):
        components = self.engine.components(["apple", "banana"])
        self.assertGreater(components["matrix"].size, 0)
        self.assertGreaterEqual(float(components["matrix"].min()), 0.0)
        self.assertLessEqual(float(components["matrix"].max()), 1.0)

    def test_ranking_is_deterministic(self):
        first = self.engine.recommend(["apple", "banana"])["recommendations"]
        second = self.engine.recommend(["apple", "banana"])["recommendations"]
        self.assertEqual(
            [item["id"] for item in first], [item["id"] for item in second]
        )

    def test_multiple_ingredients_rank_combined_recipe_first(self):
        result = self.engine.recommend(["apple", "banana"], limit=3)
        self.assertEqual(result["recommendations"][0]["name"], "Apple Banana Smoothie")

    def test_unknown_ingredient_is_reported(self):
        result = self.engine.recommend(["dragonfruit"], limit=3)
        self.assertEqual(result["unknown"], ["dragonfruit"])
        self.assertEqual(result["recommendations"], [])

    def test_matched_and_missing_ingredients_are_listed(self):
        result = self.engine.recommend(["apple"], limit=10)
        pie = next(
            item for item in result["recommendations"] if item["name"] == "Apple Pie"
        )
        self.assertEqual(pie["matched_ingredients"], ["apple"])
        self.assertIn("flour", pie["missing_ingredients"])
        self.assertIn("butter", pie["substitutions"])

    def test_taxonomy_is_valid(self):
        labels = load_taxonomy()
        self.assertEqual(len(labels), 15)
        self.assertEqual(sum(1 for label in labels.values() if label.is_ingredient), 5)
        self.assertTrue(labels["carrot"].experimental)

    def test_weights_must_sum_to_one(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "weights.json"
            path.write_text(json.dumps({"coverage": 0.5}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_weights(path)

    def test_normalization_and_whole_word_match(self):
        self.assertEqual(normalize_text("  Fresh  Apple (chopped) "), "fresh apple")
        self.assertTrue(contains_term("apple", "granny smith apple"))
        self.assertFalse(contains_term("apple", "pineapple"))


if __name__ == "__main__":
    unittest.main()
