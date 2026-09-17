"""Import all models so Alembic and Base.metadata see them."""

from app.models.models import (  # noqa: F401
    ComplianceResult,
    ComplianceRule,
    Evidence,
    FieldRuleMapping,
    Inspection,
    InspectionImage,
    OCRResult,
    Product,
    ProductField,
    Regulation,
    RegulationChunk,
    Report,
    User,
)
