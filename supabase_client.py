"""
Supabase Database Client for Legal Metrology Compliance System.

Provides dual-mode operation:
1. Supabase PostgreSQL Cloud Mode: When SUPABASE_URL and SUPABASE_KEY are provided
   in .env or environment variables, persists scans, products, and violations to Supabase.
2. Local Fallback Mode: When Supabase is not yet configured, gracefully maintains local
   operation and guides the user via the UI on how to connect their Supabase project.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger("supabase_client")


def _clean_supabase_url(url: str) -> str:
    """Normalize Supabase URL by removing trailing slashes and /rest/v1 paths."""
    cleaned = (url or "").strip().rstrip("/")
    cleaned = re.sub(r"/rest/v1/?$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.rstrip("/")


_supabase_client = None
_connection_tested = False
_is_connected = False
_connection_error = None


def get_client():
    """Lazily initialize and return the Supabase client."""
    global _supabase_client, _connection_tested, _is_connected, _connection_error
    if _supabase_client is not None and _is_connected:
        return _supabase_client

    load_dotenv(override=True)
    raw_url = os.environ.get("SUPABASE_URL", "").strip()
    raw_key = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_ANON_KEY", "")).strip()
    clean_url = _clean_supabase_url(raw_url)

    if not clean_url or not raw_key:
        _connection_tested = True
        _is_connected = False
        _connection_error = "SUPABASE_URL and SUPABASE_KEY not configured in .env file."
        return None

    try:
        from supabase import create_client, Client
        client = create_client(clean_url, raw_key)
        # Test connectivity with a lightweight ping
        client.table("products").select("id").limit(1).execute()
        _supabase_client = client
        _connection_tested = True
        _is_connected = True
        _connection_error = None
        logger.info("Successfully connected to Supabase: %s", clean_url)
        return _supabase_client
    except Exception as exc:
        _connection_tested = True
        _is_connected = False
        _connection_error = str(exc)
        logger.warning("Failed to connect to Supabase: %s", exc)
        return None


def get_supabase_status() -> Dict[str, Any]:
    """Return the current Supabase connectivity status for display in the UI."""
    client = get_client()
    raw_url = os.environ.get("SUPABASE_URL", "").strip()
    raw_key = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_ANON_KEY", "")).strip()
    clean_url = _clean_supabase_url(raw_url)
    configured = bool(clean_url and raw_key)

    # Hide key secrets in UI
    masked_url = ""
    if clean_url:
        masked_url = clean_url if len(clean_url) <= 30 else (clean_url[:25] + "...")

    return {
        "configured": configured,
        "connected": _is_connected,
        "url": masked_url,
        "error": _connection_error,
        "mode": "Supabase Cloud DB" if _is_connected else "Local SQLite Fallback (Dual-Mode Ready)",
    }


def save_product_to_supabase(name: str, brand: str = "", category: str = "other") -> Optional[int]:
    """Persist or retrieve product record in Supabase."""
    client = get_client()
    if not client:
        return None

    try:
        # Check if product already exists
        res = client.table("products").select("id").eq("name", name).eq("brand", brand).limit(1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["id"]

        # Insert new product
        insert_res = client.table("products").insert({
            "name": name,
            "brand": brand,
            "category": category,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        if insert_res.data and len(insert_res.data) > 0:
            return insert_res.data[0]["id"]
    except Exception as exc:
        logger.warning("Supabase save_product error: %s", exc)
    return None


def save_scan_to_supabase(
    product_id: Optional[int],
    inspector_username: str,
    image_url: str,
    raw_ocr_text: str,
    extracted_fields_json: dict,
    min_font_height_mm: Optional[float],
    compliance_score: float,
    status: str,
    report_url: Optional[str] = None,
    violations: Optional[List[dict]] = None,
) -> Optional[int]:
    """Persist scan result and associated violations in Supabase."""
    client = get_client()
    if not client:
        return None

    try:
        scan_payload = {
            "product_id": product_id,
            "inspector_username": inspector_username,
            "image_url": image_url,
            "raw_ocr_text": raw_ocr_text,
            "extracted_fields_json": extracted_fields_json,
            "min_font_height_mm": min_font_height_mm,
            "compliance_score": float(compliance_score),
            "status": status,
            "report_url": report_url,
            "created_at": datetime.utcnow().isoformat(),
        }

        scan_res = client.table("scans").insert(scan_payload).execute()
        if not scan_res.data or len(scan_res.data) == 0:
            return None

        scan_id = scan_res.data[0]["id"]

        # Insert violations if present
        if violations and len(violations) > 0:
            viol_payload = []
            for v in violations:
                viol_payload.append({
                    "scan_id": scan_id,
                    "rule_code": v.get("rule_code", "LM-R6"),
                    "field": v.get("field", "unknown"),
                    "description": v.get("description", ""),
                    "severity": v.get("severity", "major"),
                    "created_at": datetime.utcnow().isoformat(),
                })
            client.table("violations").insert(viol_payload).execute()

        return scan_id
    except Exception as exc:
        logger.warning("Supabase save_scan error: %s", exc)
        return None


def get_recent_scans_from_supabase(limit: int = 10) -> Optional[List[dict]]:
    """Retrieve recent scans directly from Supabase."""
    client = get_client()
    if not client:
        return None

    try:
        res = client.table("scans").select("*, products(*)").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as exc:
        logger.warning("Supabase get_recent_scans error: %s", exc)
        return None
