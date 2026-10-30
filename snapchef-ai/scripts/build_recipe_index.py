"""Build the ingredient -> recipe index used by the recommendation engine.

Run once (or whenever the recipe corpus changes):
    uv run python -m scripts.build_recipe_index
"""

from pathlib import Path
import time

import numpy as np
import polars as pl

from snapchef_ai.ingredients import normalize_text

BASE_DIR = Path(__file__).resolve().parents[1]
RECIPE_PATH = BASE_DIR / "data" / "raw" / "receiptfood_dataset" / "recipes.parquet"
OUT_DIR = BASE_DIR / "data" / "processed"
COLUMNS = [
    "RecipeId",
    "Name",
    "RecipeIngredientParts",
    "AggregatedRating",
    "ReviewCount",
]
META_ROW_GROUP = 1024


def build(recipe_path: Path = RECIPE_PATH, out_dir: Path = OUT_DIR) -> dict[str, float]:
    started = time.perf_counter()
    frame = (
        pl.read_parquet(recipe_path, columns=COLUMNS)
        .sort("RecipeId")
        .with_row_index("rec_idx")
        .with_columns(
            pl.col("Name")
            .cast(pl.String)
            .map_elements(normalize_text, return_dtype=pl.String)
            .alias("name_norm")
        )
    )
    frame = frame.with_columns(
        pl.int_ranges(0, pl.col("RecipeIngredientParts").list.len()).alias("pos")
    ).explode(["RecipeIngredientParts", "pos"])

    frame = frame.drop_nulls("RecipeIngredientParts").with_columns(
        pl.col("RecipeIngredientParts")
        .cast(pl.String)
        .map_elements(normalize_text, return_dtype=pl.String)
        .alias("part_norm")
    )
    frame = frame.filter(pl.col("part_norm").str.len_chars() > 0)
    # Recipes without an ingredient list leave gaps in rec_idx; remap to a dense range.
    ordered_recipes = (
        frame.select("rec_idx").unique().sort("rec_idx")["rec_idx"].to_numpy()
    )
    frame = frame.with_columns(
        pl.Series(
            "rec_idx",
            np.searchsorted(ordered_recipes, frame["rec_idx"].to_numpy()).astype(
                np.int32
            ),
        )
    )

    vocab = (
        frame.select(pl.col("part_norm").alias("text"))
        .unique()
        .sort("text")
        .with_row_index("ing_id")
    )
    frame = frame.join(vocab, left_on="part_norm", right_on="text", how="left")

    names = frame["name_norm"].to_list()
    parts = frame["part_norm"].to_list()
    recs = frame["rec_idx"].to_list()
    name_hits = np.zeros(len(parts), dtype=np.uint8)
    previous = -1
    tokens: set[str] = set()
    for index, (rec_idx, part) in enumerate(zip(recs, parts)):
        if rec_idx != previous:
            previous = rec_idx
            tokens = set(names[rec_idx].split())
        name_hits[index] = int(
            any(len(token) >= 3 and token in tokens for token in part.split())
        )

    frame = frame.with_columns(pl.Series("name_hit", name_hits))
    frame = frame.sort(["ing_id", "rec_idx", "pos"])

    ing_ids = frame["ing_id"].to_numpy().astype(np.uint16)
    rec_idx = frame["rec_idx"].to_numpy().astype(np.int32)
    positions = frame["pos"].to_numpy().astype(np.uint8)
    name_hit = frame["name_hit"].to_numpy().astype(np.uint8)

    vocab_size = vocab.height
    recipe_count = frame["rec_idx"].n_unique()
    offsets = np.zeros(vocab_size + 1, dtype=np.int64)
    np.cumsum(np.bincount(ing_ids, minlength=vocab_size), out=offsets[1:])

    total_per_recipe = (
        frame.group_by("rec_idx")
        .len()
        .sort("rec_idx")["len"]
        .to_numpy()
        .astype(np.uint8)
    )
    recipe_ids = (
        frame.select(["rec_idx", "RecipeId"])
        .unique("rec_idx")
        .sort("rec_idx")["RecipeId"]
        .to_numpy()
        .astype(np.int32)
    )

    ratings = (
        frame.select(["rec_idx", "AggregatedRating"]).unique("rec_idx").sort("rec_idx")
    )
    mean_rating = float(ratings["AggregatedRating"].mean() or 0.0)
    max_reviews = int(frame["ReviewCount"].max() or 0)
    meta = (
        frame.select(["rec_idx", "AggregatedRating", "ReviewCount"])
        .unique("rec_idx")
        .sort("rec_idx")
    )
    rating_array = (
        meta["AggregatedRating"].fill_null(mean_rating).to_numpy().astype(np.float32)
    )
    review_array = meta["ReviewCount"].fill_null(0).to_numpy().astype(np.int32)

    out_dir.mkdir(parents=True, exist_ok=True)
    meta = pl.read_parquet(recipe_path).sort("RecipeId")
    meta_ids = meta["RecipeId"].to_numpy()
    meta_positions = np.searchsorted(meta_ids, recipe_ids).astype(np.int32)
    meta.write_parquet(
        out_dir / "recipe_meta.parquet",
        row_group_size=META_ROW_GROUP,
        compression="zstd",
    )
    np.savez_compressed(
        out_dir / "recipe_index.npz",
        ing_id=ing_ids,
        rec_idx=rec_idx,
        pos=positions,
        name_hit=name_hit,
        offsets=offsets,
        total_per_recipe=total_per_recipe,
        recipe_ids=recipe_ids,
        meta_positions=meta_positions,
        meta_row_group=np.array(META_ROW_GROUP),
        ratings=rating_array,
        reviews=review_array,
        mean_rating=np.array(mean_rating, dtype=np.float32),
        max_reviews=np.array(max_reviews, dtype=np.int64),
    )
    vocab.write_parquet(out_dir / "ingredient_vocab.parquet")

    stats = {
        "recipes": int(recipe_count),
        "pairs": int(len(ing_ids)),
        "vocabulary": int(vocab_size),
        "seconds": round(time.perf_counter() - started, 1),
        "mean_rating": round(mean_rating, 3),
        "max_reviews": max_reviews,
        "artifact_mb": round(
            (out_dir / "recipe_index.npz").stat().st_size / 1024**2, 1
        ),
    }
    return stats


if __name__ == "__main__":
    for key, value in build().items():
        print(f"{key}: {value}")
