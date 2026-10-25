"""tests/test_ocr.py
Unit tests for Optical Character Recognition (OCR) in app/ocr.py.

Following docs/03_TECHNICAL_DESIGN.md (section 7 and 9) and prompt P10:
- Validate Pillow upload validation (JPG/PNG only, max 5 MB).
- In-memory processing only (never written to disk).
- Text extraction with Tesseract.
- Error handling for invalid formats, corrupted bytes, empty input, and blank images (no_text_found).
"""

import io
import pytest
from PIL import Image, ImageDraw

from app.ocr import (
    MAX_IMAGE_BYTES,
    OCRError,
    extract_text_from_image,
    get_tesseract_cmd
)


def create_sample_text_image(text: str, fmt: str = "PNG") -> bytes:
    """Helper to generate an in-memory image containing crisp black text on white background."""
    img = Image.new("RGB", (900, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 100), text, fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_tesseract_binary_detection():
    """Verify that a valid tesseract binary path is located."""
    cmd = get_tesseract_cmd()
    assert len(cmd) > 0


def test_ocr_success_with_clean_image():
    """Verify OCR extracts readable text from synthetic PNG and JPEG images."""
    sample_phrase = "Urgent opening for Full Stack Web Developer at Mumbai branch"
    png_bytes = create_sample_text_image(sample_phrase, fmt="PNG")
    extracted_png = extract_text_from_image(png_bytes)

    assert "Developer" in extracted_png or "Full Stack" in extracted_png
    assert len(extracted_png) > 15

    jpeg_bytes = create_sample_text_image(sample_phrase, fmt="JPEG")
    extracted_jpeg = extract_text_from_image(jpeg_bytes)
    assert "Developer" in extracted_jpeg or "Full Stack" in extracted_jpeg


def test_ocr_rejects_blank_image_no_text_found():
    """Verify that an image with no text raises OCRError('no_text_found')."""
    blank_img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    buf = io.BytesIO()
    blank_img.save(buf, format="PNG")

    with pytest.raises(OCRError) as exc_info:
        extract_text_from_image(buf.getvalue())
    assert "no_text_found" in str(exc_info.value)


def test_ocr_rejects_unsupported_format():
    """Verify that non-JPEG/PNG formats (e.g. GIF, BMP) are rejected."""
    gif_img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    gif_img.save(buf, format="GIF")

    with pytest.raises(OCRError) as exc_info:
        extract_text_from_image(buf.getvalue())
    assert "Unsupported image format" in str(exc_info.value)


def test_ocr_rejects_oversized_payload():
    """Verify that images exceeding 5 MB are rejected immediately."""
    oversized_bytes = b"0" * (MAX_IMAGE_BYTES + 1024)
    with pytest.raises(OCRError) as exc_info:
        extract_text_from_image(oversized_bytes)
    assert "5 MB" in str(exc_info.value)


def test_ocr_rejects_corrupted_and_empty_data():
    """Verify that empty, None, and corrupted payloads are cleanly rejected."""
    with pytest.raises(OCRError):
        extract_text_from_image(b"")

    with pytest.raises(OCRError):
        extract_text_from_image(None)

    with pytest.raises(OCRError):
        extract_text_from_image(b"not a valid image byte stream")
