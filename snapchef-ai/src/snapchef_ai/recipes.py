"""Ingredient-based recipe search and ranking.

The engine works on a prebuilt artifact (see scripts/build_recipe_index.py) so a
request never scans the 4M-row recipe corpus.
"""

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from snapchef_ai.ingredients import contains_term, normalize_text, word_pattern

BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = BASE_DIR / "data" / "processed"
RECIPE_PATH = BASE_DIR / "data" / "raw" / "receiptfood_dataset" / "recipes.parquet"
META_PATH = ARTIFACT_DIR / "recipe_meta.parquet"
WEIGHTS_PATH = Path(__file__).with_name("ranking_weights.json")
SUBSTITUTIONS_PATH = Path(__file__).with_name("substitutions.json")

RATING_PRIOR_COUNT = 10.0
ECONOMY_MISSING_CAP = 10
MIN_INGREDIENTS = 3
SUPPLY_FLOOR = 4
META_ROW_GROUP = 1024
COMPONENTS = (
    "coverage",
    "name",
    "position",
    "supply",
    "economy",
    "rating",
    "popularity",
)
RESPONSE_COLUMNS = [
    "RecipeId",
    "Name",
    "Description",
    "Images",
    "TotalTime",
    "RecipeServings",
    "AggregatedRating",
    "ReviewCount",
    "RecipeIngredientQuantities",
    "RecipeIngredientParts",
    "RecipeInstructions",
]


def as_list(value: Any) -> list[Any]:
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


def load_weights(path: Path = WEIGHTS_PATH) -> dict[str, float]:
    weights = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(weights) != set(COMPONENTS):
        raise ValueError(f"ranking weights must define exactly {COMPONENTS}")
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"ranking weights must sum to 1.0, got {total}")
    return weights


def load_substitutions(path: Path = SUBSTITUTIONS_PATH) -> dict[str, list[str]]:
    if not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


class RecipeEngine:
    """Rank recipes by how well they match a basket of detected ingredients."""

    def __init__(
        self,
        artifact_dir: Path = ARTIFACT_DIR,
        recipe_path: Path = RECIPE_PATH,
        weights: dict[str, float] | None = None,
    ):
        payload = np.load(artifact_dir / "recipe_index.npz")
        self.ing_id = payload["ing_id"].astype(np.int32)
        self.rec_idx = payload["rec_idx"].astype(np.int32)
        self.pos = payload["pos"].astype(np.int8)
        self.name_hit = payload["name_hit"].astype(np.float32)
        self.offsets = payload["offsets"].astype(np.int64)
        self.total_per_recipe = payload["total_per_recipe"].astype(np.int32)
        self.recipe_ids = payload["recipe_ids"].astype(np.int64)
        self.meta_positions = payload["meta_positions"].astype(np.int32)
        self.meta_row_group = (
            int(payload["meta_row_group"])
            if "meta_row_group" in payload
            else META_ROW_GROUP
        )
        self.ratings = payload["ratings"].astype(np.float32)
        self.reviews = payload["reviews"].astype(np.float32)
        self.mean_rating = float(payload["mean_rating"])
        self.max_reviews = max(1, int(payload["max_reviews"]))

        vocab = pl.read_parquet(artifact_dir / "ingredient_vocab.parquet")
        self.vocab_text = vocab["text"].to_list()
        self.weights = weights or load_weights()
        self.substitutions = load_substitutions()
        artifact_meta = artifact_dir / "recipe_meta.parquet"
        self.recipe_path = artifact_meta if artifact_meta.exists() else recipe_path
        self.recipe_count = len(self.recipe_ids)

        votes = self.reviews
        prior = RATING_PRIOR_COUNT
        self.rating_bayes = (
            (votes / (votes + prior)) * self.ratings
            + (prior / (votes + prior)) * self.mean_rating
        ) / 5.0
        self.popularity = np.clip(
            np.log1p(self.reviews) / math.log1p(self.max_reviews), 0.0, 1.0
        )
        self._resolve_cache: dict[str, list[int]] = {}

    def resolve(self, term: str) -> list[int]:
        """Vocabulary ids whose text contains the whole term."""
        normalized = normalize_text(term)
        if not normalized:
            return []
        if normalized in self._resolve_cache:
            return self._resolve_cache[normalized]
        pattern = word_pattern(normalized)
        ids = [
            index for index, text in enumerate(self.vocab_text) if pattern.search(text)
        ]
        self._resolve_cache[normalized] = ids
        return ids

    def components(self, items: list[str]) -> dict[str, Any]:
        """Return the per-recipe scoring components for a basket (0..1 each)."""
        resolved: list[tuple[str, list[int]]] = []
        unknown: list[str] = []
        for item in items:
            term = normalize_text(item)
            vids = self.resolve(term) if term else []
            if vids and term:
                resolved.append((term, vids))
            else:
                unknown.append(str(item))

        empty = np.zeros((0, len(COMPONENTS)), dtype=np.float32)
        if not resolved:
            return {
                "terms": [],
                "unknown": unknown,
                "ids": np.zeros(0, dtype=np.int64),
                "matrix": empty,
                "missing": np.zeros(0, dtype=np.int32),
                "rating": np.zeros(0, dtype=np.float32),
                "popularity": np.zeros(0, dtype=np.float32),
                "matched": np.zeros(0, dtype=np.float32),
            }

        count = self.recipe_count
        coverage_sum = np.zeros(count, dtype=np.float32)
        position_sum = np.zeros(count, dtype=np.float32)
        name_sum = np.zeros(count, dtype=np.float32)
        matched = np.zeros(count, dtype=np.float32)
        total_idf = 0.0

        for _, vids in resolved:
            pair_index = np.concatenate(
                [np.arange(self.offsets[v], self.offsets[v + 1]) for v in vids]
            )
            recipes = self.rec_idx[pair_index]
            positions = self.pos[pair_index]
            hits = self.name_hit[pair_index]

            order = np.lexsort((positions, recipes))
            recipes, positions, hits = recipes[order], positions[order], hits[order]
            first = np.concatenate(([True], recipes[1:] != recipes[:-1]))
            recipes, positions, hits = recipes[first], positions[first], hits[first]

            idf = math.log((count + 1) / (len(recipes) + 1))
            total_idf += idf
            position_score = np.clip(1.0 - positions / 5.0, 0.0, 1.0)
            # recipes is deduplicated above, so fancy-index accumulation is safe.
            coverage_sum[recipes] += idf
            position_sum[recipes] += position_score.astype(np.float32)
            name_sum[recipes] += hits.astype(np.float32)
            matched[recipes] += 1.0

        candidates = np.flatnonzero(matched > 0)
        candidates = candidates[self.total_per_recipe[candidates] >= MIN_INGREDIENTS]
        if candidates.size == 0:
            return {
                "terms": [term for term, _ in resolved],
                "unknown": unknown,
                "ids": np.zeros(0, dtype=np.int64),
                "matrix": empty,
                "missing": np.zeros(0, dtype=np.int32),
                "rating": np.zeros(0, dtype=np.float32),
                "popularity": np.zeros(0, dtype=np.float32),
                "matched": np.zeros(0, dtype=np.float32),
            }

        coverage = coverage_sum[candidates] / max(total_idf, 1e-9)
        position = position_sum[candidates] / matched[candidates]
        name_match = name_sum[candidates] / matched[candidates]
        supply = np.clip(
            matched[candidates]
            / np.maximum(self.total_per_recipe[candidates], SUPPLY_FLOOR),
            0.0,
            1.0,
        )
        missing = np.maximum(self.total_per_recipe[candidates] - matched[candidates], 0)
        economy = 1.0 - np.minimum(missing, ECONOMY_MISSING_CAP) / ECONOMY_MISSING_CAP
        rating = self.rating_bayes[candidates]
        popularity = self.popularity[candidates]

        matrix = np.stack(
            [coverage, name_match, position, supply, economy, rating, popularity],
            axis=1,
        ).astype(np.float32)
        return {
            "terms": [term for term, _ in resolved],
            "unknown": unknown,
            "ids": self.recipe_ids[candidates],
            "matrix": matrix,
            "missing": missing.astype(np.int32),
            "rating": rating,
            "popularity": popularity,
            "matched": matched[candidates],
        }

    def rank(
        self,
        components: dict[str, Any],
        limit: int = 5,
        weights: dict[str, float] | None = None,
    ) -> list[int]:
        ids = components["ids"]
        if ids.size == 0:
            return []
        vector = np.array(
            [
                self.weights[name] if weights is None else weights[name]
                for name in COMPONENTS
            ],
            dtype=np.float32,
        )
        score = components["matrix"] @ vector
        pool = min(ids.size, max(limit * 20, 100))
        shortlist = (
            np.argpartition(-score, pool - 1)[:pool]
            if pool < ids.size
            else np.arange(ids.size)
        )
        order = np.lexsort(
            (
                ids[shortlist],
                -components["rating"][shortlist],
                components["missing"][shortlist],
                -score[shortlist],
            )
        )
        return [int(index) for index in shortlist[order[:limit]]]

    def recommend(self, items: list[str], limit: int = 5) -> dict[str, Any]:
        components = self.components(items)
        if components["ids"].size == 0:
            return {
                "ingredients": components["terms"],
                "unknown": components["unknown"],
                "recommendations": [],
            }

        vector = np.array([self.weights[name] for name in COMPONENTS], dtype=np.float32)
        score = components["matrix"] @ vector
        top = self.rank(components, limit)
        rows = self._metadata([int(components["ids"][index]) for index in top])

        recommendations = []
        for index in top:
            row = rows.get(int(components["ids"][index]))
            if row is None:
                continue
            matrix = components["matrix"][index]
            recommendations.append(
                self._format(
                    row,
                    score=float(score[index]),
                    coverage=float(matrix[0]),
                    main=0.5 * float(matrix[1]) + 0.5 * float(matrix[2]),
                    supply=float(matrix[3]),
                    missing=int(components["missing"][index]),
                    terms=components["terms"],
                )
            )
        return {
            "ingredients": components["terms"],
            "unknown": components["unknown"],
            "recommendations": recommendations,
        }

    def get_recipe(self, recipe_id: int) -> dict[str, Any] | None:
        if int(recipe_id) not in set(self.recipe_ids.tolist()):
            return None
        rows = self._metadata([recipe_id])
        row = rows.get(recipe_id)
        if row is None:
            return None
        return self._format(
            row,
            score=0.0,
            coverage=0.0,
            main=0.0,
            supply=0.0,
            missing=0,
            terms=[],
        )

    def _metadata(self, recipe_ids: list[int]) -> dict[int, dict[str, Any]]:
        if not recipe_ids:
            return {}
        present = [
            rid for rid in recipe_ids if int(rid) in set(self.recipe_ids.tolist())
        ]
        if not present:
            return {}
        positions = self.meta_positions[np.searchsorted(self.recipe_ids, present)]
        groups = sorted(
            {int(position) // self.meta_row_group for position in positions}
        )
        frames = [
            pl.scan_parquet(self.recipe_path)
            .select(RESPONSE_COLUMNS)
            .slice(group * self.meta_row_group, self.meta_row_group)
            .collect()
            for group in groups
        ]
        frame = pl.concat(frames).filter(pl.col("RecipeId").is_in(present))
        return {int(row["RecipeId"]): row for row in frame.to_dicts()}

    def _format(
        self,
        row: dict[str, Any],
        score: float,
        coverage: float,
        main: float,
        supply: float,
        missing: int,
        terms: list[str],
    ) -> dict[str, Any]:
        parts = as_list(row.get("RecipeIngredientParts"))
        quantities = as_list(row.get("RecipeIngredientQuantities"))
        matched_names: list[str] = []
        missing_names: list[str] = []
        for part in parts:
            normalized = normalize_text(part)
            if any(contains_term(term, normalized) for term in terms):
                matched_names.append(part)
            else:
                missing_names.append(part)

        substitutions = {}
        for name in missing_names:
            normalized = normalize_text(name)
            for key, options in self.substitutions.items():
                if contains_term(normalize_text(key), normalized):
                    substitutions[name] = options
                    break

        images = as_list(row.get("Images"))
        return {
            "id": int(row["RecipeId"]),
            "name": row.get("Name"),
            "description": row.get("Description"),
            "image_url": images[0] if images else None,
            "total_time": row.get("TotalTime"),
            "servings": row.get("RecipeServings"),
            "rating": row.get("AggregatedRating"),
            "review_count": row.get("ReviewCount"),
            "match_score": round(score, 4),
            "coverage": round(coverage, 4),
            "main_relevance": round(main, 4),
            "supply": round(supply, 4),
            "missing_count": missing,
            "matched_ingredients": matched_names,
            "missing_ingredients": missing_names,
            "substitutions": substitutions,
            "ingredients": [
                {
                    "quantity": quantities[index] if index < len(quantities) else None,
                    "name": name,
                }
                for index, name in enumerate(parts)
            ],
            "instructions": as_list(row.get("RecipeInstructions")),
        }
