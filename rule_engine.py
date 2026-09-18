"""
Rule Engine & Structured Information Extraction for Legal Metrology Compliance.

Implements Steps 4, 5 & 6 of the Methodology Workflow:
4. Structured Information Extraction: Convert OCR text into structured product fields
   (product_name, net_quantity, mrp, manufacturer, manufactured_date, best_before,
   customer_care, country_of_origin, unit_sale_price).
5. RAG Legal Integration: Link each extracted field to traceable statutory provisions
   from the Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011.
6. Compliance Engine: Check & verify against statutory mandates, determine field status
   (Pass, Review, Violation), confidence score, and compute overall compliance outcome.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import rag_engine

# ---------------------------------------------------------------------------
# Declarations Configuration & Regex Detectors
# ---------------------------------------------------------------------------
FIELD_DETECTORS = {
    "product_name": {
        "label": "Product Name",
        "severity": "major",
        "extract_regex": r"(?:name|product|item)?\s*[:\-]?\s*([a-zA-Z0-9\s]{3,40})",
    },
    "net_quantity": {
        "label": "Net Quantity",
        "severity": "critical",
        "extract_regex": r"(?:net\s*(?:qty|quantity|wt|weight|vol|volume)?\s*[:\-]?\s*)?(\b\d+(?:\.\d+)?\s*(?:g|gm|gms|kg|ml|l|litre|liter|mg|units?|pieces?|N)\b)",
        "unit_regex": r"\b\d+(?:\.\d+)?\s*(g|gm|gms|kg|ml|l|litre|liter|mg)\b",
    },
    "mrp": {
        "label": "MRP (Retail Price)",
        "severity": "critical",
        "extract_regex": r"(?:m\.?r\.?p\.?|maximum\s+retail\s+price)\s*[\.\:₹<=\s]*\s*([₹\d\.,\/-]+(?:\s*incl\.?\s*of\s*all\s*taxes)?)",
        "value_regex": r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)",
    },
    "manufacturer_details": {
        "label": "Manufacturer / Packer",
        "severity": "critical",
        "extract_regex": r"(?:mfg|manufactured|marketed|packed|pkd|mkt)\.?\s*(?:by|for|at)?\s*[:\-]?\s*([a-zA-Z0-9\s\.,&'\(\)\-]{5,80}(?:pvt\.?\s*ltd|ltd|limited|llp|foods|industries|corp)?)",
    },
    "mfg_date": {
        "label": "Manufacturing Date",
        "severity": "major",
        "extract_regex": r"(?:mfg|mfd|pkd|packed|date\s+of\s+mfg)?\.?\s*(?:on|date)?\s*[:\-]?\s*(\b(?:\d{1,2}[\/\.-]\d{2,4}|[a-zA-Z]{3,9}\s*\d{4})\b)",
    },
    "best_before": {
        "label": "Best Before / Expiry",
        "severity": "major",
        "extract_regex": r"(?:best\s+before|expiry|use\s+by)\s*[:\-]?\s*([a-zA-Z0-9\s\/\.-]{3,35})",
    },
    "consumer_care": {
        "label": "Customer Care",
        "severity": "major",
        "extract_regex": r"(?:consumer|customer)\s*(?:care|cell|helpline|support)?\s*[:\-]?\s*([a-zA-Z0-9\s@\.\-\+]{6,60}|\b1800[\s-]?\d{3,6}\b|[\w\.-]+@[\w\.-]+\.\w+)",
    },
    "country_of_origin": {
        "label": "Country of Origin",
        "severity": "minor",
        "extract_regex": r"(?:country\s+of\s+origin|made\s+in)\s*[:\-]?\s*([a-zA-Z]{3,20})",
        "conditional": True,
    },
    "unit_sale_price": {
        "label": "Unit Sale Price (USP)",
        "severity": "minor",
        "extract_regex": r"(?:usp|unit\s+sale\s+price)?\s*[:\-]?\s*(₹?\s*\d+(?:\.\d+)?\s*\/\s*(?:g|kg|ml|l|unit|piece))",
    },
}

# Second Schedule Font Slabs
FONT_SIZE_SLABS_MM = [
    {"max_area_cm2": 100, "min_height_mm": 1.0},
    {"max_area_cm2": 500, "min_height_mm": 2.0},
    {"max_area_cm2": 2500, "min_height_mm": 4.0},
    {"max_area_cm2": None, "min_height_mm": 6.0},
]
DEFAULT_MIN_FONT_MM = 1.0


def min_font_requirement_mm(pdp_area_cm2: Optional[float]) -> float:
    """Determine minimum statutory font height (mm) as per Second Schedule."""
    if pdp_area_cm2 is None:
        return DEFAULT_MIN_FONT_MM
    for slab in FONT_SIZE_SLABS_MM:
        if slab["max_area_cm2"] is None or pdp_area_cm2 <= slab["max_area_cm2"]:
            return slab["min_height_mm"]
    return FONT_SIZE_SLABS_MM[-1]["min_height_mm"]


def find_matching_token_box(field_key: str, detected_str: str, ocr_words: List[dict]) -> Tuple[Optional[List[int]], float]:
    """
    Locate the precise bounding box and average confidence score in OCR results
    for an extracted field value.
    """
    if not detected_str or not ocr_words:
        return None, 0.0

    detected_tokens = [t.lower() for t in re.findall(r"\w+", detected_str) if len(t) > 1]
    matching_boxes: List[List[int]] = []
    confidences: List[float] = []

    for w in ocr_words:
        w_text = w.get("text", "").lower()
        # Direct token match or substring match
        if any(dt in w_text or w_text in dt for dt in detected_tokens):
            matching_boxes.append(w["bbox"])
            confidences.append(w.get("confidence", 80.0))

    if not matching_boxes:
        # Fallback: check for field keywords
        field_terms = field_key.split("_")
        for w in ocr_words:
            if any(term in w.get("text", "").lower() for term in field_terms):
                matching_boxes.append(w["bbox"])
                confidences.append(w.get("confidence", 75.0))

    if matching_boxes:
        x_min = min(b[0] for b in matching_boxes)
        y_min = min(b[1] for b in matching_boxes)
        x_max = max(b[2] for b in matching_boxes)
        y_max = max(b[3] for b in matching_boxes)
        avg_conf = sum(confidences) / len(confidences) if confidences else 85.0
        return [x_min, y_min, x_max, y_max], round(avg_conf, 1)

    return None, 0.0


def extract_structured_fields(
    raw_ocr_text: str,
    ocr_words: List[dict],
    product_metadata: dict,
    image_path: Optional[str] = None,
    crop_dir: Optional[str] = None,
    is_imported: bool = False,
) -> Dict[str, Any]:
    """
    Extract structured fields, match with RAG legal provisions,
    generate evidence bounding boxes and crops, and compute status.
    """
    from ocr_engine import generate_evidence_crop

    extracted: Dict[str, Any] = {}
    lines = raw_ocr_text.split("\n")
    text_lower = raw_ocr_text.lower()

    for field_key, detector in FIELD_DETECTORS.items():
        if field_key == "country_of_origin" and not is_imported and "origin" not in text_lower and "made in" not in text_lower:
            continue

        detected_val: Optional[str] = None
        confidence: float = 0.0
        status: str = "Violation"
        bbox: Optional[List[int]] = None
        crop_filename: Optional[str] = None

        # 1. Regex & heuristic extraction
        regex = detector.get("extract_regex")
        if regex:
            match = re.search(regex, raw_ocr_text, flags=re.IGNORECASE)
            if match:
                detected_val = match.group(1).strip() if match.groups() else match.group(0).strip()

        # Custom field normalizations
        if field_key == "product_name":
            name_input = product_metadata.get("name", "").strip()
            if name_input and (name_input.lower() in text_lower or any(word.lower() in text_lower for word in name_input.split())):
                detected_val = name_input
                status = "Pass"
                confidence = 98.0
            elif detected_val:
                status = "Pass"
                confidence = 88.0
            else:
                detected_val = name_input or "Not clearly detected"
                status = "Review" if name_input else "Violation"
                confidence = 65.0

        elif field_key == "mrp":
            # 1. Spatial and token-aware price search
            mrp_anchor = next((w for w in ocr_words if any(k in w.get("text", "").lower() for k in ["mrp", "retail price", "taxes", "incl"])), None)
            mrp_candidates = []

            for w in ocr_words:
                txt = w.get("text", "").strip()
                w_conf = w.get("confidence", 0)
                # Filter out low-confidence noise (< 35%) and dates
                if w_conf < 35:
                    continue
                if re.search(r"\b(0[1-9]|1[0-2])[\/\.-]\d{2,4}\b", txt):
                    continue

                val_candidate = None
                # Check for Indian packaging slash notation where '90/-' is read as '901.', '90/.', '90.-', '90/='
                clean_slash = re.match(r"^(\d{1,5})(?:1\.|1\-|\/[-=]?|\/\.|\.-|\/=|\/)$", txt)
                if clean_slash:
                    val_candidate = clean_slash.group(1)
                else:
                    # Check for ₹ or Rs prefix or standalone price
                    clean_num = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)", txt, flags=re.IGNORECASE)
                    if clean_num:
                        val_candidate = clean_num.group(1)

                if val_candidate:
                    try:
                        num_val = float(val_candidate)
                        # Plausible consumer goods price range (filter out single stray digits like 1 unless anchored)
                        if 5 <= num_val <= 50000:
                            dist = abs(w.get("y", 0) - mrp_anchor.get("y", 0)) if mrp_anchor else 0
                            mrp_candidates.append({
                                "val": val_candidate,
                                "conf": w_conf,
                                "bbox": w.get("bbox"),
                                "dist": dist,
                            })
                    except ValueError:
                        pass

            if mrp_candidates:
                # Prioritize vertical proximity to MRP / taxes label, then confidence
                mrp_candidates.sort(key=lambda c: (c["dist"], -c["conf"]))
                best_mrp = mrp_candidates[0]
                detected_val = f"₹{best_mrp['val']}"
                status = "Pass"
                confidence = best_mrp["conf"]
                bbox = best_mrp["bbox"]
            else:
                # Regex fallback on raw text
                mrp_m = re.search(r"(?:m\.?r\.?p\.?|maximum\s+retail\s+price)[^\d\n]*[₹\s]*([0-9]{2,5}(?:\.[0-9]{2})?)", raw_ocr_text, flags=re.IGNORECASE)
                if mrp_m:
                    detected_val = f"₹{mrp_m.group(1)}"
                    status = "Pass"
                    confidence = 92.0
                elif detected_val and detected_val != "1":
                    if not detected_val.startswith("₹") and not detected_val.lower().startswith("rs"):
                        clean_num = re.search(r"\d+(?:\.\d{1,2})?", detected_val)
                        detected_val = f"₹{clean_num.group(0)}" if clean_num else detected_val
                    status = "Pass"
                    confidence = 88.0
                else:
                    detected_val = "Not detected"
                    status = "Violation"
                    confidence = 0.0

        elif field_key == "net_quantity":
            qty_m = re.search(r"\b(\d+(?:\.\d+)?\s*(?:g|gm|gms|kg|ml|l|litre|liter|mg))\b", raw_ocr_text, flags=re.IGNORECASE)
            if qty_m:
                detected_val = qty_m.group(1).strip()
                if "gms" in detected_val.lower() or "gm" in detected_val.lower():
                    status = "Review"
                    confidence = 94.0
                else:
                    status = "Pass"
                    confidence = 97.0
            elif detected_val:
                status = "Pass"
                confidence = 89.0
            else:
                detected_val = "Not detected"
                status = "Violation"
                confidence = 0.0

        elif field_key == "manufacturer_details":
            # Strictly avoid matching "Mfg. Date" or "Date" as manufacturer
            sanitized_text = re.sub(r"mfg\.?\s*date[^\n]*", "", raw_ocr_text, flags=re.IGNORECASE)
            
            # 1. Search for genuine manufacturer or marketer statements
            mfg_m = re.search(r"(?:manufactured|mfd|marketed|mktd|packed|pkd)\.?\s*(?:by|for|at)\s*[:\-]?\s*([a-zA-Z0-9\s\.,&'\(\)\-]{6,100})", sanitized_text, flags=re.IGNORECASE)
            company_m = re.search(r"([a-zA-Z0-9\s\.,&'\(\)\-]{4,60}\s+(?:pvt\.?\s*ltd|private\s+limited|ltd\.|limited|llp|pharma|laboratories|healthcare|foods|industries|corp))", sanitized_text, flags=re.IGNORECASE)
            addr_m = re.search(r"(\d+[^\n\r]*(?:village|plot|industrial\s+area|road|street|nagar|marg)[^\n\r]*)", sanitized_text, flags=re.IGNORECASE)

            if mfg_m and "date" not in mfg_m.group(1).lower():
                detected_val = mfg_m.group(1).strip()
                status = "Pass"
                confidence = 94.0
            elif company_m:
                detected_val = company_m.group(1).strip()
                status = "Pass"
                confidence = 92.0
            elif addr_m:
                val = addr_m.group(1).strip()
                # Remove trailing commas or punctuation
                val = re.sub(r"[,;\-\s]+$", "", val)
                detected_val = val
                status = "Pass"
                confidence = 89.0
            elif product_metadata.get("brand") and product_metadata.get("brand").lower() in text_lower:
                detected_val = f"{product_metadata.get('brand')} (from brand declaration)"
                status = "Review"
                confidence = 80.0
            else:
                detected_val = "Not detected"
                status = "Violation"
                confidence = 0.0

        elif field_key == "mfg_date":
            # Extract all chronological date tokens (MM/YY or MM/YYYY)
            date_tokens = []
            for w in ocr_words:
                txt = w.get("text", "")
                if w.get("confidence", 0) >= 35:
                    m = re.search(r"\b(0[1-9]|1[0-2])[\/\.-](\d{2,4})\b", txt)
                    if m:
                        mo = int(m.group(1))
                        yr = int(m.group(2))
                        full_yr = yr if yr > 100 else (2000 + yr)
                        date_tokens.append({
                            "token": m.group(0),
                            "sort_key": (full_yr, mo),
                            "bbox": w.get("bbox"),
                            "conf": w.get("confidence", 90.0),
                            "y": w.get("y", 0),
                        })

            date_tokens.sort(key=lambda d: d["sort_key"])
            if date_tokens:
                # Manufacturing date is the earlier date
                mfg_item = date_tokens[0]
                detected_val = mfg_item["token"]
                status = "Pass"
                confidence = mfg_item["conf"]
                bbox = mfg_item["bbox"]
            else:
                date_m = re.search(r"\b(0[1-9]|1[0-2])[\/\.-](20\d{2}|\d{2})\b", raw_ocr_text)
                if date_m:
                    detected_val = date_m.group(0)
                    status = "Pass"
                    confidence = 92.0
                else:
                    detected_val = "Not detected"
                    status = "Violation"
                    confidence = 0.0

        elif field_key == "best_before":
            # Extract all chronological date tokens
            date_tokens = []
            for w in ocr_words:
                txt = w.get("text", "")
                if w.get("confidence", 0) >= 35:
                    m = re.search(r"\b(0[1-9]|1[0-2])[\/\.-](\d{2,4})\b", txt)
                    if m:
                        mo = int(m.group(1))
                        yr = int(m.group(2))
                        full_yr = yr if yr > 100 else (2000 + yr)
                        date_tokens.append({
                            "token": m.group(0),
                            "sort_key": (full_yr, mo),
                            "bbox": w.get("bbox"),
                            "conf": w.get("confidence", 90.0),
                            "y": w.get("y", 0),
                        })

            date_tokens.sort(key=lambda d: d["sort_key"])
            if len(date_tokens) > 1:
                # Expiry date is the later date (e.g. 04/27)
                exp_item = date_tokens[-1]
                detected_val = exp_item["token"]
                status = "Pass"
                confidence = exp_item["conf"]
                bbox = exp_item["bbox"]
            else:
                # Look for shelf life or expiration statements
                bb_m = re.search(r"(?:best\s+before|expiry|use\s+by)\s*[:\-]?\s*(\b(?:\d{1,2}[\/\.-]\d{2,4}|\d+\s+months?|\d+\s+days?|[a-zA-Z]{3,9}\s*\d{4})\b)", raw_ocr_text, flags=re.IGNORECASE)
                if bb_m and bb_m.group(1).lower() != "date":
                    detected_val = bb_m.group(1).strip()
                    status = "Pass"
                    confidence = 91.0
                elif "best before" in text_lower or "expiry" in text_lower:
                    detected_val = "Declared on packaging"
                    status = "Pass"
                    confidence = 86.0
                else:
                    detected_val = "Optional / Not detected"
                    status = "Pass"
                    confidence = 75.0

        elif field_key == "consumer_care":
            phone_m = re.search(r"\b1800[\s-]?\d{3,6}\b|(?:\+91|0)?[789]\d{9}", raw_ocr_text)
            email_m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_ocr_text)
            if phone_m or email_m:
                val_parts = []
                if phone_m:
                    val_parts.append(phone_m.group(0))
                if email_m:
                    val_parts.append(email_m.group(0))
                detected_val = ", ".join(val_parts)
                status = "Pass"
                confidence = 95.0
            elif detected_val:
                status = "Review"
                confidence = 84.0
            else:
                detected_val = "Not detected"
                status = "Violation"
                confidence = 0.0

        elif field_key == "country_of_origin":
            origin_m = re.search(r"(?:country\s+of\s+origin|made\s+in)\s*[:\-]?\s*([a-zA-Z]{3,20})", raw_ocr_text, flags=re.IGNORECASE)
            if origin_m:
                detected_val = origin_m.group(1).strip().capitalize()
                status = "Pass"
                confidence = 96.0
            elif "india" in text_lower:
                detected_val = "India"
                status = "Pass"
                confidence = 88.0
            elif is_imported:
                detected_val = "Not detected"
                status = "Violation"
                confidence = 0.0
            else:
                detected_val = "Domestic Commodity"
                status = "Pass"
                confidence = 85.0

        elif field_key == "unit_sale_price":
            usp_m = re.search(r"(?:usp|unit\s+sale\s+price)[^\n\d]*([₹\d\.]+\s*(?:\/|\s*per\s*)(?:g|gm|kg|ml|l|unit))", raw_ocr_text, flags=re.IGNORECASE)
            if usp_m:
                detected_val = usp_m.group(1).strip()
                status = "Pass"
                confidence = 92.0
            elif detected_val:
                status = "Pass"
                confidence = 85.0
            else:
                detected_val = "Not detected / Not applicable"
                status = "Review"
                confidence = 70.0

        # 2. Extract Bounding Box for OCR Evidence
        if status != "Violation" and detected_val and detected_val != "Not detected":
            bbox, token_conf = find_matching_token_box(field_key, detected_val, ocr_words)
            if token_conf > 0:
                confidence = round((confidence * 0.5) + (token_conf * 0.5), 1)

            # Generate evidence crop image if image_path and bbox are available
            if image_path and bbox and crop_dir:
                crop_filename = generate_evidence_crop(image_path, bbox, crop_dir, field_key)

        # 3. Retrieve Traceable Legal Basis from RAG Knowledge Base
        legal_basis = rag_engine.retrieve_legal_basis(field_key)

        extracted[field_key] = {
            "label": detector["label"],
            "detected_value": detected_val or "Not detected",
            "confidence": f"{round(confidence)}%" if confidence > 0 else "—",
            "confidence_num": round(confidence, 1),
            "status": status,  # 'Pass', 'Review', 'Violation'
            "bbox": bbox,
            "crop_filename": crop_filename,
            "legal_basis": legal_basis,
        }

    return extracted


def evaluate_overall_compliance(
    extracted_fields: Dict[str, Any],
    font_ok: bool,
    detected_font_mm: Optional[float],
    required_font_mm: float,
) -> Dict[str, Any]:
    """
    Compute overall compliance outcome, statutory score, and list of infractions.
    Matches the 3 banners from the workflow pic:
    - COMPLIANT: All required declarations present
    - REVIEW REQUIRED: Some details could not be verified
    - NON-COMPLIANT: Missing/incorrect mandatory declarations
    """
    score = 100.0
    violations = []
    pass_count = 0
    total_checks = 0

    # Essential mandatory declarations under Rule 6
    essential_fields = ["product_name", "mrp", "net_quantity", "manufacturer_details", "mfg_date", "consumer_care"]

    for key, f_data in extracted_fields.items():
        total_checks += 1
        st = f_data["status"]
        legal = f_data.get("legal_basis", {})

        if st == "Pass":
            pass_count += 1
        elif st == "Review":
            pass_count += 0.5
            score -= 10.0
            violations.append({
                "rule_code": legal.get("rule_code", "LM-R6"),
                "field": key,
                "description": f"Ambiguous or non-standard declaration for {f_data['label']}: '{f_data['detected_value']}'",
                "severity": "minor",
            })
        elif st == "Violation":
            penalty = 25.0 if key in essential_fields else 10.0
            score -= penalty
            violations.append({
                "rule_code": legal.get("rule_code", "LM-R6"),
                "field": key,
                "description": f"Missing mandatory statutory declaration: {f_data['label']} ({legal.get('clause', 'Rule 6')})",
                "severity": "critical" if key in essential_fields else "major",
            })

    if not font_ok:
        score -= 15.0
        violations.append({
            "rule_code": "LM-R7 / Second Schedule",
            "field": "font_size",
            "description": f"Detected font height ({detected_font_mm} mm) is below the statutory minimum ({required_font_mm} mm) for this display panel area.",
            "severity": "major",
        })

    score = max(0.0, min(100.0, score))

    # Overall outcome decision
    critical_violations = [v for v in violations if v["severity"] == "critical"]
    if len(critical_violations) > 0 or score < 65.0:
        outcome = "non_compliant"
        outcome_title = "NON-COMPLIANT"
        outcome_desc = "Missing or incorrect mandatory declarations under Legal Metrology Rules."
    elif score < 85.0 or len(violations) > 0:
        outcome = "review"
        outcome_title = "REVIEW REQUIRED"
        outcome_desc = "Some packaging details or print formats require manual verification."
    else:
        outcome = "compliant"
        outcome_title = "COMPLIANT"
        outcome_desc = "All required statutory declarations present and verified."

    return {
        "score": round(score, 1),
        "status": outcome,
        "outcome_title": outcome_title,
        "outcome_desc": outcome_desc,
        "pass_count": int(pass_count),
        "total_checks": total_checks,
        "violations": violations,
    }
