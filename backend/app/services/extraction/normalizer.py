"""
Deterministic Normalization Services for Legal Metrology Declarations.

Normalizes extracted values for:
- Currency and price (INR, Rs, ₹)
- Net quantity (mass, volume, count, length)
- Packaging and manufacturing dates
- Consumer care contacts (phone, email, web)
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


# ==============================================================================
# 1. CURRENCY & PRICE NORMALIZATION
# ==============================================================================

def normalize_mrp(raw_text: str) -> Dict[str, Any]:
    """
    Normalizes MRP strings into numeric value, standard currency, and tax-inclusive status.

    Examples:
        "MRP Rs. 25.00 (incl. of all taxes)" -> {
            "value": 25.0,
            "currency": "INR",
            "is_inclusive": True,
            "raw_value": "MRP Rs. 25.00 (incl. of all taxes)"
        }
    """
    if not raw_text:
        return {"value": None, "currency": "INR", "is_inclusive": False, "raw_value": raw_text}

    text = str(raw_text).strip()

    # Check for inclusive of taxes
    tax_pattern = re.compile(r'(?:incl|inclusive).*?(?:tax|all\s*taxes)', re.IGNORECASE)
    is_inclusive = bool(tax_pattern.search(text))

    # Extract numeric amount
    price_pattern = re.compile(r'(?:(?:MRP|M\.R\.P\.?|Rs\.?|₹|INR)\s*[:.]?\s*)?([0-9]+(?:[,.][0-9]{1,2})?)', re.IGNORECASE)
    match = price_pattern.search(text)

    val: Optional[float] = None
    if match:
        clean_num = match.group(1).replace(',', '')
        try:
            val = float(clean_num)
        except ValueError:
            val = None

    return {
        "value": val,
        "currency": "INR",
        "is_inclusive": is_inclusive,
        "raw_value": raw_text
    }


# ==============================================================================
# 2. NET QUANTITY NORMALIZATION
# ==============================================================================

def normalize_net_quantity(raw_text: str) -> Dict[str, Any]:
    """
    Normalizes net quantity strings to numerical value and standard unit under
    Legal Metrology (Packaged Commodities) Rules, 2011 standard units (g, kg, ml, L, etc.)

    Examples:
        "500 gm" -> {"value": 500.0, "unit": "g", "is_standard_unit": True, "raw_value": "500 gm"}
        "1.5 Litre" -> {"value": 1.5, "unit": "L", "is_standard_unit": True, "raw_value": "1.5 Litre"}
    """
    if not raw_text:
        return {"value": None, "unit": None, "is_standard_unit": False, "raw_value": raw_text}

    text = str(raw_text).strip()

    # Pattern capturing magnitude and unit
    qty_pattern = re.compile(
        r'([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)',
        re.IGNORECASE
    )
    match = qty_pattern.search(text)

    if not match:
        return {"value": None, "unit": None, "is_standard_unit": False, "raw_value": raw_text}

    raw_val_str, raw_unit_str = match.group(1), match.group(2).lower()

    try:
        val = float(raw_val_str)
    except ValueError:
        val = None

    # Legal Metrology Standard Unit Canonical Mapping
    UNIT_MAP = {
        # Mass
        "g": "g",
        "gm": "g",
        "gms": "g",
        "gram": "g",
        "grams": "g",
        "kg": "kg",
        "kgs": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "mg": "mg",

        # Volume
        "ml": "ml",
        "millilitre": "ml",
        "millilitres": "ml",
        "l": "L",
        "lt": "L",
        "ltr": "L",
        "litre": "L",
        "litres": "L",

        # Length / Dimension
        "m": "m",
        "meter": "m",
        "metre": "m",
        "cm": "cm",
        "mm": "mm",

        # Number / Count
        "u": "units",
        "unit": "units",
        "units": "units",
        "n": "units",
        "pc": "pieces",
        "pcs": "pieces",
        "piece": "pieces",
        "pieces": "pieces"
    }

    canonical_unit = UNIT_MAP.get(raw_unit_str, raw_unit_str)
    standard_units = {"g", "kg", "mg", "ml", "L", "m", "cm", "mm", "units", "pieces"}
    is_standard = canonical_unit in standard_units

    return {
        "value": val,
        "unit": canonical_unit,
        "is_standard_unit": is_standard,
        "raw_value": raw_text
    }


# ==============================================================================
# 3. DATE NORMALIZATION
# ==============================================================================

MONTH_ABBRS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def normalize_date(raw_text: str) -> Dict[str, Any]:
    """
    Normalizes Indian package date formats into ISO strings (YYYY-MM-DD or YYYY-MM).
    Supports formats:
        - MM/YYYY or MM/YY
        - DD/MM/YYYY or DD-MM-YYYY
        - MMM YYYY or MMM YY (e.g. OCT 2024, NOV/24)
    """
    if not raw_text:
        return {"iso_date": None, "year": None, "month": None, "day": None, "raw_value": raw_text}

    text = str(raw_text).strip()

    # Case 1: MMM YYYY or MMM/YYYY (e.g., "OCT 2024", "NOV-2023", "DEC/24")
    named_month_match = re.search(r'([a-zA-Z]{3})[\s\/\.\-]+([0-9]{2,4})', text)
    if named_month_match:
        m_str, y_str = named_month_match.group(1).lower(), named_month_match.group(2)
        if m_str in MONTH_ABBRS:
            month = MONTH_ABBRS[m_str]
            year = int(y_str) if len(y_str) == 4 else 2000 + int(y_str)
            return {
                "iso_date": f"{year:04d}-{month:02d}",
                "year": year,
                "month": month,
                "day": None,
                "raw_value": raw_text
            }

    # Case 2: DD/MM/YYYY or DD-MM-YYYY
    full_date_match = re.search(r'([0-9]{1,2})[\/\.\-]([0-9]{1,2})[\/\.\-]([0-9]{2,4})', text)
    if full_date_match:
        d, m, y = int(full_date_match.group(1)), int(full_date_match.group(2)), int(full_date_match.group(3))
        year = y if y >= 100 else 2000 + y
        if 1 <= m <= 12 and 1 <= d <= 31:
            return {
                "iso_date": f"{year:04d}-{m:02d}-{d:02d}",
                "year": year,
                "month": m,
                "day": d,
                "raw_value": raw_text
            }

    # Case 3: MM/YYYY or MM/YY (very common on Indian packaged commodities: Rule 6(1)(d))
    month_year_match = re.search(r'([0-9]{1,2})[\/\.\-]([0-9]{2,4})', text)
    if month_year_match:
        m, y = int(month_year_match.group(1)), int(month_year_match.group(2))
        year = y if y >= 100 else 2000 + y
        if 1 <= m <= 12:
            return {
                "iso_date": f"{year:04d}-{m:02d}",
                "year": year,
                "month": m,
                "day": None,
                "raw_value": raw_text
            }

    return {"iso_date": None, "year": None, "month": None, "day": None, "raw_value": raw_text}


# ==============================================================================
# 4. CONTACT INFORMATION NORMALIZATION
# ==============================================================================

def normalize_phone(raw_text: str) -> Optional[str]:
    """Extracts and formats 10-digit, toll-free 1800, or +91 telephone numbers."""
    if not raw_text:
        return None
    # 1800 Toll free
    toll_free = re.search(r'(?:1800|1860)[\s\-]?[0-9]{3,4}[\s\-]?[0-9]{3,4}', raw_text)
    if toll_free:
        return re.sub(r'[\s\-]', '', toll_free.group(0))

    # Standard 10 digit or +91
    phone_match = re.search(r'(?:\+91[\s\-]?)?[6-9][0-9]{9}', raw_text)
    if phone_match:
        cleaned = re.sub(r'[\s\-]', '', phone_match.group(0))
        return cleaned
    return None


def normalize_email(raw_text: str) -> Optional[str]:
    """Extracts valid email addresses."""
    if not raw_text:
        return None
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
    if email_match:
        return email_match.group(0).lower()
    return None


def normalize_website(raw_text: str) -> Optional[str]:
    """Extracts URL or website domain."""
    if not raw_text:
        return None
    web_match = re.search(r'(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?', raw_text)
    if web_match:
        url = web_match.group(0)
        if not url.startswith('http') and 'www.' in url:
            url = 'https://' + url
        return url
    return None
