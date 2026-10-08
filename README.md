# LEAFSIGHT: Intelligent Rice Leaf Disease Recognition System

An end-to-end deep learning platform combining **Vision Transformers (ViT-B/16)**, **Gated Recurrent Units (GRU)**, and **Multi-Layer Attention Rollout Explainability** for high-accuracy, transparent rice disease diagnosis.

---

## 1. Project Overview

**LEAFSIGHT** is a full-stack computer vision application engineered to detect and classify major rice foliar diseases from leaf imagery. By integrating patch-level visual embeddings from a pretrained Vision Transformer with sequential spatial modeling via a Gated Recurrent Unit, LEAFSIGHT achieves state-of-the-art diagnostic performance while providing visual attention maps that explain model predictions.

---

## 2. Problem Statement

Rice (*Oryza sativa*) is the primary dietary staple for over 3.5 billion people. However, foliar diseases such as Bacterial Blight, Rice Blast, Brown Spot, and Tungro frequently cause catastrophic yield reductions ranging from 10% to over 50%. 

Key challenges in conventional management include:
- **Visual ambiguity**: Early symptoms of distinct diseases share overlapping visual discoloration.
- **Scarcity of domain experts**: Agricultural extension officers cannot manually inspect all remote smallholder farms.
- **Black-box AI mistrust**: Traditional deep learning models provide predictions without visual reasoning, hindering adoption by agronomists and farmers.

---

## 3. Project Objectives

1. **High-Accuracy Automated Diagnosis**: Classify rice leaf imagery into 4 major disease categories with high reliability.
2. **Hybrid Spatial-Sequential Modeling**: Leverage global attention from Vision Transformers combined with GRU sequence aggregation across spatial patch tokens.
3. **Transparent Model Explainability**: Implement ViT Attention Rollout to highlight the specific foliar regions that drove the classification.
4. **Interactive Full-Stack Web Application**: Provide a responsive, low-latency web interface for real-time field image diagnosis.

---

## 4. End-to-End System Architecture

```text
Rice Leaf Image
       │
       ▼
 Preprocessing (224×224, ImageNet Normalization)
       │
       ▼
   ViT-B/16 (12 Transformer Layers, 16×16 Patches)
       │
       ▼
 Patch Features (196 Spatial Tokens, 768-dim)
       │
       ▼
      GRU (Hidden Dim: 128, Sequential Aggregation)
       │
       ▼
   Classifier (Dropout 0.3 + Linear Projection to 4 Classes)
       │
       ▼
 Disease Prediction + Confidence + Probabilities
       │
       ▼
 Explainability (ViT Attention Rollout Heatmap Overlay)
```

---

## 5. Dataset Summary & Preprocessing

### Evaluated Disease Classes:
1. **Bacterial Blight** (*Xanthomonas oryzae pv. oryzae*)
2. **Rice Blast** (*Magnaporthe oryzae*)
3. **Brown Spot** (*Bipolaris oryzae*)
4. **Rice Tungro Disease** (*Rice Tungro Bacilliform & Spherical Viruses*)

### Dataset Sanitization & Splits:
- **Deduplication**: MD5 perceptual byte hashing purged all intra-class redundant duplicates and resolved cross-class conflicting labels.
- **Train Split (70%)**: Used for parameter optimization.
- **Validation Split (15%)**: Used for hyperparameter tuning and model checkpointing.
- **Test Split (15% - 721 images)**: Strictly held out and evaluated only once after all training phases.

### Preprocessing Pipeline:
- Resolution: $224 \times 224 \times 3$ RGB.
- Normalization: ImageNet channel distribution ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$).
- Training Augmentations: Random resized cropping, random horizontal flips ($p=0.5$), random rotation ($\pm 15^\circ$), and color jitter (brightness/contrast $\pm 0.2$).

---

## 6. Two-Stage Training & Fine-Tuning Strategy

### Stage A: Frozen ViT Feature Aggregation
- **Backbone**: Pretrained `google/vit-base-patch16-224-in21k` with all 12 encoder layers frozen.
- **Trainable Modules**: GRU ($768 \rightarrow 128$) + Linear Classifier ($128 \rightarrow 4$).
- **Optimizer**: AdamW ($\text{lr} = 10^{-4}$).
- **Validation Accuracy**: **98.75%**.

### Stage B: Progressive Layer Fine-Tuning
- **Strategy**: Unfrozen the top 2 transformer encoder layers (Layers 10 & 11) alongside the GRU and classifier.
- **Optimizer**: AdamW with lower learning rate ($\text{lr} = 10^{-5}$) and weight decay $0.01$.
- **Validation Accuracy**: **99.72%** (**+0.97 percentage points** improvement).

---

## 7. Verified Evaluation Results

The final fine-tuned model (`model/best_vit_gru_finetuned.pth`) was evaluated on the independent 721-sample test set:

| Evaluation Metric | Score | Detailed Performance |
| :--- | :---: | :--- |
| **Test Accuracy** | **99.86%** | **720 / 721 Correct Predictions** |
| **Macro Precision** | **99.83%** | Balanced across all 4 classes |
| **Macro Recall** | **99.88%** | Balanced across all 4 classes |
| **Macro F1-Score** | **99.85%** | Harmonic mean of precision & recall |

### Per-Class Performance Breakdown:
- **Bacterial Blight**: Precision `100.00%` | Recall `99.50%` | F1-Score `99.75%` (200 test images)
- **Rice Blast**: Precision `99.31%` | Recall `100.00%` | F1-Score `99.65%` (144 test images)
- **Brown Spot**: Precision `100.00%` | Recall `100.00%` | F1-Score `100.00%` (179 test images)
- **Rice Tungro**: Precision `100.00%` | Recall `100.00%` | F1-Score `100.00%` (198 test images)

### Error Analysis:
Across the entire 721-image test set, exactly **one sample was misclassified**:
- **Actual**: `Bacterialblight` | **Predicted**: `Blast` | **Confidence**: `78.78%`
- The sample contained atypical necrotic edge lesions resembling blast symptoms, and the model exhibited appropriately lower confidence ($78.78\%$) compared to its mean test confidence ($>99\%$).

---

## 8. Model Explainability (ViT Attention Rollout)

LEAFSIGHT implements multi-layer ViT Attention Rollout configured with `attn_implementation="eager"`.

By recursively calculating attention flow across all 12 transformer encoder layers:
1. Multi-head self-attentions are averaged across heads and combined with residual identity matrices.
2. Layer matrices are multiplied from input to output.
3. The CLS token attention to all 196 patch tokens is extracted, reshaped to $14 \times 14$, upsampled to $224 \times 224$, and rendered as a blended Jet colormap overlay.

> **Note**: This attention visualization indicates image regions that received stronger visual attention during feature extraction to assist agronomic verification.

---

## 9. Full-Stack Web Application

The LEAFSIGHT web interface is designed for clean, responsive, and intuitive agricultural diagnostics:

- **Backend (FastAPI)**: High-performance asynchronous REST API that caches the 346 MB model in memory at startup, supporting both CUDA GPU acceleration and CPU inference.
- **Frontend (React + Vite)**: Modern user interface featuring drag-and-drop file upload, instant image previews, real-time diagnostic cards, horizontal probability distributions, and interactive attention map inspection.

---

## 10. Repository Structure

```text
LEAFSIGHT/
├── backend/
│   ├── main.py                     # FastAPI application endpoints and CORS setup
│   ├── inference_service.py        # Cached singleton ViT-GRU inference service
│   ├── explainability_service.py   # ViT Attention Rollout heatmap generator
│   └── requirements.txt            # Backend Python dependencies
│
├── frontend/
│   ├── package.json                # Frontend dependencies (React, Vite, Lucide)
│   ├── vite.config.js              # Vite build and proxy configuration
│   ├── index.html                  # HTML entry point with metadata and fonts
│   └── src/
│       ├── App.jsx                 # Main application state and layout
│       ├── config.js               # Centralized API configuration & disease metadata
│       ├── main.jsx                # React root mount
│       ├── components/
│       │   ├── Header.jsx          # Header with live backend connection badge
│       │   ├── BenchmarkBanner.jsx # Verified test metrics banner
│       │   ├── ImageUploader.jsx   # Drag & drop upload and sample selectors
│       │   ├── ResultCard.jsx      # Diagnosis, confidence pill & disease guide
│       │   ├── ProbabilityBars.jsx # Calibrated 4-class probability bars
│       │   ├── AttentionHeatmap.jsx# Interactive attention rollout visualization
│       │   └── Footer.jsx          # Project footer
│       └── styles/
│           ├── App.css             # Light natural agricultural design system
│           └── index.css           # CSS reset rules
│
├── docs/
│   ├── ARCHITECTURE.md             # In-depth architectural specification
│   ├── METHODOLOGY.md              # Detailed training and evaluation methodology
│   ├── RESULTS.md                  # Complete experimental data and tables
│   ├── DEMO_SCRIPT.md              # 3–5 minute presentation and viva script
│   ├── VIVA_QA.md                  # Comprehensive viva questions and answers
│   └── PROJECT_SUMMARY.md          # Formal executive summary
│
├── model/
│   ├── class_names.json            # Target disease class names
│   ├── config.json                 # Model hyperparameter configuration
│   └── finetuning_config.json      # Stage B fine-tuning parameters
│
├── outputs/
│   ├── test_results.json           # Serialized test evaluation metrics
│   ├── confusion_matrix.png        # Test confusion matrix plot
│   ├── accuracy_curve.png          # Stage A training accuracy curves
│   ├── finetuning_accuracy_curve.png # Stage B fine-tuning accuracy curves
│   └── explainability/             # Sample attention rollout visualizations
│
├── scripts/
│   ├── audit_dataset.py            # Dataset auditing and duplicate checker
│   ├── prepare_dataset.py          # Data cleaner and 70/15/15 splitter
│   ├── preprocess.py               # Preprocessing and PyTorch dataloader setup
│   ├── build_model.py              # ViT-GRU architecture verification
│   ├── sanity_train.py             # Quick multi-epoch sanity trainer
│   ├── train.py                    # Stage A baseline training script
│   ├── finetune.py                 # Stage B fine-tuning script
│   ├── evaluate.py                 # Final test set benchmark evaluation
│   ├── explain.py                  # Standalone attention rollout generator
│   └── inference.py                # Command-line single-image predictor
│
└── README.md                       # Master documentation file
```

---

## 11. Installation & Setup Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) NVIDIA GPU with CUDA support for accelerated inference

---

### Step 1: Clone Repository
```bash
git clone https://github.com/bharatraghupatruni-ai/leafsight.git
cd leafsight
```

---

### Step 2: Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Start FastAPI backend server (from project root)
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

---

### Step 3: Frontend Setup
```bash
# Open a new terminal and navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
- Web Application URL: `http://localhost:5173/`

---

## 12. REST API Specification

### 1. `GET /api/health`
Checks backend status and active compute hardware.
```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "cuda"
}
```

### 2. `POST /api/predict`
Accepts `multipart/form-data` with `file: UploadFile`.
```json
{
  "prediction": "Blast",
  "confidence": 0.9746,
  "probabilities": {
    "Bacterialblight": 0.0028,
    "Blast": 0.9746,
    "Brownspot": 0.0224,
    "Tungro": 0.0002
  },
  "image_size": [300, 300],
  "request_id": "4b62ce29-3ca0-4f7e-8b1c-032d165fab27"
}
```

### 3. `POST /api/explain`
Accepts `multipart/form-data` with `file: UploadFile`. Computes classification and returns the ViT Attention Rollout overlay as a Base64-encoded PNG data URL.
```json
{
  "prediction": "Blast",
  "confidence": 0.9746,
  "probabilities": {
    "Bacterialblight": 0.0028,
    "Blast": 0.9746,
    "Brownspot": 0.0224,
    "Tungro": 0.0002
  },
  "heatmap_base64": "data:image/png;base64,iVBORw0KGgoAAAANSU...",
  "description": "Attention visualization showing image regions that received stronger attention during the ViT prediction."
}
```

---

## 13. CLI Inference Example

To test inference directly from the command line:

```bash
python scripts/inference.py --image data/processed/test/Blast/BLAST1_003.jpg
```

**Output:**
```text
============================================================
LEAFSIGHT INFERENCE
============================================================
Device: cuda

Prediction:
Blast

Confidence:
97.46%

Class probabilities:
Bacterialblight: 0.28%
Blast: 97.46%
Brownspot: 2.24%
Tungro: 0.02%
============================================================
```

---

## 14. Limitations & Future Scope

### Current Limitations:
- Evaluated on individual leaf images under standardized/semi-controlled lighting.
- Does not currently perform multi-lesion pixel segmentation or multi-disease co-infection detection.

### Future Scope:
- **Mobile Edge Deployment**: Quantization (INT8 / ONNX Runtime) for offline edge deployment on agricultural drones or smartphones.
- **Multi-Label Pathology**: Extension to segment multiple overlapping leaf infections simultaneously.
- **Temporal Progression Tracking**: Integration with historical crop growth stages and local weather data to forecast disease propagation risk.

---

## 15. Project Metadata

- **Project**: LEAFSIGHT
- **Repository**: [bharatraghupatruni-ai/leafsight](https://github.com/bharatraghupatruni-ai/leafsight)
- **License**: MIT License
