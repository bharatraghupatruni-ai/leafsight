import io
import base64
from typing import Dict, Any
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import torch

from .inference_service import get_inference_service, IMAGE_SIZE, NORM_MEAN, NORM_STD


def compute_attention_rollout(attentions: tuple) -> torch.Tensor:
    """
    Computes ViT Attention Rollout across all transformer layers.
    attentions is a tuple of tensors with shape: [layers, batch, heads, tokens, tokens]
    """
    attention_stack = torch.stack(attentions)
    
    # Average across all attention heads
    attention = attention_stack.mean(dim=2)
    
    # Add identity matrix to account for residual connections
    identity = torch.eye(attention.size(-1), device=attention.device)
    identity = identity.unsqueeze(0).unsqueeze(0)
    attention = attention + identity
    
    # Normalize rows
    attention = attention / (attention.sum(dim=-1, keepdim=True) + 1e-8)
    
    # Recursively multiply attention matrices across layers
    rollout = attention[0]
    for layer in range(1, attention.shape[0]):
        rollout = torch.bmm(attention[layer], rollout)
        
    # Extract CLS token attention to patch tokens (ignore CLS self-attention at index 0)
    cls_attention = rollout[0, 0, 1:]
    return cls_attention


def generate_heatmap_overlay(
    cls_attention: torch.Tensor,
    original_pil: Image.Image
) -> tuple[str, str]:
    """
    Transforms 1D patch attention into a 2D interpolated heatmap and blends with the input image.
    Returns: (blended_data_url, pure_heatmap_data_url)
    """
    # 196 patches corresponds to 14x14 grid for 224x224 input with 16x16 patch size
    attention_2d = cls_attention.reshape(14, 14).detach().cpu().numpy()
    
    # Min-max normalization
    min_val = attention_2d.min()
    max_val = attention_2d.max()
    norm_attention = (attention_2d - min_val) / (max_val - min_val + 1e-8)
    
    # Upsample attention map to 224x224 using bilinear interpolation
    tensor_att = torch.tensor(norm_attention).unsqueeze(0).unsqueeze(0)
    upsampled_att = torch.nn.functional.interpolate(
        tensor_att,
        size=(IMAGE_SIZE, IMAGE_SIZE),
        mode="bilinear",
        align_corners=False
    )[0, 0].numpy()
    
    # Prepare original image resized to 224x224
    img_resized = original_pil.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
    img_np = np.array(img_resized, dtype=np.float32) / 255.0
    
    # Apply colormap (jet)
    cmap = plt.get_cmap("jet")
    colored_heatmap = cmap(upsampled_att)[:, :, :3]
    
    # Pure attention map
    pure_uint8 = (np.clip(colored_heatmap, 0.0, 1.0) * 255).astype(np.uint8)
    pure_pil = Image.fromarray(pure_uint8)
    buf_pure = io.BytesIO()
    pure_pil.save(buf_pure, format="PNG")
    pure_b64 = f"data:image/png;base64,{base64.b64encode(buf_pure.getvalue()).decode('utf-8')}"
    
    # Blend: 55% original image + 45% heatmap
    blended = 0.55 * img_np + 0.45 * colored_heatmap
    blended = np.clip(blended, 0.0, 1.0)
    blended_uint8 = (blended * 255).astype(np.uint8)
    out_pil = Image.fromarray(blended_uint8)
    buffer = io.BytesIO()
    out_pil.save(buffer, format="PNG")
    blended_b64 = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
    
    return blended_b64, pure_b64


class ExplainabilityService:
    @staticmethod
    def explain(image: Image.Image) -> Dict[str, Any]:
        service = get_inference_service()
        model = service.model
        if model is None:
            raise RuntimeError("Model is not initialized.")
            
        input_tensor, original_size = service.preprocess_image(image)
        
        with torch.no_grad():
            outputs, vit_output = model(input_tensor, return_vit_output=True)
            probabilities = torch.softmax(outputs, dim=1)[0]
            
        predicted_index = int(torch.argmax(probabilities).item())
        predicted_class = service.class_names[predicted_index]
        confidence = float(probabilities[predicted_index].item())
        
        prob_dict = {
            class_name: round(float(probabilities[i].item()), 4)
            for i, class_name in enumerate(service.class_names)
        }
        
        attentions = vit_output.attentions
        if attentions is None:
            raise RuntimeError("ViT attentions were not returned. Ensure attn_implementation='eager'.")
            
        cls_attention = compute_attention_rollout(attentions)
        blended_b64, pure_b64 = generate_heatmap_overlay(cls_attention, image)
        
        return {
            "prediction": predicted_class,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "heatmap_base64": blended_b64,
            "pure_heatmap_base64": pure_b64,
            "description": "Attention visualization showing image regions that received stronger attention during the ViT prediction."
        }
