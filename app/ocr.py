"""app/ocr.py
Image validation and Optical Character Recognition (OCR) for DAR Fake Job Detector.

Following docs/03_TECHNICAL_DESIGN.md (sections 7 and 9) and roadmap prompt P10:
- Validate upload with Pillow (JPG/PNG only, max 5 MB, verify true image integrity).
- Process strictly in memory (io.BytesIO) — never save image to disk.
- Discard EXIF metadata.
- Preprocess: greyscale conversion ('L'), auto-contrast enhancement.
- Intelligent resizing: scale small images to target width ~1500 px (cap max dimension at 4000 px).
- Pytesseract execution: lang="eng", psm 3; if < 20 characters, fallback to psm 6.
- Configurable Tesseract binary path via TESSERACT_CMD env variable or system default.
- Return extracted text or raise OCRError("no_text_found").
"""

import io
import os
import re
from PIL import Image, ImageOps
import pytesseract

# Constants
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_FORMATS = {"JPEG", "PNG"}
TARGET_WIDTH = 1000
MAX_DIMENSION = 1600


class OCRError(Exception):
    """Custom exception raised for image validation or OCR failures."""
    pass


def get_tesseract_cmd() -> str:
    """Retrieve Tesseract executable path from environment, config, or system PATH."""
    env_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if env_cmd:
        return env_cmd

    # Check common Homebrew / Unix locations on macOS and Linux
    common_locations = [
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/usr/bin/tesseract",
    ]
    for loc in common_locations:
        if os.path.exists(loc) and os.access(loc, os.X_OK):
            return loc

    return "tesseract"


def extract_text_from_image(image_bytes: bytes) -> str:
    """Validate image bytes and perform OCR in memory to extract text.

    Args:
        image_bytes: Raw binary content of the uploaded file.

    Returns:
        Extracted, cleaned text string.

    Raises:
        OCRError: If the image is invalid, exceeds 5 MB, or no text is detected.
    """
    if not image_bytes or not isinstance(image_bytes, (bytes, bytearray)):
        raise OCRError("No image data provided.")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise OCRError("Image file exceeds the 5 MB size limit.")

    # 1. Validate image format and integrity with Pillow in memory
    try:
        buffer = io.BytesIO(image_bytes)
        img = Image.open(buffer)
        img_format = img.format
        if not img_format or img_format.upper() not in ALLOWED_FORMATS:
            raise OCRError("Unsupported image format. Please upload a JPG or PNG image.")
        img.verify()
    except OCRError:
        raise
    except Exception as e:
        raise OCRError(f"Invalid or corrupted image file: {e}")

    # Re-open image after verify() since verify() closes the stream / marks state
    try:
        buffer.seek(0)
        img = Image.open(buffer)
        # Create a clean copy in memory to discard EXIF and metadata
        img = img.copy()
    except Exception as e:
        raise OCRError(f"Failed to process image: {e}")

    # 2. Preprocess: Convert to greyscale
    if img.mode != "L":
        img = img.convert("L")

    # 3. Enhance contrast
    try:
        img = ImageOps.autocontrast(img)
    except Exception:
        pass  # If autocontrast fails on an unusual palette, continue with greyscale

    # 4. Fast Resize: downscale large images (cap at 1600 px) and scale up tiny images (< 600 px)
    w, h = img.size
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        scale = min(MAX_DIMENSION / float(w), MAX_DIMENSION / float(h))
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    elif w < 600 and w > 0:
        scale = TARGET_WIDTH / float(w)
        new_w = TARGET_WIDTH
        new_h = int(h * scale)
        if new_h > MAX_DIMENSION:
            new_h = MAX_DIMENSION
            new_w = int(w * (MAX_DIMENSION / float(h)))
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)

    # 5. Configure Tesseract path
    pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()

    # 6. Run OCR with PSM 3 (Fully automatic page segmentation)
    raw_text = ""
    try:
        raw_text = pytesseract.image_to_string(img, lang="eng", config="--psm 3")
    except Exception as e:
        # Check if tesseract binary is missing
        err_msg = str(e).lower()
        if "not found" in err_msg or "no such file" in err_msg:
            raise OCRError("Tesseract OCR engine is not installed or configured on the server.")
        raw_text = ""

    # Clean text
    clean_text = re.sub(r"[ \t]+", " ", raw_text).strip()

    # 7. Fallback to PSM 6 (Assume a single uniform block of text) if < 20 chars
    if len(clean_text) < 20:
        try:
            psm6_text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
            psm6_clean = re.sub(r"[ \t]+", " ", psm6_text).strip()
            if len(psm6_clean) > len(clean_text):
                clean_text = psm6_clean
        except Exception:
            pass

    # Normalize multiple newlines to clean paragraphs
    clean_text = re.sub(r"\n\s*\n+", "\n\n", clean_text).strip()

    if not clean_text or len(clean_text) < 10:
        raise OCRError("no_text_found")

    return clean_text
