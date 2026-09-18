"""
AI-Powered Computer Vision & PaddleOCR Pipeline for Legal Metrology Verification.

Responsibilities:
1. Preprocess packaging image: EXIF auto-orientation, CLAHE contrast enhancement,
   resizing and noise reduction.
2. Run high-accuracy deep learning OCR using PaddleOCR (replacing Tesseract).
   Extracts full text, word/line bounding boxes, and per-detection confidence scores.
3. Detect Barcodes / QR codes on packaging using OpenCV for digital provenance & e-commerce compliance.
4. Generate high-resolution evidence crops with highlighted bounding box overlays
   for the 'Evidence from OCR' inspection dossier.
5. Calibrate and estimate physical font heights (mm) against Second Schedule statutory slabs.
"""

import os
import uuid
import logging
import cv2
import numpy as np
from PIL import Image, ImageOps
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("ocr_engine")

# Lazy singleton for PaddleOCR
_paddle_ocr = None


def get_paddle_ocr():
    """Lazily load PaddleOCR instance to avoid slow cold-start on import."""
    global _paddle_ocr
    if _paddle_ocr is not None:
        return _paddle_ocr

    try:
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
        from paddleocr import PaddleOCR
        # Initialize PaddleOCR with English language, angle classification, and production PP-OCRv4
        _paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en", ocr_version="PP-OCRv4")
        logger.info("PaddleOCR (PP-OCRv4) engine initialized successfully.")
        return _paddle_ocr
    except Exception as exc:
        logger.error("Failed to initialize PaddleOCR: %s", exc)
        return None


# Default fallback DPI assumption if no physical calibration marker is provided
FALLBACK_DPI = 150
MM_PER_INCH = 25.4


def fallback_px_per_mm() -> float:
    return FALLBACK_DPI / MM_PER_INCH


def load_oriented_image(image_path: str) -> np.ndarray:
    """Load image from disk and apply EXIF orientation correction for upright processing."""
    try:
        pil_img = Image.open(image_path)
        pil_img = ImageOps.exif_transpose(pil_img)
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        arr = np.ascontiguousarray(np.array(pil_img), dtype=np.uint8)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        logger.warning("PIL load_oriented_image failed (%s), trying cv2 fallback", exc)
        try:
            with open(image_path, "rb") as f:
                file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is not None:
                return np.ascontiguousarray(img)
        except Exception:
            pass
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
        return np.ascontiguousarray(img)


def detect_barcode_or_qr(image: np.ndarray) -> Dict[str, Any]:
    """Detect presence of QR code or 1D barcode on product packaging using OpenCV."""
    result = {"has_code": False, "type": None, "data": None, "bbox": None}
    
    # 1. Check for QR code
    try:
        qr_detector = cv2.QRCodeDetector()
        val, points, _ = qr_detector.detectAndDecode(image)
        if val and points is not None and len(points) > 0:
            pts = points[0].astype(int)
            x_min = int(np.min(pts[:, 0]))
            y_min = int(np.min(pts[:, 1]))
            x_max = int(np.max(pts[:, 0]))
            y_max = int(np.max(pts[:, 1]))
            return {
                "has_code": True,
                "type": "QR Code",
                "data": val,
                "bbox": [x_min, y_min, x_max, y_max],
                "verified": True,
            }
    except Exception as exc:
        logger.debug("QR detection check skipped: %s", exc)

    # 2. Check for 1D Barcode if OpenCV contrib is present
    try:
        if hasattr(cv2, "barcode") and hasattr(cv2.barcode, "BarcodeDetector"):
            bardet = cv2.barcode.BarcodeDetector()
            ret = bardet.detectAndDecode(image)
            if ret and len(ret) >= 3:
                if len(ret) == 4:
                    _, decoded_info, decoded_type, corners = ret
                else:
                    decoded_info, decoded_type, corners = ret[0], ret[1], ret[2]
                if decoded_info and len(decoded_info) > 0 and decoded_info[0]:
                    pts = corners[0].astype(int)
                    x_min = int(np.min(pts[:, 0]))
                    y_min = int(np.min(pts[:, 1]))
                    x_max = int(np.max(pts[:, 0]))
                    y_max = int(np.max(pts[:, 1]))
                    return {
                        "has_code": True,
                        "type": decoded_type[0] if decoded_type else "1D Barcode",
                        "data": decoded_info[0],
                        "bbox": [x_min, y_min, x_max, y_max],
                        "verified": True,
                    }
    except Exception as exc:
        logger.debug("Barcode detection check skipped: %s", exc)

    return result


def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """
    Run deep-learning PaddleOCR on the product image.
    Returns:
      - raw_text: complete consolidated text string
      - words: list of detected text segments with bounding boxes and confidence scores
      - barcode_info: QR/barcode detection if present
      - image_dimensions: [width, height]
    """
    img = load_oriented_image(image_path)
    h, w = img.shape[:2]

    # Pre-processing: contrast enhancement using CLAHE with safe fallback
    enhanced_bgr = img
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)
        enhanced_bgr = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
    except Exception as exc:
        logger.warning("CLAHE enhancement skipped due to exception: %s", exc)
        enhanced_bgr = img

    barcode_info = detect_barcode_or_qr(img)

    paddle_engine = get_paddle_ocr()
    detected_words: List[Dict[str, Any]] = []
    lines: List[str] = []

    if paddle_engine is not None:
        try:
            raw_results = paddle_engine.ocr(img)
            
            # Handle both PaddleX OCRResult (dict-like) and classic PaddleOCR nested list
            if raw_results and len(raw_results) > 0:
                first = raw_results[0]

                # Format A: Modern PaddleOCR / PaddleX OCRResult object
                if hasattr(first, "__getitem__") and hasattr(first, "get") and "rec_texts" in first:
                    texts = first.get("rec_texts", [])
                    scores = first.get("rec_scores", [])
                    boxes = first.get("rec_boxes", first.get("rec_polys", []))

                    for i, text_str in enumerate(texts):
                        text_str = str(text_str).strip()
                        if not text_str:
                            continue
                        conf = float(scores[i]) if i < len(scores) else 0.85
                        box = boxes[i] if i < len(boxes) else None

                        if box is not None:
                            arr = np.array(box)
                            if arr.ndim == 1 and len(arr) == 4:
                                x_min, y_min, x_max, y_max = int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3])
                            elif arr.ndim == 2:
                                x_min = int(np.min(arr[:, 0]))
                                y_min = int(np.min(arr[:, 1]))
                                x_max = int(np.max(arr[:, 0]))
                                y_max = int(np.max(arr[:, 1]))
                            else:
                                x_min, y_min, x_max, y_max = 0, 0, w, h
                        else:
                            x_min, y_min, x_max, y_max = 0, 0, w, h

                        box_w = max(1, x_max - x_min)
                        box_h = max(1, y_max - y_min)
                        lines.append(text_str)
                        detected_words.append({
                            "text": text_str,
                            "confidence": round(conf * 100, 1),
                            "x": x_min,
                            "y": y_min,
                            "w": box_w,
                            "h": box_h,
                            "bbox": [x_min, y_min, x_max, y_max],
                        })

                # Format B: Classic PaddleOCR nested list: [ [ [ [x1,y1],... ], (text, conf) ], ... ]
                elif isinstance(first, list):
                    for entry in first:
                        if not entry or len(entry) < 2:
                            continue
                        box = entry[0]
                        text_tuple = entry[1]
                        text_str = str(text_tuple[0]).strip()
                        conf = float(text_tuple[1])

                        if not text_str:
                            continue

                        x_coords = [pt[0] for pt in box]
                        y_coords = [pt[1] for pt in box]
                        x_min = int(max(0, min(x_coords)))
                        y_min = int(max(0, min(y_coords)))
                        x_max = int(min(w, max(x_coords)))
                        y_max = int(min(h, max(y_coords)))
                        box_w = max(1, x_max - x_min)
                        box_h = max(1, y_max - y_min)

                        lines.append(text_str)
                        detected_words.append({
                            "text": text_str,
                            "confidence": round(conf * 100, 1),
                            "x": x_min,
                            "y": y_min,
                            "w": box_w,
                            "h": box_h,
                            "bbox": [x_min, y_min, x_max, y_max],
                        })
        except Exception as exc:
            logger.error("PaddleOCR execution failed: %s", exc)

    # Fallback to Tesseract if PaddleOCR failed to initialize or produce output
    if not detected_words:
        try:
            import pytesseract
            pil_img = Image.fromarray(enhanced_bgr)
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            n = len(data["text"])
            for i in range(n):
                txt = data["text"][i].strip()
                conf_val = int(data["conf"][i]) if str(data["conf"][i]).lstrip("-").isdigit() else 0
                if txt and conf_val >= 20:
                    x = int(data["left"][i])
                    y = int(data["top"][i])
                    bw = int(data["width"][i])
                    bh = int(data["height"][i])
                    detected_words.append({
                        "text": txt,
                        "confidence": float(conf_val),
                        "x": x,
                        "y": y,
                        "w": bw,
                        "h": bh,
                        "bbox": [x, y, x + bw, y + bh],
                    })
                    lines.append(txt)
        except Exception as exc:
            logger.warning("Fallback OCR also failed: %s", exc)

    raw_text = "\n".join(lines)
    return {
        "raw_text": raw_text,
        "words": detected_words,
        "barcode_info": barcode_info,
        "image_dimensions": [w, h],
    }


def generate_evidence_crop(
    image_path: str,
    bbox: List[int],
    output_dir: str,
    label: str = "field",
) -> Optional[str]:
    """
    Generate an annotated crop of the detected declaration region
    with a crisp green bounding box overlay, matching the workflow pic.
    Returns relative path to the crop image.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        img = load_oriented_image(image_path)
        h, w = img.shape[:2]

        x_min, y_min, x_max, y_max = bbox
        pad_x = int((x_max - x_min) * 0.35) + 20
        pad_y = int((y_max - y_min) * 0.45) + 15

        crop_x1 = max(0, x_min - pad_x)
        crop_y1 = max(0, y_min - pad_y)
        crop_x2 = min(w, x_max + pad_x)
        crop_y2 = min(h, y_max + pad_y)

        crop = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()

        # Draw green bounding box on the crop
        rel_x1 = x_min - crop_x1
        rel_y1 = y_min - crop_y1
        rel_x2 = x_max - crop_x1
        rel_y2 = y_max - crop_y1

        # Glowing green box styling: (B, G, R) = (50, 205, 50)
        cv2.rectangle(crop, (rel_x1, rel_y1), (rel_x2, rel_y2), (50, 205, 50), 3)

        fname = f"crop_{label}_{uuid.uuid4().hex[:8]}.jpg"
        save_path = os.path.join(output_dir, fname)
        ok, buf = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if ok:
            with open(save_path, "wb") as f:
                f.write(buf)
        else:
            cv2.imwrite(save_path, crop)
        return fname
    except Exception as exc:
        logger.warning("Could not generate evidence crop: %s", exc)
        return None


def estimate_font_heights_mm(words: List[dict], px_per_mm: Optional[float] = None) -> Dict[str, Any]:
    """Convert pixel bounding-box heights to physical millimeter measurements."""
    calibrated = px_per_mm is not None and px_per_mm > 0
    ratio = px_per_mm if calibrated else fallback_px_per_mm()

    heights_mm = []
    for w in words:
        h_mm = w["h"] / ratio
        heights_mm.append({**w, "height_mm": round(h_mm, 2)})

    # Filter candidate declaration tokens
    candidate_heights = [
        w["height_mm"] for w in heights_mm
        if 2 <= len(w["text"]) <= 14 and w["confidence"] >= 50
        and any(c.isalnum() for c in w["text"])
        and w["h"] >= 4
    ]
    min_height = min(candidate_heights) if candidate_heights else None

    return {
        "calibrated": calibrated,
        "px_per_mm_used": round(ratio, 3),
        "min_declaration_font_mm": round(min_height, 2) if min_height else None,
    }


def estimate_pdp_area_cm2(
    image_path: str,
    px_per_mm: Optional[float] = None,
    image_dims: Optional[List[int]] = None,
) -> Optional[float]:
    """Estimate Principal Display Panel (PDP) area in cm² from calibrated dimensions."""
    if px_per_mm is None or px_per_mm <= 0:
        return None
    try:
        if image_dims and len(image_dims) == 2 and image_dims[0] > 0 and image_dims[1] > 0:
            w_px, h_px = image_dims[0], image_dims[1]
        else:
            with Image.open(image_path) as im:
                w_px, h_px = im.size
        w_mm, h_mm = w_px / px_per_mm, h_px / px_per_mm
        return round((w_mm * h_mm) / 100.0, 1)
    except Exception:
        return None


def analyze_image(image_path: str, px_per_mm: Optional[float] = None) -> Dict[str, Any]:
    """
    Top-level entry point called by Flask app:
    - PaddleOCR text & bounding box extraction
    - Millimeter font height measurement
    - Barcode & QR code scanning
    - PDP area calculation
    """
    ocr_result = extract_text_and_boxes(image_path)
    fonts = estimate_font_heights_mm(ocr_result["words"], px_per_mm=px_per_mm)
    pdp_area = estimate_pdp_area_cm2(
        image_path,
        px_per_mm=px_per_mm,
        image_dims=ocr_result.get("image_dimensions"),
    )

    return {
        "raw_text": ocr_result["raw_text"],
        "words": ocr_result["words"],
        "barcode_info": ocr_result["barcode_info"],
        "image_dimensions": ocr_result["image_dimensions"],
        "word_count": len(ocr_result["words"]),
        "min_declaration_font_mm": fonts["min_declaration_font_mm"],
        "font_measurement_calibrated": fonts["calibrated"],
        "pdp_area_cm2": pdp_area,
    }
