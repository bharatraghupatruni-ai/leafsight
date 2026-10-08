import os
import argparse

import numpy as np
import torch
import torch.nn as nn

from PIL import Image
from torchvision import transforms
from transformers import ViTModel


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "model/best_vit_gru_finetuned.pth"

IMAGE_SIZE = 224

GRU_HIDDEN_SIZE = 128
GRU_LAYERS = 1
DROPOUT = 0.3

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# PREPROCESSING
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

        return self.classifier(
            features
        )


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    if not os.path.exists(MODEL_PATH):

        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location="cpu"
    )

    class_names = checkpoint[
        "class_names"
    ]

    model = ViTGRU(
        num_classes=len(class_names),
        hidden_size=GRU_HIDDEN_SIZE,
        num_layers=GRU_LAYERS,
        dropout=DROPOUT
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(DEVICE)

    model.eval()

    return model, class_names


# ============================================================
# PREDICTION
# ============================================================

def predict(image_path):

    if not os.path.exists(image_path):

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    model, class_names = load_model()

    image = Image.open(
        image_path
    ).convert("RGB")

    original_size = image.size

    input_tensor = transform(
        image
    ).unsqueeze(0).to(DEVICE)

    with torch.no_grad():

        outputs = model(
            input_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )[0]

    predicted_index = torch.argmax(
        probabilities
    ).item()

    predicted_class = class_names[
        predicted_index
    ]

    confidence = probabilities[
        predicted_index
    ].item()

    # All class probabilities
    class_probabilities = {}

    for i, class_name in enumerate(
        class_names
    ):

        class_probabilities[
            class_name
        ] = probabilities[i].item()

    return {
        "prediction": predicted_class,
        "confidence": confidence,
        "class_probabilities":
            class_probabilities,
        "image_size":
            original_size
    }


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=
        "LEAFSIGHT Rice Disease Predictor"
    )

    parser.add_argument(
        "--image",
        required=True,
        help=
        "Path to the rice leaf image"
    )

    args = parser.parse_args()

    print("\n")
    print("=" * 60)
    print("LEAFSIGHT INFERENCE")
    print("=" * 60)

    print(
        f"Device: {DEVICE}"
    )

    result = predict(
        args.image
    )

    print("\nPrediction:")
    print(
        result["prediction"]
    )

    print("\nConfidence:")
    print(
        f"{result['confidence'] * 100:.2f}%"
    )

    print("\nClass probabilities:")

    for class_name, probability in (
        result["class_probabilities"]
        .items()
    ):

        print(
            f"{class_name}: "
            f"{probability * 100:.2f}%"
        )

    print("\nOriginal image size:")
    print(
        result["image_size"]
    )

    print("\n")
    print("=" * 60)


if __name__ == "__main__":
    main()