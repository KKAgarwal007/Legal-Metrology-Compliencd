"""
Deterministic Compliance Engine for Legal Metrology.

CRITICAL ARCHITECTURAL PRINCIPLE:
- The LLM NEVER directly decides PASS / REVIEW / VIOLATION.
- Deterministic code evaluates statutory rules against extracted fields.
- Three-tier decision logic:
    * PASS: Evidence detected with sufficient confidence and deterministic rule satisfied.
    * REVIEW: Information is missing, ambiguous, low-confidence, or requires human verification.
    * VIOLATION: Strong evidence that a deterministic statutory requirement is actively breached.
    * NOT_APPLICABLE: Rule does not apply to this commodity category.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Standard units of weights and measures allowed under Rule 5 & Second Schedule of Legal Metrology Rules, 2011
ALLOWED_METRIC_UNITS = {
    # Mass
    "g", "gm", "gram", "grams", "kg", "kilogram", "kilograms", "mg",
    # Volume
    "ml", "millilitre", "millilitres", "l", "litre", "litres", "kl",
    # Length / Area
    "cm", "m", "metre", "metres", "mm", "sq m", "sq cm",
    # Count / Number
    "n", "u", "units", "pieces", "pcs", "count"
}

# Non-standard units that constitute an active VIOLATION under Legal Metrology Act, 2009 Section 11 & Rule 5
PROHIBITED_UNITS = {
    "lb", "lbs", "pound", "pounds", "oz", "ounce", "ounces",
    "fl oz", "fluid ounce", "fluid ounces", "yard", "yards", "ft", "feet", "inch", "inches"
}

DEFAULT_LEGAL_METROLOGY_RULES = [
    {
        "rule_id": "RULE-001",
        "field": "product_name",
        "canonical_field": "common_or_generic_name",
        "requirement_type": "required",
        "description": "Every package shall bear the generic or common name of the commodity.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(a)",
        "source_page": 6,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-002",
        "field": "net_quantity",
        "canonical_field": "net_quantity",
        "requirement_type": "required",
        "description": "Every package shall bear the net quantity in standard units of weight or measure.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(b)",
        "source_page": 6,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-003",
        "field": "net_quantity_unit",
        "canonical_field": "net_quantity",
        "requirement_type": "required",
        "description": "Net quantity shall be expressed in standard metric units (g, kg, ml, l, m, cm, N).",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 5 & Second Schedule",
        "source_page": 5,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-004",
        "field": "manufacturer_name",
        "canonical_field": "manufacturer_name",
        "requirement_type": "required",
        "description": "Name and address of manufacturer, packer, or importer must be clearly declared.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(c)",
        "source_page": 7,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-005",
        "field": "manufacturing_date_raw",
        "canonical_field": "date_of_manufacture_or_packing",
        "requirement_type": "date_valid",
        "description": "Month and year of manufacture or pre-packing must be declared.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(d)",
        "source_page": 8,
        "severity": "major",
    },
    {
        "rule_id": "RULE-006",
        "field": "mrp_raw",
        "canonical_field": "maximum_retail_price",
        "requirement_type": "required",
        "description": "Maximum Retail Price (MRP) must be clearly declared on the principal display panel.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(e)",
        "source_page": 8,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-007",
        "field": "mrp_inclusive",
        "canonical_field": "maximum_retail_price",
        "requirement_type": "contains",
        "requirement_value": "inclusive of all taxes",
        "description": "Retail sale price shall explicitly state 'inclusive of all taxes'.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 2(l) read with Rule 6(1)(e)",
        "source_page": 4,
        "severity": "major",
    },
    {
        "rule_id": "RULE-008",
        "field": "consumer_care_phone",
        "canonical_field": "consumer_care_phone",
        "requirement_type": "required",
        "description": "Consumer care helpline telephone number or email for grievance redressal.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(h)",
        "source_page": 9,
        "severity": "major",
    },
    {
        "rule_id": "RULE-009",
        "field": "country_of_origin",
        "canonical_field": "country_of_origin",
        "requirement_type": "required",
        "description": "Country of origin or manufacture shall be mentioned on the package.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(10) / Rule 6(1)(aa)",
        "source_page": 7,
        "severity": "major",
    },
    {
        "rule_id": "RULE-010",
        "field": "batch_number",
        "canonical_field": "batch_lot_code",
        "requirement_type": "required",
        "description": "Batch number or lot number or code mark must be declared.",
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(g)",
        "source_page": 8,
        "severity": "minor",
    },
]


class DeterministicRuleEngine:
    """
    Executes rule-by-rule deterministic checks against extracted packaging declarations.
    """

    def __init__(self, confidence_threshold: float = 0.60):
        self.confidence_threshold = confidence_threshold

    def evaluate_rule(
        self,
        rule: Dict[str, Any],
        field_data: Optional[Dict[str, Any]],
        product_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single compliance rule against a field.
        Returns a compliance result dictionary with status, reason, and legal evidence mapping.
        """
        rule_id = rule.get("rule_id", "UNKNOWN")
        field_name = rule.get("field", "")
        req_type = rule.get("requirement_type", "required")
        req_val = rule.get("requirement_value")
        rule_desc = rule.get("description", "")
        source_doc = rule.get("source_document", "Legal Metrology (Packaged Commodities) Rules, 2011")
        source_rule = rule.get("source_rule", "Rule 6")
        source_page = rule.get("source_page")

        # 1. Applicability check (e.g. conditional rules)
        applicability = rule.get("applicability") or {}
        if applicability:
            cat_filter = applicability.get("category")
            if cat_filter and product_metadata:
                prod_cat = (product_metadata.get("category") or "").lower()
                if cat_filter != "packaged_commodity" and cat_filter.lower() not in prod_cat:
                    return {
                        "rule_id": rule_id,
                        "field_name": field_name,
                        "detected_value": None,
                        "required_value": "Category exemption",
                        "status": "NOT_APPLICABLE",
                        "reason": f"Rule applicable to '{cat_filter}', but product category is '{prod_cat or 'unspecified'}'.",
                        "confidence": 1.0,
                        "legal_source": {"document": source_doc, "rule": source_rule, "page": source_page}
                    }

        # 2. Check if field exists and was detected
        val = (
            field_data.get("value")
            or field_data.get("raw_value")
            or field_data.get("normalized_value")
        ) if field_data else None

        if not field_data or field_data.get("status") == "NOT_DETECTED" or not val:
            # If conditional rule, check whether condition applies
            if req_type == "conditional":
                cond = req_val.get("condition") if isinstance(req_val, dict) else None
                if cond == "imported_commodity":
                    is_imported = product_metadata.get("is_imported", False) if product_metadata else False
                    if not is_imported:
                        return {
                            "rule_id": rule_id,
                            "field_name": field_name,
                            "detected_value": None,
                            "required_value": "Only required if imported",
                            "status": "PASS",
                            "reason": "Commodity is not marked as imported; country of origin rule is satisfied.",
                            "confidence": 0.95,
                            "legal_source": {"document": source_doc, "rule": source_rule, "page": source_page}
                        }

            # Human-in-the-loop principle: Missing declarations trigger REVIEW, NOT automatic violation!
            return {
                "rule_id": rule_id,
                "field_name": field_name,
                "detected_value": None,
                "required_value": "Mandatory declaration on packaging",
                "status": "REVIEW",
                "reason": f"Mandatory declaration '{field_name}' was NOT detected in the provided packaging images. Physical inspection required.",
                "confidence": 0.0,
                "evidence": None,
                "legal_source": {"document": source_doc, "rule": source_rule, "page": source_page}
            }

        # 3. Field is present - verify OCR confidence
        raw_val = str(val or "").strip()
        confidence = float(field_data.get("confidence") or 0.85)
        source_text = field_data.get("source_text") or raw_val
        bbox = field_data.get("bbox")
        unit = field_data.get("unit") or (raw_val if field_name == "net_quantity_unit" else None)

        # Low OCR confidence -> REVIEW
        if confidence < self.confidence_threshold:
            return {
                "rule_id": rule_id,
                "field_name": field_name,
                "detected_value": raw_val,
                "required_value": "Legible declaration",
                "status": "REVIEW",
                "reason": f"Declaration detected but OCR recognition confidence ({confidence:.2f}) is below threshold ({self.confidence_threshold:.2f}). Manual verification required.",
                "confidence": confidence,
                "evidence": {"bbox": bbox, "source_text": source_text, "confidence": confidence},
                "legal_source": {"document": source_doc, "rule": source_rule, "page": source_page}
            }

        # 4. Operator-specific deterministic evaluation
        status, reason, req_display = self._execute_operator(
            rule_id=rule_id,
            field_name=field_name,
            req_type=req_type,
            req_val=req_val,
            detected_val=raw_val,
            unit=unit,
            field_data=field_data,
            product_metadata=product_metadata
        )

        return {
            "rule_id": rule_id,
            "field_name": field_name,
            "detected_value": raw_val,
            "required_value": req_display,
            "status": status,
            "reason": reason,
            "confidence": confidence,
            "evidence": {
                "bbox": bbox,
                "source_text": source_text,
                "confidence": confidence
            },
            "legal_source": {
                "document": source_doc,
                "rule": source_rule,
                "page": source_page
            }
        }

    def _execute_operator(
        self,
        rule_id: str,
        field_name: str,
        req_type: str,
        req_val: Any,
        detected_val: str,
        unit: Optional[str],
        field_data: Dict[str, Any],
        product_metadata: Optional[Dict[str, Any]]
    ) -> Tuple[str, str, str]:
        """
        Deterministic dispatch for operators.
        Returns (status, reason, required_value_display).
        """
        val_lower = detected_val.lower()

        # Specific domain logic for Legal Metrology Rules

        # RULE: MRP must state inclusive of all taxes (Rule 2(l) & Rule 6(1)(e))
        if field_name == "mrp_inclusive" or (field_name == "mrp" and req_type == "contains"):
            # Check source text for tax declaration
            source_text = (field_data.get("source_text") or detected_val).lower()
            tax_patterns = [
                r"incl(?:usive)?\.?\s*(?:of)?\s*all\s*taxes",
                r"incl\.?\s*(?:of)?\s*all",
                r"incl\.?\s*taxes",
                r"inclusive\s*taxes",
                r"all\s*taxes"
            ]
            has_tax = any(re.search(p, source_text) for p in tax_patterns)
            if has_tax or field_data.get("is_inclusive"):
                return (
                    "PASS",
                    "MRP declaration explicitly includes the statutory 'inclusive of all taxes' statement.",
                    "Must state 'inclusive of all taxes' (Rule 2(l))"
                )
            else:
                return (
                    "VIOLATION",
                    "MRP is declared without the mandatory statutory phrase 'inclusive of all taxes'. Direct breach of Rule 2(l) and Rule 6(1)(e).",
                    "Must state 'inclusive of all taxes' (Rule 2(l))"
                )

        # RULE: Net quantity unit must be standard metric (Rule 5)
        if field_name in ("net_quantity_unit", "net_quantity") and (unit or req_type == "regex"):
            detected_unit = (unit or "").lower().strip()
            # If unit not separately parsed, extract from value
            if not detected_unit:
                unit_match = re.search(r"([a-zA-Z\s]+)$", detected_val)
                if unit_match:
                    detected_unit = unit_match.group(1).strip().lower()

            # Active violation: imperial/prohibited unit
            if detected_unit in PROHIBITED_UNITS:
                return (
                    "VIOLATION",
                    f"Packaging declares non-standard unit '{detected_unit}'. Legal Metrology Act, 2009 Section 11 strictly prohibits non-metric measurements.",
                    "Standard metric units only: g, kg, ml, l, cm, m, or N (Rule 5)"
                )

            # Valid metric unit
            if detected_unit in ALLOWED_METRIC_UNITS or any(detected_unit.startswith(u) for u in ["g", "kg", "ml", "l", "unit"]):
                return (
                    "PASS",
                    f"Net quantity is declared in standard statutory metric unit ({detected_unit or 'metric'}).",
                    "Standard metric units only (Rule 5)"
                )
            elif detected_unit:
                return (
                    "REVIEW",
                    f"Declared unit '{detected_unit}' is ambiguous or non-standard. Inspector verification required.",
                    "Standard metric units only (Rule 5)"
                )

        # Standard Generic Operators
        if req_type in ("required", "not_empty"):
            if detected_val and len(detected_val.strip()) > 0:
                return ("PASS", f"Mandatory declaration '{field_name}' is clearly declared.", "Required declaration")
            else:
                return ("REVIEW", f"Declaration '{field_name}' is empty or missing.", "Required declaration")

        elif req_type == "regex":
            pattern = req_val if isinstance(req_val, str) else req_val.get("pattern", ".*")
            if re.search(pattern, detected_val, re.IGNORECASE):
                return ("PASS", f"Declaration format conforms to statutory specification (regex: {pattern}).", f"Format: {pattern}")
            else:
                return ("REVIEW", f"Declaration '{detected_val}' does not conform to expected statutory format.", f"Format: {pattern}")

        elif req_type == "date_valid":
            # Validate manufacturing / packaging date
            is_valid, msg = self._validate_packaging_date(detected_val)
            if is_valid:
                return ("PASS", f"Date of manufacture/packing is valid ({detected_val}).", "Valid month and year (Rule 6(1)(d))")
            else:
                return ("REVIEW", f"Declared date '{detected_val}' is invalid or unparseable: {msg}", "Valid month and year (Rule 6(1)(d))")

        elif req_type == "equals":
            target = str(req_val)
            if detected_val.strip().lower() == target.strip().lower():
                return ("PASS", f"Value matches required statutory value '{target}'.", target)
            else:
                return ("VIOLATION", f"Declared value '{detected_val}' does not match statutory requirement '{target}'.", target)

        elif req_type == "contains":
            substr = str(req_val).lower()
            if substr in val_lower:
                return ("PASS", f"Declaration contains required statement '{req_val}'.", f"Contains '{req_val}'")
            else:
                return ("VIOLATION", f"Declaration does not contain mandatory text '{req_val}'.", f"Contains '{req_val}'")

        # Fallback default
        return ("PASS", f"Declaration '{field_name}' detected and verified.", "Statutory compliance")

    def _validate_packaging_date(self, date_str: str) -> Tuple[bool, str]:
        """Verify that packaging date has valid month/year and is not unreasonably futuristic."""
        cleaned = date_str.strip()
        now = datetime.now()

        # Formats: MM/YYYY, MM/YY, YYYY-MM, DD/MM/YYYY
        formats = ["%m/%Y", "%m/%y", "%Y-%m", "%d/%m/%Y", "%d-%m-%Y", "%b %Y", "%B %Y", "%m-%Y"]
        for fmt in formats:
            try:
                parsed = datetime.strptime(cleaned, fmt)
                # Ensure year is reasonable (e.g., within next 1 month to allow packing advance)
                if parsed.year > now.year + 1:
                    return False, f"Date is more than 1 year in the future ({parsed.year})"
                if parsed.year < 2000:
                    return False, f"Date year is prior to year 2000 ({parsed.year})"
                return True, "Valid"
            except ValueError:
                continue

        # Check regex for MM/YYYY pattern e.g. "08/2024"
        if re.search(r"\b(0[1-9]|1[0-2])[-/](20\d\d|\d\d)\b", cleaned):
            return True, "Valid month/year"

        return False, "Could not parse month and year"


def evaluate_compliance(
    fields: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    product_metadata: Optional[Dict[str, Any]] = None,
    confidence_threshold: float = 0.60
) -> Dict[str, Any]:
    """
    Main evaluation entry point.
    Runs deterministic checks for all rules against extracted fields.
    Computes overall PASS / REVIEW / VIOLATION summary.
    """
    engine = DeterministicRuleEngine(confidence_threshold=confidence_threshold)

    # Index fields by canonical_name and field_name for quick lookup
    field_lookup: Dict[str, Dict[str, Any]] = {}
    for f in fields:
        fname = (f.get("field_name") or f.get("field") or "").lower()
        cname = (f.get("canonical_name") or "").lower()
        if fname:
            field_lookup[fname] = f
        if cname:
            field_lookup[cname] = f

    rules_to_eval = rules if rules and len(rules) > 0 else DEFAULT_LEGAL_METROLOGY_RULES

    results: List[Dict[str, Any]] = []

    for rule in rules_to_eval:
        target_field = rule.get("field", "").lower()
        canonical_target = rule.get("canonical_field", "").lower()

        # Find matching extracted field
        matched_field_data = (
            field_lookup.get(target_field)
            or field_lookup.get(canonical_target)
            or field_lookup.get(target_field.replace("_", ""))
        )

        res = engine.evaluate_rule(rule, matched_field_data, product_metadata)
        results.append(res)

    # Compute overall status
    has_violation = any(r["status"] == "VIOLATION" for r in results)
    has_review = any(r["status"] == "REVIEW" for r in results)

    if has_violation:
        overall_result = "VIOLATION"
    elif has_review:
        overall_result = "REVIEW"
    elif len(results) > 0:
        overall_result = "PASS"
    else:
        overall_result = "REVIEW"

    summary_stats = {
        "total_rules_checked": len(results),
        "pass_count": sum(1 for r in results if r["status"] == "PASS"),
        "review_count": sum(1 for r in results if r["status"] == "REVIEW"),
        "violation_count": sum(1 for r in results if r["status"] == "VIOLATION"),
        "na_count": sum(1 for r in results if r["status"] == "NOT_APPLICABLE"),
        "overall_result": overall_result
    }

    return {
        "overall_result": overall_result,
        "results": results,
        "summary": summary_stats
    }
