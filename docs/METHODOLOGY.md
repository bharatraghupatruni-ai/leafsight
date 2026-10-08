# LEAFSIGHT Research & Development Methodology

This document outlines the end-to-end data processing, training strategy, optimization protocols, and evaluation methodologies employed in LEAFSIGHT.

---

## 1. Dataset Preparation & Integrity Verification

### A. Raw Data Audit
The raw rice leaf image archive was audited using [audit_dataset.py](file:///d:/LEAFSIGHT/scripts/audit_dataset.py) to assess class balance, format consistency, image corruption, and duplicate content.

### B. Duplicate Detection and Sanitization
To prevent data leakage and label ambiguity:
- **MD5 Perceptual Hashing**: Generated cryptographic checksums for all image byte streams.
- **Intra-class Duplicates**: Identical duplicate images within the same disease class were deduplicated, retaining exactly one authoritative instance.
- **Cross-class Duplicates**: Images with identical byte hashes appearing under conflicting disease labels were identified and purged to eliminate label contamination.

### C. Partitioning Strategy
The cleaned dataset was partitioned using a strict, fixed-seed random split:
- **Training Set (70%)**: Used for parameter optimization.
- **Validation Set (15%)**: Used for hyperparameter tuning, model selection, and early stopping.
- **Test Set (15%)**: **721 images**, completely isolated and evaluated strictly once after all training and fine-tuning was finalized.

```text
Dataset Split:
├── Train (70%): Parameter learning
├── Validation (15%): Checkpointing and early stopping
└── Test (15% - 721 images): Final benchmark evaluation
```

---

## 2. Preprocessing & Augmentation Pipeline

### Training Augmentations
To enhance generalizability and guard against overfitting on varying field lighting and angles:
1. **Resize**: Rescaled to $256 \times 256$.
2. **Random Resized Crop**: Random crop with scale range $[0.8, 1.0]$ resized to $224 \times 224$.
3. **Random Horizontal Flip**: Bernoulli probability $p = 0.5$.
4. **Random Rotation**: Rotation range $\pm 15^\circ$.
5. **Color Jitter**: Brightness jitter factor $0.2$, Contrast jitter factor $0.2$.
6. **Tensor Conversion**: Scaled to float values $[0, 1]$.
7. **ImageNet Normalization**: Channel-wise mean $[0.485, 0.456, 0.406]$ and std $[0.229, 0.224, 0.225]$.

### Validation & Test Transforms
Deterministic evaluation pipeline:
1. **Resize**: Fixed resolution to $224 \times 224$.
2. **Tensor Conversion**: Scaled to float $[0, 1]$.
3. **ImageNet Normalization**: Matching training mean and standard deviation.

---

## 3. Two-Stage Training Protocol

### Stage A: Feature Aggregation (Frozen ViT Backbone)
- **Backbone**: Pretrained ViT-B/16 on ImageNet-21k (`google/vit-base-patch16-224-in21k`).
- **ViT Status**: All 12 transformer encoder layers were frozen (`requires_grad = False`).
- **Trainable Parameters**: GRU sequence aggregator ($768 \rightarrow 128$) and linear classification head ($128 \rightarrow 4$).
- **Optimizer**: `AdamW` ($\text{lr} = 10^{-4}$).
- **Loss Function**: `CrossEntropyLoss`.
- **Batch Size**: 4.
- **Validation Accuracy Achieved**: **98.75%**.
- **Checkpoint Saved**: `model/best_vit_gru.pth`.

### Stage B: Progressive Layer Fine-Tuning
- **Objective**: Adapt high-level visual attention heads to disease-specific leaf lesion textures.
- **Unfreezing Strategy**: The top 2 transformer encoder layers (Layers 10 and 11) of the ViT backbone were unfrozen alongside the GRU and classification head.
- **Learning Rate**: Reduced to $\text{lr} = 10^{-5}$ to prevent catastrophic forgetting.
- **Weight Decay**: $0.01$.
- **Validation Accuracy Achieved**: **99.72%** (an improvement of **+0.97 percentage points** over Stage A).
- **Final Checkpoint Saved**: `model/best_vit_gru_finetuned.pth`.

---

## 4. Evaluation & Metrics Protocol

### Metric Definitions
- **Accuracy**: $\frac{\text{TP} + \text{TN}}{\text{Total Samples}}$
- **Macro Precision**: Arithmetic mean of precision scores across all 4 disease classes (unweighted by class frequency):
  $$\text{Macro Precision} = \frac{1}{C} \sum_{c=1}^C \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}$$
- **Macro Recall**: Arithmetic mean of recall scores across all 4 disease classes:
  $$\text{Macro Recall} = \frac{1}{C} \sum_{c=1}^C \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}$$
- **Macro F1-Score**: Harmonic mean of macro precision and macro recall:
  $$\text{Macro F1} = 2 \cdot \frac{\text{Macro Precision} \cdot \text{Macro Recall}}{\text{Macro Precision} + \text{Macro Recall}}$$

---

## 5. Explainability Protocol (ViT Attention Rollout)

1. The model was configured with `attn_implementation="eager"` to extract self-attention weight tensors across all 12 transformer layers.
2. Self-attention weights were averaged over the 12 attention heads and combined with the residual identity matrix.
3. Multi-layer matrix rollout was computed from layer 1 to layer 12.
4. The resulting 196 patch attention weights were reshaped to a $14 \times 14$ grid, interpolated to $224 \times 224$, and superimposed on the original leaf image using a Jet colormap.
5. The visualization is presented to users as an attention map indicating image regions that received stronger visual attention during feature extraction.
