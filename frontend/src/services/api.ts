import axios from 'axios'
import type {
  Inspection,
  InspectionCreate,
  InspectionImage,
  OCRResult,
  ProductField,
  ComplianceResult,
  Evidence,
  Report,
  ProcessingStatus,
  RAGSearchQuery,
  RAGSearchResult,
  Regulation,
  DashboardStats,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Inspections
export async function createInspection(data: InspectionCreate): Promise<Inspection> {
  const response = await api.post<Inspection>('/inspections', data)
  return response.data
}

export async function getInspections(
  page = 1,
  limit = 20,
  status?: string,
  inspectorId?: string,
  overallResult?: string,
  search?: string
): Promise<{ items: Inspection[]; total: number; page: number; limit: number }> {
  const response = await api.get('/inspections', {
    params: {
      page,
      limit,
      page_size: limit,
      status,
      inspector_id: inspectorId,
      overall_result: overallResult,
      search,
    },
  })
  return response.data
}

export async function getInspection(id: string): Promise<Inspection> {
  const response = await api.get<Inspection>(`/inspections/${id}`)
  return response.data
}

// Images
export async function uploadImages(
  inspectionId: string,
  files: { file: File; image_type: string }[]
): Promise<InspectionImage[]> {
  const formData = new FormData()
  files.forEach((f) => {
    formData.append('files', f.file)
    formData.append('image_types', f.image_type)
  })
  const response = await api.post<InspectionImage[]>(
    `/inspections/${inspectionId}/images`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  )
  return response.data
}

// Pipeline Steps
export async function runOCR(inspectionId: string): Promise<OCRResult[]> {
  const response = await api.post<OCRResult[]>(`/ocr/${inspectionId}`)
  return response.data
}

export async function runExtraction(inspectionId: string): Promise<ProductField[]> {
  const response = await api.post<ProductField[]>(`/extract/${inspectionId}`)
  return response.data
}

export async function runCompliance(inspectionId: string): Promise<ComplianceResult[]> {
  const response = await api.post<ComplianceResult[]>(`/compliance/${inspectionId}`)
  return response.data
}

export async function processInspection(inspectionId: string): Promise<ProcessingStatus> {
  const response = await api.post<ProcessingStatus>(`/process/${inspectionId}`)
  return response.data
}

export async function getProcessingStatus(inspectionId: string): Promise<ProcessingStatus> {
  const response = await api.get<ProcessingStatus>(`/process/${inspectionId}/status`)
  return response.data
}

// Inspection Details
export async function getOCRResults(inspectionId: string): Promise<OCRResult[]> {
  const response = await api.get<OCRResult[]>(`/inspections/${inspectionId}/ocr`)
  return response.data
}

export async function getFields(inspectionId: string): Promise<ProductField[]> {
  const response = await api.get<ProductField[]>(`/inspections/${inspectionId}/fields`)
  return response.data
}

export async function getComplianceResults(inspectionId: string): Promise<ComplianceResult[]> {
  const response = await api.get<ComplianceResult[]>(`/inspections/${inspectionId}/compliance`)
  return response.data
}

export async function getEvidence(inspectionId: string): Promise<Evidence[]> {
  const response = await api.get<Evidence[]>(`/inspections/${inspectionId}/evidence`)
  return response.data
}

export async function updateField(
  fieldId: string,
  data: { normalized_value?: string; status?: string }
): Promise<ProductField> {
  const response = await api.patch<ProductField>(`/fields/${fieldId}`, data)
  return response.data
}

export async function getReport(inspectionId: string): Promise<Report> {
  const response = await api.get<Report>(`/inspections/${inspectionId}/report`)
  return response.data
}

export async function downloadReportPDF(inspectionId: string): Promise<Blob> {
  const response = await api.get(`/inspections/${inspectionId}/report/pdf`, {
    responseType: 'blob',
  })
  return response.data
}

// RAG
export async function searchRAG(data: RAGSearchQuery): Promise<RAGSearchResult[]> {
  const response = await api.post<RAGSearchResult[]>('/rag/search', data)
  return response.data
}

// Regulations
export async function getRegulations(): Promise<Regulation[]> {
  const response = await api.get<Regulation[]>('/regulations')
  return response.data
}

export async function ingestRegulation(file: File, documentName: string): Promise<Regulation> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('document_name', documentName)
  const response = await api.post<Regulation>('/regulations/ingest', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// Health & Stats
export async function getHealth(): Promise<{ status: string; version: string }> {
  const response = await api.get('/health')
  return response.data
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await api.get<DashboardStats>('/dashboard/stats')
  return response.data
}

export default api
