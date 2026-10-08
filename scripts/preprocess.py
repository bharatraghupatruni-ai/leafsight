from pathlib import Path
import json
import matplotlib.pyplot as plt
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader


# ==========================================
# SETTINGS
# ==========================================

DATA_DIR = Path("data/processed")
IMAGE_SIZE = 224
BATCH_SIZE = 16

# Windows-friendly
NUM_WORKERS = 0


# ==========================================
# TRAIN TRANSFORMS
# ==========================================

train_transform = transforms.Compose([
    transforms.Resize((256, 256)),

    transforms.RandomResizedCrop(
        IMAGE_SIZE,
        scale=(0.8, 1.0)
    ),

    transforms.RandomHorizontalFlip(
        p=0.5
    ),

    transforms.RandomRotation(
        degrees=15
    ),

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


# ==========================================
# VALIDATION / TEST TRANSFORMS
# ==========================================

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ==========================================
# CREATE DATASETS
# ==========================================

train_dataset = datasets.ImageFolder(
    DATA_DIR / "train",
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    DATA_DIR / "val",
    transform=eval_transform
)

test_dataset = datasets.ImageFolder(
    DATA_DIR / "test",
    transform=eval_transform
)


# ==========================================
# CLASS INFORMATION
# ==========================================

class_names = train_dataset.classes

print("\n==========================================")
print("       LEAFSIGHT PREPROCESSING")
print("==========================================")

print("\nClasses:")

for index, name in enumerate(class_names):
    print(f"{index}: {name}")


print("\nNumber of classes:", len(class_names))


# ==========================================
# SAVE CLASS NAMES
# ==========================================

model_dir = Path("model")
model_dir.mkdir(exist_ok=True)

with open(
    model_dir / "class_names.json",
    "w"
) as file:

    json.dump(
        class_names,
        file,
        indent=4
    )


# ==========================================
# DATASET SIZES
# ==========================================

print("\nDataset sizes:")
print("Train:", len(train_dataset))
print("Validation:", len(val_dataset))
print("Test:", len(test_dataset))


# ==========================================
# DATALOADERS
# ==========================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS
)


# ==========================================
# TEST ONE BATCH
# ==========================================

images, labels = next(iter(train_loader))

print("\nFirst training batch:")
print("Image tensor shape:", images.shape)
print("Label tensor shape:", labels.shape)


# ==========================================
# EXPECTED SHAPE CHECK
# ==========================================

expected_shape = (
    BATCH_SIZE,
    3,
    IMAGE_SIZE,
    IMAGE_SIZE
)

if images.shape == expected_shape:

    print("\nSUCCESS:")
    print("Preprocessing output is correct.")

else:

    print("\nWARNING:")
    print("Unexpected tensor shape.")


# ==========================================
# VISUALIZE SAMPLE IMAGES
# ==========================================

# Convert normalized tensor back approximately
mean = torch.tensor(
    [0.485, 0.456, 0.406]
).view(3, 1, 1)

std = torch.tensor(
    [0.229, 0.224, 0.225]
).view(3, 1, 1)

display_images = images[:8] * std + mean
display_images = torch.clamp(
    display_images,
    0,
    1
)

fig, axes = plt.subplots(
    2,
    4,
    figsize=(12, 6)
)

for i, ax in enumerate(axes.flat):

    image = display_images[i].permute(
        1, 2, 0
    )

    ax.imshow(image)

    ax.set_title(
        class_names[labels[i].item()]
    )

    ax.axis("off")


plt.tight_layout()

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

plt.savefig(
    output_dir / "preprocessing_samples.png"
)

plt.show()


# ==========================================
# FINAL
# ==========================================

print("\nSaved:")
print("model/class_names.json")
print("outputs/preprocessing_samples.png")

print("\n==========================================")
print("       PHASE 1 PREPROCESSING DONE")
print("==========================================")