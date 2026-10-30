"""Tune and validate the recipe ranking weights.

Two signals are reported separately:
  * automatic: relevance = ingredient term appears in the recipe name (biased, large)
  * manual: graded 0-3 judgments in eval/ranking_judgments.json (small, independent)

Weights are selected on the automatic tune split, then checked on a hold-out
split and on the manual judgments. Run: uv run python -m scripts.tune_ranking
"""

from itertools import product
import json
import math
from pathlib import Path

import numpy as np

from snapchef_ai.recipes import COMPONENTS, RecipeEngine

BASE_DIR = Path(__file__).resolve().parents[1]
JUDGMENTS_PATH = BASE_DIR / "eval" / "ranking_judgments.json"

TUNE_BASKETS = [
    ["apple"],
    ["banana"],
    ["orange"],
    ["broccoli"],
    ["carrot"],
    ["egg"],
    ["tomato"],
    ["onion"],
    ["garlic"],
    ["chicken"],
]
HOLDOUT_BASKETS = [["strawberry"], ["potato"], ["mushroom"], ["lemon"], ["cheese"]]
MANUAL_BASKETS = [
    ["apple"],
    ["banana"],
    ["broccoli", "carrot"],
    ["egg", "tomato", "onion"],
    ["chicken", "garlic"],
]
FIXED = {"economy": 0.05, "rating": 0.05, "popularity": 0.05}


def ndcg(grades: list[int], k: int) -> float:
    gains = [
        (2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(grades[:k])
    ]
    ideal = sorted(grades, reverse=True)[:k]
    best = [(2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(ideal)]
    return sum(gains) / sum(best) if sum(best) else 0.0


def auto_grades(engine, basket, weights, k=10):
    components = engine.components(basket)
    rows = engine._metadata(
        [int(components["ids"][i]) for i in engine.rank(components, k, weights)]
    )
    terms = components["terms"]
    grades = []
    for recipe_id in engine.rank(components, k, weights):
        row = rows.get(int(components["ids"][recipe_id]))
        if row is None:
            grades.append(0)
            continue
        name = str(row["Name"]).lower()
        grades.append(1 if any(term in name for term in terms) else 0)
    return grades


def manual_grades(engine, basket, weights, judgments, k=5):
    components = engine.components(basket)
    ids = [int(components["ids"][i]) for i in engine.rank(components, k, weights)]
    grades = judgments.get("+".join(basket), {})
    return [grades.get(str(recipe_id), 0) for recipe_id in ids]


def evaluate(engine, baskets, weights_factory, judgments=None, k=10):
    scores = []
    for basket in baskets:
        weights = weights_factory(engine, basket)
        grades = (
            manual_grades(engine, basket, weights, judgments, 5)
            if judgments
            else auto_grades(engine, basket, weights, k)
        )
        scores.append(ndcg(grades, len(grades)))
    return float(np.mean(scores))


def main():
    engine = RecipeEngine()
    baseline = engine.weights
    judgments = json.loads(JUDGMENTS_PATH.read_text(encoding="utf-8"))["baskets"]

    grid = []
    for coverage, name, position, supply in product(
        (0.25, 0.35, 0.45), (0.10, 0.20, 0.30), (0.10, 0.15, 0.20), (0.05, 0.10, 0.15)
    ):
        scale = (1.0 - sum(FIXED.values())) / (coverage + name + position + supply)
        weights = {
            "coverage": coverage * scale,
            "name": name * scale,
            "position": position * scale,
            "supply": supply * scale,
            **FIXED,
        }
        grid.append(weights)

    results = []
    for index, weights in enumerate(grid):
        tune = evaluate(engine, TUNE_BASKETS, lambda _e, _b, w=weights: w)
        results.append((tune, index, weights))
    results.sort(reverse=True)

    print(f"baseline weights: {baseline}")
    print(
        "baseline tune  : %.4f"
        % evaluate(engine, TUNE_BASKETS, lambda _e, _b: baseline)
    )
    print(
        "baseline holdout: %.4f"
        % evaluate(engine, HOLDOUT_BASKETS, lambda _e, _b: baseline)
    )
    print(
        "baseline manual : %.4f"
        % evaluate(engine, MANUAL_BASKETS, lambda _e, _b: baseline, judgments)
    )
    print("\nper-basket manual nDCG@5 with baseline weights:")
    for basket in MANUAL_BASKETS:
        weights = baseline
        grades = manual_grades(engine, basket, weights, judgments, 5)
        print(
            "  %-26s grades=%s ndcg=%.3f" % ("+".join(basket), grades, ndcg(grades, 5))
        )

    print("\ntop configs on tune (auto nDCG@10):")
    for tune, index, weights in results[:5]:
        holdout = evaluate(engine, HOLDOUT_BASKETS, lambda _e, _b, w=weights: w)
        manual = evaluate(
            engine, MANUAL_BASKETS, lambda _e, _b, w=weights: w, judgments=judgments
        )
        print(
            "  tune=%.4f holdout=%.4f manual=%.4f  %s"
            % (
                tune,
                holdout,
                manual,
                {key: round(value, 3) for key, value in weights.items()},
            )
        )


if __name__ == "__main__":
    main()
