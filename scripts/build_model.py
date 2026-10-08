import torch
import torch.nn as nn
from transformers import ViTModel


# ==========================================
# SETTINGS
# ==========================================

MODEL_NAME = "google/vit-base-patch16-224-in21k"

NUM_CLASSES = 4
GRU_HIDDEN_SIZE = 128
GRU_LAYERS = 1
DROPOUT = 0.3


# ==========================================
# DEVICE
# ==========================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("\n==========================================")
print("        LEAFSIGHT — VIT + GRU")
print("==========================================")

print("\nDevice:", device)

if torch.cuda.is_available():

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )


# ==========================================
# MODEL
# ==========================================

class ViTGRU(nn.Module):

    def __init__(
        self,
        num_classes=NUM_CLASSES,
        hidden_size=GRU_HIDDEN_SIZE,
        gru_layers=GRU_LAYERS,
        dropout=DROPOUT
    ):

        super().__init__()

        # ----------------------------------
        # Pretrained ViT
        # ----------------------------------

        self.vit = ViTModel.from_pretrained(
            MODEL_NAME
        )

        # Freeze ViT initially
        for parameter in self.vit.parameters():
            parameter.requires_grad = False


        # ViT-B/16 hidden size = 768
        vit_hidden_size = self.vit.config.hidden_size


        # ----------------------------------
        # GRU
        # ----------------------------------

        self.gru = nn.GRU(
            input_size=vit_hidden_size,
            hidden_size=hidden_size,
            num_layers=gru_layers,
            batch_first=True
        )


        # ----------------------------------
        # Classifier
        # ----------------------------------

        self.dropout = nn.Dropout(
            dropout
        )

        self.classifier = nn.Linear(
            hidden_size,
            num_classes
        )


    # ======================================
    # FORWARD
    # ======================================

    def forward(self, images):

        # ----------------------------------
        # ViT
        # ----------------------------------

        vit_output = self.vit(
            pixel_values=images
        )

        # Shape:
        # [batch, sequence, 768]

        patch_features = vit_output.last_hidden_state


        # ----------------------------------
        # Remove CLS token
        # ----------------------------------

        patch_features = patch_features[:, 1:, :]

        # Shape:
        # [batch, 196, 768]


        # ----------------------------------
        # GRU
        # ----------------------------------

        gru_output, hidden = self.gru(
            patch_features
        )

        # hidden shape:
        # [layers, batch, hidden_size]


        # ----------------------------------
        # Last GRU hidden state
        # ----------------------------------

        final_features = hidden[-1]

        # Shape:
        # [batch, 128]


        # ----------------------------------
        # Classification
        # ----------------------------------

        final_features = self.dropout(
            final_features
        )

        logits = self.classifier(
            final_features
        )

        # Shape:
        # [batch, 4]

        return logits


# ==========================================
# CREATE MODEL
# ==========================================

model = ViTGRU()

model = model.to(device)


# ==========================================
# MODEL INFORMATION
# ==========================================

total_parameters = sum(
    parameter.numel()
    for parameter in model.parameters()
)

trainable_parameters = sum(
    parameter.numel()
    for parameter in model.parameters()
    if parameter.requires_grad
)


print("\nModel Information")
print("-----------------")

print(
    "Total parameters:",
    f"{total_parameters:,}"
)

print(
    "Trainable parameters:",
    f"{trainable_parameters:,}"
)


# ==========================================
# TEST FORWARD PASS
# ==========================================

print("\nRunning forward-pass test...")


batch_size = 2

dummy_images = torch.randn(
    batch_size,
    3,
    224,
    224
).to(device)


with torch.no_grad():

    output = model(
        dummy_images
    )


print(
    "Input shape:",
    tuple(dummy_images.shape)
)

print(
    "Output shape:",
    tuple(output.shape)
)


# ==========================================
# VERIFY
# ==========================================

expected_shape = (
    batch_size,
    NUM_CLASSES
)

if tuple(output.shape) == expected_shape:

    print("\nSUCCESS")
    print(
        "ViT → GRU → Classifier "
        "pipeline is working."
    )

else:

    print("\nERROR")
    print(
        "Unexpected output shape."
    )


print("\n==========================================")
print("        PHASE 2 ARCHITECTURE TEST DONE")
print("==========================================")