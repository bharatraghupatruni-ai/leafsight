# LEAFSIGHT Project Summary

**Project Title**: LEAFSIGHT: Intelligent Rice Leaf Disease Recognition System  
**Core Architecture**: Vision Transformer (`ViT-B/16`) + Gated Recurrent Unit (`GRU`) + Linear Classification Head  
**Explainability**: Multi-Layer ViT Attention Rollout  
**Application Stack**: FastAPI (Python 3.11 / PyTorch) + React 19 (Vite)  

---

## 1. Executive Summary
LEAFSIGHT is a high-performance, explainable deep learning diagnostic application designed for automated recognition of major rice foliar diseases: **Bacterial Blight**, **Rice Blast**, **Brown Spot**, and **Rice Tungro Disease**. By extracting 196 patch tokens from a pretrained Vision Transformer and modeling their spatial sequence with a Gated Recurrent Unit, the system captures both fine-grained textural lesions and macro-level spatial patterns across leaf blades.

On a strictly isolated test set of 721 images, LEAFSIGHT achieved **99.86% test accuracy** and **99.85% Macro-F1**, successfully classifying 720 out of 721 test samples.

---

## 2. Key Highlights & Achievements

1. **Novel Hybrid Architecture**:
   - Replaces standard pooling with sequence-aware GRU spatial modeling on ViT patch tokens.
   - Preserves all 196 patch tokens without discarding spatial information into a single scalar vector.

2. **Progressive Two-Stage Training**:
   - **Stage A (Frozen Backbone)**: Achieved 98.75% validation accuracy.
   - **Stage B (Progressive Fine-Tuning of Top 2 Layers)**: Lifted validation accuracy to 99.72% (+0.97%).

3. **Transparent Explainability**:
   - Implemented Attention Rollout with `attn_implementation="eager"`.
   - Generates pixel-level visual overlays showing which leaf regions influenced the prediction.

4. **Production-Ready Full-Stack Web Platform**:
   - FastAPI server with cached in-memory PyTorch model and GPU acceleration.
   - React 19 single-page application with responsive UI, real-time probability visualization, and interactive attention map inspection.

---

## 3. Verified Performance Metrics

| Evaluation Metric | Value |
| :--- | :--- |
| **Test Accuracy** | **99.86%** |
| **Macro Precision** | **99.83%** |
| **Macro Recall** | **99.88%** |
| **Macro F1-Score** | **99.85%** |
| **Correct Test Predictions** | **720 / 721** |
| **Bacterial Blight F1-Score** | **99.75%** |
| **Rice Blast F1-Score** | **99.65%** |
| **Brown Spot F1-Score** | **100.00%** |
| **Rice Tungro F1-Score** | **100.00%** |

---

## 4. Technology Stack

- **Machine Learning**: PyTorch, Torchvision, Hugging Face Transformers, NumPy, PIL, Matplotlib, Scikit-learn
- **Backend**: FastAPI, Uvicorn, Python-Multipart, Pydantic
- **Frontend**: React 19, Vite, Lucide-React, CSS3 Custom Properties
- **Version Control**: Git & GitHub (`bharatraghupatruni-ai/leafsight`)
