# SnapChef

SnapChef is a full-stack food app: a React UI + FastAPI service that classifies a food photo (10 dishes) and recommends recipes from a 522k-recipe corpus. An optional SSDLite320 detector suggests ingredient candidates (experimental, requires user confirmation); a manual ingredient basket is the primary input for recommendations.

## Project structure

```text
snapchef/
├── snapchef-ai/        # Python backend (FastAPI, model, recipes, tests)
│   ├── data/raw/       # Datasets (gitignored)
│   ├── data/processed/ # Recipe index artifacts (gitignored, generated)
│   ├── models/         # MobileNetV3 checkpoint
│   ├── scripts/        # Index build, ranking tune, detector eval, benchmark
│   ├── src/snapchef_ai/
│   └── tests/
├── web/                # React + Vite frontend
└── DESIGN.md           # UI palette and content guidance
```

## Prerequisites

- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)
- Node.js 20.19+ or 22.12+ and [`pnpm`](https://pnpm.io/)

## Setup

```bash
git clone <repository-url>
cd snapchef

# Backend
cd snapchef-ai
uv sync
# Download datasets (see Dataset setup below), then build the recipe index:
uv run python -m scripts.build_recipe_index

# Frontend
cd ../web
pnpm install
```

### Dataset setup

1. [Food-101 Resized](https://www.kaggle.com/datasets/ekojsalim/food-101-resized) → `snapchef-ai/data/raw/imagefood_dataset/224/{train,test}/<class_name>/`
2. [Food.com Recipes and Reviews](https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews) → `snapchef-ai/data/raw/receiptfood_dataset/recipes.parquet` (preferred) or `recipes.csv`

Do not commit datasets or replace `models/best_food_model.pth` without coordination.

Optional frontend config (`web/.env.local`):

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Run

Terminal 1 (backend, from `snapchef-ai/`):

```bash
uv run uvicorn snapchef_ai.api:app --reload
```

API at `http://127.0.0.1:8000`, docs at `/docs`.

Terminal 2 (frontend, from `web/`):

```bash
pnpm dev
```

Open `http://localhost:5173`.

## Test

```bash
# Backend (from snapchef-ai/)
uv run python -m unittest discover -s tests -v

# Frontend (from web/)
pnpm test
pnpm lint
pnpm build
```

## Config

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Backend URL for the frontend |
| `SNAPCHEF_CORS_ORIGINS` | Local Vite origins | Allowed browser origins |
| `SNAPCHEF_MIN_CONFIDENCE` | `0.70` | Minimum confidence for a known prediction |
| `SNAPCHEF_MIN_MARGIN` | `0.20` | Minimum margin between top two classes |

## API

- `GET /health` — service status
- `GET /api/classes` — supported foods + taxonomy metadata
- `POST /api/predict` — classify an image; returns `prediction`, `detected_items`, `recommendations`, `recipes`, `path`
- `POST /api/recommend` — rank recipes for an ingredient basket

Detection scores are raw model scores, not calibrated probabilities.
