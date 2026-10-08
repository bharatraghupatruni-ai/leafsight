# LEAFSIGHT Experimental Results & Performance Analysis

This document provides a detailed breakdown of the experimental results and quantitative performance of the final fine-tuned LEAFSIGHT model (`model/best_vit_gru_finetuned.pth`) evaluated on the independent 721-image test set.

---

## 1. Overall Test-Set Benchmark Summary

| Metric | Score | Detailed Ratio |
| :--- | :--- | :--- |
| **Test Accuracy** | **99.86%** | $720 / 721$ Correct |
| **Macro Precision** | **99.83%** | Unweighted class average |
| **Macro Recall** | **99.88%** | Unweighted class average |
| **Macro F1-Score** | **99.85%** | Harmonic mean of precision & recall |
| **Weighted Precision** | **99.86%** | Frequency-weighted |
| **Weighted Recall** | **99.86%** | Frequency-weighted |
| **Weighted F1-Score** | **99.86%** | Frequency-weighted |

---

## 2. Per-Class Classification Report

| Disease Class | Precision | Recall | F1-Score | Test Support |
| :--- | :---: | :---: | :---: | :---: |
| **Bacterial Blight** | **100.00%** | **99.50%** | **99.75%** | 200 images |
| **Rice Blast** | **99.31%** | **100.00%** | **99.65%** | 144 images |
| **Brown Spot** | **100.00%** | **100.00%** | **100.00%** | 179 images |
| **Rice Tungro** | **100.00%** | **100.00%** | **100.00%** | 198 images |
| **Macro Average** | **99.83%** | **99.88%** | **99.85%** | 721 images |
| **Weighted Average** | **99.86%** | **99.86%** | **99.86%** | 721 images |

---

## 3. Confusion Matrix

```text
                     Predicted Labels
                 Bacterialblight   Blast   Brownspot   Tungro
Actual Labels
Bacterialblight        199           1         0         0
Blast                    0         144         0         0
Brownspot                0           0       179         0
Tungro                   0           0         0       198
```

- **True Positives**: 720
- **False Positives**: 1 (Blast falsely predicted for 1 Bacterial Blight sample)
- **False Negatives**: 1 (1 Bacterial Blight sample misclassified)

---

## 4. Single Test-Set Error Analysis

Across the entire 721-sample test set, exactly **one sample was misclassified**:

- **Ground Truth**: `Bacterialblight`
- **Model Prediction**: `Blast`
- **Prediction Confidence**: `78.78%`
- **Observed Behavior**: The sample contained necrotic edge discoloration that visually shared overlapping color and textural attributes with early-stage blast lesions. The model exhibited lower confidence ($78.78\%$) on this anomalous sample compared to its mean test confidence ($>99\%$), accurately reflecting higher classification uncertainty.

---

## 5. Confidence Distribution Analysis

| Metric | Value |
| :--- | :--- |
| **Mean Overall Confidence** | **99.24%** |
| **Mean Confidence on Correct Predictions** | **99.27%** |
| **Confidence on Single Incorrect Prediction** | **78.78%** |

The significant gap between average correct confidence ($99.27\%$) and the error confidence ($78.78\%$) demonstrates well-calibrated softmax probability outputs.

---

## 6. Ablation & Progressive Fine-Tuning Comparison

| Training Phase | Backbone Configuration | Validation Accuracy | Final Test Accuracy |
| :--- | :--- | :---: | :---: |
| **Stage A** | Frozen ViT-B/16 + GRU + Linear Head | 98.75% | 98.61% |
| **Stage B (Final)** | ViT-B/16 (Top 2 Layers Unfrozen) + GRU + Linear Head | **99.72%** | **99.86%** |
| **Delta / Gain** | Progressive Layer Adaptation | **+0.97%** | **+1.25%** |

Fine-tuning the upper attention layers enabled the Vision Transformer to refine patch attention weights specifically for agricultural rice foliar characteristics, delivering high diagnostic fidelity.
