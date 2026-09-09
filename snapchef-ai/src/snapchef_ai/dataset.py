# %% [markdown]
# ## 1. Import Library & Setup Path

# %%
from pathlib import Path
from torch.utils.data import DataLoader
from torchvision import transforms, datasets

# Setup path
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw" / "imagefood_dataset"

# %% [markdown]
# ## 2. Transformation image (Preprocessing & Augmentasi)

# Basic parameter
BATCH_SIZE = 32
IMAGE_SIZE = (224, 224)  # Standard input for MobileNet / EfficientNet

# %% Transformation for data training
train_transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# %% Transformation for data validation / testing
val_transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# %% [markdown]
# ## 3. Core Functions & Data Loaders

# %% Function to get dataloaders and class names
def get_dataloaders(batch_size=BATCH_SIZE, num_workers=2):
    """
    Load dataset and return train_loader, val_loader, and class_names.
    """
    train_dataset = datasets.ImageFolder(
        root=DATA_DIR / "224" / "train", 
        transform=train_transform
    )
    val_dataset = datasets.ImageFolder(
        root=DATA_DIR / "224" / "test", 
        transform=val_transform
    )

    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=num_workers, 
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=num_workers, 
        pin_memory=True
    )

    return train_loader, val_loader, train_dataset.classes

# %% Function to decode prediction index to class name
def decode_prediction(prediction_idx, class_names):
    """
    Convert prediction index to class name.
    
    Args:
        prediction_idx: Integer index of predicted class
        class_names: List of class names from dataset
        
    Returns:
        String class name
    """
    return class_names[prediction_idx]

# %% [markdown]
# ## 4. Dataset Info & Testing (for debugging)

# %% Print dataset information when running this script directly
if __name__ == "__main__":
    # Test loading data via get_dataloaders function
    train_loader, val_loader, class_names = get_dataloaders()
    
    num_classes = len(class_names)
    idx_to_class = {idx: cls_name for idx, cls_name in enumerate(class_names)}
    
    print(f"Number of training samples: {len(train_loader.dataset)}")
    print(f"Number of validation samples: {len(val_loader.dataset)}")
    print(f"Number of classes: {num_classes}")
    print(f"Class names: {class_names}")
    print(f"Training batches: {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    
    # Test loading one batch
    images, labels = next(iter(train_loader))
    print(f"\nSample batch shape: {images.shape}")
    print(f"Sample labels shape: {labels.shape}")
    print(f"Sample labels: {labels[:5]}")
    print(f"Sample class names: {[decode_prediction(l.item(), class_names) for l in labels[:5]]}")