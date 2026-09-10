# SnapChef

SnapChef is a full-stack food analysis application that classifies an uploaded food image and recommends matching recipes. The current implementation combines a React single-page interface with a FastAPI service backed by a fine-tuned MobileNetV3 model.

The bundled checkpoint reaches **84.90% validation accuracy** across 10 supported Food-101 classes: bread pudding, chicken curry, donuts, garlic bread, gnocchi, samosa, sashimi, seaweed salad, spaghetti carbonara, and takoyaki. Images outside these classes may be returned as `unknown` when confidence or prediction margin is too low.

## Current Features

- Drag-and-drop or file-picker image upload for JPEG, PNG, and WebP files up to 5 MB.
- Food classification with confidence, top-three candidates, and unknown-image handling.
- Up to five ranked recipe recommendations with ingredients and instructions.
- Responsive React interface connected to the FastAPI prediction endpoint.
- Backend and frontend automated tests.

## Technology Stack

- **AI/API:** Python 3.12, PyTorch, Torchvision, FastAPI, Polars, and Uvicorn.
- **Frontend:** React 19, Vite 8, Tailwind CSS 4, shadcn/Base UI components, and Hugeicons.
- **Testing:** Python `unittest`, Vitest, and Testing Library.
- **Package managers:** `uv` for Python and `pnpm` for the frontend.

## Project Structure

```text
snapchef/
|-- DESIGN.md                  # UI palette and content guidance
|-- snapchef-ai/
|   |-- data/raw/              # Local image and recipe datasets
|   |-- models/                # Model checkpoints
|   |-- src/snapchef_ai/       # Training, inference, recipes, and API
|   `-- tests/                 # Backend unit tests
`-- web/
    |-- public/                # Static assets
    `-- src/
        |-- components/        # Feature components
        |   `-- ui/            # Reusable UI primitives
        |-- layouts/           # Shared page layouts
        |-- lib/               # API client and formatting helpers
        `-- tests/             # Frontend tests
```

## Prerequisites

Install the following tools before starting:

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20.19+ or 22.12+
- [`pnpm`](https://pnpm.io/installation)
- Git

## Dataset Setup

Datasets are intentionally excluded from Git. Download both sources:

1. [Food-101 Resized](https://www.kaggle.com/datasets/ekojsalim/food-101-resized) for image classification.
2. [Food.com Recipes and Reviews](https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews) for recipe recommendations.

Extract the image dataset so the selected class folders are under:

```text
snapchef-ai/data/raw/imagefood_dataset/224/
|-- train/<class_name>/*.{jpg,jpeg,png,webp}
`-- test/<class_name>/*.{jpg,jpeg,png,webp}
```

Folder names must match the supported class names above, using underscores. Place the recipe data at `snapchef-ai/data/raw/receiptfood_dataset/recipes.parquet` (preferred) or `snapchef-ai/data/raw/receiptfood_dataset/recipes.csv`. The application does not currently use the reviews file.

Do not commit downloaded datasets. Coordinate with collaborators before replacing `snapchef-ai/models/best_food_model.pth`.

## Setup

1. Clone the repository and enter it:

   ```bash
   git clone <repository-url>
   cd snapchef
   ```

2. Install backend dependencies:

   ```bash
   cd snapchef-ai
   uv sync
   ```

3. Add the datasets using the structure described above. The existing checkpoint can be used immediately; retraining is not required for normal development.

4. Install frontend dependencies:

   ```bash
   cd ../web
   pnpm install
   ```

5. Optionally create `web/.env.local` when the API is hosted elsewhere:

   ```dotenv
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

## Run Locally

Start the API from `snapchef-ai/`:

```bash
uv run uvicorn snapchef_ai.api:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `http://127.0.0.1:8000/docs`.

In a second terminal, start the frontend from `web/`:

```bash
pnpm dev
```

Open `http://localhost:5173` and upload a supported food image.

## Validation and Build Commands

From `snapchef-ai/`:

```bash
uv run python -m unittest discover -s tests -v  # Run backend tests
uv run python -m snapchef_ai.evaluate           # Evaluate the checkpoint
uv run python -m snapchef_ai.train              # Retrain and save the best model
uv build                                        # Build the Python package
```

From `web/`:

```bash
pnpm test     # Run frontend tests once
pnpm lint     # Run Oxlint
pnpm build    # Create the production bundle
pnpm preview  # Preview the production bundle
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Backend URL used by the frontend. |
| `SNAPCHEF_CORS_ORIGINS` | Local Vite origins | Comma-separated allowed browser origins. |
| `SNAPCHEF_MIN_CONFIDENCE` | Application default | Minimum confidence for a known prediction. |
| `SNAPCHEF_MIN_MARGIN` | Application default | Minimum margin between the top two classes. |

## API Overview

- `GET /health` checks service and model readiness.
- `GET /api/classes` lists supported food classes.
- `POST /api/predict` accepts an image and returns the prediction, top candidates, and recipe recommendations.

## Roadmap

- **Stage 1:** Build the classification model, recommendation pipeline, and FastAPI service.
- **Stage 2:** Integrate and refine the React web interface (current stage).
- **Stage 3:** Add camera capture and Progressive Web App capabilities.
