# %% [markdown]
# ## 1. Import Libraries

# %%
from pathlib import Path
import time
import torch
import torch.nn as nn
import torch.optim as optim
from snapchef_ai.dataset import get_dataloaders
from snapchef_ai.model import get_model

# %% [markdown]
# ## 2. Configuration & Setup Path

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)  # Create the models folder if it does not exist

# Hyperparameters
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EPOCHS = 10
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# %% [markdown]
# ## 3. Helper Training & Validation Functions

# %%
def train_one_epoch(model, dataloader, criterion, optimizer, device):
    """Train the model for one epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)

        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)

        # Backward pass & optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Calculate statistics
        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

def validate_one_epoch(model, dataloader, criterion, device):
    """Evaluate the model on the validation set."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():  # Disable gradient calculations to save memory
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

# %% [markdown]
# ## 4. Main Training Pipeline

# %%
def run_training():
    print(f"Using device: {DEVICE}")

    # 1. Load Data
    train_loader, val_loader, class_names = get_dataloaders(batch_size=BATCH_SIZE)
    num_classes = len(class_names)
    print(f"Loaded {num_classes} classes: {class_names}")

    # 2. Initialize Model, Loss Function, and Optimizer
    model = get_model(num_classes=num_classes, pretrained=True).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    best_val_acc = 0.0

    # 3. Training Loop
    print("\n--- Starting Training ---")
    start_time = time.time()

    for epoch in range(EPOCHS):
        epoch_start = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, DEVICE)
        val_loss, val_acc = validate_one_epoch(model, val_loader, criterion, DEVICE)

        epoch_duration = time.time() - epoch_start

        print(
            f"Epoch [{epoch+1}/{EPOCHS}] ({epoch_duration:.1f}s) | "
            f"Train Loss: {train_loss:.4f} - Train Acc: {train_acc*100:.2f}% | "
            f"Val Loss: {val_loss:.4f} - Val Acc: {val_acc*100:.2f}%"
        )

        # Save the best model based on validation accuracy
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_path = MODEL_DIR / "best_food_model.pth"
            torch.save({
                'model_state_dict': model.state_dict(),
                'class_names': class_names,
                'num_classes': num_classes
            }, save_path)
            print(f"  --> Saved new best model (Val Acc: {val_acc*100:.2f}%) to {save_path.name}")

    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time/60:.2f} minutes.")
    print(f"Best Validation Accuracy: {best_val_acc*100:.2f}%")

# %% [markdown]
# ## 5. Execution Entry Point

# %%
if __name__ == "__main__":
    run_training()
# %%
