"""Pydantic v2 schemas for request/response validation."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Helpers ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    database: str = "connected"


class ProcessingStage(BaseModel):
    name: str
    status: str = "pending"  # pending, running, completed, failed
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingStatus(BaseModel):
    inspection_id: UUID
    status: str
    stages: List[ProcessingStage]
    current_stage: Optional[str] = None
    progress_pct: float = 0.0


# ── Users ────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "inspector"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Inspections ──────────────────────────────────────────────────────────────

class InspectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    product_category: Optional[str] = None
    notes: Optional[str] = None


class InspectionCreate(InspectionBase):
    inspector_id: Optional[UUID] = None


class InspectionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    product_category: Optional[str] = None
    status: Optional[str] = None
    overall_result: Optional[str] = None
    notes: Optional[str] = None


class InspectionResponse(InspectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    inspector_id: Optional[UUID] = None
    status: str
    overall_result: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    image_count: Optional[int] = None


class InspectionDetailResponse(InspectionResponse):
    images: List["ImageUploadResponse"] = []
    product: Optional["ProductResponse"] = None
    compliance_results: List["ComplianceResultResponse"] = []


class InspectionListResponse(BaseModel):
    items: List[InspectionResponse]
    total: int
    page: int
    page_size: int


# ── Images ───────────────────────────────────────────────────────────────────

class ImageUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    inspection_id: UUID
    original_path: str
    processed_path: Optional[str] = None
    ocr_visualization_path: Optional[str] = None
    image_type: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime


# ── OCR ──────────────────────────────────────────────────────────────────────

class OCRResultBase(BaseModel):
    text: str
    confidence: float
    bbox: List[float]
    page: int = 1
    confidence_category: Optional[str] = None


class OCRResultResponse(OCRResultBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    image_id: UUID
    is_corrected: bool = False
    corrected_text: Optional[str] = None
    corrected_by: Optional[UUID] = None
    corrected_at: Optional[datetime] = None
    created_at: datetime


class OCRCorrectionRequest(BaseModel):
    corrected_text: str
    corrected_by: Optional[UUID] = None


# ── Products ─────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    inspection_id: UUID
    raw_extraction: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[float] = None
    extraction_model: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    fields: List["ProductFieldResponse"] = []


# ── Product Fields ───────────────────────────────────────────────────────────

class ProductFieldBase(BaseModel):
    field_name: str
    canonical_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    confidence: Optional[float] = None
    source_text: Optional[str] = None
    bbox: Optional[List[float]] = None
    status: str = "DETECTED"


class ProductFieldResponse(ProductFieldBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    image_id: Optional[UUID] = None
    original_value: Optional[str] = None
    corrected_by: Optional[UUID] = None
    corrected_at: Optional[datetime] = None
    created_at: datetime


class ProductFieldUpdate(BaseModel):
    """Manual correction of an extracted field."""
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    corrected_by: Optional[UUID] = None


# ── Compliance Rules ─────────────────────────────────────────────────────────

class ComplianceRuleBase(BaseModel):
    rule_id: str
    field: str
    canonical_field: str
    requirement_type: str
    requirement_value: Optional[Dict[str, Any]] = None
    description: str
    applicability: Optional[Dict[str, Any]] = None
    source_document: Optional[str] = None
    source_rule: Optional[str] = None
    source_page: Optional[int] = None
    severity: str = "major"


class ComplianceRuleResponse(ComplianceRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
    created_at: datetime


# ── Compliance Results ───────────────────────────────────────────────────────

class ComplianceResultBase(BaseModel):
    field_name: str
    detected_value: Optional[str] = None
    required_value: Optional[str] = None
    status: str  # PASS, REVIEW, VIOLATION, NOT_APPLICABLE
    reason: str
    confidence: Optional[float] = None


class ComplianceResultResponse(ComplianceResultBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    inspection_id: UUID
    rule_id: UUID
    evidence_id: Optional[UUID] = None
    created_at: datetime
    rule: Optional[ComplianceRuleResponse] = None
    evidence: Optional["EvidenceResponse"] = None


# ── Evidence ─────────────────────────────────────────────────────────────────

class EvidenceBase(BaseModel):
    bbox: Optional[List[float]] = None
    source_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    legal_document: Optional[str] = None
    legal_rule: Optional[str] = None
    legal_page: Optional[int] = None
    legal_text: Optional[str] = None


class EvidenceResponse(EvidenceBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    compliance_result_id: Optional[UUID] = None
    image_id: Optional[UUID] = None
    created_at: datetime


# ── Reports ──────────────────────────────────────────────────────────────────

class ReportBase(BaseModel):
    report_type: str = "full"


class ReportResponse(ReportBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    inspection_id: UUID
    file_path: Optional[str] = None
    report_data: Optional[Dict[str, Any]] = None
    generated_at: datetime
    report_hash: Optional[str] = None
    created_at: datetime


# ── Regulations ──────────────────────────────────────────────────────────────

class RegulationBase(BaseModel):
    document_name: str
    version: Optional[str] = None
    effective_date: Optional[date] = None
    source_url: Optional[str] = None


class RegulationResponse(RegulationBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    file_path: Optional[str] = None
    total_pages: Optional[int] = None
    is_processed: bool
    created_at: datetime


class RegulationChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    regulation_id: UUID
    chunk_index: int
    text: str
    section: Optional[str] = None
    rule: Optional[str] = None
    page: Optional[int] = None
    created_at: datetime


# ── RAG ──────────────────────────────────────────────────────────────────────

class RAGSearchQuery(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None  # e.g. {"section": "Rule 6"}


class RAGSearchResult(BaseModel):
    chunk_id: UUID
    document: str
    rule: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    text: str
    similarity: float


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResult]
    total: int


# ── Dashboard ──────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_inspections: int
    compliant: int
    review_required: int
    violations: int
    recent_inspections: List[InspectionResponse]


# ── Rebuild forward refs ─────────────────────────────────────────────────────

InspectionDetailResponse.model_rebuild()
ProductResponse.model_rebuild()
ComplianceResultResponse.model_rebuild()
