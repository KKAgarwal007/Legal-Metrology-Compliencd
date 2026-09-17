"""Image preprocessing pipeline and visualization utilities for OCR."""

import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    cv2 = None
    HAS_CV2 = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None
    HAS_PIL = False


def preprocess_image(image_path: str, output_path: str) -> Dict[str, Any]:
    """Preprocess image with OpenCV to optimize OCR accuracy.

    Pipeline:
    1. Read original image (preserving color information).
    2. Resize / upscale if smallest dimension < 1200px.
    3. Grayscale conversion.
    4. Contrast enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization).
    5. Denoising (fastNlMeansDenoising or Gaussian blur).
    6. Unsharp masking kernel for sharpening.
    7. Save processed image to output_path.

    Returns:
        dict: Metadata detailing dimensions and applied preprocessing steps.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    steps_applied: List[str] = []

    if not HAS_CV2 or cv2 is None:
        # Fallback if cv2 is unavailable: copy image via PIL or filesystem
        if HAS_PIL and Image is not None and os.path.exists(image_path):
            with Image.open(image_path) as img:
                w, h = img.size
                img.save(output_path)
            return {
                "original_path": image_path,
                "processed_path": output_path,
                "width": w,
                "height": h,
                "steps_applied": ["fallback_copy"],
            }
        return {
            "original_path": image_path,
            "processed_path": output_path,
            "width": 0,
            "height": 0,
            "steps_applied": ["none"],
        }

    # 1. Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image from '{image_path}'")

    orig_h, orig_w = img.shape[:2]
    steps_applied.append("load_original")

    # 2. Resize / upscale if smallest dimension < 1200px
    min_dim = min(orig_h, orig_w)
    target_min_dim = 1200
    if min_dim < target_min_dim and min_dim > 0:
        scale = target_min_dim / float(min_dim)
        # Cap scale at 3.0 to prevent excessive memory usage
        scale = min(scale, 3.0)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        steps_applied.append(f"resize_upscale_{scale:.2f}x")
    else:
        steps_applied.append("resize_skipped")

    curr_h, curr_w = img.shape[:2]

    # 3. Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    steps_applied.append("grayscale")

    # 4. Contrast enhancement using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    steps_applied.append("clahe_contrast_enhancement")

    # 5. Denoising
    # Using fastNlMeansDenoising for grayscale images or GaussianBlur
    try:
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10, templateWindowSize=7, searchWindowSize=21)
        steps_applied.append("fast_nl_means_denoising")
    except Exception:
        denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
        steps_applied.append("gaussian_denoising")

    # 6. Unsharp masking kernel for sharpening
    # Standard sharpening kernel: [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]
    sharpening_kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ], dtype=np.float32)
    sharpened = cv2.filter2D(denoised, -1, sharpening_kernel)
    steps_applied.append("unsharp_mask_sharpening")

    # 7. Save processed image
    cv2.imwrite(output_path, sharpened)

    return {
        "original_path": image_path,
        "processed_path": output_path,
        "width": curr_w,
        "height": curr_h,
        "steps_applied": steps_applied,
    }


def _get_bbox_coordinates(bbox: Any, img_w: int, img_h: int) -> Tuple[int, int, int, int]:
    """Normalize bounding box to (x1, y1, x2, y2) integer coordinates."""
    if not bbox:
        return (0, 0, 0, 0)

    # If format is 4-point polygon: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4 and isinstance(bbox[0], (list, tuple)):
        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        x1, x2 = int(min(xs)), int(max(xs))
        y1, y2 = int(min(ys)), int(max(ys))
    # If format is [x1, y1, x2, y2]
    elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    else:
        return (0, 0, 0, 0)

    # Clamp coordinates to image boundaries
    x1 = max(0, min(x1, img_w - 1))
    y1 = max(0, min(y1, img_h - 1))
    x2 = max(0, min(x2, img_w - 1))
    y2 = max(0, min(y2, img_h - 1))

    return (x1, y1, x2, y2)


def draw_ocr_boxes(image_path: str, ocr_results: List[Dict[str, Any]], output_path: str) -> str:
    """Draw bounding boxes and confidence labels on image.

    Color coding (BGR for OpenCV):
    - High confidence (>= 0.90): Green (0, 255, 0)
    - Medium confidence (0.60 - 0.89): Yellow/Orange (0, 165, 255)
    - Low confidence (< 0.60): Red (0, 0, 255)

    Draws clean semi-transparent background for label text.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not HAS_CV2 or cv2 is None:
        # Fallback to copy if OpenCV not available
        if HAS_PIL and Image is not None and os.path.exists(image_path):
            with Image.open(image_path) as img:
                img.save(output_path)
            return output_path
        return image_path

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image for visualization from '{image_path}'")

    img_h, img_w = img.shape[:2]
    # Overlay layer for semi-transparent label backgrounds
    overlay = img.copy()

    for item in ocr_results:
        confidence = float(item.get("confidence", 0.0))
        text = str(item.get("text", "")).strip()
        bbox = item.get("bbox", [])

        # Determine color by confidence threshold
        if confidence >= 0.90:
            color = (0, 200, 0)     # High: Green
            conf_tier = "HIGH"
        elif confidence >= 0.60:
            color = (0, 165, 255)   # Medium: Orange/Yellow
            conf_tier = "MED"
        else:
            color = (0, 0, 240)     # Low: Red
            conf_tier = "LOW"

        x1, y1, x2, y2 = _get_bbox_coordinates(bbox, img_w, img_h)
        if x2 <= x1 or y2 <= y1:
            continue

        # Draw main bounding box rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Label text: "[0.94] MRP Rs. 20"
        display_text = f"{text[:25]}... ({confidence:.2f})" if len(text) > 25 else f"{text} ({confidence:.2f})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        font_thickness = 1

        (tw, th), baseline = cv2.getTextSize(display_text, font, font_scale, font_thickness)

        # Position label above bounding box if space permits, otherwise inside
        label_y1 = max(0, y1 - th - baseline - 4)
        label_y2 = y1 if y1 - th - baseline - 4 >= 0 else y1 + th + baseline + 4
        label_x2 = min(img_w, x1 + tw + 6)

        # Draw filled background for label on overlay
        cv2.rectangle(overlay, (x1, label_y1), (label_x2, label_y2), color, -1)

    # Blend overlay with original for 70% opacity label background
    alpha = 0.75
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    # Draw the text on top of blended background
    for item in ocr_results:
        confidence = float(item.get("confidence", 0.0))
        text = str(item.get("text", "")).strip()
        bbox = item.get("bbox", [])

        x1, y1, x2, y2 = _get_bbox_coordinates(bbox, img_w, img_h)
        if x2 <= x1 or y2 <= y1:
            continue

        display_text = f"{text[:25]}... ({confidence:.2f})" if len(text) > 25 else f"{text} ({confidence:.2f})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        font_thickness = 1

        (tw, th), baseline = cv2.getTextSize(display_text, font, font_scale, font_thickness)
        text_y = y1 - baseline - 2 if y1 - th - baseline - 4 >= 0 else y1 + th + 2
        text_x = x1 + 3

        # White or black text depending on label color brightness
        text_color = (255, 255, 255)
        cv2.putText(img, display_text, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

    cv2.imwrite(output_path, img)
    return output_path
