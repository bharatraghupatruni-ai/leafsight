# LEAFSIGHT Project Demonstration Script (3–5 Minutes)

*This guide provides a structured, concise speaking script for presenting the LEAFSIGHT project during final-year project reviews, academic demonstrations, and viva sessions.*

---

## 1. Problem Statement (30 seconds)
> "Good morning/afternoon, professors and evaluators. Rice is a staple food for over half the world's population. However, foliar diseases such as Bacterial Blight, Rice Blast, Brown Spot, and Tungro cause devastating crop yield losses of 10% to 50% annually. Traditional visual inspection by agronomists is labor-intensive, slow, and inaccessible to smallholder farmers in remote areas. Early and accurate automated disease diagnosis is critical."

---

## 2. Proposed Solution (30 seconds)
> "To address this challenge, we developed **LEAFSIGHT**, an intelligent full-stack rice disease diagnostic system. LEAFSIGHT combines the state-of-the-art visual representation capabilities of Vision Transformers (ViT) with the sequential context modeling of Gated Recurrent Units (GRU), complete with an attention rollout explainability module and a real-time web platform."

---

## 3. Dataset & Preprocessing (30 seconds)
> "Our dataset comprises thousands of curated field images across four primary rice pathology classes: Bacterial Blight, Blast, Brown Spot, and Tungro. We performed data integrity audits, purged intra-class and cross-class duplicates using MD5 hashing, and established a clean 70-15-15 split. The test set of 721 images was completely isolated until final evaluation. Images are resized to 224x224 and normalized using standard ImageNet parameters."

---

## 4. Model Architecture (30 seconds)
> "Instead of standard CNNs, our architecture uses a pretrained **ViT-B/16** backbone. The 224x224 image is divided into 196 non-overlapping 16x16 patches. We remove the generic CLS token to retain the pure sequence of 196 patch embeddings. These spatial patch vectors are processed by a **GRU** layer to model directional lesion continuity across the leaf blade, followed by dropout regularization and a 4-class linear classifier."

---

## 5. Two-Stage Training Protocol (30 seconds)
> "We trained the network in two distinct stages:
> - **Stage A**: We froze the entire ViT backbone and trained only the GRU and classifier using AdamW with learning rate 1e-4, achieving 98.75% validation accuracy.
> - **Stage B**: We unfroze the top 2 ViT transformer encoder layers and fine-tuned with a lower learning rate of 1e-5 and weight decay 0.01. This lifted our validation accuracy to 99.72%."

---

## 6. Experimental Results (30 seconds)
> "On the strictly held-out test set of 721 images, LEAFSIGHT achieved:
> - **99.86% Test Accuracy**
> - **99.85% Macro F1-Score**
> - **720 correct predictions out of 721**
> Both Brown Spot and Tungro achieved 100% precision and recall, with Bacterial Blight at 99.75% F1 and Blast at 99.65% F1."

---

## 7. Model Explainability (30 seconds)
> "A major limitation of deep learning in agriculture is the black-box problem. In LEAFSIGHT, we implemented **ViT Attention Rollout**. By recursively tracking attention flow across all 12 transformer layers, we generate a high-resolution attention heatmap overlaid on the leaf image. This visualizes exactly which visual regions and lesions received the highest model attention during classification."

---

## 8. Web Application Stack (30 seconds)
> "We developed an end-to-end web application with:
> - A high-performance **FastAPI backend** that loads the trained PyTorch model once into GPU/CPU memory at startup.
> - A modern, responsive **React + Vite frontend** that supports drag-and-drop uploads, instant diagnostic reports, horizontal probability bars, and interactive attention map visualization."

---

## 9. Live System Walkthrough (45 seconds)
*(Demonstrate on the live browser UI at http://localhost:5173)*
1. "Here is the LEAFSIGHT interface showing live backend status on CUDA."
2. "We can drag and drop a field image or select one of our quick test samples."
3. *(Click 'Rice Blast Sample' and click 'Analyze Leaf')*
4. "Within milliseconds, the backend returns:
   - Predicted Disease: **Rice Blast**
   - Confidence: **97.46%**
   - Calibrated probability distribution across all 4 classes.
   - Causal pathogen and actionable agronomic management advice.
   - The **Model Attention** heatmap, clearly highlighting the spindle-shaped blast lesion."
5. *(Click 'Reset' to demonstrate clean reset state)*

---

## 10. Conclusion (15 seconds)
> "In conclusion, LEAFSIGHT demonstrates how combining Vision Transformers, Recurrent Units, and explainability mechanisms creates a highly accurate, transparent, and practical tool for agricultural diagnostics. Thank you, and we welcome any questions."
