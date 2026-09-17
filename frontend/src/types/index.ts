// TypeScript interfaces for Legal Metrology Compliance System

export type ComplianceStatus = 'PASS' | 'REVIEW' | 'VIOLATION' | 'NOT_APPLICABLE'
export type ConfidenceCategory = 'HIGH' | 'MEDIUM' | 'LOW'
export type FieldStatus = 'DETECTED' | 'NOT_DETECTED' | 'AMBIGUOUS' | 'LOW_CONFIDENCE' | 'MANUALLY_CORRECTED'
export type ImageType = 'front' | 'back' | 'side' | 'top' | 'bottom' | 'label'
export type InspectionStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
}

export interface InspectionImage {
  id: string
  inspection_id: string
  original_path: string
  processed_path?: string | null
  ocr_visualization_path?: string | null
  image_type: ImageType
  file_name: string
  file_size?: number | null
  mime_type?: string | null
  width?: number | null
  height?: number | null
  created_at: string
}

export interface OCRResult {
  id: string
  image_id: string
  text: string
  confidence: number
  bbox: [number, number, number, number] | number[]
  page: number
  confidence_category: ConfidenceCategory
  is_corrected?: boolean
  corrected_text?: string | null
  corrected_by?: string | null
  corrected_at?: string | null
  created_at?: string
}

export interface ProductField {
  id: string
  product_id: string
  field_name: string
  canonical_name: string
  raw_value?: string | null
  normalized_value?: string | null
  unit?: string | null
  currency?: string | null
  confidence?: number | null
  source_text?: string | null
  bbox?: [number, number, number, number] | number[] | null
  image_id?: string | null
  status: FieldStatus
  original_value?: string | null
  corrected_by?: string | null
  corrected_at?: string | null
  created_at: string
}

export interface Product {
  id: string
  inspection_id: string
  raw_extraction?: Record<string, any> | null
  product_name?: string | null
  brand?: string | null
  category?: string | null
  extraction_confidence?: number | null
  extraction_model?: string | null
  fields?: ProductField[]
  created_at: string
  updated_at?: string | null
}

export interface ComplianceRule {
  id: string
  rule_id: string
  field: string
  canonical_field: string
  requirement_type: string
  requirement_value?: any
  description: string
  applicability?: Record<string, any> | null
  source_document?: string | null
  source_rule?: string | null
  source_page?: number | null
  is_active: boolean
  severity: 'critical' | 'major' | 'minor'
  created_at: string
}

export interface Evidence {
  id: string
  compliance_result_id?: string | null
  image_id?: string | null
  bbox?: [number, number, number, number] | number[] | null
  source_text?: string | null
  ocr_confidence?: number | null
  legal_document?: string | null
  legal_rule?: string | null
  legal_page?: number | null
  legal_text?: string | null
  created_at: string
}

export interface ComplianceResult {
  id: string
  inspection_id: string
  rule_id: string
  field_name: string
  detected_value?: string | null
  required_value?: string | null
  status: ComplianceStatus
  reason: string
  confidence?: number | null
  evidence_id?: string | null
  evidence?: Evidence | null
  rule?: ComplianceRule | null
  created_at: string
}

export interface Inspection {
  id: string
  inspector_id?: string | null
  title: string
  description?: string | null
  product_category?: string | null
  status: InspectionStatus
  overall_result?: ComplianceStatus | null
  notes?: string | null
  created_at: string
  updated_at?: string | null
  images?: InspectionImage[]
  product?: Product | null
  compliance_results?: ComplianceResult[]
}

export interface InspectionCreate {
  title: string
  description?: string
  product_category?: string
}

export interface Report {
  id: string
  inspection_id: string
  report_type: string
  file_path?: string | null
  report_data?: Record<string, any> | null
  generated_at: string
  report_hash?: string | null
  created_at: string
}

export interface ProcessingStage {
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number
  message?: string
}

export interface ProcessingStatus {
  inspection_id: string
  stages: ProcessingStage[]
  current_stage?: string
  overall_progress: number
}

export interface RAGSearchQuery {
  query: string
  top_k?: number
  filters?: Record<string, any>
}

export interface RAGSearchResult {
  chunk_id: string
  document: string
  rule?: string | null
  page?: number | null
  text: string
  similarity: number
}

export interface Regulation {
  id: string
  document_name: string
  version?: string | null
  effective_date?: string | null
  source_url?: string | null
  file_path?: string | null
  total_pages?: number | null
  is_processed: boolean
  created_at: string
}

export interface DashboardStats {
  total_inspections: number
  compliant: number
  review_required: number
  violations: number
  recent_inspections: Inspection[]
}
