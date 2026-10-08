import os
import json
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from transformers import ViTModel

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)


# ============================================================
# CONFIGURATION
# ============================================================

TEST_DIR = "data/processed/test"

MODEL_PATH = "model/best_vit_gru_finetuned.pth"

OUTPUT_DIR = "outputs"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

IMAGE_SIZE = 224

BATCH_SIZE = 4

GRU_HIDDEN_SIZE = 128
GRU_LAYERS = 1
DROPOUT = 0.3

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# TRANSFORM
# ============================================================

test_transform = transforms.Compose([
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

test_dataset = datasets.ImageFolder(
    TEST_DIR,
    transform=test_transform
)

class_names = test_dataset.classes

num_classes = len(class_names)

print("\nClasses:")

for i, name in enumerate(class_names):
    print(f"{i}: {name}")

print(
    f"\nTest images: {len(test_dataset)}"
)


# ============================================================
# DATALOADER
# ============================================================

test_loader = DataLoader(
    test_dataset,
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

        self.vit = ViTModel.from_pretrained(
            "google/vit-base-patch16-224-in21k"
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

    def forward(self, x):

        vit_output = self.vit(
            pixel_values=x
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

        return output


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading final candidate model...")

model = ViTGRU(
    num_classes=num_classes,
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
    f"Loaded checkpoint from "
    f"fine-tuning epoch {checkpoint['epoch']}"
)

print(
    f"Validation accuracy of checkpoint: "
    f"{checkpoint['val_accuracy'] * 100:.2f}%"
)

print(
    f"Device: {DEVICE}"
)

if torch.cuda.is_available():

    print(
        f"GPU: "
        f"{torch.cuda.get_device_name(0)}"
    )


# ============================================================
# TEST EVALUATION
# ============================================================

all_labels = []
all_predictions = []
all_probabilities = []

print("\n")
print("=" * 60)
print("STARTING FINAL TEST EVALUATION")
print("=" * 60)


with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(
            DEVICE,
            non_blocking=True
        )

        outputs = model(images)

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        predictions = outputs.argmax(
            dim=1
        )

        all_labels.extend(
            labels.numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )

        all_probabilities.extend(
            probabilities.cpu().numpy()
        )


all_labels = np.array(
    all_labels
)

all_predictions = np.array(
    all_predictions
)

all_probabilities = np.array(
    all_probabilities
)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    all_labels,
    all_predictions
)

precision_macro = precision_score(
    all_labels,
    all_predictions,
    average="macro",
    zero_division=0
)

recall_macro = recall_score(
    all_labels,
    all_predictions,
    average="macro",
    zero_division=0
)

f1_macro = f1_score(
    all_labels,
    all_predictions,
    average="macro",
    zero_division=0
)

precision_weighted = precision_score(
    all_labels,
    all_predictions,
    average="weighted",
    zero_division=0
)

recall_weighted = recall_score(
    all_labels,
    all_predictions,
    average="weighted",
    zero_division=0
)

f1_weighted = f1_score(
    all_labels,
    all_predictions,
    average="weighted",
    zero_division=0
)


# ============================================================
# PRINT MAIN RESULTS
# ============================================================

print("\n")
print("=" * 60)
print("FINAL TEST RESULTS")
print("=" * 60)

print(
    f"Test Accuracy:       {accuracy * 100:.2f}%"
)

print(
    f"Macro Precision:     {precision_macro * 100:.2f}%"
)

print(
    f"Macro Recall:        {recall_macro * 100:.2f}%"
)

print(
    f"Macro F1-Score:      {f1_macro * 100:.2f}%"
)

print(
    f"Weighted Precision:  {precision_weighted * 100:.2f}%"
)

print(
    f"Weighted Recall:     {recall_weighted * 100:.2f}%"
)

print(
    f"Weighted F1-Score:   {f1_weighted * 100:.2f}%"
)


# ============================================================
# PER-CLASS REPORT
# ============================================================

print("\n")
print("=" * 60)
print("PER-CLASS CLASSIFICATION REPORT")
print("=" * 60)

report = classification_report(
    all_labels,
    all_predictions,
    target_names=class_names,
    digits=4,
    zero_division=0
)

print(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    all_labels,
    all_predictions
)

print("\n")
print("=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(cm)


# ============================================================
# SAVE CONFUSION MATRIX IMAGE
# ============================================================

fig, ax = plt.subplots(
    figsize=(8, 7)
)

display = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=class_names
)

display.plot(
    ax=ax,
    values_format="d"
)

plt.title(
    "LEAFSIGHT Test Confusion Matrix"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "confusion_matrix.png"
    ),
    dpi=200,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# CLASS-WISE METRICS
# ============================================================

report_dict = classification_report(
    all_labels,
    all_predictions,
    target_names=class_names,
    output_dict=True,
    zero_division=0
)

class_metrics = {}

for class_name in class_names:

    class_metrics[class_name] = {

        "precision": report_dict[
            class_name
        ]["precision"],

        "recall": report_dict[
            class_name
        ]["recall"],

        "f1_score": report_dict[
            class_name
        ]["f1-score"],

        "support": report_dict[
            class_name
        ]["support"]
    }


# ============================================================
# CONFIDENCE ANALYSIS
# ============================================================

confidence = np.max(
    all_probabilities,
    axis=1
)

correct_mask = (
    all_predictions == all_labels
)

correct_confidence = confidence[
    correct_mask
]

incorrect_confidence = confidence[
    ~correct_mask
]

print("\n")
print("=" * 60)
print("CONFIDENCE ANALYSIS")
print("=" * 60)

print(
    f"Average confidence: "
    f"{confidence.mean() * 100:.2f}%"
)

if len(correct_confidence) > 0:

    print(
        f"Correct prediction confidence: "
        f"{correct_confidence.mean() * 100:.2f}%"
    )

if len(incorrect_confidence) > 0:

    print(
        f"Incorrect prediction confidence: "
        f"{incorrect_confidence.mean() * 100:.2f}%"
    )


# ============================================================
# ERROR ANALYSIS
# ============================================================

incorrect_indices = np.where(
    ~correct_mask
)[0]

print("\n")
print("=" * 60)
print("ERROR ANALYSIS")
print("=" * 60)

print(
    f"Correct predictions: "
    f"{correct_mask.sum()}"
)

print(
    f"Incorrect predictions: "
    f"{len(incorrect_indices)}"
)

print(
    f"Total test images: "
    f"{len(all_labels)}"
)


# ============================================================
# SAVE RESULTS JSON
# ============================================================

results = {

    "model": "ViT-B/16 + GRU",

    "checkpoint":
        MODEL_PATH,

    "test_images":
        int(len(all_labels)),

    "validation_accuracy":
        float(checkpoint["val_accuracy"]),

    "test_accuracy":
        float(accuracy),

    "macro_precision":
        float(precision_macro),

    "macro_recall":
        float(recall_macro),

    "macro_f1":
        float(f1_macro),

    "weighted_precision":
        float(precision_weighted),

    "weighted_recall":
        float(recall_weighted),

    "weighted_f1":
        float(f1_weighted),

    "average_confidence":
        float(confidence.mean()),

    "correct_predictions":
        int(correct_mask.sum()),

    "incorrect_predictions":
        int(len(incorrect_indices)),

    "class_metrics":
        class_metrics,

    "confusion_matrix":
        cm.tolist()
}


with open(
    os.path.join(
        OUTPUT_DIR,
        "test_results.json"
    ),
    "w"
) as file:

    json.dump(
        results,
        file,
        indent=4
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 60)
print("PHASE 4 TEST EVALUATION COMPLETE")
print("=" * 60)

print(
    f"FINAL TEST ACCURACY: "
    f"{accuracy * 100:.2f}%"
)

print(
    f"FINAL MACRO-F1: "
    f"{f1_macro * 100:.2f}%"
)

print("\nSaved files:")

print(
    "outputs/test_results.json"
)

print(
    "outputs/confusion_matrix.png"
)

print("\n")
print(
    "The test set has now been evaluated."
)