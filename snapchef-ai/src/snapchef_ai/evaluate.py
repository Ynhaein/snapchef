"""Evaluate a SnapChef checkpoint against the held-out image split."""

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision import datasets

from snapchef_ai.dataset import DATA_DIR, val_transform
from snapchef_ai.model import get_model

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "best_food_model.pth"


def evaluate(model_path: Path, data_dir: Path, batch_size: int = 64) -> None:
    """Print overall and per-class accuracy for a checkpoint."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint = torch.load(model_path, map_location=device)
    class_names = checkpoint["class_names"]
    model = get_model(checkpoint["num_classes"], pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device).eval()

    dataset = datasets.ImageFolder(data_dir, transform=val_transform)
    if dataset.classes != class_names:
        raise ValueError("Dataset classes do not match checkpoint class_names.")

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    correct_by_class = torch.zeros(len(class_names), dtype=torch.long)
    total_by_class = torch.zeros(len(class_names), dtype=torch.long)

    with torch.inference_mode():
        for images, labels in loader:
            predictions = model(images.to(device)).argmax(dim=1).cpu()
            for class_index in range(len(class_names)):
                mask = labels == class_index
                total_by_class[class_index] += mask.sum()
                correct_by_class[class_index] += (predictions[mask] == class_index).sum()

    total = int(total_by_class.sum())
    correct = int(correct_by_class.sum())
    print(f"Overall accuracy: {correct / total:.2%} ({correct}/{total})")
    for index, name in enumerate(class_names):
        class_total = int(total_by_class[index])
        class_correct = int(correct_by_class[index])
        accuracy = class_correct / class_total if class_total else 0.0
        print(f"{name:24} {accuracy:.2%} ({class_correct}/{class_total})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--data", type=Path, default=DATA_DIR / "224" / "test")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    evaluate(args.model, args.data, args.batch_size)


if __name__ == "__main__":
    main()
