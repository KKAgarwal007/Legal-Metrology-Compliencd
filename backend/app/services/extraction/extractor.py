"""
Structured Information Extraction Service for Packaged Commodities.

Extracts required Legal Metrology declarations from raw OCR tokens.
Supports:
1. Primary Mode: LLM-based structured JSON extraction via Gemini API.
2. Fallback Mode: Deterministic regex and heuristic rule-based extraction.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.extraction.normalizer import (
    normalize_date,
    normalize_email,
    normalize_mrp,
    normalize_net_quantity,
    normalize_phone,
    normalize_website,
)

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


# ==============================================================================
# PROMPT DEFINITION FOR LLM EXTRACTION
# ==============================================================================

EXTRACTION_SYSTEM_PROMPT = """You are an expert Legal Metrology compliance inspection parser for packaged commodities in India.
Your task is to extract mandatory declarations according to the Legal Metrology (Packaged Commodities) Rules, 2011 from the provided OCR transcript of a product's packaging.

CRITICAL INSTRUCTIONS:
1. NEVER invent, guess, or hallucinate missing information.
2. If a field is not present in the OCR transcript, mark status as "NOT_DETECTED" and value as null.
3. If information is partially visible or ambiguous, mark status as "AMBIGUOUS" or "LOW_CONFIDENCE".
4. If clearly present, mark status as "DETECTED".
5. Provide exact 'source_text' from the transcript that supports the extraction.
6. Provide bounding box [x1, y1, x2, y2] if available from the matching OCR item.

OUTPUT JSON FORMAT ONLY (No markdown codeblocks, raw json only):
{
  "product_name": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": [x1,y1,x2,y2] or null, "status": "DETECTED" | "NOT_DETECTED" | "AMBIGUOUS" | "LOW_CONFIDENCE"},
  "brand": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "category": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "manufacturer_name": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "manufacturer_address": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "packer_name": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "packer_address": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "importer_name": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "importer_address": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "net_quantity_raw": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "mrp_raw": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "batch_number": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "manufacturing_date_raw": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "packing_date_raw": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "best_before_raw": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "use_by_raw": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "country_of_origin": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "consumer_care_phone": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "consumer_care_email": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."},
  "consumer_care_website": {"value": string or null, "source_text": string or null, "confidence": float, "bbox": null, "status": "..."}
}
"""


# ==============================================================================
# FALLBACK DETERMINISTIC EXTRACTOR (REGEX / HEURISTICS)
# ==============================================================================

def _fallback_deterministic_extract(ocr_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts declarations using compiled regular expressions when LLM API is unavailable.
    """
    results: Dict[str, Any] = {}

    # Helper to initialize empty field structure
    def make_field(val=None, src=None, conf=0.0, bbox=None, status="NOT_DETECTED"):
        return {
            "value": val,
            "source_text": src,
            "confidence": conf,
            "bbox": bbox,
            "status": status
        }

    keys = [
        "product_name", "brand", "category", "manufacturer_name", "manufacturer_address",
        "packer_name", "packer_address", "importer_name", "importer_address",
        "net_quantity_raw", "mrp_raw", "batch_number", "manufacturing_date_raw",
        "packing_date_raw", "best_before_raw", "use_by_raw", "country_of_origin",
        "consumer_care_phone", "consumer_care_email", "consumer_care_website"
    ]
    for k in keys:
        results[k] = make_field()

    full_lines = [item.get("text", "").strip() for item in ocr_items if item.get("text")]

    # 1. Search for MRP
    mrp_re = re.compile(r'(?:MRP|M\.R\.P\.?|Rs\.?|₹)\s*[:.]?\s*([0-9]+(?:[,.][0-9]{1,2})?)', re.IGNORECASE)
    for item in ocr_items:
        txt = item.get("text", "")
        m = mrp_re.search(txt)
        if m:
            results["mrp_raw"] = make_field(
                val=txt,
                src=txt,
                conf=item.get("confidence", 0.9),
                bbox=item.get("bbox"),
                status="DETECTED"
            )
            break

    # 2. Search for Net Quantity
    net_qty_re = re.compile(
        r'(?:Net\s*(?:Qty|Quantity|Wt|Weight)|Net)\s*[:.]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|grams|ml|mL|l|L|ltr|units|pieces|pcs))',
        re.IGNORECASE
    )
    for item in ocr_items:
        txt = item.get("text", "")
        m = net_qty_re.search(txt)
        if m:
            results["net_quantity_raw"] = make_field(
                val=m.group(1),
                src=txt,
                conf=item.get("confidence", 0.9),
                bbox=item.get("bbox"),
                status="DETECTED"
            )
            break
        # Also check standalone weight/volume tokens (e.g. "500 g", "1 L")
        standalone_m = re.match(r'^([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|ml|mL|L))$', txt, re.IGNORECASE)
        if standalone_m and results["net_quantity_raw"]["status"] == "NOT_DETECTED":
            results["net_quantity_raw"] = make_field(
                val=standalone_m.group(1),
                src=txt,
                conf=item.get("confidence", 0.8),
                bbox=item.get("bbox"),
                status="DETECTED"
            )

    # 3. Search for Manufacturing / Packing Date
    mfg_re = re.compile(r'(?:Mfg|Mfg\.|Pkd|Packed|Date of Mfg|Mfd)\s*[:.]?\s*([0-9]{1,2}[/\-.][0-9]{2,4}|[A-Za-z]{3}\s*[/\-.]?\s*[0-9]{2,4})', re.IGNORECASE)
    for item in ocr_items:
        txt = item.get("text", "")
        m = mfg_re.search(txt)
        if m:
            results["manufacturing_date_raw"] = make_field(
                val=m.group(1),
                src=txt,
                conf=item.get("confidence", 0.85),
                bbox=item.get("bbox"),
                status="DETECTED"
            )
            break

    # 4. Search for Best Before
    bb_re = re.compile(r'(?:Best\s*Before|Use\s*By|Expiry|Exp\.?)\s*[:.]?\s*([0-9A-Za-z\s/\-.]+)', re.IGNORECASE)
    for item in ocr_items:
        txt = item.get("text", "")
        m = bb_re.search(txt)
        if m:
            results["best_before_raw"] = make_field(
                val=m.group(1).strip(),
                src=txt,
                conf=item.get("confidence", 0.85),
                bbox=item.get("bbox"),
                status="DETECTED"
            )
            break

    # 5. Search for Batch / Lot
    batch_re = re.compile(r'(?:Batch|Lot|B\.No\.?|Batch\s*No\.?)\s*[:.]?\s*([A-Za-z0-9\-]+)', re.IGNORECASE)
    for item in ocr_items:
        txt = item.get("text", "")
        m = batch_re.search(txt)
        if m:
            results["batch_number"] = make_field(
                val=m.group(1),
                src=txt,
                conf=item.get("confidence", 0.85),
                bbox=item.get("bbox"),
                status="DETECTED"
            )
            break

    # 6. Search for Manufacturer
    mfr_re = re.compile(r'(?:Manufactured\s*by|Mfd\s*by|Packed\s*by|Marketed\s*by)\s*[:.]?\s*(.*)', re.IGNORECASE)
    for i, item in enumerate(ocr_items):
        txt = item.get("text", "")
        m = mfr_re.search(txt)
        if m:
            val = m.group(1).strip()
            # If line just had header, take next line as name/address
            if not val and i + 1 < len(ocr_items):
                val = ocr_items[i + 1].get("text", "").strip()
            results["manufacturer_name"] = make_field(
                val=val or txt,
                src=txt,
                conf=item.get("confidence", 0.8),
                bbox=item.get("bbox"),
                status="DETECTED" if val else "AMBIGUOUS"
            )
            break

    # 7. Search for Country of Origin
    coo_re = re.compile(r'(?:Made\s*in|Country\s*of\s*Origin\s*[:.]?)\s*([A-Za-z]+)', re.IGNORECASE)
    for item in ocr_items:
        txt = item.get("text", "")
        m = coo_re.search(txt)
        if m:
            results["country_of_origin"] = make_field(
                val=m.group(1).capitalize(),
                src=txt,
                conf=item.get("confidence", 0.9),
                bbox=item.get("bbox"),
                status="DETECTED"
            )
            break

    # 8. Consumer Care Details (Phone, Email, Web)
    for item in ocr_items:
        txt = item.get("text", "")
        phone = normalize_phone(txt)
        if phone and results["consumer_care_phone"]["status"] == "NOT_DETECTED":
            results["consumer_care_phone"] = make_field(
                val=phone,
                src=txt,
                conf=item.get("confidence", 0.88),
                bbox=item.get("bbox"),
                status="DETECTED"
            )

        email = normalize_email(txt)
        if email and results["consumer_care_email"]["status"] == "NOT_DETECTED":
            results["consumer_care_email"] = make_field(
                val=email,
                src=txt,
                conf=item.get("confidence", 0.92),
                bbox=item.get("bbox"),
                status="DETECTED"
            )

        web = normalize_website(txt)
        if web and results["consumer_care_website"]["status"] == "NOT_DETECTED":
            results["consumer_care_website"] = make_field(
                val=web,
                src=txt,
                conf=item.get("confidence", 0.85),
                bbox=item.get("bbox"),
                status="DETECTED"
            )

    # 9. Top-most prominent line often acts as product/brand name if not identified
    if full_lines and results["product_name"]["status"] == "NOT_DETECTED":
        first_line_item = ocr_items[0]
        results["product_name"] = make_field(
            val=first_line_item.get("text"),
            src=first_line_item.get("text"),
            conf=first_line_item.get("confidence", 0.7),
            bbox=first_line_item.get("bbox"),
            status="DETECTED"
        )

    return results


# ==============================================================================
# MAIN EXTRACTION & NORMALIZATION ENTRYPOINT
# ==============================================================================

def extract_product_declarations(
    ocr_items: List[Dict[str, Any]],
    product_category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main extraction function. Takes raw OCR tokens, runs LLM extraction
    (or deterministic regex fallback), and normalizes all fields into canonical
    Legal Metrology structures.
    """
    raw_extraction: Optional[Dict[str, Any]] = None
    extraction_model = "regex_fallback"

    # Format OCR for consumption
    transcript_lines = []
    for item in ocr_items:
        text = item.get("text", "").strip()
        conf = item.get("confidence", 0.0)
        bbox = item.get("bbox", [])
        if text:
            transcript_lines.append(f"Text: '{text}' (Confidence: {conf:.2f}, BBox: {bbox})")
    ocr_transcript = "\n".join(transcript_lines)

    # Attempt Gemini API if key is available
    if HAS_GENAI and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here":
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.LLM_MODEL or "gemini-2.0-flash")

            user_prompt = f"Product Category: {product_category or 'General Packaged Commodity'}\n\nOCR Transcript:\n{ocr_transcript}"
            response = model.generate_content(
                [EXTRACTION_SYSTEM_PROMPT, user_prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            if response.text:
                raw_extraction = json.loads(response.text)
                extraction_model = settings.LLM_MODEL or "gemini-2.0-flash"
        except Exception as e:
            logger.warning(f"Gemini extraction failed or timed out: {e}. Falling back to deterministic parser.")
            raw_extraction = None

    # Use deterministic fallback if LLM was skipped or failed
    if not raw_extraction:
        raw_extraction = _fallback_deterministic_extract(ocr_items)

    # ==========================================================================
    # NORMALIZATION PASS
    # ==========================================================================
    normalized_fields: List[Dict[str, Any]] = []

    # Map raw fields to canonical schema
    field_mappings = [
        ("product_name", "common_or_generic_name"),
        ("brand", "brand_name"),
        ("manufacturer_name", "manufacturer_name"),
        ("manufacturer_address", "manufacturer_address"),
        ("packer_name", "packer_name"),
        ("packer_address", "packer_address"),
        ("importer_name", "importer_name"),
        ("importer_address", "importer_address"),
        ("mrp_raw", "maximum_retail_price"),
        ("net_quantity_raw", "net_quantity"),
        ("batch_number", "batch_lot_code"),
        ("manufacturing_date_raw", "date_of_manufacture_or_packing"),
        ("best_before_raw", "best_before_or_use_by"),
        ("country_of_origin", "country_of_origin"),
        ("consumer_care_phone", "consumer_care_phone"),
        ("consumer_care_email", "consumer_care_email"),
        ("consumer_care_website", "consumer_care_website"),
    ]

    for raw_key, canonical_name in field_mappings:
        item = raw_extraction.get(raw_key, {})
        val = item.get("value")
        status = item.get("status", "NOT_DETECTED" if val is None else "DETECTED")
        src_text = item.get("source_text")
        conf = item.get("confidence", 0.0)
        bbox = item.get("bbox")

        norm_val = None
        unit = None
        currency = None

        if canonical_name == "maximum_retail_price" and val:
            mrp_norm = normalize_mrp(str(val))
            norm_val = str(mrp_norm["value"]) if mrp_norm["value"] is not None else None
            currency = mrp_norm["currency"]
        elif canonical_name == "net_quantity" and val:
            qty_norm = normalize_net_quantity(str(val))
            norm_val = str(qty_norm["value"]) if qty_norm["value"] is not None else None
            unit = qty_norm["unit"]
        elif canonical_name in ("date_of_manufacture_or_packing", "best_before_or_use_by") and val:
            date_norm = normalize_date(str(val))
            norm_val = date_norm["iso_date"] or str(val)
        else:
            norm_val = str(val) if val is not None else None

        normalized_fields.append({
            "field_name": raw_key,
            "canonical_name": canonical_name,
            "raw_value": str(val) if val is not None else None,
            "normalized_value": norm_val,
            "unit": unit,
            "currency": currency,
            "confidence": conf,
            "source_text": src_text,
            "bbox": bbox,
            "status": status
        })

    product_summary = {
        "product_name": raw_extraction.get("product_name", {}).get("value"),
        "brand": raw_extraction.get("brand", {}).get("value"),
        "category": product_category or raw_extraction.get("category", {}).get("value"),
        "extraction_model": extraction_model,
        "raw_extraction": raw_extraction,
        "fields": normalized_fields
    }

    return product_summary
