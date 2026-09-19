"""FastAPI router defining all API endpoints for the Legal Metrology Compliance System."""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.database.session import get_db
from app.services.ocr import ocr_service, preprocess_image, draw_ocr_boxes
from app.services.extraction import extract_product_declarations
from app.services.compliance import evaluate_compliance, DeterministicRuleEngine
from app.services.compliance.rule_engine import DEFAULT_LEGAL_METROLOGY_RULES
from app.services.rag import search_legal_regulations, ingest_pdf_regulation
from app.services.reporting import generate_report_data, render_html_report, export_report_pdf, compute_sha256_signature
from app.models.models import (
    ComplianceResult,
    ComplianceRule,
    Evidence,
    Inspection,
    InspectionImage,
    OCRResult,
    Product,
    ProductField,
    Regulation,
    Report,
)
from app.schemas.schemas import (
    ComplianceResultResponse,
    DashboardStats,
    EvidenceResponse,
    HealthResponse,
    ImageUploadResponse,
    InspectionCreate,
    InspectionDetailResponse,
    InspectionListResponse,
    InspectionResponse,
    InspectionUpdate,
    OCRCorrectionRequest,
    OCRResultResponse,
    ProcessingStatus,
    ProductFieldResponse,
    ProductFieldUpdate,
    ProductResponse,
    RAGSearchQuery,
    RAGSearchResponse,
    RAGSearchResult,
    RegulationResponse,
    ReportResponse,
)
from app.utils.file_utils import (
    generate_file_hash,
    save_upload,
    validate_image_file,
)

router = APIRouter(prefix="/api")


# ===========================================================================
# Health
# ===========================================================================
@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check API and database health."""
    db_status = "connected"
    try:
        await db.execute(select(func.now()))
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        version=settings.app_version,
        database=db_status,
    )


@router.get(
    "/dashboard/stats",
    response_model=DashboardStats,
    tags=["Dashboard"],
)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics including counts and recent inspections."""
    # Total inspections
    total_result = await db.execute(select(func.count(Inspection.id)))
    total_inspections = total_result.scalar_one()

    # Compliant (PASS)
    compliant_result = await db.execute(
        select(func.count(Inspection.id)).where(Inspection.overall_result == "PASS")
    )
    compliant = compliant_result.scalar_one()

    # Review required
    review_result = await db.execute(
        select(func.count(Inspection.id)).where(Inspection.overall_result == "REVIEW")
    )
    review_required = review_result.scalar_one()

    # Violations
    violations_result = await db.execute(
        select(func.count(Inspection.id)).where(Inspection.overall_result == "VIOLATION")
    )
    violations = violations_result.scalar_one()

    # Recent inspections (last 5)
    recent_query = (
        select(Inspection)
        .order_by(Inspection.created_at.desc())
        .limit(5)
    )
    recent_result = await db.execute(recent_query)
    recent_inspections = list(recent_result.scalars().all())

    return DashboardStats(
        total_inspections=total_inspections,
        compliant=compliant,
        review_required=review_required,
        violations=violations,
        recent_inspections=recent_inspections,
    )


# ===========================================================================
# Inspections CRUD
# ===========================================================================
@router.post(
    "/inspections",
    response_model=InspectionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Inspections"],
)
async def create_inspection(
    payload: InspectionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new inspection record."""
    inspection = Inspection(
        id=uuid.uuid4(),
        title=payload.title,
        description=payload.description,
        product_category=payload.product_category,
        notes=payload.notes,
        inspector_id=payload.inspector_id,
        status="pending",
    )
    db.add(inspection)
    await db.flush()
    await db.refresh(inspection)
    return inspection


@router.get(
    "/inspections",
    response_model=InspectionListResponse,
    tags=["Inspections"],
)
async def list_inspections(
    page: int = Query(1, ge=1),
    page_size: Optional[int] = Query(None),
    limit: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    verdict_filter: Optional[str] = Query(None, alias="overall_result"),
    category: Optional[str] = Query(None),
    inspector_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List inspections with pagination, search, category, and inspector filters."""
    effective_limit = limit or page_size or 10
    effective_limit = max(1, min(100, effective_limit))

    query = select(Inspection)
    total_query = select(func.count(Inspection.id))

    if status_filter and status_filter != "ALL":
        query = query.where(Inspection.status == status_filter)
        total_query = total_query.where(Inspection.status == status_filter)

    if verdict_filter and verdict_filter != "ALL":
        query = query.where(Inspection.overall_result == verdict_filter)
        total_query = total_query.where(Inspection.overall_result == verdict_filter)

    if category and category != "ALL":
        query = query.where(Inspection.product_category == category)
        total_query = total_query.where(Inspection.product_category == category)

    if inspector_id and inspector_id not in ("ALL", "all", "my"):
        try:
            insp_uuid = UUID(inspector_id)
            query = query.where(Inspection.inspector_id == insp_uuid)
            total_query = total_query.where(Inspection.inspector_id == insp_uuid)
        except (ValueError, TypeError):
            pass

    if search and search.strip():
        term = f"%{search.strip()}%"
        search_clause = (
            Inspection.title.ilike(term)
            | Inspection.description.ilike(term)
            | Inspection.product_category.ilike(term)
        )
        query = query.where(search_clause)
        total_query = total_query.where(search_clause)

    total_result = await db.execute(total_query)
    total = total_result.scalar_one()

    offset = (page - 1) * effective_limit
    query = query.order_by(Inspection.created_at.desc()).offset(offset).limit(effective_limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return InspectionListResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=effective_limit,
    )


@router.get(
    "/inspections/{inspection_id}",
    response_model=InspectionDetailResponse,
    tags=["Inspections"],
)
async def get_inspection(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full inspection details including images, product fields, and results."""
    query = (
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(
            selectinload(Inspection.images),
            selectinload(Inspection.product).selectinload(Product.fields),
            selectinload(Inspection.compliance_results).selectinload(ComplianceResult.rule),
            selectinload(Inspection.compliance_results).selectinload(ComplianceResult.evidence),
        )
    )
    result = await db.execute(query)
    inspection = result.scalar_one_or_none()

    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found.",
        )
    return inspection


# ===========================================================================
# Images
# ===========================================================================
@router.post(
    "/inspections/{inspection_id}/images",
    response_model=List[ImageUploadResponse],
    status_code=status.HTTP_201_CREATED,
    tags=["Images"],
)
async def upload_inspection_images(
    inspection_id: UUID,
    files: List[UploadFile] = File(...),
    image_types: Optional[List[str]] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Upload one or more product images for an inspection."""
    # Verify inspection exists
    insp_result = await db.execute(
        select(Inspection).where(Inspection.id == inspection_id)
    )
    if not insp_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found.",
        )

    upload_dir = os.path.join(settings.upload_dir, str(inspection_id), "original")
    saved_images: List[InspectionImage] = []

    for idx, file in enumerate(files):
        await validate_image_file(file)
        saved_path = await save_upload(file, upload_dir)
        img_type = "front"
        if image_types and idx < len(image_types):
            img_type = image_types[idx]

        file_size = os.path.getsize(saved_path) if os.path.exists(saved_path) else None

        img_record = InspectionImage(
            id=uuid.uuid4(),
            inspection_id=inspection_id,
            original_path=saved_path,
            image_type=img_type,
            file_name=file.filename or "unknown.jpg",
            file_size=file_size,
            mime_type=file.content_type,
        )
        db.add(img_record)
        saved_images.append(img_record)

    await db.flush()
    for img in saved_images:
        await db.refresh(img)

    return saved_images


# ===========================================================================
# Pipeline Stages
# ===========================================================================
@router.post(
    "/ocr/{inspection_id}",
    response_model=List[OCRResultResponse],
    tags=["Pipeline"],
)
async def run_ocr(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Execute OCR (PaddleOCR with Tesseract fallback) on inspection images."""
    # Verify inspection
    insp_result = await db.execute(
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(selectinload(Inspection.images))
    )
    inspection = insp_result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    if not inspection.images:
        raise HTTPException(status_code=400, detail="No images found for this inspection.")

    new_ocr_records: List[OCRResult] = []

    for image in inspection.images:
        orig_path = image.original_path
        if not os.path.exists(orig_path):
            continue

        # 1. Preprocessing
        proc_dir = os.path.join(settings.upload_dir, str(inspection_id), "processed")
        vis_dir = os.path.join(settings.upload_dir, str(inspection_id), "visualization")
        os.makedirs(proc_dir, exist_ok=True)
        os.makedirs(vis_dir, exist_ok=True)

        proc_filename = f"proc_{os.path.basename(orig_path)}"
        proc_path = os.path.join(proc_dir, proc_filename)
        vis_filename = f"vis_{os.path.basename(orig_path)}"
        vis_path = os.path.join(vis_dir, vis_filename)

        try:
            preprocess_info = preprocess_image(orig_path, proc_path)
            image.processed_path = proc_path
            image.width = preprocess_info.get("width")
            image.height = preprocess_info.get("height")
        except Exception:
            proc_path = orig_path

        # 2. OCR extraction
        try:
            detections = ocr_service.extract_text_regions(proc_path)
        except Exception:
            detections = []

        # 3. Draw bounding boxes
        try:
            draw_ocr_boxes(proc_path, detections, vis_path)
            image.ocr_visualization_path = vis_path
        except Exception:
            pass

        # 4. Save OCR records
        for det in detections:
            ocr_record = OCRResult(
                id=uuid.uuid4(),
                image_id=image.id,
                text=det.get("text", ""),
                confidence=float(det.get("confidence", 0.0)),
                bbox=det.get("bbox", []),
                page=int(det.get("page", 1)),
                confidence_category=det.get("confidence_category", "LOW_CONFIDENCE"),
                is_corrected=False,
                created_at=datetime.now(timezone.utc),
            )
            db.add(ocr_record)
            new_ocr_records.append(ocr_record)

    await db.commit()
    return new_ocr_records


@router.post(
    "/extract/{inspection_id}",
    response_model=ProductResponse,
    tags=["Pipeline"],
)
async def run_extraction(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Extract structured fields from OCR results using multi-modal LLM / heuristic fallback."""
    insp_result = await db.execute(
        select(Inspection).where(Inspection.id == inspection_id)
    )
    inspection = insp_result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    # 1. Fetch all OCR results for this inspection
    ocr_query = (
        select(OCRResult)
        .join(InspectionImage)
        .where(InspectionImage.inspection_id == inspection_id)
    )
    ocr_rows = (await db.execute(ocr_query)).scalars().all()

    ocr_items = []
    for row in ocr_rows:
        text_val = row.corrected_text if row.is_corrected and row.corrected_text else row.text
        ocr_items.append({
            "text": text_val,
            "confidence": row.confidence,
            "bbox": row.bbox,
            "image_id": str(row.image_id),
            "confidence_category": row.confidence_category
        })

    # 2. Run extraction
    extraction_data = extract_product_declarations(
        ocr_items=ocr_items,
        product_category=inspection.product_category
    )

    # 3. Find or create Product record
    prod_query = (
        select(Product)
        .where(Product.inspection_id == inspection_id)
        .options(selectinload(Product.fields))
    )
    product = (await db.execute(prod_query)).scalar_one_or_none()

    if not product:
        product = Product(
            id=uuid.uuid4(),
            inspection_id=inspection_id,
            product_name=extraction_data.get("product_name"),
            brand=extraction_data.get("brand"),
            category=extraction_data.get("category") or inspection.product_category,
            raw_extraction=extraction_data.get("raw_extraction"),
            extraction_confidence=extraction_data.get("extraction_confidence", 0.85),
            extraction_model=extraction_data.get("extraction_model", "deterministic_extractor_v1")
        )
        db.add(product)
        await db.flush()
    else:
        product.product_name = extraction_data.get("product_name") or product.product_name
        product.brand = extraction_data.get("brand") or product.brand
        product.category = extraction_data.get("category") or product.category
        product.raw_extraction = extraction_data.get("raw_extraction")
        product.extraction_confidence = extraction_data.get("extraction_confidence", 0.85)

    # 4. Clear and recreate/update ProductFields
    # Delete old fields to avoid duplicates
    existing_fields_query = select(ProductField).where(ProductField.product_id == product.id)
    existing_fields = (await db.execute(existing_fields_query)).scalars().all()
    for f in existing_fields:
        await db.delete(f)
    await db.flush()

    # Insert new extracted fields
    raw_fields = extraction_data.get("fields", [])
    for field_dict in raw_fields:
        image_id_val = None
        if field_dict.get("image_id"):
            try:
                image_id_val = UUID(field_dict.get("image_id"))
            except (ValueError, TypeError):
                pass

        field_name_val = field_dict.get("field_name") or field_dict.get("field") or ""
        new_field = ProductField(
            id=uuid.uuid4(),
            product_id=product.id,
            field_name=field_name_val,
            canonical_name=field_dict.get("canonical_name", field_name_val),
            raw_value=field_dict.get("raw_value"),
            normalized_value=str(field_dict.get("normalized_value")) if field_dict.get("normalized_value") is not None else None,
            unit=field_dict.get("unit"),
            currency=field_dict.get("currency"),
            confidence=field_dict.get("confidence"),
            source_text=field_dict.get("source_text"),
            bbox=field_dict.get("bbox"),
            image_id=image_id_val,
            status=field_dict.get("status", "DETECTED")
        )
        db.add(new_field)

    await db.flush()

    # Re-query with eager fields
    refreshed = (await db.execute(
        select(Product)
        .where(Product.id == product.id)
        .options(selectinload(Product.fields))
    )).scalar_one()

    return refreshed


@router.post(
    "/compliance/{inspection_id}",
    response_model=List[ComplianceResultResponse],
    tags=["Pipeline"],
)
async def run_compliance(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Execute deterministic compliance checks against retrieved legal rules."""
    insp_result = await db.execute(
        select(Inspection).where(Inspection.id == inspection_id)
    )
    inspection = insp_result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    # 1. Fetch Product and its Fields
    prod_query = (
        select(Product)
        .where(Product.inspection_id == inspection_id)
        .options(selectinload(Product.fields))
    )
    product = (await db.execute(prod_query)).scalar_one_or_none()
    if not product:
        # If extraction hasn't run yet, run extraction first
        product = await run_extraction(inspection_id=inspection_id, db=db)

    # 2. Fetch all active compliance rules
    rules_query = select(ComplianceRule).where(ComplianceRule.is_active == True)
    rules_rows = (await db.execute(rules_query)).scalars().all()

    # If no compliance rules seeded in database yet, auto-seed standard statutory rules
    if not rules_rows:
        for r_def in DEFAULT_LEGAL_METROLOGY_RULES:
            rule_record = ComplianceRule(
                id=uuid.uuid4(),
                rule_id=r_def["rule_id"],
                field=r_def["field"],
                canonical_field=r_def.get("canonical_field", r_def["field"]),
                requirement_type=r_def.get("requirement_type", "required"),
                requirement_value=r_def.get("requirement_value"),
                description=r_def.get("description", ""),
                source_document=r_def.get("source_document", "Legal Metrology (Packaged Commodities) Rules, 2011"),
                source_rule=r_def.get("source_rule", "Rule 6"),
                source_page=r_def.get("source_page", 1),
                severity=r_def.get("severity", "major"),
                is_active=True,
            )
            db.add(rule_record)
        await db.flush()
        rules_rows = (await db.execute(rules_query)).scalars().all()

    rules_dicts = []
    for r in rules_rows:
        rules_dicts.append({
            "id": r.id,
            "rule_id": r.rule_id,
            "field": r.field,
            "canonical_field": r.canonical_field,
            "requirement_type": r.requirement_type,
            "requirement_value": r.requirement_value,
            "description": r.description,
            "applicability": r.applicability,
            "source_document": r.source_document,
            "source_rule": r.source_rule,
            "source_page": r.source_page,
            "severity": r.severity
        })

    # Prepare field dictionaries
    field_dicts = []
    field_obj_map = {}
    for f in product.fields:
        f_dict = {
            "id": f.id,
            "field": f.field_name,
            "canonical_field": f.canonical_name,
            "raw_value": f.raw_value,
            "normalized_value": f.normalized_value,
            "unit": f.unit,
            "currency": f.currency,
            "confidence": f.confidence or 0.85,
            "source_text": f.source_text,
            "bbox": f.bbox,
            "image_id": f.image_id,
            "status": f.status
        }
        field_dicts.append(f_dict)
        field_obj_map[f.field_name] = f

    # 3. Deterministic evaluation
    product_meta = {
        "name": product.product_name,
        "brand": product.brand,
        "category": product.category or inspection.product_category
    }

    eval_payload = evaluate_compliance(
        fields=field_dicts,
        rules=rules_dicts,
        product_metadata=product_meta,
        confidence_threshold=settings.ocr_confidence_medium
    )
    eval_results = eval_payload.get("results", [])

    # 4. Remove previous compliance results and evidence for this inspection
    existing_results = (await db.execute(
        select(ComplianceResult).where(ComplianceResult.inspection_id == inspection_id)
    )).scalars().all()

    for old_res in existing_results:
        # Delete related evidence
        ev_query = select(Evidence).where(Evidence.compliance_result_id == old_res.id)
        evs = (await db.execute(ev_query)).scalars().all()
        for ev in evs:
            await db.delete(ev)
        await db.delete(old_res)
    await db.flush()

    # 5. Persist new compliance results and evidence
    rule_id_map = {r.rule_id: r.id for r in rules_rows}

    created_results = []
    overall_statuses = []

    for item in eval_results:
        rule_db_id = rule_id_map.get(item["rule_id"])
        if not rule_db_id:
            continue

        comp_res_id = uuid.uuid4()
        comp_res = ComplianceResult(
            id=comp_res_id,
            inspection_id=inspection_id,
            rule_id=rule_db_id,
            field_name=item["field_name"],
            detected_value=item.get("detected_value"),
            required_value=item.get("required_value"),
            status=item["status"],
            reason=item["reason"],
            confidence=item.get("confidence")
        )
        db.add(comp_res)
        await db.flush()

        overall_statuses.append(item["status"])

        # Create Evidence record
        ev_data = item.get("evidence") or {}
        legal_src = item.get("legal_source") or {}
        evidence_record = Evidence(
            id=uuid.uuid4(),
            compliance_result_id=comp_res_id,
            image_id=ev_data.get("image_id"),
            bbox=ev_data.get("bbox"),
            source_text=ev_data.get("source_text"),
            ocr_confidence=ev_data.get("confidence") or ev_data.get("ocr_confidence"),
            legal_document=legal_src.get("document") or ev_data.get("legal_document"),
            legal_rule=legal_src.get("rule") or ev_data.get("legal_rule"),
            legal_page=legal_src.get("page") or ev_data.get("legal_page"),
            legal_text=ev_data.get("legal_text") or legal_src.get("text")
        )
        db.add(evidence_record)
        created_results.append(comp_res)

    # 6. Compute overall inspection verdict
    inspection.overall_result = eval_payload.get("overall_result", "REVIEW")

    inspection.status = "completed"
    await db.flush()

    # 7. Query back with relationships
    query = (
        select(ComplianceResult)
        .where(ComplianceResult.inspection_id == inspection_id)
        .options(
            selectinload(ComplianceResult.rule),
            selectinload(ComplianceResult.evidence),
        )
    )
    final_results = (await db.execute(query)).scalars().all()
    return list(final_results)


@router.post(
    "/process/{inspection_id}",
    response_model=ProcessingStatus,
    tags=["Pipeline"],
)
async def process_full_pipeline(
    inspection_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """One-click processing: runs preprocessing, OCR, extraction, rules, and compliance."""
    insp_result = await db.execute(
        select(Inspection).where(Inspection.id == inspection_id)
    )
    inspection = insp_result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    inspection.status = "processing"
    await db.flush()

    now = datetime.now(timezone.utc)

    # Run complete pipeline
    # 1. OCR (if not already run)
    await run_ocr(inspection_id=inspection_id, db=db)

    # 2. Extraction
    await run_extraction(inspection_id=inspection_id, db=db)

    # 3. Compliance evaluation
    await run_compliance(inspection_id=inspection_id, db=db)

    # 4. Report generation
    await get_inspection_report(inspection_id=inspection_id, db=db)

    inspection.status = "completed"
    await db.flush()

    return ProcessingStatus(
        inspection_id=inspection_id,
        status="completed",
        current_stage="completed",
        progress_pct=100.0,
        stages=[
            {"name": "preprocessing", "status": "completed", "started_at": now, "completed_at": now},
            {"name": "ocr", "status": "completed", "started_at": now, "completed_at": now},
            {"name": "extraction", "status": "completed", "started_at": now, "completed_at": now},
            {"name": "rule_retrieval", "status": "completed", "started_at": now, "completed_at": now},
            {"name": "compliance_check", "status": "completed", "started_at": now, "completed_at": now},
            {"name": "report_generation", "status": "completed", "started_at": now, "completed_at": now},
        ],
    )


# ===========================================================================
# Inspection Details: Sub-resources
# ===========================================================================
@router.get(
    "/inspections/{inspection_id}/ocr",
    response_model=List[OCRResultResponse],
    tags=["Inspections"],
)
async def get_inspection_ocr(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all OCR results for an inspection's images."""
    query = (
        select(OCRResult)
        .join(InspectionImage)
        .where(InspectionImage.inspection_id == inspection_id)
        .order_by(OCRResult.created_at.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/inspections/{inspection_id}/fields",
    response_model=List[ProductFieldResponse],
    tags=["Inspections"],
)
async def get_inspection_fields(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all extracted product fields for an inspection."""
    query = (
        select(ProductField)
        .join(Product)
        .where(Product.inspection_id == inspection_id)
        .order_by(ProductField.created_at.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/inspections/{inspection_id}/compliance",
    response_model=List[ComplianceResultResponse],
    tags=["Inspections"],
)
async def get_inspection_compliance(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get compliance check results for an inspection."""
    query = (
        select(ComplianceResult)
        .where(ComplianceResult.inspection_id == inspection_id)
        .options(
            selectinload(ComplianceResult.rule),
            selectinload(ComplianceResult.evidence),
        )
        .order_by(ComplianceResult.created_at.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/inspections/{inspection_id}/evidence",
    response_model=List[EvidenceResponse],
    tags=["Inspections"],
)
async def get_inspection_evidence(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all evidence records linking detections to legal requirements."""
    query = (
        select(Evidence)
        .join(ComplianceResult)
        .where(ComplianceResult.inspection_id == inspection_id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/inspections/{inspection_id}/report",
    response_model=ReportResponse,
    tags=["Reports"],
)
async def get_inspection_report(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get or generate the final inspection compliance report with SHA-256 tamper evidence."""
    query = (
        select(Report)
        .where(Report.inspection_id == inspection_id)
        .order_by(Report.created_at.desc())
    )
    result = await db.execute(query)
    report = result.scalars().first()

    if not report or not report.report_data or report.report_data.get("status") == "draft":
        # Load complete inspection with relations
        insp_q = (
            select(Inspection)
            .where(Inspection.id == inspection_id)
            .options(
                selectinload(Inspection.images),
                selectinload(Inspection.product).selectinload(Product.fields),
                selectinload(Inspection.compliance_results).selectinload(ComplianceResult.rule),
                selectinload(Inspection.compliance_results).selectinload(ComplianceResult.evidence)
            )
        )
        inspection = (await db.execute(insp_q)).scalar_one_or_none()
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found.")

        # Gather OCR results count
        ocr_count_q = (
            select(func.count(OCRResult.id))
            .join(InspectionImage)
            .where(InspectionImage.inspection_id == inspection_id)
        )
        ocr_count = (await db.execute(ocr_count_q)).scalar() or 0

        # Build payload for report generator
        insp_dict = {
            "id": str(inspection.id),
            "title": inspection.title,
            "description": inspection.description,
            "product_category": inspection.product_category,
            "status": inspection.status,
            "overall_result": inspection.overall_result or "REVIEW",
            "created_at": inspection.created_at.isoformat() if inspection.created_at else None
        }

        prod_dict = None
        fields_list = []
        if inspection.product:
            prod_dict = {
                "product_name": inspection.product.product_name,
                "brand": inspection.product.brand,
                "category": inspection.product.category,
                "extraction_confidence": inspection.product.extraction_confidence
            }
            for f in inspection.product.fields:
                fields_list.append({
                    "field": f.field_name,
                    "canonical_field": f.canonical_name,
                    "raw_value": f.raw_value,
                    "normalized_value": f.normalized_value,
                    "unit": f.unit,
                    "currency": f.currency,
                    "confidence": f.confidence,
                    "source_text": f.source_text,
                    "status": f.status
                })

        comp_list = []
        for cr in inspection.compliance_results:
            ev = cr.evidence if hasattr(cr, "evidence") else None
            comp_list.append({
                "rule_id": cr.rule.rule_id if cr.rule else "RULE",
                "field_name": cr.field_name,
                "detected_value": cr.detected_value,
                "required_value": cr.required_value,
                "status": cr.status,
                "reason": cr.reason,
                "confidence": cr.confidence,
                "evidence": {
                    "source_text": ev.source_text if ev else None,
                    "ocr_confidence": ev.ocr_confidence if ev else None,
                    "legal_document": ev.legal_document if ev else (cr.rule.source_document if cr.rule else None),
                    "legal_rule": ev.legal_rule if ev else (cr.rule.source_rule if cr.rule else None)
                } if ev or cr.rule else None
            })

        ocr_summary = {
            "total_detections": ocr_count,
            "processed_images_count": len(inspection.images)
        }

        report_payload = generate_report_data(
            inspection=insp_dict,
            product=prod_dict,
            fields=fields_list,
            compliance_results=comp_list,
            ocr_summary=ocr_summary
        )

        report_hash = compute_sha256_signature(report_payload)

        # Render HTML/PDF report to file
        report_dir = os.path.join(settings.upload_dir, str(inspection_id), "reports")
        os.makedirs(report_dir, exist_ok=True)
        pdf_path = os.path.join(report_dir, f"audit_report_{inspection_id}.pdf")
        html_path = os.path.join(report_dir, f"audit_report_{inspection_id}.html")

        try:
            render_html_report(report_payload, output_path=html_path)
            export_report_pdf(report_payload, output_pdf_path=pdf_path)
            final_report_path = pdf_path if os.path.exists(pdf_path) else html_path
        except Exception:
            final_report_path = html_path

        if not report:
            report = Report(
                id=uuid.uuid4(),
                inspection_id=inspection_id,
                report_type="full",
                file_path=final_report_path,
                report_data=report_payload,
                report_hash=report_hash
            )
            db.add(report)
        else:
            report.file_path = final_report_path
            report.report_data = report_payload
            report.report_hash = report_hash

        await db.flush()
        await db.refresh(report)

    return report


# ===========================================================================
# Manual Correction
# ===========================================================================
@router.patch(
    "/fields/{field_id}",
    response_model=ProductFieldResponse,
    tags=["Corrections"],
)
async def correct_product_field(
    field_id: UUID,
    payload: ProductFieldUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Manually correct an extracted product field. Preserves original value."""
    result = await db.execute(
        select(ProductField).where(ProductField.id == field_id)
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="Product field not found.")

    # Preserve original value on first correction
    if field.status != "MANUALLY_CORRECTED":
        field.original_value = field.raw_value

    if payload.raw_value is not None:
        field.raw_value = payload.raw_value
    if payload.normalized_value is not None:
        field.normalized_value = payload.normalized_value
    if payload.unit is not None:
        field.unit = payload.unit
    if payload.currency is not None:
        field.currency = payload.currency

    field.status = "MANUALLY_CORRECTED"
    field.corrected_by = payload.corrected_by
    field.corrected_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(field)
    return field


# ===========================================================================
# RAG & Regulations
# ===========================================================================
@router.post(
    "/rag/search",
    response_model=RAGSearchResponse,
    tags=["RAG"],
)
async def rag_search(
    query: RAGSearchQuery,
    db: AsyncSession = Depends(get_db),
):
    """Semantic search over Legal Metrology legal documents."""
    results = await search_legal_regulations(
        query=query.query,
        db=db,
        top_k=query.top_k or 5
    )

    pydantic_results = [
        RAGSearchResult(
            chunk_id=r.get("chunk_id") or uuid.uuid4(),
            document=r.get("document", "Legal Metrology Rules, 2011"),
            rule=r.get("rule", "Rule 6"),
            page=r.get("page", 1),
            text=r.get("text", ""),
            similarity=float(r.get("similarity", 0.9))
        )
        for r in results
    ]

    return RAGSearchResponse(
        query=query.query,
        results=pydantic_results,
        total=len(pydantic_results),
    )


@router.post(
    "/regulations/ingest",
    response_model=RegulationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Regulations"],
)
async def ingest_regulation(
    file: UploadFile = File(...),
    document_name: str = Form(...),
    version: Optional[str] = Form(None),
    effective_date: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Upload and ingest a Legal Metrology Act/Rules PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    dest_dir = os.path.join(settings.upload_dir, "regulations")
    saved_path = await save_upload(file, dest_dir)

    # Parse effective_date if provided
    parsed_date = None
    if effective_date:
        try:
            parsed_date = datetime.strptime(effective_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    reg = Regulation(
        id=uuid.uuid4(),
        document_name=document_name,
        version=version,
        effective_date=parsed_date,
        source_url=source_url,
        file_path=saved_path,
        is_processed=False,
    )
    db.add(reg)
    await db.flush()
    await db.refresh(reg)

    # Ingest document chunks & embeddings
    try:
        await ingest_pdf_regulation(
            pdf_path=saved_path,
            document_name=document_name,
            db=db,
            version=version,
            effective_date=effective_date,
            source_url=source_url
        )
        reg.is_processed = True
        await db.flush()
        await db.refresh(reg)
    except Exception:
        pass

    return reg
