"""
Unit tests for deterministic normalization functions.
"""

import unittest
from app.services.extraction.normalizer import (
    normalize_mrp,
    normalize_net_quantity,
    normalize_date,
    normalize_phone,
    normalize_email
)

class TestNormalizer(unittest.TestCase):

    def test_price_normalization(self):
        # Symbol with decimal and taxes
        res1 = normalize_mrp("MRP ₹250.50 (incl. of all taxes)")
        self.assertEqual(res1["currency"], "INR")
        self.assertEqual(res1["value"], 250.50)
        self.assertTrue(res1["is_inclusive"])

        # Rs. without decimal
        res2 = normalize_mrp("Rs. 45 only")
        self.assertEqual(res2["currency"], "INR")
        self.assertEqual(res2["value"], 45.0)

    def test_quantity_normalization(self):
        # Grams
        res1 = normalize_net_quantity("Net Wt. 500 gm")
        self.assertEqual(res1["value"], 500.0)
        self.assertEqual(res1["unit"], "g")
        self.assertTrue(res1["is_standard_unit"])

        # Kilograms
        res2 = normalize_net_quantity("Net Weight: 2.5 kg")
        self.assertEqual(res2["value"], 2.5)
        self.assertEqual(res2["unit"], "kg")
        self.assertTrue(res2["is_standard_unit"])

        # Millilitres
        res3 = normalize_net_quantity("Volume: 750 mL")
        self.assertEqual(res3["value"], 750.0)
        self.assertEqual(res3["unit"], "ml")
        self.assertTrue(res3["is_standard_unit"])

    def test_date_normalization(self):
        # Month Year
        res1 = normalize_date("Mfg Date: 08/2024")
        self.assertEqual(res1["iso_date"], "2024-08")
        self.assertEqual(res1["year"], 2024)
        self.assertEqual(res1["month"], 8)

        # Day Month Year
        res2 = normalize_date("Pkd: 15/10/2023")
        self.assertEqual(res2["iso_date"], "2023-10-15")

        # Named Month (e.g. OCT 2024)
        res3 = normalize_date("Pkd: OCT 2024")
        self.assertEqual(res3["iso_date"], "2024-10")

    def test_contact_normalization(self):
        phone_res = normalize_phone("Call toll free: 1800-200-1234 or +91 98765 43210")
        self.assertIsNotNone(phone_res)
        self.assertIn("1800", phone_res)

        email_res = normalize_email("Consumer feedback: care@brandfoods.co.in")
        self.assertEqual(email_res, "care@brandfoods.co.in")

if __name__ == "__main__":
    unittest.main()
