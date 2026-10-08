# LEAFSIGHT Comprehensive Viva & Technical Interview Q&A

This document provides concise, technically rigorous answers to common questions asked during project viva examinations, technical reviews, and academic evaluations.

---

### Q1: Why use a Vision Transformer (ViT) instead of a standard Convolutional Neural Network (CNN)?
**Answer**: CNNs rely on local receptive fields (typically $3 \times 3$ or $5 \times 5$ filters) and build global context only through deep stacking of pooling layers. Vision Transformers use Multi-Head Self-Attention (MHSA) to model global relationships across all image patches from the very first layer. This allows the model to capture long-range contextual relationships across large foliar surfaces and varied lesion patterns much more effectively.

---

### Q2: Why use patch features and why remove the `[CLS]` token?
**Answer**: In standard ViT classification, the `[CLS]` token aggregates global information into a single vector. By removing the `[CLS]` token (`patch_features = vit_output.last_hidden_state[:, 1:, :]`), we preserve the explicit sequence of all 196 distinct spatial patch vectors ($14 \times 14$ grid). This allows our downstream GRU to model sequential spatial transitions and contiguous lesion shapes across the leaf surface.

---

### Q3: Why place a GRU after the Vision Transformer?
**Answer**: While ViT captures pairwise self-attention between patches, a Gated Recurrent Unit (GRU) provides directional sequence modeling. By feeding the 196 patch tokens sequentially through a GRU, the model learns directional spatial gradients (such as longitudinal leaf streaks characteristic of Bacterial Blight or circular lesion margins in Brown Spot) with fewer parameters and lower computational overhead than an LSTM.

---

### Q4: Why use a pretrained ViT model (`vit-base-patch16-224-in21k`)?
**Answer**: Training Vision Transformers from scratch requires massive datasets (hundreds of millions of images) because ViTs lack the inductive biases (translation equivariance) present in CNNs. Initializing with ImageNet-21k weights provides robust visual feature extractors (edges, textures, shapes) that converge rapidly with high accuracy on agricultural data.

---

### Q5: Why did you freeze the ViT backbone initially in Stage A?
**Answer**: If a randomly initialized classification head and GRU are trained alongside an unfrozen pretrained backbone, large initial gradient updates backpropagate into the backbone and destroy the pretrained representations (catastrophic forgetting). Freezing the ViT allows the GRU and classifier to learn stable representations first.

---

### Q6: Why did you fine-tune only the upper 2 ViT layers in Stage B?
**Answer**: Lower transformer layers capture generic low-level features (edges, color gradients) that are universally applicable. Upper layers capture task-specific semantic representations. Unfreezing only the top 2 layers allows domain-specific adaptation to leaf lesions while maintaining regularization and computational efficiency.

---

### Q7: Why is the input resolution $224 \times 224$?
**Answer**: The pretrained ViT-B/16 architecture expects $224 \times 224$ images, yielding an integer grid of $(224/16) \times (224/16) = 14 \times 14 = 196$ patches of dimension $16 \times 16$. This maintains compatibility with the pretrained position embeddings.

---

### Q8: Why apply standard ImageNet normalization ($\mu=[0.485, 0.456, 0.406], \sigma=[0.229, 0.224, 0.225]$)?
**Answer**: The pretrained ViT weights were learned on ImageNet distributions. Applying identical normalization ensures that input activations match the expected numerical range of the pretrained transformer layers.

---

### Q9: Why use the AdamW optimizer instead of standard SGD or Adam?
**Answer**: AdamW decouples weight decay from the gradient update calculation. In standard Adam, $L_2$ regularization is combined with gradient momentum, which leads to suboptimal weight decay for parameters with large historical gradients. AdamW ensures effective weight decay regularization, which is crucial for transformer stability.

---

### Q10: Why use Cross-Entropy Loss?
**Answer**: Cross-Entropy Loss measures the performance of a classification model whose output is a probability distribution over discrete mutual classes, penalizing confident incorrect predictions exponentially through logarithmic loss.

---

### Q11: Why is Macro-F1 preferred over standard accuracy alone?
**Answer**: Accuracy can be deceptive if any class imbalance exists. Macro-F1 calculates the harmonic mean of precision and recall for each class independently and averages them with equal weight, ensuring that rare or smaller disease classes receive equal scrutiny.

---

### Q12: What is ViT Attention Rollout and why require `attn_implementation="eager"`?
**Answer**: Attention Rollout recursively multiplies attention matrices across all transformer layers to track how information flows from input patches to the final representation. In modern Hugging Face Transformers, the default attention implementation is SDPA (Scaled Dot-Product Attention) for speed, which fuses operations and discards intermediate attention weights. Setting `attn_implementation="eager"` forces explicit attention matrix computation, enabling rollout extraction.

---

### Q13: What does the $99.86\%$ test accuracy actually mean?
**Answer**: It means that on a completely unseen, held-out test split of 721 rice leaf images, the model correctly predicted 720 samples and made exactly 1 error.

---

### Q14: Why not claim "100% perfect accuracy"?
**Answer**: Perfect accuracy in empirical machine learning often indicates overfitting, data leakage, or evaluation on training data. Acknowledging the single test error ($720/721$) and analyzing its confidence ($78.78\%$) demonstrates rigorous scientific integrity.

---

### Q15: Why is the test set strictly isolated?
**Answer**: If test images are used for tuning hyperparameters or feature selection, data leakage occurs, inflating performance estimates. Isolating the 721 test images until final evaluation guarantees an unbiased measurement of generalizability.

---

### Q16: Why use FastAPI for the backend?
**Answer**: FastAPI provides asynchronous request handling, automatic OpenAPI documentation (`/docs`), fast Pydantic schema validation, and native support for singleton lifespan management to load the 346 MB PyTorch model once in memory.

---

### Q17: Why use React + Vite for the frontend?
**Answer**: Vite offers instantaneous hot module replacement (HMR) and optimized build times. React provides a declarative component hierarchy for managing stateful UI transitions (drag-and-drop, preview, loading spinners, real-time probability bars, and attention map toggles).

---

### Q18: How do the frontend and backend communicate?
**Answer**: The React frontend sends standard asynchronous `multipart/form-data` HTTP `POST` requests (`/api/predict` or `/api/explain`) to the FastAPI server using `fetch()`. The backend returns JSON responses containing classification labels, confidence values, class probabilities, and base64-encoded attention heatmaps.

---

### Q19: What happens step-by-step when a user uploads an image?
**Answer**:
1. Client selects or drops an image; React creates an in-memory preview URL (`URL.createObjectURL`).
2. Client clicks "Analyze Leaf"; React attaches the file to `FormData` and sends a `POST /api/explain` request.
3. FastAPI receives the byte stream, validates image headers and integrity with PIL.
4. Image is resized to $224 \times 224$ and normalized to a PyTorch tensor on CUDA/CPU.
5. Model runs `ViT-B/16` forward pass with `output_attentions=True` inside `torch.no_grad()`.
6. Patch features ($196 \times 768$) pass through the GRU and classifier to compute softmax probabilities.
7. Attention Rollout generates a 2D interpolated attention map and blends it with the original image.
8. Server returns JSON with disease diagnosis, confidence, probability distribution, and base64 heatmap.
9. React renders the diagnosis badge, probability progress bars, and interactive attention view.

---

### Q20: What are the key limitations of the current system?
**Answer**:
- Tested primarily on single-leaf imagery under controlled/semi-controlled backgrounds.
- Extreme field occlusion or multi-disease co-infection on a single leaf requires multi-label segmentation extensions in future work.
