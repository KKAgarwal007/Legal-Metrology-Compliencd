-- Legal Metrology Compliance System - Database Initialization
-- Creates all tables, indexes, and extensions for the application

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'inspector',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================
-- INSPECTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS inspections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspector_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    product_category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    overall_result VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_inspections_inspector_id ON inspections(inspector_id);
CREATE INDEX idx_inspections_status ON inspections(status);
CREATE INDEX idx_inspections_overall_result ON inspections(overall_result);
CREATE INDEX idx_inspections_created_at ON inspections(created_at DESC);

-- ============================================================
-- INSPECTION IMAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS inspection_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    original_path VARCHAR(1000) NOT NULL,
    processed_path VARCHAR(1000),
    ocr_visualization_path VARCHAR(1000),
    image_type VARCHAR(50) DEFAULT 'front',
    file_name VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_inspection_images_inspection_id ON inspection_images(inspection_id);
CREATE INDEX idx_inspection_images_image_type ON inspection_images(image_type);

-- ============================================================
-- OCR RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS ocr_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id UUID NOT NULL REFERENCES inspection_images(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    bbox JSONB NOT NULL,
    page INTEGER DEFAULT 1,
    confidence_category VARCHAR(20),
    is_corrected BOOLEAN DEFAULT FALSE,
    corrected_text TEXT,
    corrected_by UUID REFERENCES users(id) ON DELETE SET NULL,
    corrected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ocr_results_image_id ON ocr_results(image_id);
CREATE INDEX idx_ocr_results_confidence ON ocr_results(confidence);
CREATE INDEX idx_ocr_results_confidence_category ON ocr_results(confidence_category);

-- ============================================================
-- PRODUCTS
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID UNIQUE NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    raw_extraction JSONB,
    product_name VARCHAR(500),
    brand VARCHAR(255),
    category VARCHAR(100),
    extraction_confidence FLOAT,
    extraction_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_products_inspection_id ON products(inspection_id);
CREATE INDEX idx_products_category ON products(category);

-- ============================================================
-- PRODUCT FIELDS
-- ============================================================
CREATE TABLE IF NOT EXISTS product_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    canonical_name VARCHAR(100) NOT NULL,
    raw_value TEXT,
    normalized_value TEXT,
    unit VARCHAR(50),
    currency VARCHAR(10),
    confidence FLOAT,
    source_text TEXT,
    bbox JSONB,
    image_id UUID REFERENCES inspection_images(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'DETECTED',
    original_value TEXT,
    corrected_by UUID REFERENCES users(id) ON DELETE SET NULL,
    corrected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_product_fields_product_id ON product_fields(product_id);
CREATE INDEX idx_product_fields_field_name ON product_fields(field_name);
CREATE INDEX idx_product_fields_canonical_name ON product_fields(canonical_name);
CREATE INDEX idx_product_fields_status ON product_fields(status);

-- ============================================================
-- REGULATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS regulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_name VARCHAR(500) NOT NULL,
    version VARCHAR(100),
    effective_date DATE,
    source_url VARCHAR(1000),
    file_path VARCHAR(1000),
    total_pages INTEGER,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_regulations_document_name ON regulations(document_name);

-- ============================================================
-- REGULATION CHUNKS
-- ============================================================
CREATE TABLE IF NOT EXISTS regulation_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    regulation_id UUID NOT NULL REFERENCES regulations(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    section VARCHAR(200),
    rule VARCHAR(200),
    page INTEGER,
    metadata_ JSONB,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_regulation_chunks_regulation_id ON regulation_chunks(regulation_id);
CREATE INDEX idx_regulation_chunks_section ON regulation_chunks(section);
CREATE INDEX idx_regulation_chunks_rule ON regulation_chunks(rule);

-- ============================================================
-- COMPLIANCE RULES
-- ============================================================
CREATE TABLE IF NOT EXISTS compliance_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    field VARCHAR(100) NOT NULL,
    canonical_field VARCHAR(100) NOT NULL,
    requirement_type VARCHAR(50) NOT NULL,
    requirement_value JSONB,
    description TEXT NOT NULL,
    applicability JSONB,
    source_document VARCHAR(500),
    source_rule VARCHAR(200),
    source_page INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    severity VARCHAR(20) DEFAULT 'major',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_compliance_rules_rule_id ON compliance_rules(rule_id);
CREATE INDEX idx_compliance_rules_field ON compliance_rules(field);
CREATE INDEX idx_compliance_rules_canonical_field ON compliance_rules(canonical_field);
CREATE INDEX idx_compliance_rules_is_active ON compliance_rules(is_active);

-- ============================================================
-- FIELD RULE MAPPINGS
-- ============================================================
CREATE TABLE IF NOT EXISTS field_rule_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_name VARCHAR(100) NOT NULL,
    canonical_field VARCHAR(100) NOT NULL,
    rule_id UUID NOT NULL REFERENCES compliance_rules(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_field_rule_mappings_field_name ON field_rule_mappings(field_name);
CREATE INDEX idx_field_rule_mappings_canonical_field ON field_rule_mappings(canonical_field);
CREATE INDEX idx_field_rule_mappings_rule_id ON field_rule_mappings(rule_id);

-- ============================================================
-- COMPLIANCE RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS compliance_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES compliance_rules(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    detected_value TEXT,
    required_value TEXT,
    status VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    confidence FLOAT,
    evidence_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_compliance_results_inspection_id ON compliance_results(inspection_id);
CREATE INDEX idx_compliance_results_rule_id ON compliance_results(rule_id);
CREATE INDEX idx_compliance_results_status ON compliance_results(status);
CREATE INDEX idx_compliance_results_field_name ON compliance_results(field_name);

-- ============================================================
-- EVIDENCE
-- ============================================================
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compliance_result_id UUID REFERENCES compliance_results(id) ON DELETE CASCADE,
    image_id UUID REFERENCES inspection_images(id) ON DELETE SET NULL,
    bbox JSONB,
    source_text TEXT,
    ocr_confidence FLOAT,
    legal_document VARCHAR(500),
    legal_rule VARCHAR(200),
    legal_page INTEGER,
    legal_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evidence_compliance_result_id ON evidence(compliance_result_id);
CREATE INDEX idx_evidence_image_id ON evidence(image_id);

-- Add the FK from compliance_results to evidence now that evidence table exists
ALTER TABLE compliance_results
    ADD CONSTRAINT fk_compliance_results_evidence
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE SET NULL;

-- ============================================================
-- REPORTS
-- ============================================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    report_type VARCHAR(50) DEFAULT 'full',
    file_path VARCHAR(1000),
    report_data JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    report_hash VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reports_inspection_id ON reports(inspection_id);
CREATE INDEX idx_reports_report_type ON reports(report_type);

-- ============================================================
-- IVFFLAT index for vector similarity search (create after data load)
-- ============================================================
-- Run after inserting regulation chunks:
-- CREATE INDEX idx_regulation_chunks_embedding ON regulation_chunks
--   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
