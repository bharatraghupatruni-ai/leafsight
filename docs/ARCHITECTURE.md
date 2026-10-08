# LEAFSIGHT System Architecture

LEAFSIGHT utilizes a hybrid deep learning architecture that combines a pretrained Vision Transformer (**ViT-B/16**) for fine-grained patch representation learning with a Gated Recurrent Unit (**GRU**) for sequential spatial context aggregation, followed by a linear classification head.

---

## 1. High-Level Pipeline

```text
Rice Leaf Image (RGB)
        │
        ▼
[ Preprocessing & Normalization ] (224 × 224, ImageNet Mean & Std)
        │
        ▼
[ Pretrained ViT-B/16 Encoder ] (16×16 Patches, 12 Transformer Layers, 768 Hidden Dim)
        │
        ▼
[ Discard CLS Token ] ──────────► [ 196 Spatial Patch Tokens ] (Shape: [Batch, 196, 768])
        │
        ▼
[ Gated Recurrent Unit (GRU) ] (Hidden Dim: 128, Batch First, 1 Layer)
        │
        ▼
[ Final Sequential Hidden State ] (Shape: [Batch, 128])
        │
        ▼
[ Dropout (p = 0.3) ]
        │
        ▼
[ Linear Classifier Head ] ─────► [ 4 Class Logits ] (Shape: [Batch, 4])
        │
        ▼
[ Softmax Activation ] ─────────► [ Disease Probabilities & Diagnostic Output ]
```

---

## 2. Architectural Components

### A. Input & Preprocessing
- **Dimensions**: Images are standardized to $224 \times 224 \times 3$.
- **Normalization**: Standard ImageNet channel-wise normalization:
  - $\mu = [0.485, 0.456, 0.406]$
  - $\sigma = [0.229, 0.224, 0.225]$

### B. Vision Transformer (ViT-B/16)
- **Base Model**: `google/vit-base-patch16-224-in21k`
- **Patch Resolution**: $16 \times 16$ non-overlapping spatial patches.
- **Number of Patches**: $(224 / 16) \times (224 / 16) = 14 \times 14 = 196$ patches.
- **Embedding Dimension**: 768.
- **Attention Configuration**: Configured with `attn_implementation="eager"` to support attention matrix extraction for ViT attention rollout explainability.

### C. CLS Token Removal & Spatial Sequence Retention
In standard ViT classification, the `[CLS]` token is used as an aggregated summary representation. In LEAFSIGHT, the `[CLS]` token is removed (`patch_features = vit_output.last_hidden_state[:, 1:, :]`), preserving the explicit sequence of all 196 individual patch features. This allows subsequent layers to process structured spatial patch transitions across the leaf surface.

### D. Gated Recurrent Unit (GRU)
- **Input Dimension**: 768 (matching ViT patch embedding size).
- **Hidden Dimension**: 128.
- **Layers**: 1 layer, batch-first.
- **Purpose**: Sequentially integrates contextual information across the 196 spatial patch tokens, learning directional lesion gradients and spatial co-occurrences of fungal or bacterial foliar damage.

### E. Classification Head
- **Regularization**: Dropout ($p = 0.3$) applied to the final GRU hidden state ($h_T \in \mathbb{R}^{128}$).
- **Linear Projection**: Fully connected layer projecting $\mathbb{R}^{128} \rightarrow \mathbb{R}^{4}$.
- **Output Classes**:
  1. `Bacterialblight`
  2. `Blast`
  3. `Brownspot`
  4. `Tungro`

---

## 3. Explainability Architecture (ViT Attention Rollout)

To provide transparent visual justification for each diagnosis without retraining or auxiliary models:
1. Multi-head self-attentions are averaged across all attention heads for each layer.
2. An identity matrix is added to represent the residual stream connections:
   $$A_{\text{layer}} = 0.5 \cdot A + 0.5 \cdot I$$
3. Attention matrices are recursively multiplied across layers from input to output:
   $$R = \prod_{l=1}^{L} A_l$$
4. The rollout attention vector from the `[CLS]` token to all 196 patch tokens is extracted.
5. The 1D vector ($196$) is reshaped into a 2D matrix ($14 \times 14$), min-max normalized, bilinearly interpolated to $224 \times 224$, and rendered as a blended Jet colormap overlay.

---

## 4. Full-Stack Web Integration

```text
Browser Client (React + Vite)
        │
        ├── POST /api/predict (Multipart Form Image Upload)
        │       │
        │       ▼
        ├── FastAPI Backend (Inference Service - Cached Singleton)
        │       │
        │       └── Model Forward Pass (torch.no_grad, CUDA/CPU)
        │
        └── POST /api/explain (Multipart Form Image Upload)
                │
                ▼
        ├── FastAPI Backend (Explainability Service)
                │
                └── Attention Rollout Computation → Base64 PNG Overlay
```
