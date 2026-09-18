-- ==============================================================================
-- Legal Metrology Compliance (LMC) System - Supabase Schema
-- Run this in your Supabase SQL Editor (https://app.supabase.com/project/_/sql)
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. Products Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(120) DEFAULT 'other',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_name ON public.products(name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON public.products(brand);

-- ------------------------------------------------------------------------------
-- 2. Scans Table
-- Stores OCR analysis, PaddleOCR bounding boxes, confidence scores, and RAG citations
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.scans (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES public.products(id) ON DELETE CASCADE,
    inspector_username VARCHAR(100) DEFAULT 'inspector',
    image_url TEXT NOT NULL,
    raw_ocr_text TEXT,
    extracted_fields_json JSONB,
    min_font_height_mm NUMERIC(5, 2),
    compliance_score NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    status VARCHAR(50) NOT NULL DEFAULT 'review', -- 'compliant', 'review', 'non_compliant'
    report_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scans_status ON public.scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_product_id ON public.scans(product_id);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON public.scans(created_at DESC);

-- ------------------------------------------------------------------------------
-- 3. Violations Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.violations (
    id BIGSERIAL PRIMARY KEY,
    scan_id BIGINT REFERENCES public.scans(id) ON DELETE CASCADE,
    rule_code VARCHAR(80) NOT NULL,
    field VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(30) DEFAULT 'major', -- 'critical', 'major', 'minor'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_violations_scan_id ON public.violations(scan_id);
CREATE INDEX IF NOT EXISTS idx_violations_rule_code ON public.violations(rule_code);

-- ------------------------------------------------------------------------------
-- 4. RAG Legal Rules Knowledge Base Table
-- Official statutory provisions indexed from Legal Metrology Act & Rules
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rag_legal_rules (
    id VARCHAR(80) PRIMARY KEY,
    rule_code VARCHAR(80) NOT NULL,
    field VARCHAR(100) NOT NULL,
    field_name VARCHAR(150) NOT NULL,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    clause VARCHAR(255) NOT NULL,
    requirement TEXT NOT NULL,
    penalties TEXT NOT NULL,
    official_text TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 5. Seed RAG Legal Provisions into Supabase
-- ------------------------------------------------------------------------------
INSERT INTO public.rag_legal_rules (id, rule_code, field, field_name, title, source, clause, requirement, penalties, official_text, tags)
VALUES
('RAG-MRP', 'LM-R6(1)(e) / R18', 'mrp', 'Maximum Retail Price (MRP)', 
 'Declaration of Maximum Retail Price (Inclusive of all Taxes)',
 'Legal Metrology (Packaged Commodities) Rules, 2011',
 'Rule 6(1)(e) read with Rule 18(1) & Section 36(1)',
 'The retail sale price shall be clearly declared in the format "MRP Rs / ₹ ... incl. of all taxes". No dealer shall sell at a price exceeding MRP.',
 'Section 36(1) & 36(2): Penalty up to ₹25,000 for 1st offence, ₹50,000 for 2nd offence, and up to ₹1,00,000 or imprisonment for subsequent offences.',
 'Rule 6(1)(e): The retail sale price of the package shall clearly indicate that it is the maximum retail price, inclusive of all taxes, and the price in Indian currency shall be mentioned in unambiguous bold numerals.',
 ARRAY['mrp', 'price', 'retail', 'taxes', 'rupees']),

('RAG-NETQTY', 'LM-R6(1)(b) / R11 / R12', 'net_quantity', 'Net Quantity Declaration',
 'Declaration of Net Quantity in Standard Units',
 'Legal Metrology (Packaged Commodities) Rules, 2011',
 'Rule 6(1)(b), Rule 11, Rule 12 & Second Schedule',
 'Net quantity in standard units (g, kg, ml, l) or number must be declared on the principal display panel without non-standard qualifiers.',
 'Section 36(1) & Section 30: Fine up to ₹25,000 for non-compliant declarations, and fine for short measure packages.',
 'Rule 6(1)(b): The net quantity, in terms of the standard unit of weight or measure, of the commodity contained in the package shall be declared on the principal display panel.',
 ARRAY['net quantity', 'weight', 'volume', 'grams', 'kg', 'ml', 'litres']),

('RAG-MFG-DETAILS', 'LM-R6(1)(a)', 'manufacturer_details', 'Manufacturer / Packer / Importer Details',
 'Name and Complete Postal Address of Manufacturer or Packer',
 'Legal Metrology (Packaged Commodities) Rules, 2011',
 'Rule 6(1)(a) & Rule 6(2)',
 'Every package must bear the name and complete postal address of manufacturer, packer, or importer with valid PIN code.',
 'Section 36(1): Fine up to ₹25,000 for first offence. Non-disclosure of manufacturer identity can lead to package seizure.',
 'Rule 6(1)(a): The name and complete address of the manufacturer or where the manufacturer is not the packer, the name and address of the manufacturer and packer and for any imported package the name and address of the importer shall be declared.',
 ARRAY['manufacturer', 'packer', 'importer', 'address', 'company', 'mfd by']),

('RAG-MFG-DATE', 'LM-R6(1)(f)', 'mfg_date', 'Month & Year of Manufacture / Packaging',
 'Month and Year of Manufacture, Packing or Import',
 'Legal Metrology (Packaged Commodities) Rules, 2011',
 'Rule 6(1)(f)',
 'The month and year of manufacture, packing or import shall be declared. Best Before / Expiry date must also be given for perishables.',
 'Section 36(1): Statutory penalty up to ₹25,000. Future-dated packages constitute deceptive packaging practices.',
 'Rule 6(1)(f): The month and year in which the commodity is manufactured or pre-packed or imported shall be declared on the package.',
 ARRAY['mfg date', 'manufactured', 'pkd', 'packed on', 'best before', 'expiry']),

('RAG-CONSUMER-CARE', 'LM-R6(1)(g)', 'consumer_care', 'Consumer Care Redressal Details',
 'Consumer Helpline Contact Details & Grievance Redressal',
 'Legal Metrology (Packaged Commodities) Rules, 2011',
 'Rule 6(1)(g)',
 'Every pre-packaged commodity must mention the name, address, telephone number, and e-mail address for consumer complaints.',
 'Section 36(1): Fine up to ₹25,000 for omission or illegibility of consumer redressal details.',
 'Rule 6(1)(g): The name, address, telephone number, and e-mail address of the person who can be or the office which can be contacted, in case of consumer complaints, shall be mentioned.',
 ARRAY['consumer care', 'customer care', 'toll free', 'helpline', 'email', 'phone']),

('RAG-ORIGIN', 'LM-R6(8)', 'country_of_origin', 'Country of Origin',
 'Mandatory Country of Origin on Imported Pre-Packaged Goods',
 'Legal Metrology (Packaged Commodities) Rules, 2011',
 'Rule 6(8)',
 'Every package containing imported goods shall mention the country of origin or manufacture in clear words.',
 'Section 36(1): Penalty up to ₹25,000 and possible detention of unlabelled imported consignments.',
 'Rule 6(8): Every package containing an imported commodity shall bear the name of the country of origin or manufacture or assembly.',
 ARRAY['country of origin', 'imported', 'made in', 'origin']),

('RAG-UNIT-PRICE', 'LM-R6(1)(d)', 'unit_sale_price', 'Unit Sale Price (USP)',
 'Mandatory Declaration of Unit Sale Price (per g, kg, ml, l)',
 'Legal Metrology (Packaged Commodities) (Second Amendment) Rules, 2022',
 'Rule 6(1)(d)',
 'Commodities must declare unit sale price per gram/ml (<1kg/1L) or per kg/L (>1kg/1L) for consumer price transparency.',
 'Section 36(1): Penalty up to ₹25,000 for non-declaration or misleading unit pricing.',
 'Rule 6(1)(d): The unit sale price shall be declared on the package in rupees per kg/litre or rupees per gram/milliliter.',
 ARRAY['unit sale price', 'usp', 'per gram', 'per kg', 'price per unit'])
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    requirement = EXCLUDED.requirement,
    penalties = EXCLUDED.penalties,
    official_text = EXCLUDED.official_text;

-- ------------------------------------------------------------------------------
-- 6. Row-Level Security (RLS) Configuration
-- Enable public / anon read access and authenticated insert
-- ------------------------------------------------------------------------------
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.violations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rag_legal_rules ENABLE ROW LEVEL SECURITY;

-- Allow read access to all clients
CREATE POLICY "Allow public read products" ON public.products FOR SELECT USING (true);
CREATE POLICY "Allow public read scans" ON public.scans FOR SELECT USING (true);
CREATE POLICY "Allow public read violations" ON public.violations FOR SELECT USING (true);
CREATE POLICY "Allow public read rag_legal_rules" ON public.rag_legal_rules FOR SELECT USING (true);

-- Allow insert/update for application service role and anon key
CREATE POLICY "Allow anon insert products" ON public.products FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anon insert scans" ON public.scans FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anon insert violations" ON public.violations FOR INSERT WITH CHECK (true);
