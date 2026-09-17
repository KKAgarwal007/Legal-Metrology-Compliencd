"""SQLAlchemy ORM models for the Legal Metrology Compliance System."""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="inspector", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    inspections = relationship("Inspection", back_populates="inspector")


# ---------------------------------------------------------------------------
# Inspections
# ---------------------------------------------------------------------------
class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    product_category = Column(String(100), nullable=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    overall_result = Column(String(20), nullable=True)  # PASS, REVIEW, VIOLATION
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    inspector = relationship("User", back_populates="inspections")
    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    product = relationship("Product", back_populates="inspection", uselist=False, cascade="all, delete-orphan")
    compliance_results = relationship("ComplianceResult", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Inspection Images
# ---------------------------------------------------------------------------
class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    original_path = Column(String(1000), nullable=False)
    processed_path = Column(String(1000), nullable=True)
    ocr_visualization_path = Column(String(1000), nullable=True)
    image_type = Column(String(20), default="front", nullable=False)  # front, back, side, top, bottom, label
    file_name = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    inspection = relationship("Inspection", back_populates="images")
    ocr_results = relationship("OCRResult", back_populates="image", cascade="all, delete-orphan")
    product_fields = relationship("ProductField", back_populates="source_image")
    evidence_items = relationship("Evidence", back_populates="image")


# ---------------------------------------------------------------------------
# OCR Results
# ---------------------------------------------------------------------------
class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    image_id = Column(UUID(as_uuid=True), ForeignKey("inspection_images.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox = Column(JSONB, nullable=False)  # [x1, y1, x2, y2]
    page = Column(Integer, default=1, nullable=False)
    confidence_category = Column(String(10), nullable=True)  # HIGH, MEDIUM, LOW
    is_corrected = Column(Boolean, default=False, nullable=False)
    corrected_text = Column(Text, nullable=True)
    corrected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    corrected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    image = relationship("InspectionImage", back_populates="ocr_results")
    corrector = relationship("User", foreign_keys=[corrected_by])

    __table_args__ = (
        Index("ix_ocr_results_confidence", "confidence"),
    )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    raw_extraction = Column(JSONB, nullable=True)
    product_name = Column(String(500), nullable=True)
    brand = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    extraction_confidence = Column(Float, nullable=True)
    extraction_model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    inspection = relationship("Inspection", back_populates="product")
    fields = relationship("ProductField", back_populates="product", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Product Fields
# ---------------------------------------------------------------------------
class ProductField(Base):
    __tablename__ = "product_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    canonical_name = Column(String(100), nullable=False, index=True)
    raw_value = Column(String(1000), nullable=True)
    normalized_value = Column(String(1000), nullable=True)
    unit = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    confidence = Column(Float, nullable=True)
    source_text = Column(String(2000), nullable=True)
    bbox = Column(JSONB, nullable=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey("inspection_images.id"), nullable=True)
    status = Column(String(30), default="DETECTED", nullable=False)  # DETECTED, NOT_DETECTED, AMBIGUOUS, LOW_CONFIDENCE, MANUALLY_CORRECTED
    original_value = Column(String(1000), nullable=True)
    corrected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    corrected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="fields")
    source_image = relationship("InspectionImage", back_populates="product_fields")
    corrector = relationship("User", foreign_keys=[corrected_by])

    __table_args__ = (
        Index("ix_product_fields_field_name", "field_name"),
    )


# ---------------------------------------------------------------------------
# Regulations
# ---------------------------------------------------------------------------
class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    document_name = Column(String(500), nullable=False)
    version = Column(String(100), nullable=True)
    effective_date = Column(Date, nullable=True)
    source_url = Column(String(1000), nullable=True)
    file_path = Column(String(1000), nullable=True)
    total_pages = Column(Integer, nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    chunks = relationship("RegulationChunk", back_populates="regulation", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Regulation Chunks (with pgvector embeddings)
# ---------------------------------------------------------------------------
class RegulationChunk(Base):
    __tablename__ = "regulation_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    regulation_id = Column(UUID(as_uuid=True), ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    section = Column(String(200), nullable=True)
    rule = Column(String(200), nullable=True)
    page = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    regulation = relationship("Regulation", back_populates="chunks")

    __table_args__ = (
        Index("ix_regulation_chunks_section", "section"),
        Index("ix_regulation_chunks_rule", "rule"),
    )


# ---------------------------------------------------------------------------
# Compliance Rules
# ---------------------------------------------------------------------------
class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    rule_id = Column(String(50), unique=True, nullable=False, index=True)
    field = Column(String(100), nullable=False)
    canonical_field = Column(String(100), nullable=False, index=True)
    requirement_type = Column(String(50), nullable=False)  # required, not_empty, equals, etc.
    requirement_value = Column(JSONB, nullable=True)
    description = Column(Text, nullable=False)
    applicability = Column(JSONB, nullable=True)
    source_document = Column(String(500), nullable=True)
    source_rule = Column(String(200), nullable=True)
    source_page = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    severity = Column(String(20), default="major", nullable=False)  # critical, major, minor
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    field_mappings = relationship("FieldRuleMapping", back_populates="rule", cascade="all, delete-orphan")
    compliance_results = relationship("ComplianceResult", back_populates="rule")


# ---------------------------------------------------------------------------
# Field ↔ Rule Mappings
# ---------------------------------------------------------------------------
class FieldRuleMapping(Base):
    __tablename__ = "field_rule_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    field_name = Column(String(100), nullable=False, index=True)
    canonical_field = Column(String(100), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("compliance_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    rule = relationship("ComplianceRule", back_populates="field_mappings")


# ---------------------------------------------------------------------------
# Compliance Results
# ---------------------------------------------------------------------------
class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("compliance_rules.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    detected_value = Column(String(1000), nullable=True)
    required_value = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False)  # PASS, REVIEW, VIOLATION, NOT_APPLICABLE
    reason = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    inspection = relationship("Inspection", back_populates="compliance_results")
    rule = relationship("ComplianceRule", back_populates="compliance_results")
    evidence = relationship("Evidence", foreign_keys=[evidence_id], back_populates="compliance_result")

    __table_args__ = (
        Index("ix_compliance_results_status", "status"),
    )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------
class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    compliance_result_id = Column(UUID(as_uuid=True), ForeignKey("compliance_results.id"), nullable=True, index=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey("inspection_images.id"), nullable=True, index=True)
    bbox = Column(JSONB, nullable=True)
    source_text = Column(String(2000), nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    legal_document = Column(String(500), nullable=True)
    legal_rule = Column(String(200), nullable=True)
    legal_page = Column(Integer, nullable=True)
    legal_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    compliance_result = relationship("ComplianceResult", foreign_keys=[compliance_result_id], back_populates="evidence")
    image = relationship("InspectionImage", back_populates="evidence_items")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), default="full", nullable=False)
    file_path = Column(String(1000), nullable=True)
    report_data = Column(JSONB, nullable=True)
    generated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    report_hash = Column(String(64), nullable=True)  # SHA-256
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    inspection = relationship("Inspection", back_populates="reports")
