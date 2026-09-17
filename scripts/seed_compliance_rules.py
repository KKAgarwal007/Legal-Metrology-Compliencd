"""
Seed Compliance Rules for Legal Metrology (Packaged Commodities) Rules, 2011.

Seeds the compliance_rules and field_rule_mappings tables with initial rules
derived from the Legal Metrology (Packaged Commodities) Rules, 2011.

Usage:
    python scripts/seed_compliance_rules.py

Requires:
    - PostgreSQL running with the legal_metrology database
    - Tables created via scripts/init_db.sql
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/legal_metrology",
)

RULES = [
    {
        "rule_id": "RULE-001",
        "field": "mrp",
        "canonical_field": "maximum_retail_price",
        "requirement_type": "required",
        "requirement_value": None,
        "description": "Every package shall bear the retail sale price of the package.",
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(e)",
        "source_page": None,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-002",
        "field": "net_quantity",
        "canonical_field": "net_quantity",
        "requirement_type": "required",
        "requirement_value": None,
        "description": (
            "Every package shall bear the net quantity of the commodity "
            "in terms of standard unit of weight or measure."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(b)",
        "source_page": None,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-003",
        "field": "manufacturer_name",
        "canonical_field": "manufacturer_name",
        "requirement_type": "required",
        "requirement_value": None,
        "description": (
            "Every package shall bear the name and address of the "
            "manufacturer or packer or importer."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(a)",
        "source_page": None,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-004",
        "field": "manufacturer_address",
        "canonical_field": "manufacturer_address",
        "requirement_type": "required",
        "requirement_value": None,
        "description": (
            "The address of the manufacturer or packer or importer "
            "shall be declared on the package."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(a)",
        "source_page": None,
        "severity": "major",
    },
    {
        "rule_id": "RULE-005",
        "field": "product_name",
        "canonical_field": "common_or_generic_name",
        "requirement_type": "required",
        "requirement_value": None,
        "description": "Every package shall bear the common or generic name of the commodity.",
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(a)",
        "source_page": None,
        "severity": "critical",
    },
    {
        "rule_id": "RULE-006",
        "field": "manufacturing_date",
        "canonical_field": "date_of_manufacture_or_packing",
        "requirement_type": "required",
        "requirement_value": None,
        "description": (
            "Every package shall declare the month and year of manufacture "
            "or packing or import."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(d)",
        "source_page": None,
        "severity": "major",
    },
    {
        "rule_id": "RULE-007",
        "field": "best_before",
        "canonical_field": "best_before_or_use_by",
        "requirement_type": "conditional",
        "requirement_value": {"condition": "perishable_commodity", "then": "required"},
        "description": (
            "Best before or use by date is required for commodities "
            "where it is applicable."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(d)",
        "source_page": None,
        "severity": "major",
    },
    {
        "rule_id": "RULE-008",
        "field": "consumer_care_info",
        "canonical_field": "consumer_care_details",
        "requirement_type": "required",
        "requirement_value": None,
        "description": "Every package shall bear customer care details.",
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(2)",
        "source_page": None,
        "severity": "minor",
    },
    {
        "rule_id": "RULE-009",
        "field": "country_of_origin",
        "canonical_field": "country_of_origin",
        "requirement_type": "conditional",
        "requirement_value": {"condition": "imported_commodity", "then": "required"},
        "description": (
            "In case of imported package, the country of origin shall be mentioned."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(f)",
        "source_page": None,
        "severity": "major",
    },
    {
        "rule_id": "RULE-010",
        "field": "mrp_inclusive",
        "canonical_field": "mrp_includes_all_taxes",
        "requirement_type": "required",
        "requirement_value": None,
        "description": (
            "The retail sale price shall be the maximum price inclusive of all taxes "
            "at which the package may be sold to the ultimate consumer."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 2(l)",
        "source_page": None,
        "severity": "major",
    },
    {
        "rule_id": "RULE-011",
        "field": "batch_number",
        "canonical_field": "batch_lot_code",
        "requirement_type": "required",
        "requirement_value": None,
        "description": (
            "The batch number or lot number or code number shall be "
            "mentioned on every package."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 6(1)(c)",
        "source_page": None,
        "severity": "major",
    },
    {
        "rule_id": "RULE-012",
        "field": "net_quantity_unit",
        "canonical_field": "net_quantity_standard_unit",
        "requirement_type": "required",
        "requirement_value": None,
        "description": (
            "Net quantity shall be expressed in terms of standard units "
            "of weights and measures."
        ),
        "applicability": {"category": "packaged_commodity"},
        "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "source_rule": "Rule 5",
        "source_page": None,
        "severity": "major",
    },
]


def get_connection():
    """Create a psycopg2 connection from DATABASE_URL."""
    return psycopg2.connect(DATABASE_URL)


def seed_compliance_rules(conn):
    """Insert or update compliance rules."""
    cur = conn.cursor()
    inserted = 0
    updated = 0

    for rule in RULES:
        rule_uuid = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Check if rule already exists
        cur.execute(
            "SELECT id FROM compliance_rules WHERE rule_id = %s",
            (rule["rule_id"],),
        )
        existing = cur.fetchone()

        if existing:
            # Update existing rule
            cur.execute(
                """
                UPDATE compliance_rules SET
                    field = %s,
                    canonical_field = %s,
                    requirement_type = %s,
                    requirement_value = %s,
                    description = %s,
                    applicability = %s,
                    source_document = %s,
                    source_rule = %s,
                    source_page = %s,
                    severity = %s
                WHERE rule_id = %s
                RETURNING id
                """,
                (
                    rule["field"],
                    rule["canonical_field"],
                    rule["requirement_type"],
                    json.dumps(rule["requirement_value"]) if rule["requirement_value"] else None,
                    rule["description"],
                    json.dumps(rule["applicability"]) if rule.get("applicability") else None,
                    rule["source_document"],
                    rule["source_rule"],
                    rule["source_page"],
                    rule["severity"],
                    rule["rule_id"],
                ),
            )
            db_rule_id = existing[0]
            updated += 1
            print(f"  Updated: {rule['rule_id']} — {rule['field']}")
        else:
            # Insert new rule
            cur.execute(
                """
                INSERT INTO compliance_rules (
                    id, rule_id, field, canonical_field, requirement_type,
                    requirement_value, description, applicability,
                    source_document, source_rule, source_page,
                    is_active, severity, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    rule_uuid,
                    rule["rule_id"],
                    rule["field"],
                    rule["canonical_field"],
                    rule["requirement_type"],
                    json.dumps(rule["requirement_value"]) if rule["requirement_value"] else None,
                    rule["description"],
                    json.dumps(rule["applicability"]) if rule.get("applicability") else None,
                    rule["source_document"],
                    rule["source_rule"],
                    rule["source_page"],
                    True,
                    rule["severity"],
                    now,
                ),
            )
            db_rule_id = rule_uuid
            inserted += 1
            print(f"  Inserted: {rule['rule_id']} — {rule['field']}")

    conn.commit()
    print(f"\nCompliance rules: {inserted} inserted, {updated} updated.")
    return cur


def seed_field_rule_mappings(conn):
    """Create field_rule_mappings connecting field names to compliance rules."""
    cur = conn.cursor()

    # Remove old mappings to avoid duplicates
    cur.execute("DELETE FROM field_rule_mappings")

    count = 0
    for rule in RULES:
        # Look up the compliance_rules row by rule_id
        cur.execute(
            "SELECT id FROM compliance_rules WHERE rule_id = %s",
            (rule["rule_id"],),
        )
        row = cur.fetchone()
        if not row:
            print(f"  WARNING: rule {rule['rule_id']} not found — skipping mapping")
            continue

        cr_id = row[0]
        mapping_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        cur.execute(
            """
            INSERT INTO field_rule_mappings (
                id, field_name, canonical_field, rule_id, priority, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                mapping_id,
                rule["field"],
                rule["canonical_field"],
                cr_id,
                1,
                now,
            ),
        )
        count += 1

    conn.commit()
    print(f"Field-rule mappings: {count} created.")


def main():
    print("=" * 60)
    print("Seeding Compliance Rules")
    print("Legal Metrology (Packaged Commodities) Rules, 2011")
    print("=" * 60)
    print(f"\nDatabase: {DATABASE_URL}\n")

    try:
        conn = get_connection()
        print("Connected to database.\n")
    except Exception as exc:
        print(f"ERROR: Could not connect to database: {exc}")
        print("Ensure PostgreSQL is running and the database exists.")
        sys.exit(1)

    try:
        print("--- Compliance Rules ---")
        seed_compliance_rules(conn)
        print()
        print("--- Field-Rule Mappings ---")
        seed_field_rule_mappings(conn)
        print()
        print("Done.")
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
