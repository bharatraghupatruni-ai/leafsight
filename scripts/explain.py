import os
import json
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torchvision import datasets, transforms
from transformers import ViTModel


# ============================================================
# CONFIGURATION
# ============================================================

TEST_DIR = "data/processed/test"

MODEL_PATH = "model/best_vit_gru_finetuned.pth"

OUTPUT_DIR = "outputs/explainability"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

IMAGE_SIZE = 224

GRU_HIDDEN_SIZE = 128
GRU_LAYERS = 1
DROPOUT = 0.3

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# TRANSFORM
# ============================================================

transform = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# DATASET
# ============================================================

dataset = datasets.ImageFolder(
    TEST_DIR,
    transform=transform
)

class_names = dataset.classes


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

        self.vit = ViTModel.from_pretrained(
    "google/vit-base-patch16-224-in21k",
    attn_implementation="eager"
)

        vit_hidden_size = (
            self.vit.config.hidden_size
        )

        self.gru = nn.GRU(
            input_size=vit_hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )

        self.dropout = nn.Dropout(
            dropout
        )

        self.classifier = nn.Linear(
            hidden_size,
            num_classes
        )

    def forward(
        self,
        x,
        return_vit_output=False
    ):

        vit_output = self.vit(
            pixel_values=x,
            output_attentions=True
        )

        patch_features = (
            vit_output.last_hidden_state[:, 1:, :]
        )

        gru_output, _ = self.gru(
            patch_features
        )

        features = gru_output[:, -1, :]

        features = self.dropout(
            features
        )

        output = self.classifier(
            features
        )

        if return_vit_output:
            return output, vit_output

        return output


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading trained model...")

model = ViTGRU(
    num_classes=len(class_names),
    hidden_size=GRU_HIDDEN_SIZE,
    num_layers=GRU_LAYERS,
    dropout=DROPOUT
)

checkpoint = torch.load(
    MODEL_PATH,
    map_location="cpu"
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model = model.to(DEVICE)

model.eval()

print(
    f"Model loaded successfully."
)

print(
    f"Device: {DEVICE}"
)


# ============================================================
# ATTENTION ROLLOUT
# ============================================================

def attention_rollout(attentions):

    # attentions:
    # [layers, batch, heads, tokens, tokens]

    attention_stack = torch.stack(
        attentions
    )

    # Average attention heads
    attention = attention_stack.mean(
        dim=2
    )

    # Add identity matrix
    identity = torch.eye(
        attention.size(-1),
        device=attention.device
    )

    identity = identity.unsqueeze(0).unsqueeze(0)

    attention = attention + identity

    # Normalize rows
    attention = attention / (
        attention.sum(
            dim=-1,
            keepdim=True
        ) + 1e-8
    )

    # Rollout through layers
    rollout = attention[0]

    for layer in range(
        1,
        attention.shape[0]
    ):

        rollout = torch.bmm(
            attention[layer],
            rollout
        )

    # CLS token attention to patches
    cls_attention = rollout[
        0,
        0,
        1:
    ]

    return cls_attention


# ============================================================
# CREATE HEATMAP
# ============================================================

def create_heatmap(
    attention,
    original_image,
    filename,
    title
):

    # ViT-B/16 with 224x224
    # gives 14 x 14 patches

    attention = attention.reshape(
        14,
        14
    )

    attention = attention.detach().cpu().numpy()

    # Normalize
    attention = (
        attention - attention.min()
    ) / (
        attention.max()
        - attention.min()
        + 1e-8
    )

    # Resize attention map
    attention = np.array(
        torch.nn.functional.interpolate(
            torch.tensor(
                attention
            ).unsqueeze(0).unsqueeze(0),
            size=(
                IMAGE_SIZE,
                IMAGE_SIZE
            ),
            mode="bilinear",
            align_corners=False
        )[0, 0]
    )

    # Original image
    image = original_image.permute(
        1,
        2,
        0
    ).numpy()

    # Undo normalization
    mean = np.array(
        [0.485, 0.456, 0.406]
    )

    std = np.array(
        [0.229, 0.224, 0.225]
    )

    image = image * std + mean

    image = np.clip(
        image,
        0,
        1
    )

    # Plot
    plt.figure(
        figsize=(7, 7)
    )

    plt.imshow(image)

    plt.imshow(
        attention,
        alpha=0.45,
        cmap="jet"
    )

    plt.axis("off")

    plt.title(title)

    plt.tight_layout()

    plt.savefig(
        filename,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# EXPLAIN SAMPLE IMAGES
# ============================================================

print("\n")
print("=" * 60)
print("GENERATING EXPLAINABILITY RESULTS")
print("=" * 60)


# Choose one image from each class
selected_indices = []

for class_index in range(
    len(class_names)
):

    for index in range(
        len(dataset)
    ):

        if dataset.targets[index] == class_index:

            selected_indices.append(
                index
            )

            break


for sample_number, index in enumerate(
    selected_indices,
    start=1
):

    image, label = dataset[index]

    input_tensor = image.unsqueeze(
        0
    ).to(DEVICE)

    with torch.no_grad():

        outputs, vit_output = model(
            input_tensor,
            return_vit_output=True
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        prediction = outputs.argmax(
            dim=1
        ).item()

        confidence = probabilities[
            0,
            prediction
        ].item()

    # Get attention
    attentions = vit_output.attentions

    if attentions is None:

        print(
            "Attention values were not returned."
        )

        continue

    attention = attention_rollout(
        attentions
    )

    filename = os.path.join(
        OUTPUT_DIR,
        f"sample_{sample_number}_"
        f"{class_names[label]}.png"
    )

    title = (
        f"Actual: {class_names[label]} | "
        f"Predicted: {class_names[prediction]} | "
        f"Confidence: {confidence * 100:.2f}%"
    )

    create_heatmap(
        attention,
        image,
        filename,
        title
    )

    print(
        f"\nSample {sample_number}"
    )

    print(
        f"Actual: "
        f"{class_names[label]}"
    )

    print(
        f"Predicted: "
        f"{class_names[prediction]}"
    )

    print(
        f"Confidence: "
        f"{confidence * 100:.2f}%"
    )

    print(
        f"Saved: {filename}"
    )


# ============================================================
# FIND MISCLASSIFIED IMAGE
# ============================================================

print("\n")
print("=" * 60)
print("SEARCHING FOR MISCLASSIFIED TEST IMAGE")
print("=" * 60)

misclassified_found = False

for index in range(
    len(dataset)
):

    image, label = dataset[index]

    input_tensor = image.unsqueeze(
        0
    ).to(DEVICE)

    with torch.no_grad():

        outputs, vit_output = model(
            input_tensor,
            return_vit_output=True
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        prediction = outputs.argmax(
            dim=1
        ).item()

        confidence = probabilities[
            0,
            prediction
        ].item()

    if prediction != label:

        misclassified_found = True

        attention = attention_rollout(
            vit_output.attentions
        )

        filename = os.path.join(
            OUTPUT_DIR,
            "misclassified_test_image.png"
        )

        title = (
            f"Actual: {class_names[label]} | "
            f"Predicted: {class_names[prediction]} | "
            f"Confidence: {confidence * 100:.2f}%"
        )

        create_heatmap(
            attention,
            image,
            filename,
            title
        )

        print(
            f"\nMisclassified image found."
        )

        print(
            f"Actual: "
            f"{class_names[label]}"
        )

        print(
            f"Predicted: "
            f"{class_names[prediction]}"
        )

        print(
            f"Confidence: "
            f"{confidence * 100:.2f}%"
        )

        print(
            f"Saved: {filename}"
        )

        break


if not misclassified_found:

    print(
        "No misclassified images found."
    )


# ============================================================
# COMPLETE
# ============================================================

print("\n")
print("=" * 60)
print("PHASE 5 EXPLAINABILITY COMPLETE")
print("=" * 60)

print(
    "Explainability outputs saved in:"
)

print(
    "outputs/explainability/"
)