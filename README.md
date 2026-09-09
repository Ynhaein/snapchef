# SnapChef

SnapChef is a food-image classification and recipe recommendation project. Given a food image, the current machine-learning pipeline predicts the most likely food class and searches the local Food.com dataset for matching recipes.

The project is currently in its first stage: developing and evaluating the image classifier. Website integration, camera input, and Progressive Web App support are planned for later stages.

## Current Status

- Architecture: MobileNetV3 Small with transfer learning
- Input size: 224 × 224 RGB images
- Supported classes: 10
- Test accuracy: 84.90% on the current 1,000-image test split
- Included checkpoint: `snapchef-ai/models/best_food_model.pth`
- Inference output: top-three candidates with confidence and an optional `unknown` result

The model currently supports:

`bread_pudding`, `chicken_curry`, `donuts`, `garlic_bread`, `gnocchi`, `samosa`, `sashimi`, `seaweed_salad`, `spaghetti_carbonara`, and `takoyaki`.

Images outside these classes may be marked as `unknown`, but an unsupported food can still receive an incorrect high-confidence prediction. The current confidence guardrail is not a complete out-of-distribution detector.

## Project Structure

```text
snapchef/
├── README.md
└── snapchef-ai/
    ├── data/                         # Local datasets; excluded from Git
    ├── models/
    │   └── best_food_model.pth       # Current trained checkpoint
    ├── src/snapchef_ai/
    │   ├── dataset.py                # Data loading and image transforms
    │   ├── evaluate.py               # Overall and per-class evaluation
    │   ├── model.py                  # MobileNetV3 classifier
    │   ├── recommend.py              # Inference and recipe matching
    │   └── train.py                  # Training and checkpoint creation
    ├── tests/
    ├── pyproject.toml
    └── uv.lock
```

## Prerequisites

Install the following tools before starting:

- [Git](https://git-scm.com/)
- [Python 3.12 or newer](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

CUDA is optional. PyTorch automatically uses a supported GPU when one is available and otherwise runs on the CPU.

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd snapchef/snapchef-ai
```

Replace `<repository-url>` with this repository's Git URL. If your cloned directory has a different name, adjust the `cd` command accordingly.

### 2. Install the Python dependencies

```bash
uv sync
```

This creates a local virtual environment and installs the exact dependency versions recorded in `uv.lock`.

### 3. Download the image dataset

Download [Food-101 Resized](https://www.kaggle.com/datasets/ekojsalim/food-101-resized) from Kaggle. From its 224-pixel training and test splits, copy the 10 supported class directories into this structure:

```text
snapchef-ai/data/raw/imagefood_dataset/224/
├── train/
│   ├── bread_pudding/
│   ├── chicken_curry/
│   └── ...the remaining supported classes
└── test/
    ├── bread_pudding/
    ├── chicken_curry/
    └── ...the remaining supported classes
```

Directory names must match the supported class names exactly. The current dataset contains 900 training images and 100 test images per class.

### 4. Download the recipe dataset

Download [Food.com Recipes and Reviews](https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews) from Kaggle. Extract at least `recipes.csv` into:

```text
snapchef-ai/data/raw/receiptfood_dataset/
└── recipes.csv
```

`reviews.csv` is not required by the current recommendation pipeline. Dataset files are intentionally excluded from Git because of their size.

### 5. Verify the installation

Run the automated tests:

```bash
uv run python -m unittest discover -s tests -v
```

Evaluate the included checkpoint against the local test split:

```bash
uv run python -m snapchef_ai.evaluate
```

The current checkpoint should report an overall accuracy of approximately 84.90% when evaluated against the expected test dataset.

## Running Inference

The inference module selects the first available image from the test dataset and prints its prediction and matching recipe preview:

```bash
uv run python -m snapchef_ai.recommend
```

The existing checkpoint is ready to use, so retraining is not required for normal evaluation or inference.

The abstention thresholds can be changed through environment variables:

```text
SNAPCHEF_MIN_CONFIDENCE=0.70
SNAPCHEF_MIN_MARGIN=0.20
```

## Training

To train a new model using the prepared training and test directories, run:

```bash
uv run python -m snapchef_ai.train
```

Training may download pretrained torchvision weights. When validation accuracy improves, the script replaces `models/best_food_model.pth`. Coordinate with other contributors before committing a new checkpoint, and record the dataset or training changes that produced it.

## Roadmap

1. Build and evaluate the machine-learning model and serving API.
2. Integrate prediction and recipe results into a website frontend.
3. Add camera capture and package the website as a Progressive Web App.

## Collaboration Notes

- Do not commit the local `data/` directory.
- Keep preprocessing consistent between training and inference.
- Run the unit tests and evaluator before submitting model-related changes.
- Document changes to classes, transforms, hyperparameters, or checkpoints in the pull request.
