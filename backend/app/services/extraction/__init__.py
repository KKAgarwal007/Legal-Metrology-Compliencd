"""Extraction & Normalization package."""
from app.services.extraction.extractor import extract_product_declarations
from app.services.extraction.normalizer import (
    normalize_mrp,
    normalize_net_quantity,
    normalize_date,
    normalize_phone,
    normalize_email,
    normalize_website,
)

normalize_currency_and_price = normalize_mrp

__all__ = [
    "extract_product_declarations",
    "normalize_mrp",
    "normalize_currency_and_price",
    "normalize_net_quantity",
    "normalize_date",
    "normalize_phone",
    "normalize_email",
    "normalize_website",
]
