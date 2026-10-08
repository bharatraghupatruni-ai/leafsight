import os
import json
import random
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from transformers import ViTModel


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = "data/processed"

TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")

MODEL_DIR = "model"
OUTPUT_DIR = "outputs"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

BATCH_SIZE = 4
NUM_EPOCHS = 15
LEARNING_RATE = 1e-4
PATIENCE = 4

IMAGE_SIZE = 224
GRU_HIDDEN_SIZE = 128
GRU_LAYERS = 1
DROPOUT = 0.3

SEED = 42

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# DATA TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomResizedCrop(
        IMAGE_SIZE,
        scale=(0.8, 1.0)
    ),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# DATASETS
# ============================================================

train_dataset = datasets.ImageFolder(
    TRAIN_DIR,
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    VAL_DIR,
    transform=val_transform
)

class_names = train_dataset.classes
num_classes = len(class_names)

print("\nClasses:")
for i, name in enumerate(class_names):
    print(f"{i}: {name}")

print(f"\nNumber of classes: {num_classes}")

print("\nDataset sizes:")
print(f"Train: {len(train_dataset)}")
print(f"Validation: {len(val_dataset)}")


# ============================================================
# DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)


# ============================================================
# MODEL
# ============================================================

class ViTGRU(nn.Module):

    def __init__(
        self,
        num_classes,
        hidden_size=128,
        num_layers=1,
        dropout=0.3
    ):
        super().__init__()

        print("\nLoading pretrained ViT...")

        self.vit = ViTModel.from_pretrained(
            "google/vit-base-patch16-224-in21k"
        )

        # Freeze ViT
        for parameter in self.vit.parameters():
            parameter.requires_grad = False

        vit_hidden_size = self.vit.config.hidden_size

        self.gru = nn.GRU(
            input_size=vit_hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )

        self.dropout = nn.Dropout(dropout)

        self.classifier = nn.Linear(
            hidden_size,
            num_classes
        )

    def forward(self, x):

        # ViT feature extraction
        vit_output = self.vit(
            pixel_values=x
        )

        # Remove CLS token
        patch_features = vit_output.last_hidden_state[:, 1:, :]

        # GRU processes patch sequence
        gru_output, _ = self.gru(
            patch_features
        )

        # Take final GRU output
        features = gru_output[:, -1, :]

        features = self.dropout(features)

        output = self.classifier(features)

        return output


# ============================================================
# CREATE MODEL
# ============================================================

model = ViTGRU(
    num_classes=num_classes,
    hidden_size=GRU_HIDDEN_SIZE,
    num_layers=GRU_LAYERS,
    dropout=DROPOUT
)

model = model.to(DEVICE)


# ============================================================
# MODEL INFORMATION
# ============================================================

total_parameters = sum(
    p.numel()
    for p in model.parameters()
)

trainable_parameters = sum(
    p.numel()
    for p in model.parameters()
    if p.requires_grad
)

print("\nModel:")
print("Architecture: ViT-B/16 → GRU → Classifier")
print(f"Total parameters: {total_parameters:,}")
print(f"Trainable parameters: {trainable_parameters:,}")
print(f"Device: {DEVICE}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")


# ============================================================
# LOSS + OPTIMIZER
# ============================================================

criterion = nn.CrossEntropyLoss()

optimizer = torch.optim.AdamW(
    filter(
        lambda p: p.requires_grad,
        model.parameters()
    ),
    lr=LEARNING_RATE
)


# ============================================================
# MIXED PRECISION
# ============================================================

use_amp = DEVICE.type == "cuda"

if use_amp:
    scaler = torch.amp.GradScaler("cuda")
else:
    scaler = None


# ============================================================
# TRAINING FUNCTION
# ============================================================

def train_one_epoch():

    model.train()

    # Keep ViT frozen
    model.vit.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in train_loader:

        images = images.to(
            DEVICE,
            non_blocking=True
        )

        labels = labels.to(
            DEVICE,
            non_blocking=True
        )

        optimizer.zero_grad(set_to_none=True)

        if use_amp:

            with torch.amp.autocast(
                device_type="cuda",
                dtype=torch.float16
            ):

                outputs = model(images)

                loss = criterion(
                    outputs,
                    labels
                )

            scaler.scale(loss).backward()

            scaler.step(optimizer)

            scaler.update()

        else:

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()

            optimizer.step()

        running_loss += (
            loss.item() * images.size(0)
        )

        predictions = outputs.argmax(dim=1)

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_accuracy = correct / total

    return epoch_loss, epoch_accuracy


# ============================================================
# VALIDATION FUNCTION
# ============================================================

@torch.no_grad()
def validate():

    model.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in val_loader:

        images = images.to(
            DEVICE,
            non_blocking=True
        )

        labels = labels.to(
            DEVICE,
            non_blocking=True
        )

        if use_amp:

            with torch.amp.autocast(
                device_type="cuda",
                dtype=torch.float16
            ):

                outputs = model(images)

                loss = criterion(
                    outputs,
                    labels
                )

        else:

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

        running_loss += (
            loss.item() * images.size(0)
        )

        predictions = outputs.argmax(dim=1)

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_accuracy = correct / total

    return epoch_loss, epoch_accuracy


# ============================================================
# TRAINING LOOP
# ============================================================

history = {
    "train_loss": [],
    "train_accuracy": [],
    "val_loss": [],
    "val_accuracy": []
}

best_val_accuracy = 0.0
best_epoch = 0
epochs_without_improvement = 0

print("\n")
print("=" * 60)
print("STARTING PROPER TRAINING")
print("=" * 60)


for epoch in range(NUM_EPOCHS):

    print(
        f"\nEpoch {epoch + 1}/{NUM_EPOCHS}"
    )

    train_loss, train_accuracy = train_one_epoch()

    val_loss, val_accuracy = validate()

    history["train_loss"].append(train_loss)
    history["train_accuracy"].append(train_accuracy)
    history["val_loss"].append(val_loss)
    history["val_accuracy"].append(val_accuracy)

    print(
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_accuracy * 100:.2f}%"
    )

    print(
        f"Val Loss: {val_loss:.4f} | "
        f"Val Acc: {val_accuracy * 100:.2f}%"
    )

    # Save best model
    if val_accuracy > best_val_accuracy:

        best_val_accuracy = val_accuracy
        best_epoch = epoch + 1
        epochs_without_improvement = 0

        checkpoint = {
            "epoch": epoch + 1,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "val_accuracy": val_accuracy,
            "class_names": class_names
        }

        torch.save(
            checkpoint,
            os.path.join(
                MODEL_DIR,
                "best_vit_gru.pth"
            )
        )

        print(
            "✓ New best model saved."
        )

    else:

        epochs_without_improvement += 1

        print(
            f"No improvement "
            f"({epochs_without_improvement}/{PATIENCE})"
        )

    # Early stopping
    if epochs_without_improvement >= PATIENCE:

        print("\nEarly stopping triggered.")

        break


# ============================================================
# SAVE HISTORY
# ============================================================

with open(
    os.path.join(
        OUTPUT_DIR,
        "training_history.json"
    ),
    "w"
) as file:

    json.dump(
        history,
        file,
        indent=4
    )


# ============================================================
# SAVE CONFIGURATION
# ============================================================

config = {
    "architecture": "ViT-B/16 -> GRU -> Classifier",
    "vit_model": "google/vit-base-patch16-224-in21k",
    "num_classes": num_classes,
    "classes": class_names,
    "image_size": IMAGE_SIZE,
    "batch_size": BATCH_SIZE,
    "epochs": NUM_EPOCHS,
    "learning_rate": LEARNING_RATE,
    "gru_hidden_size": GRU_HIDDEN_SIZE,
    "gru_layers": GRU_LAYERS,
    "dropout": DROPOUT,
    "optimizer": "AdamW",
    "loss": "CrossEntropyLoss",
    "vit_frozen": True,
    "best_epoch": best_epoch,
    "best_validation_accuracy": best_val_accuracy
}

with open(
    os.path.join(
        MODEL_DIR,
        "config.json"
    ),
    "w"
) as file:

    json.dump(
        config,
        file,
        indent=4
    )


# ============================================================
# TRAINING CURVES
# ============================================================

epochs_completed = range(
    1,
    len(history["train_loss"]) + 1
)

plt.figure(figsize=(10, 5))

plt.plot(
    epochs_completed,
    history["train_loss"],
    label="Train Loss"
)

plt.plot(
    epochs_completed,
    history["val_loss"],
    label="Validation Loss"
)

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("LEAFSIGHT Training and Validation Loss")
plt.legend()
plt.grid(True)

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "loss_curve.png"
    ),
    dpi=150,
    bbox_inches="tight"
)

plt.close()


plt.figure(figsize=(10, 5))

plt.plot(
    epochs_completed,
    [
        x * 100
        for x in history["train_accuracy"]
    ],
    label="Train Accuracy"
)

plt.plot(
    epochs_completed,
    [
        x * 100
        for x in history["val_accuracy"]
    ],
    label="Validation Accuracy"
)

plt.xlabel("Epoch")
plt.ylabel("Accuracy (%)")
plt.title("LEAFSIGHT Training and Validation Accuracy")
plt.legend()
plt.grid(True)

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "accuracy_curve.png"
    ),
    dpi=150,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 60)
print("PHASE 3 TRAINING COMPLETE")
print("=" * 60)

print(
    f"Best Epoch: {best_epoch}"
)

print(
    f"Best Validation Accuracy: "
    f"{best_val_accuracy * 100:.2f}%"
)

print("\nSaved files:")

print(
    "model/best_vit_gru.pth"
)

print(
    "model/config.json"
)

print(
    "outputs/training_history.json"
)

print(
    "outputs/loss_curve.png"
)

print(
    "outputs/accuracy_curve.png"
)

print("\nIMPORTANT:")
print(
    "Test set has NOT been used."
)

print(
    "Final test evaluation will happen in Phase 4."
)