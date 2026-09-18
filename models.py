"""
Database models for the Legal Metrology Compliance Checker.

Tables:
    User        - enforcement officials / admins (role-based access)
    Product     - a logical packaged-commodity record (can have many scans
                  over time, e.g. re-inspection of the same SKU)
    Scan        - one image-scan event, with extracted text, OCR metadata,
                  computed compliance score and a link to the generated PDF
    Violation   - individual rule violations found in a Scan
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="inspector")  # 'inspector' | 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(255))
    category = db.Column(db.String(120))          # e.g. food, cosmetics, electronics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scans = db.relationship("Scan", backref="product", lazy=True,
                             cascade="all, delete-orphan")


class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    inspector_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    image_path = db.Column(db.String(400), nullable=False)
    raw_ocr_text = db.Column(db.Text)
    extracted_fields_json = db.Column(db.Text)     # JSON dump of extracted declarations
    min_font_height_mm = db.Column(db.Float)        # smallest detected declaration text height
    compliance_score = db.Column(db.Float)           # 0-100
    status = db.Column(db.String(20))                 # 'compliant' | 'non_compliant' | 'review'
    report_path = db.Column(db.String(400))            # generated PDF path
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    inspector = db.relationship("User")
    violations = db.relationship("Violation", backref="scan", lazy=True,
                                  cascade="all, delete-orphan")

    @property
    def image_filename(self):
        import os
        return os.path.basename(self.image_path) if self.image_path else ""


class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scan.id"), nullable=False)
    rule_code = db.Column(db.String(50))         # e.g. 'LM-R6-NETQTY'
    field = db.Column(db.String(80))             # e.g. 'net_quantity'
    description = db.Column(db.String(500))
    severity = db.Column(db.String(20))          # 'critical' | 'major' | 'minor'
