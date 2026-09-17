"""
Unit tests for Report Generation & SHA-256 Tamper Evidence.
"""

import unittest
from app.services.reporting.report_generator import (
    generate_report_data,
    compute_sha256_signature,
    STATUTORY_DISCLAIMER
)

class TestReporting(unittest.TestCase):

    def test_report_generation_and_tamper_hash(self):
        sample_inspection = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Sample Biscuit Scan",
            "status": "completed",
            "overall_result": "PASS"
        }
        sample_product = {
            "product_name": "Digestive Biscuits",
            "brand": "NutriBite",
            "category": "Food"
        }
        sample_fields = [
            {"field": "mrp", "raw_value": "₹30.00", "status": "DETECTED"},
            {"field": "net_quantity", "raw_value": "100 g", "status": "DETECTED"}
        ]
        sample_results = [
            {"rule_id": "RULE-001", "field_name": "mrp", "status": "PASS", "reason": "Declared"}
        ]

        report = generate_report_data(
            inspection=sample_inspection,
            product=sample_product,
            fields=sample_fields,
            compliance_results=sample_results
        )

        self.assertIn("report_id", report)
        self.assertIn("tamper_evidence_hash", report)
        self.assertEqual(report["summary"]["overall_result"], "PASS")
        self.assertIn("Legal Metrology Act, 2009", report.get("statutory_disclaimer", ""))

        # Verify cryptographic tamper detection
        initial_hash = report["tamper_evidence_hash"]
        computed_hash = compute_sha256_signature(report)
        self.assertEqual(initial_hash, computed_hash)

        # Modify payload to simulate tampering
        tampered_report = dict(report)
        tampered_report["summary"] = {"overall_result": "VIOLATION"}
        tampered_hash = compute_sha256_signature(tampered_report)

        self.assertNotEqual(initial_hash, tampered_hash, "Tampered payload must produce distinct hash")

if __name__ == "__main__":
    unittest.main()
