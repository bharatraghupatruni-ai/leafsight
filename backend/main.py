import io
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from .inference_service import get_inference_service, InferenceService
from .explainability_service import ExplainabilityService


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp"
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly load the model on startup so requests are served immediately
    print("[LeafSight] FastAPI initializing...")
    try:
        service = get_inference_service()
        print(f"[LeafSight] Backend ready on device: {service.device}")
    except Exception as e:
        print(f"[LeafSight] Error preloading model: {e}")
    yield
    print("[LeafSight] Backend shutting down.")


app = FastAPI(
    title="LEAFSIGHT API",
    description="Intelligent Rice Leaf Disease Recognition Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_and_open_image(file: UploadFile, contents: bytes) -> Image.Image:
    # Check filename extension if provided
    filename = (file.filename or "").lower()
    has_valid_ext = any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)
    is_valid_mime = file.content_type in ALLOWED_IMAGE_TYPES

    if not has_valid_ext and not is_valid_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Supported formats: PNG, JPG, JPEG, WEBP, BMP."
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()  # verify integrity
        # Re-open for actual reading
        image = Image.open(io.BytesIO(contents))
        return image
    except (UnidentifiedImageError, OSError, Exception) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file is corrupted or not a valid image: {str(err)}"
        )


@app.get("/")
def root():
    return {
        "project": "LEAFSIGHT",
        "title": "Intelligent Rice Leaf Disease Recognition",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    try:
        service = get_inference_service()
        is_loaded = service.model is not None
        device_name = str(service.device)
        return {
            "status": "ok",
            "model_loaded": is_loaded,
            "device": device_name
        }
    except Exception as e:
        return {
            "status": "error",
            "model_loaded": False,
            "device": "unknown",
            "error": str(e)
        }


@app.post("/api/predict")
async def predict(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        contents = await file.read()
        image = validate_and_open_image(file, contents)
        service = get_inference_service()
        result = service.predict(image)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {str(e)}"
        )


@app.post("/api/explain")
async def explain(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        contents = await file.read()
        image = validate_and_open_image(file, contents)
        result = ExplainabilityService.explain(image)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explainability execution failed: {str(e)}"
        )
