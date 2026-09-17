"""
Seed Demo Data for Legal Metrology Compliance System.

Creates:
  1. Demo inspector user: inspector@example.com / password123
  2. Inspection 1 (PASS): Premium Basmati Rice (all rules satisfied)
  3. Inspection 2 (REVIEW): Herbal Shampoo (ambiguous batch, missing best-before)
  4. Inspection 3 (VIOLATION): Imported Chocolate (no MRP declared, imported without COO)

Usage:
    python scripts/seed_demo_data.py

Requires:
    - PostgreSQL running with tables created via scripts/init_db.sql
    - Compliance rules seeded via scripts/seed_compliance_rules.py
"""

import json
import os
import sys
import uuid
from datetime import date, datetime, timezone

import psycopg2
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/legal_metrology",
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def seed_demo_user(conn) -> str:
    """Create or return demo user ID."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", ("inspector@example.com",))
    existing = cur.fetchone()
    if existing:
        print("  Demo user already exists.")
        return existing[0]

    user_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO users (id, email, full_name, hashed_password, role, is_active, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            "inspector@example.com",
            "Senior Legal Metrology Inspector",
            hash_password("password123"),
            "inspector",
            True,
            datetime.now(timezone.utc),
        ),
    )
    conn.commit()
    print("  Demo user created: inspector@example.com / password123")
    return user_id


def get_rule_id_map(conn) -> dict:
    """Map rule_id string (e.g. 'RULE-001') to DB uuid."""
    cur = conn.cursor()
    cur.execute("SELECT rule_id, id FROM compliance_rules")
    return {row[0]: row[1] for row in cur.fetchall()}


def seed_demo_inspections(conn, user_id: str, rule_map: dict):
    """Seed 3 demo inspections with full lifecycle data."""
    cur = conn.cursor()
    now = datetime.now(timezone.utc)

    demos = [
        # =================================================================
        # DEMO 1: PASS — Premium Basmati Rice 1 kg
        # All required declarations present, legible, compliant.
        # =================================================================
        {
            "title": "Royal Feast Premium Basmati Rice 1kg",
            "category": "Food",
            "status": "completed",
            "overall_result": "PASS",
            "notes": "Full compliance verified across all Legal Metrology Rule 6 declarations.",
            "product_name": "Royal Feast Basmati Rice",
            "brand": "Royal Feast",
            "fields": [
                {
                    "field": "mrp",
                    "canonical": "maximum_retail_price",
                    "raw": "MRP Rs. 140.00 (incl. of all taxes)",
                    "norm": "140.00",
                    "unit": None,
                    "currency": "INR",
                    "conf": 0.96,
                    "src": "MRP Rs. 140.00 (incl. of all taxes)",
                    "bbox": [510, 310, 890, 355],
                    "status": "DETECTED",
                },
                {
                    "field": "net_quantity",
                    "canonical": "net_quantity",
                    "raw": "Net Qty: 1 kg",
                    "norm": "1",
                    "unit": "kg",
                    "currency": None,
                    "conf": 0.98,
                    "src": "Net Qty: 1 kg",
                    "bbox": [120, 290, 380, 335],
                    "status": "DETECTED",
                },
                {
                    "field": "manufacturer_name",
                    "canonical": "manufacturer_name",
                    "raw": "Mfd by: Heritage Agri Foods Ltd.",
                    "norm": "Heritage Agri Foods Ltd.",
                    "unit": None,
                    "currency": None,
                    "conf": 0.94,
                    "src": "Mfd by: Heritage Agri Foods Ltd.",
                    "bbox": [80, 710, 620, 750],
                    "status": "DETECTED",
                },
                {
                    "field": "manufacturer_address",
                    "canonical": "manufacturer_address",
                    "raw": "Plot 42, Industrial Area, Karnal, Haryana - 132001",
                    "norm": "Plot 42, Industrial Area, Karnal, Haryana - 132001",
                    "unit": None,
                    "currency": None,
                    "conf": 0.91,
                    "src": "Plot 42, Industrial Area, Karnal, Haryana - 132001",
                    "bbox": [80, 755, 750, 795],
                    "status": "DETECTED",
                },
                {
                    "field": "product_name",
                    "canonical": "common_or_generic_name",
                    "raw": "Basmati Rice (Long Grain)",
                    "norm": "Basmati Rice",
                    "unit": None,
                    "currency": None,
                    "conf": 0.97,
                    "src": "Basmati Rice (Long Grain)",
                    "bbox": [150, 180, 680, 230],
                    "status": "DETECTED",
                },
                {
                    "field": "manufacturing_date",
                    "canonical": "date_of_manufacture_or_packing",
                    "raw": "Pkd: 01/2026",
                    "norm": "2026-01-01",
                    "unit": None,
                    "currency": None,
                    "conf": 0.93,
                    "src": "Pkd: 01/2026",
                    "bbox": [510, 365, 780, 405],
                    "status": "DETECTED",
                },
                {
                    "field": "batch_number",
                    "canonical": "batch_lot_code",
                    "raw": "Batch No: B26-KRL-042",
                    "norm": "B26-KRL-042",
                    "unit": None,
                    "currency": None,
                    "conf": 0.92,
                    "src": "Batch No: B26-KRL-042",
                    "bbox": [510, 415, 820, 455],
                    "status": "DETECTED",
                },
                {
                    "field": "consumer_care_info",
                    "canonical": "consumer_care_details",
                    "raw": "Care: customercare@heritagefoods.in | 1800-111-2222",
                    "norm": "customercare@heritagefoods.in | 1800-111-2222",
                    "unit": None,
                    "currency": None,
                    "conf": 0.89,
                    "src": "Care: customercare@heritagefoods.in | 1800-111-2222",
                    "bbox": [80, 810, 780, 850],
                    "status": "DETECTED",
                },
            ],
            "results": [
                {
                    "rule": "RULE-001",
                    "field": "mrp",
                    "detected": "Rs. 140.00",
                    "required": "Required",
                    "status": "PASS",
                    "reason": "Retail sale price detected with high confidence (0.96) including tax declaration.",
                    "evidence_text": "MRP Rs. 140.00 (incl. of all taxes)",
                    "legal_rule": "Rule 6(1)(e)",
                },
                {
                    "rule": "RULE-002",
                    "field": "net_quantity",
                    "detected": "1 kg",
                    "required": "Required (standard unit)",
                    "status": "PASS",
                    "reason": "Net quantity detected in standard SI unit (kg) with confidence 0.98.",
                    "evidence_text": "Net Qty: 1 kg",
                    "legal_rule": "Rule 6(1)(b)",
                },
                {
                    "rule": "RULE-003",
                    "field": "manufacturer_name",
                    "detected": "Heritage Agri Foods Ltd.",
                    "required": "Required",
                    "status": "PASS",
                    "reason": "Manufacturer name clearly declared with confidence 0.94.",
                    "evidence_text": "Mfd by: Heritage Agri Foods Ltd.",
                    "legal_rule": "Rule 6(1)(a)",
                },
                {
                    "rule": "RULE-005",
                    "field": "product_name",
                    "detected": "Basmati Rice",
                    "required": "Required",
                    "status": "PASS",
                    "reason": "Generic name of commodity declared prominently.",
                    "evidence_text": "Basmati Rice (Long Grain)",
                    "legal_rule": "Rule 6(1)(a)",
                },
                {
                    "rule": "RULE-006",
                    "field": "manufacturing_date",
                    "detected": "01/2026",
                    "required": "Required (MM/YYYY)",
                    "status": "PASS",
                    "reason": "Month and year of packing declared in valid MM/YYYY format.",
                    "evidence_text": "Pkd: 01/2026",
                    "legal_rule": "Rule 6(1)(d)",
                },
                {
                    "rule": "RULE-011",
                    "field": "batch_number",
                    "detected": "B26-KRL-042",
                    "required": "Required",
                    "status": "PASS",
                    "reason": "Batch code clearly declared.",
                    "evidence_text": "Batch No: B26-KRL-042",
                    "legal_rule": "Rule 6(1)(c)",
                },
            ],
        },
        # =================================================================
        # DEMO 2: REVIEW — Herbal Essence Hair Cleanser 200ml
        # Batch code ambiguous/low confidence; customer care missing phone.
        # Requires human inspector verification.
        # =================================================================
        {
            "title": "Naturale Herbal Essence Hair Cleanser 200ml",
            "category": "Cosmetics",
            "status": "completed",
            "overall_result": "REVIEW",
            "notes": (
                "Batch code partially obscured by crimp seal (OCR conf 0.51). "
                "Consumer care email present but telephone missing. Inspector review required."
            ),
            "product_name": "Herbal Essence Hair Cleanser",
            "brand": "Naturale",
            "fields": [
                {
                    "field": "mrp",
                    "canonical": "maximum_retail_price",
                    "raw": "M.R.P. Rs. 225/-",
                    "norm": "225.00",
                    "unit": None,
                    "currency": "INR",
                    "conf": 0.88,
                    "src": "M.R.P. Rs. 225/-",
                    "bbox": [420, 580, 720, 625],
                    "status": "DETECTED",
                },
                {
                    "field": "net_quantity",
                    "canonical": "net_quantity",
                    "raw": "200 ml",
                    "norm": "200",
                    "unit": "ml",
                    "currency": None,
                    "conf": 0.94,
                    "src": "200 ml",
                    "bbox": [100, 310, 260, 350],
                    "status": "DETECTED",
                },
                {
                    "field": "manufacturer_name",
                    "canonical": "manufacturer_name",
                    "raw": "Ayur Herbals Pvt Ltd",
                    "norm": "Ayur Herbals Pvt Ltd",
                    "unit": None,
                    "currency": None,
                    "conf": 0.91,
                    "src": "Ayur Herbals Pvt Ltd",
                    "bbox": [60, 720, 480, 760],
                    "status": "DETECTED",
                },
                {
                    "field": "batch_number",
                    "canonical": "batch_lot_code",
                    "raw": "B.No. ??34A",
                    "norm": None,
                    "unit": None,
                    "currency": None,
                    "conf": 0.51,
                    "src": "B.No. ??34A",
                    "bbox": [430, 635, 680, 675],
                    "status": "LOW_CONFIDENCE",
                },
                {
                    "field": "consumer_care_info",
                    "canonical": "consumer_care_details",
                    "raw": "feedback@naturale.co.in",
                    "norm": "feedback@naturale.co.in",
                    "unit": None,
                    "currency": None,
                    "conf": 0.78,
                    "src": "feedback@naturale.co.in",
                    "bbox": [60, 830, 450, 868],
                    "status": "AMBIGUOUS",
                },
            ],
            "results": [
                {
                    "rule": "RULE-001",
                    "field": "mrp",
                    "detected": "Rs. 225/-",
                    "required": "Required",
                    "status": "PASS",
                    "reason": "Retail sale price detected.",
                    "evidence_text": "M.R.P. Rs. 225/-",
                    "legal_rule": "Rule 6(1)(e)",
                },
                {
                    "rule": "RULE-002",
                    "field": "net_quantity",
                    "detected": "200 ml",
                    "required": "Required (standard unit)",
                    "status": "PASS",
                    "reason": "Net quantity in standard SI unit (ml).",
                    "evidence_text": "200 ml",
                    "legal_rule": "Rule 6(1)(b)",
                },
                {
                    "rule": "RULE-011",
                    "field": "batch_number",
                    "detected": "B.No. ??34A",
                    "required": "Required (legible)",
                    "status": "REVIEW",
                    "reason": (
                        "Batch declaration detected with low OCR confidence (0.51). "
                        "Characters partially obscured on package crimp. Physical inspection required."
                    ),
                    "evidence_text": "B.No. ??34A",
                    "legal_rule": "Rule 6(1)(c)",
                },
                {
                    "rule": "RULE-008",
                    "field": "consumer_care_info",
                    "detected": "feedback@naturale.co.in",
                    "required": "Required (email or phone)",
                    "status": "REVIEW",
                    "reason": (
                        "Only email address detected; no postal address or telephone "
                        "number for consumer care found. Verify complete declaration on side panel."
                    ),
                    "evidence_text": "feedback@naturale.co.in",
                    "legal_rule": "Rule 6(2)",
                },
            ],
        },
        # =================================================================
        # DEMO 3: VIOLATION — Imported Dark Chocolate 100g
        # No MRP declaration found; imported product without Country of Origin.
        # Clear deterministic violations of Rule 6(1)(e) and Rule 6(1)(f).
        # =================================================================
        {
            "title": "Alpine Pure Swiss Dark Chocolate 100g (Imported)",
            "category": "Food",
            "status": "completed",
            "overall_result": "VIOLATION",
            "notes": (
                "Deterministic violations detected: (1) No MRP declaration on entire package; "
                "(2) Imported product lacks Country of Origin declaration contrary to Rule 6(1)(f)."
            ),
            "product_name": "Swiss Dark Chocolate 72%",
            "brand": "Alpine Pure",
            "fields": [
                {
                    "field": "mrp",
                    "canonical": "maximum_retail_price",
                    "raw": None,
                    "norm": None,
                    "unit": None,
                    "currency": None,
                    "conf": 0.0,
                    "src": None,
                    "bbox": None,
                    "status": "NOT_DETECTED",
                },
                {
                    "field": "net_quantity",
                    "canonical": "net_quantity",
                    "raw": "100g e",
                    "norm": "100",
                    "unit": "g",
                    "currency": None,
                    "conf": 0.95,
                    "src": "100g e",
                    "bbox": [180, 420, 310, 460],
                    "status": "DETECTED",
                },
                {
                    "field": "country_of_origin",
                    "canonical": "country_of_origin",
                    "raw": None,
                    "norm": None,
                    "unit": None,
                    "currency": None,
                    "conf": 0.0,
                    "src": None,
                    "bbox": None,
                    "status": "NOT_DETECTED",
                },
                {
                    "field": "importer_name",
                    "canonical": "importer_name",
                    "raw": "Imported & Distributed by: EuroConfect India Pvt Ltd",
                    "norm": "EuroConfect India Pvt Ltd",
                    "unit": None,
                    "currency": None,
                    "conf": 0.93,
                    "src": "Imported & Distributed by: EuroConfect India Pvt Ltd",
                    "bbox": [80, 680, 710, 720],
                    "status": "DETECTED",
                },
            ],
            "results": [
                {
                    "rule": "RULE-001",
                    "field": "mrp",
                    "detected": None,
                    "required": "Required on all packaged commodities",
                    "status": "VIOLATION",
                    "reason": (
                        "MRP declaration was not detected on any supplied panel of the package. "
                        "Rule 6(1)(e) mandates retail sale price on every packaged commodity."
                    ),
                    "evidence_text": None,
                    "legal_rule": "Rule 6(1)(e)",
                },
                {
                    "rule": "RULE-009",
                    "field": "country_of_origin",
                    "detected": None,
                    "required": "Required for all imported packaged commodities",
                    "status": "VIOLATION",
                    "reason": (
                        "Package declares importer ('EuroConfect India Pvt Ltd') indicating an "
                        "imported commodity, but no Country of Origin declaration was found, "
                        "violating Rule 6(1)(f)."
                    ),
                    "evidence_text": None,
                    "legal_rule": "Rule 6(1)(f)",
                },
                {
                    "rule": "RULE-002",
                    "field": "net_quantity",
                    "detected": "100 g",
                    "required": "Required",
                    "status": "PASS",
                    "reason": "Net quantity declared in standard SI unit (g).",
                    "evidence_text": "100g e",
                    "legal_rule": "Rule 6(1)(b)",
                },
            ],
        },
    ]

    for demo in demos:
        inspection_id = str(uuid.uuid4())
        product_id = str(uuid.uuid4())

        # 1. Insert inspection
        cur.execute(
            """
            INSERT INTO inspections (
                id, inspector_id, title, description, product_category,
                status, overall_result, notes, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                inspection_id,
                user_id,
                demo["title"],
                f"Demonstration inspection for SIH 2026: {demo['title']}",
                demo["category"],
                demo["status"],
                demo["overall_result"],
                demo["notes"],
                now,
                now,
            ),
        )

        # 2. Insert dummy image record
        image_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO inspection_images (
                id, inspection_id, original_path, image_type,
                file_name, file_size, mime_type, width, height, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                image_id,
                inspection_id,
                f"uploads/{inspection_id}/front.jpg",
                "front",
                "front.jpg",
                245760,
                "image/jpeg",
                1200,
                800,
                now,
            ),
        )

        # 3. Insert product
        cur.execute(
            """
            INSERT INTO products (
                id, inspection_id, product_name, brand, category,
                extraction_confidence, extraction_model, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                product_id,
                inspection_id,
                demo["product_name"],
                demo["brand"],
                demo["category"],
                0.93,
                "gemini-2.0-flash",
                now,
                now,
            ),
        )

        # 4. Insert product fields
        for f in demo["fields"]:
            field_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO product_fields (
                    id, product_id, field_name, canonical_name,
                    raw_value, normalized_value, unit, currency,
                    confidence, source_text, bbox, image_id,
                    status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    field_id,
                    product_id,
                    f["field"],
                    f["canonical"],
                    f["raw"],
                    f["norm"],
                    f["unit"],
                    f["currency"],
                    f["conf"],
                    f["src"],
                    json.dumps(f["bbox"]) if f["bbox"] else None,
                    image_id if f["bbox"] else None,
                    f["status"],
                    now,
                ),
            )

        # 5. Insert compliance results & evidence
        for r in demo["results"]:
            cr_id = str(uuid.uuid4())
            ev_id = str(uuid.uuid4())
            db_rule_id = rule_map.get(r["rule"])

            if not db_rule_id:
                print(f"  [WARN] Rule {r['rule']} not in DB, skipping result.")
                continue

            # Evidence first
            cur.execute(
                """
                INSERT INTO evidence (
                    id, image_id, bbox, source_text, ocr_confidence,
                    legal_document, legal_rule, legal_page, legal_text, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ev_id,
                    image_id if r["evidence_text"] else None,
                    None,
                    r["evidence_text"],
                    0.95 if r["evidence_text"] else None,
                    "Legal Metrology (Packaged Commodities) Rules, 2011",
                    r["legal_rule"],
                    None,
                    f"Requirement under {r['legal_rule']}: every package shall bear mandatory declaration.",
                    now,
                ),
            )

            # Compliance result
            cur.execute(
                """
                INSERT INTO compliance_results (
                    id, inspection_id, rule_id, field_name,
                    detected_value, required_value, status,
                    reason, confidence, evidence_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    cr_id,
                    inspection_id,
                    db_rule_id,
                    r["field"],
                    r["detected"],
                    r["required"],
                    r["status"],
                    r["reason"],
                    0.95,
                    ev_id,
                    now,
                ),
            )

            # Back-link evidence to compliance_result
            cur.execute(
                "UPDATE evidence SET compliance_result_id = %s WHERE id = %s",
                (cr_id, ev_id),
            )

        conn.commit()
        print(f"  Demo inspection created: [{demo['overall_result']}] {demo['title']}")


def main():
    print("=" * 60)
    print("Seeding Demo Data for Legal Metrology System")
    print("=" * 60)
    print(f"Database: {DATABASE_URL}\n")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Connected to PostgreSQL.\n")
    except Exception as exc:
        print(f"ERROR: Could not connect to database: {exc}")
        print("Ensure PostgreSQL is running and tables are initialized.")
        sys.exit(1)

    try:
        print("--- Step 1: Demo Inspector User ---")
        user_id = seed_demo_user(conn)

        print("\n--- Step 2: Fetching Compliance Rules ---")
        rule_map = get_rule_id_map(conn)
        print(f"  Found {len(rule_map)} compliance rules in database.")
        if not rule_map:
            print("  [WARN] No compliance rules found! Run seed_compliance_rules.py first.")

        print("\n--- Step 3: Demo Inspections (PASS, REVIEW, VIOLATION) ---")
        seed_demo_inspections(conn, user_id, rule_map)

        print("\nDemo data seeding completed successfully.")
        print("Log in with: inspector@example.com / password123")
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
