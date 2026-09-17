"""
Unit tests for the Deterministic Compliance Engine.
Tests standard unit requirements, tax inclusions, missing declarations, and three-tier verdicts.
"""

import unittest
from app.services.compliance.rule_engine import (
    DeterministicRuleEngine,
    evaluate_compliance,
    ALLOWED_METRIC_UNITS,
    PROHIBITED_UNITS
)

class TestComplianceEngine(unittest.TestCase):

    def setUp(self):
        self.engine = DeterministicRuleEngine(confidence_threshold=0.60)
        self.sample_rules = [
            {
                "rule_id": "RULE-001",
                "field": "mrp",
                "canonical_field": "maximum_retail_price",
                "requirement_type": "required",
                "description": "Every package shall bear the retail sale price.",
                "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
                "source_rule": "Rule 6(1)(e)",
                "severity": "critical"
            },
            {
                "rule_id": "RULE-002",
                "field": "net_quantity",
                "canonical_field": "net_quantity",
                "requirement_type": "required",
                "description": "Every package shall bear the net quantity.",
                "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
                "source_rule": "Rule 6(1)(b)",
                "severity": "critical"
            },
            {
                "rule_id": "RULE-010",
                "field": "mrp_inclusive",
                "canonical_field": "mrp_includes_all_taxes",
                "requirement_type": "required",
                "description": "The retail sale price shall be inclusive of all taxes.",
                "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
                "source_rule": "Rule 2(l)",
                "severity": "major"
            },
            {
                "rule_id": "RULE-012",
                "field": "net_quantity_unit",
                "canonical_field": "net_quantity_standard_unit",
                "requirement_type": "required",
                "description": "Net quantity shall be expressed in standard units.",
                "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
                "source_rule": "Rule 5",
                "severity": "major"
            }
        ]

    def test_compliant_packaging(self):
        """Test product with all declarations in standard metric units and inclusive taxes."""
        fields = [
            {
                "field": "mrp",
                "raw_value": "₹20.00",
                "normalized_value": "20.0",
                "source_text": "MRP Rs. 20 (incl. of all taxes)",
                "confidence": 0.95,
                "status": "DETECTED"
            },
            {
                "field": "net_quantity",
                "raw_value": "50 g",
                "normalized_value": "50.0",
                "unit": "g",
                "source_text": "Net Wt. 50g",
                "confidence": 0.92,
                "status": "DETECTED"
            },
            {
                "field": "mrp_inclusive",
                "raw_value": "incl. of all taxes",
                "source_text": "MRP Rs. 20 (incl. of all taxes)",
                "confidence": 0.90,
                "status": "DETECTED"
            },
            {
                "field": "net_quantity_unit",
                "raw_value": "g",
                "normalized_value": "g",
                "unit": "g",
                "source_text": "50g",
                "confidence": 0.92,
                "status": "DETECTED"
            }
        ]

        eval_payload = evaluate_compliance(fields=fields, rules=self.sample_rules)
        results = eval_payload["results"]
        statuses = [r["status"] for r in results]

        # All required checks should pass
        self.assertIn("PASS", statuses)
        self.assertNotIn("VIOLATION", statuses)
        self.assertNotIn("REVIEW", statuses)

    def test_missing_declaration_is_review_not_violation(self):
        """Important requirement: missing declarations must be marked REVIEW, not automatic VIOLATION."""
        fields = [
            {
                "field": "mrp",
                "raw_value": "₹20.00",
                "normalized_value": "20.0",
                "source_text": "MRP Rs. 20 (incl. of all taxes)",
                "confidence": 0.95,
                "status": "DETECTED"
            }
            # Net quantity is missing
        ]

        eval_payload = evaluate_compliance(fields=fields, rules=self.sample_rules)
        results = eval_payload["results"]
        net_qty_result = next((r for r in results if r["field_name"] == "net_quantity"), None)

        self.assertIsNotNone(net_qty_result)
        self.assertEqual(net_qty_result["status"], "REVIEW")
        self.assertNotEqual(net_qty_result["status"], "VIOLATION")

    def test_prohibited_imperial_units_is_violation(self):
        """Active breach: using Imperial units (ounces, lbs) violates Rule 5."""
        fields = [
            {
                "field": "mrp",
                "raw_value": "₹50.00",
                "source_text": "MRP Rs. 50 (incl. of all taxes)",
                "confidence": 0.95,
                "status": "DETECTED"
            },
            {
                "field": "net_quantity",
                "raw_value": "16 oz",
                "unit": "oz",
                "source_text": "Net Weight 16 oz",
                "confidence": 0.90,
                "status": "DETECTED"
            },
            {
                "field": "mrp_inclusive",
                "raw_value": "incl. of all taxes",
                "source_text": "MRP Rs. 50 (incl. of all taxes)",
                "confidence": 0.90,
                "status": "DETECTED"
            },
            {
                "field": "net_quantity_unit",
                "raw_value": "oz",
                "unit": "oz",
                "source_text": "Net Weight 16 oz",
                "confidence": 0.90,
                "status": "DETECTED"
            }
        ]

        eval_payload = evaluate_compliance(fields=fields, rules=self.sample_rules)
        results = eval_payload["results"]
        unit_result = next((r for r in results if r["field_name"] == "net_quantity_unit"), None)

        self.assertIsNotNone(unit_result)
        self.assertEqual(unit_result["status"], "VIOLATION")

if __name__ == "__main__":
    unittest.main()
