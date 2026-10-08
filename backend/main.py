import io
import os
import random
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image, UnidentifiedImageError

from .inference_service import get_inference_service, InferenceService
from .explainability_service import ExplainabilityService


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# Resolved absolute path to the test dataset
# Walks up from this file: backend/ → project root → data/processed/test/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DATA_DIR = _PROJECT_ROOT / "data" / "processed" / "test"

# Canonical class names (order is intentional)
KNOWN_CLASSES: List[str] = ["Bacterialblight", "Blast", "Brownspot", "Tungro"]

# Number of sample filenames to expose per class (full image served on demand)
SAMPLES_PER_CLASS = 8


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[LeafSight] FastAPI initializing…")
    try:
        service = get_inference_service()
        print(f"[LeafSight] Backend ready on device: {service.device}")
    except Exception as e:
        print(f"[LeafSight] Error preloading model: {e}")
    yield
    print("[LeafSight] Backend shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="LEAFSIGHT API",
    description="Intelligent Rice Leaf Disease Recognition Backend",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def validate_and_open_image(file: UploadFile, contents: bytes) -> Image.Image:
    filename = (file.filename or "").lower()
    has_valid_ext = any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)
    is_valid_mime = file.content_type in ALLOWED_IMAGE_TYPES

    if not has_valid_ext and not is_valid_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Supported: PNG, JPG, JPEG, WEBP, BMP.",
        )
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
        image = Image.open(io.BytesIO(contents))
        return image
    except (UnidentifiedImageError, OSError, Exception) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or invalid image: {str(err)}",
        )


def _get_class_dir(class_name: str) -> Path:
    """Resolve and validate a class directory, preventing path traversal."""
    if class_name not in KNOWN_CLASSES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown class '{class_name}'. Valid: {KNOWN_CLASSES}",
        )
    class_dir = TEST_DATA_DIR / class_name
    if not class_dir.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test data directory not found for class '{class_name}'.",
        )
    return class_dir


def _list_image_files(class_dir: Path) -> List[str]:
    """Return sorted list of image filenames in a class directory."""
    return sorted(
        f.name
        for f in class_dir.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "project": "LEAFSIGHT",
        "title": "Intelligent Rice Leaf Disease Recognition",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    try:
        service = get_inference_service()
        return {
            "status": "ok",
            "model_loaded": service.model is not None,
            "device": str(service.device),
        }
    except Exception as e:
        return {"status": "error", "model_loaded": False, "device": "unknown", "error": str(e)}


@app.get("/api/samples")
def list_samples() -> Dict[str, Any]:
    """
    Return a structured list of verified test-set samples.
    Exposes up to SAMPLES_PER_CLASS deterministically-chosen filenames per class.
    Full images are served via GET /api/samples/{class_name}/{filename}.
    """
    if not TEST_DATA_DIR.is_dir():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Test dataset directory not found on server.",
        )

    classes = []
    for cls in KNOWN_CLASSES:
        try:
            class_dir = TEST_DATA_DIR / cls
            if not class_dir.is_dir():
                continue
            all_files = _list_image_files(class_dir)
            total = len(all_files)
            # Pick evenly-spaced samples for a representative spread
            if total <= SAMPLES_PER_CLASS:
                chosen = all_files
            else:
                step = total // SAMPLES_PER_CLASS
                chosen = [all_files[i * step] for i in range(SAMPLES_PER_CLASS)]

            classes.append({
                "name": cls,
                "count": total,
                "samples": chosen,
            })
        except Exception:
            continue

    return {"classes": classes, "samples_per_class": SAMPLES_PER_CLASS}


@app.get("/api/samples/{class_name}/{filename}")
def serve_sample_image(class_name: str, filename: str):
    """
    Serve a single verified test-set image.
    Strictly validates class_name and filename to prevent path traversal.
    """
    class_dir = _get_class_dir(class_name)

    # Sanitize filename: reject anything with path separators or dots that go up
    safe_name = Path(filename).name  # strip any directory component
    if safe_name != filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    file_path = class_dir / safe_name

    # Ensure the resolved path is still inside the class directory
    try:
        file_path.resolve().relative_to(class_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename (path traversal attempt).",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found in class '{class_name}'.",
        )

    suffix = file_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".bmp": "image/bmp",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")

    return FileResponse(path=str(file_path), media_type=media_type)


@app.post("/api/predict")
async def predict(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        contents = await file.read()
        image = validate_and_open_image(file, contents)
        service = get_inference_service()
        return service.predict(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}",
        )


@app.post("/api/explain")
async def explain(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        contents = await file.read()
        image = validate_and_open_image(file, contents)
        return ExplainabilityService.explain(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explainability failed: {str(e)}",
        )
