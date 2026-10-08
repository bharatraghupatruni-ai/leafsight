import os
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms
from transformers import ViTModel


# Model & Preprocessing configuration
IMAGE_SIZE = 224
GRU_HIDDEN_SIZE = 128
GRU_LAYERS = 1
DROPOUT = 0.3

# ImageNet normalization
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Find model path relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model" / "best_vit_gru_finetuned.pth"


# ============================================================
# MODEL ARCHITECTURE (ViT-B/16 + GRU + Classifier)
# ============================================================
class ViTGRU(nn.Module):
    def __init__(
        self,
        num_classes: int = 4,
        hidden_size: int = GRU_HIDDEN_SIZE,
        num_layers: int = GRU_LAYERS,
        dropout: float = DROPOUT
    ):
        super().__init__()

        # Use eager attention implementation for compatibility with attention rollout
        self.vit = ViTModel.from_pretrained(
            "google/vit-base-patch16-224-in21k",
            attn_implementation="eager"
        )

        vit_hidden_size = self.vit.config.hidden_size

        self.gru = nn.GRU(
            input_size=vit_hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )

        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_classes)

    def forward(self, x: torch.Tensor, return_vit_output: bool = False):
        if return_vit_output:
            vit_output = self.vit(pixel_values=x, output_attentions=True)
        else:
            vit_output = self.vit(pixel_values=x)

        # Remove CLS token: shape [batch, 196, 768]
        patch_features = vit_output.last_hidden_state[:, 1:, :]

        # GRU processes patch sequence
        gru_output, hidden = self.gru(patch_features)

        # Final hidden state / output features
        features = gru_output[:, -1, :]
        features = self.dropout(features)
        output = self.classifier(features)

        if return_vit_output:
            return output, vit_output

        return output


# ============================================================
# INFERENCE SERVICE (Singleton Pattern)
# ============================================================
class InferenceService:
    _instance: Optional["InferenceService"] = None

    def __init__(self):
        self.device = DEVICE
        self.model: Optional[ViTGRU] = None
        self.class_names = ["Bacterialblight", "Blast", "Brownspot", "Tungro"]
        self.transform = transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
        ])
        self._load_model()

    @classmethod
    def get_instance(cls) -> "InferenceService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Trained model checkpoint not found at: {MODEL_PATH}")

        print(f"[LeafSight] Loading model from {MODEL_PATH} onto {self.device}...")
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")

        if "class_names" in checkpoint:
            self.class_names = checkpoint["class_names"]

        self.model = ViTGRU(
            num_classes=len(self.class_names),
            hidden_size=GRU_HIDDEN_SIZE,
            num_layers=GRU_LAYERS,
            dropout=DROPOUT
        )

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()
        print(f"[LeafSight] Model successfully loaded on {self.device} (Validation Acc: {checkpoint.get('val_accuracy', 0)*100:.2f}%)")

    def preprocess_image(self, image: Image.Image) -> Tuple[torch.Tensor, Tuple[int, int]]:
        rgb_image = image.convert("RGB")
        original_size = rgb_image.size  # (width, height)
        input_tensor = self.transform(rgb_image).unsqueeze(0).to(self.device)
        return input_tensor, original_size

    def predict(self, image: Image.Image) -> Dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Model is not initialized.")

        input_tensor, original_size = self.preprocess_image(image)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]

        predicted_index = int(torch.argmax(probabilities).item())
        predicted_class = self.class_names[predicted_index]
        confidence = float(probabilities[predicted_index].item())

        prob_dict = {
            class_name: round(float(probabilities[i].item()), 4)
            for i, class_name in enumerate(self.class_names)
        }

        return {
            "prediction": predicted_class,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "image_size": list(original_size),
            "request_id": str(uuid.uuid4())
        }


def get_inference_service() -> InferenceService:
    return InferenceService.get_instance()
