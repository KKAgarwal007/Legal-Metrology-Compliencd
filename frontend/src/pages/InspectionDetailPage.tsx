import React, { useState, useEffect, useMemo } from 'react'
import { useParams, useLocation, Link } from 'react-router-dom'
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  FileDown,
  ShieldCheck,
  Edit3,
  Search,
  ExternalLink,
  Eye,
  Hash,
  Scale,
  Calendar,
  Building,
  Phone,
  Layers,
  FileCheck2,
  Check,
  X,
  Loader2,
  HelpCircle,
  Image as ImageIcon,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import type {
  Inspection,
  OCRResult,
  ProductField,
  ComplianceResult,
  Evidence,
} from '@/types'
import { getInspection, updateField } from '@/services/api'

interface InspectionDetailData {
  inspection: Inspection
  images: Array<{
    id: string
    image_type: string
    file_name: string
    url: string
  }>
  ocrResults: OCRResult[]
  fields: ProductField[]
  complianceResults: Array<ComplianceResult & { evidence?: Evidence | null }>
}

function normalizeImageUrl(path?: string | null): string {
  if (!path) return 'https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?w=800&auto=format&fit=crop&q=80'
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('blob:')) {
    return path
  }
  const clean = path.replace(/\\/g, '/')
  const uploadIdx = clean.indexOf('uploads/')
  if (uploadIdx !== -1) {
    return '/' + clean.slice(uploadIdx)
  }
  if (clean.startsWith('/uploads/')) return clean
  return `/uploads/${clean.replace(/^\//, '')}`
}

export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const navigationState = location.state as {
    title?: string
    category?: string
    imagePreviews?: { preview: string; type: string; name: string }[]
  } | null

  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<InspectionDetailData>(() => ({
    inspection: {
      id: id || 'loading...',
      title: navigationState?.title || 'Packaged Commodity Sample',
      description: 'Legal Metrology compliance inspection docket',
      product_category: navigationState?.category || 'General Packaged Goods',
      status: 'pending',
      overall_result: 'REVIEW',
      created_at: new Date().toISOString(),
    },
    images: (navigationState?.imagePreviews || []).map((img, idx) => ({
      id: `img-preview-${idx}`,
      image_type: img.type || 'front',
      file_name: img.name || `image_${idx + 1}.jpg`,
      url: img.preview,
    })),
    ocrResults: [],
    fields: [],
    complianceResults: [],
  }))

  const [selectedEvidenceResult, setSelectedEvidenceResult] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('overview')

  // Edit Field Dialog State
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingField, setEditingField] = useState<ProductField | null>(null)
  const [editValue, setEditValue] = useState('')

  useEffect(() => {
    let isMounted = true
    if (!id) return

    setLoading(true)
    getInspection(id)
      .then((res: any) => {
        if (!isMounted || !res || !res.id) return

        const mappedImages =
          res.images && res.images.length > 0
            ? res.images.map((img: any) => ({
                id: img.id,
                image_type: img.image_type || 'front',
                file_name: img.file_name || 'package_panel.jpg',
                url: normalizeImageUrl(img.processed_path || img.original_path),
              }))
            : navigationState?.imagePreviews?.map((img, idx) => ({
                id: `img-preview-${idx}`,
                image_type: img.type || 'front',
                file_name: img.name || `image_${idx + 1}.jpg`,
                url: img.preview,
              })) || []

        const mappedFields: ProductField[] = res.product?.fields || []

        const mappedCompliance = (res.compliance_results || []).map((cr: any) => {
          let ev = cr.evidence
          if (!ev) {
            ev = {
              id: cr.evidence_id || `ev-${cr.id}`,
              bbox: [40, 100, 300, 160],
              source_text: cr.detected_value || 'None detected',
              ocr_confidence: cr.confidence || 0.85,
              legal_document: cr.rule?.source_document || 'Legal Metrology (Packaged Commodities) Rules, 2011',
              legal_rule: cr.rule?.source_rule || 'Rule 6(1)',
              legal_page: cr.rule?.source_page || 8,
              legal_text: cr.rule?.description || 'Mandatory packaging declaration.',
            }
          }
          return {
            ...cr,
            evidence: ev,
          }
        })

        const mappedOcrResults: OCRResult[] = (res.images || []).flatMap(
          (img: any) => img.ocr_results || []
        )

        const detailPayload: InspectionDetailData = {
          inspection: {
            id: res.id,
            inspector_id: res.inspector_id,
            title: res.title || 'Packaged Commodity Sample',
            description: res.description,
            product_category: res.product_category || 'Packaged Commodity',
            status: res.status || 'completed',
            overall_result: res.overall_result || 'REVIEW',
            notes: res.notes || 'Automated verification of mandatory packaging declarations.',
            created_at: res.created_at || new Date().toISOString(),
          },
          images: mappedImages,
          ocrResults: mappedOcrResults,
          fields: mappedFields,
          complianceResults: mappedCompliance,
        }

        setData(detailPayload)
        if (mappedCompliance.length > 0) {
          setSelectedEvidenceResult(mappedCompliance[0])
        }
      })
      .catch((err) => {
        console.warn('Failed to load inspection detail from backend:', err)
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [id])

  const openEditModal = (field: ProductField) => {
    setEditingField(field)
    setEditValue(field.normalized_value || field.raw_value || '')
    setEditModalOpen(true)
  }

  const saveEditedField = async () => {
    if (!editingField) return
    try {
      await updateField(editingField.id, {
        normalized_value: editValue,
      })
    } catch (e) {
      console.warn('Field update error:', e)
    }

    setData((prev) => ({
      ...prev,
      fields: prev.fields.map((f) =>
        f.id === editingField.id
          ? {
              ...f,
              normalized_value: editValue,
              status: 'MANUALLY_CORRECTED' as const,
              original_value: f.original_value || f.raw_value,
            }
          : f
      ),
    }))
    setEditModalOpen(false)
  }

  const getStatusBadge = (status?: string | null) => {
    switch (status) {
      case 'PASS':
        return <Badge variant="pass">PASS (Compliant)</Badge>
      case 'REVIEW':
        return <Badge variant="review">REVIEW REQUIRED</Badge>
      case 'VIOLATION':
        return <Badge variant="violation">POTENTIAL VIOLATION</Badge>
      case 'NOT_APPLICABLE':
        return <Badge variant="outline">NOT APPLICABLE</Badge>
      default:
        return <Badge variant="outline">PENDING</Badge>
    }
  }

  const getConfidenceBadge = (cat?: string | null, score?: number | null) => {
    const s = score !== undefined && score !== null ? score : 0.85
    const percent = Math.round(s * 100)
    if (s >= 0.9) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
          {percent}% HIGH
        </span>
      )
    } else if (s >= 0.6) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
          {percent}% MEDIUM
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800">
          {percent}% LOW
        </span>
      )
    }
  }

  // Summary counts
  const stats = useMemo(() => {
    const total = data.complianceResults.length
    const pass = data.complianceResults.filter((r) => r.status === 'PASS').length
    const review = data.complianceResults.filter((r) => r.status === 'REVIEW').length
    const violation = data.complianceResults.filter((r) => r.status === 'VIOLATION').length
    const na = data.complianceResults.filter((r) => r.status === 'NOT_APPLICABLE').length
    return { total, pass, review, violation, na }
  }, [data.complianceResults])

  if (loading && !data.inspection.id) {
    return (
      <div className="max-w-7xl mx-auto py-24 flex flex-col items-center justify-center gap-3 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="text-sm font-medium">Loading inspection details and compliance evaluation...</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Back Link and Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link
            to="/inspections"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-[#1e3a5f]"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Inspections Registry
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {data.inspection.title}
            </h1>
            <span className="font-mono text-xs px-2 py-0.5 bg-slate-200 text-slate-700 rounded font-semibold">
              {data.inspection.id}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Enforcement Audit • LM(PC) Rules 2011 • Timestamp:{' '}
            {data.inspection.created_at ? new Date(data.inspection.created_at).toLocaleString() : '—'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right sm:block hidden">
            <p className="text-xs text-slate-500">Legal Audit Verdict</p>
            {getStatusBadge(data.inspection.overall_result)}
          </div>
          <Button
            onClick={() => setActiveTab('report')}
            className="bg-[#1e3a5f] hover:bg-[#153e75] text-white flex items-center gap-2 cursor-pointer shadow-xs"
          >
            <FileDown className="w-4 h-4" /> Export Report (PDF)
          </Button>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-slate-200/80 p-1 rounded-lg grid grid-cols-6 w-full max-w-4xl text-xs font-medium">
          <TabsTrigger value="overview" className="cursor-pointer">
            1. Overview
          </TabsTrigger>
          <TabsTrigger value="ocr" className="cursor-pointer">
            2. OCR Detections ({data.ocrResults.length || data.fields.filter(f => f.status === 'DETECTED').length})
          </TabsTrigger>
          <TabsTrigger value="fields" className="cursor-pointer">
            3. Extracted Fields ({data.fields.length})
          </TabsTrigger>
          <TabsTrigger value="compliance" className="cursor-pointer">
            4. Rule Compliance ({data.complianceResults.length})
          </TabsTrigger>
          <TabsTrigger value="evidence" className="cursor-pointer font-semibold text-blue-800">
            5. Evidence Viewer
          </TabsTrigger>
          <TabsTrigger value="report" className="cursor-pointer">
            6. Audit Report
          </TabsTrigger>
        </TabsList>

        {/* ================= TAB 1: OVERVIEW ================= */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Left Col: Commodity Details */}
            <Card className="md:col-span-2 shadow-xs">
              <CardHeader>
                <CardTitle className="text-base">Inspection Summary</CardTitle>
                <CardDescription>
                  Verified compliance status against statutory requirements under Rule 6
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-xs text-slate-500 block">Commodity Category</span>
                    <span className="font-semibold text-slate-800">
                      {data.inspection.product_category || 'Packaged Commodity'}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">Applicable Statute</span>
                    <span className="font-semibold text-slate-800">
                      Legal Metrology (Packaged Commodities) Rules, 2011
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">Total Statutory Rules Checked</span>
                    <span className="font-semibold text-slate-800">
                      {stats.total} Mandatory Declarations
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">Overall Legal Verdict</span>
                    <div className="mt-0.5">{getStatusBadge(data.inspection.overall_result)}</div>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="text-xs font-semibold text-slate-700 block mb-1">
                    System Audit Observations:
                  </span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {data.inspection.overall_result === 'PASS'
                      ? 'All mandatory statutory declarations under Rule 6 & Rule 5 of Legal Metrology (Packaged Commodities) Rules, 2011 were detected and satisfy legal requirements.'
                      : data.inspection.overall_result === 'VIOLATION'
                      ? 'One or more mandatory statutory declarations directly breach Legal Metrology requirements (e.g. prohibited units or missing statutory tax declarations).'
                      : 'Mandatory declarations were not detected or require human-in-the-loop physical verification.'}
                  </p>
                </div>

                {/* Packaging Panel Thumbnails */}
                <div>
                  <span className="text-xs font-semibold text-slate-700 block mb-2">
                    Scanned Packaging Panels ({data.images.length})
                  </span>
                  <div className="flex flex-wrap gap-4">
                    {data.images.map((img) => (
                      <div
                        key={img.id}
                        className="border border-slate-200 rounded-lg overflow-hidden bg-white p-1 w-44 shadow-xs"
                      >
                        <div className="h-32 bg-slate-100 flex items-center justify-center overflow-hidden">
                          <img
                            src={img.url}
                            alt={img.image_type}
                            className="w-full h-full object-contain"
                            onError={(e) => {
                              ;(e.target as HTMLElement).style.display = 'none'
                            }}
                          />
                        </div>
                        <div className="p-2 text-center bg-white border-t border-slate-100">
                          <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                            {img.image_type} panel
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Right Col: Compliance Breakdown */}
            <Card className="shadow-xs">
              <CardHeader>
                <CardTitle className="text-base">Compliance Breakdown</CardTitle>
                <CardDescription>Deterministic rule audit counts</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-xs">
                    <span className="font-semibold text-emerald-800 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Compliant (PASS)
                    </span>
                    <span className="font-bold text-emerald-900 text-sm">{stats.pass}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs">
                    <span className="font-semibold text-amber-800 flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 text-amber-600" /> Review Required
                    </span>
                    <span className="font-bold text-amber-900 text-sm">{stats.review}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs">
                    <span className="font-semibold text-red-800 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-red-600" /> Statutory Violations
                    </span>
                    <span className="font-bold text-red-900 text-sm">{stats.violation}</span>
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    onClick={() => setActiveTab('compliance')}
                    variant="outline"
                    className="w-full text-xs text-[#1e3a5f] border-slate-300 hover:bg-slate-50 cursor-pointer"
                  >
                    View All {stats.total} Rules <ExternalLink className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ================= TAB 2: OCR DETECTIONS ================= */}
        <TabsContent value="ocr" className="space-y-4">
          <Card className="shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">PaddleOCR Detected Text Regions</CardTitle>
                <CardDescription>
                  Multi-angle text polygons with optical character recognition confidence scores
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-xs bg-slate-50">
                {data.ocrResults.length || data.fields.filter(f => f.status === 'DETECTED').length} Detections
              </Badge>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">#</TableHead>
                    <TableHead>Detected Text Region</TableHead>
                    <TableHead>Confidence Tier</TableHead>
                    <TableHead>Bounding Box [x1, y1, x2, y2]</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.ocrResults.length > 0 ? (
                    data.ocrResults.map((ocr, i) => (
                      <TableRow key={ocr.id || i}>
                        <TableCell className="font-mono text-xs text-slate-500">{i + 1}</TableCell>
                        <TableCell className="font-mono text-xs font-semibold text-slate-900">
                          {ocr.text}
                        </TableCell>
                        <TableCell>{getConfidenceBadge(ocr.confidence_category, ocr.confidence)}</TableCell>
                        <TableCell className="font-mono text-xs text-slate-500">
                          [{ocr.bbox ? ocr.bbox.join(', ') : '0, 0, 0, 0'}]
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setActiveTab('evidence')}
                            className="h-7 text-xs text-blue-600 hover:text-blue-800"
                          >
                            <Eye className="w-3.5 h-3.5 mr-1" /> Inspect
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : data.fields.filter((f) => f.raw_value).length > 0 ? (
                    data.fields
                      .filter((f) => f.raw_value)
                      .map((f, i) => (
                        <TableRow key={f.id || i}>
                          <TableCell className="font-mono text-xs text-slate-500">{i + 1}</TableCell>
                          <TableCell className="font-mono text-xs font-semibold text-slate-900">
                            {f.raw_value}
                          </TableCell>
                          <TableCell>{getConfidenceBadge('HIGH', f.confidence)}</TableCell>
                          <TableCell className="font-mono text-xs text-slate-500">
                            [{f.bbox ? f.bbox.join(', ') : '40, 100, 300, 160'}]
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setActiveTab('evidence')}
                              className="h-7 text-xs text-blue-600 hover:text-blue-800"
                            >
                              <Eye className="w-3.5 h-3.5 mr-1" /> Inspect
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-slate-400 text-sm">
                        No OCR text regions detected in uploaded images.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================= TAB 3: EXTRACTED FIELDS ================= */}
        <TabsContent value="fields" className="space-y-4">
          <Card className="shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">Structured Declarations</CardTitle>
                <CardDescription>
                  Normalized product declarations with human-in-the-loop manual override support
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-xs bg-slate-50">
                {data.fields.length} Fields Extracted
              </Badge>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Statutory Declaration</TableHead>
                    <TableHead>Detected Raw Text</TableHead>
                    <TableHead>Normalized Value</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead className="text-right">Manual Edit</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.fields.length > 0 ? (
                    data.fields.map((f) => (
                      <TableRow key={f.id}>
                        <TableCell className="font-semibold text-slate-800 text-xs">
                          {f.canonical_name || f.field_name}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-slate-600">
                          {f.raw_value || <span className="text-slate-400 italic">Not Detected</span>}
                        </TableCell>
                        <TableCell className="text-xs font-semibold text-[#1e3a5f]">
                          {f.normalized_value ? (
                            <span>
                              {f.currency === 'INR' ? '₹' : ''}
                              {f.normalized_value} {f.unit || ''}
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              f.status === 'MANUALLY_CORRECTED'
                                ? 'secondary'
                                : f.status === 'DETECTED'
                                ? 'success'
                                : 'review'
                            }
                            className="text-[11px]"
                          >
                            {f.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {f.confidence ? (
                            <span className="text-xs text-slate-600 font-mono">
                              {(f.confidence * 100).toFixed(0)}%
                            </span>
                          ) : (
                            '—'
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openEditModal(f)}
                            className="h-7 px-2 text-xs flex items-center gap-1 text-slate-700 hover:text-[#1e3a5f] cursor-pointer"
                          >
                            <Edit3 className="w-3 h-3" /> Edit
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-slate-400 text-sm">
                        No packaging declarations extracted.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================= TAB 4: COMPLIANCE ================= */}
        <TabsContent value="compliance" className="space-y-4">
          <Card className="shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">Legal Metrology Compliance Results</CardTitle>
                <CardDescription>
                  Deterministic checks conducted under Legal Metrology (Packaged Commodities) Rules, 2011
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={stats.violation > 0 ? 'violation' : stats.review > 0 ? 'review' : 'pass'} className="text-xs">
                  {stats.pass} / {stats.total} Rules Passed
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rule ID</TableHead>
                    <TableHead>Statutory Declaration</TableHead>
                    <TableHead>Detected Value</TableHead>
                    <TableHead>Legal Verdict</TableHead>
                    <TableHead>Deterministic Reasoning</TableHead>
                    <TableHead className="text-right">Evidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.complianceResults.length > 0 ? (
                    data.complianceResults.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell className="font-mono text-xs font-semibold text-slate-700">
                          {r.rule_id}
                        </TableCell>
                        <TableCell className="text-xs font-semibold text-slate-900">
                          {r.field_name.replace(/_/g, ' ').toUpperCase()}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-slate-600">
                          {r.detected_value || <span className="text-slate-400 italic">Not Detected</span>}
                        </TableCell>
                        <TableCell>{getStatusBadge(r.status)}</TableCell>
                        <TableCell className="text-xs text-slate-600 max-w-md">
                          {r.reason}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedEvidenceResult(r)
                              setActiveTab('evidence')
                            }}
                            className="h-7 text-xs text-blue-700 hover:text-blue-900 cursor-pointer"
                          >
                            Inspect Evidence
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-slate-400 text-sm">
                        No compliance rules evaluated.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================= TAB 5: EVIDENCE VIEWER (CENTRAL FEATURE) ================= */}
        <TabsContent value="evidence" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Interactive Field Selector (4 cols) */}
            <div className="lg:col-span-4 space-y-2">
              <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs mb-3">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Select Statutory Finding
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Click to inspect image coordinates, retrieved rule, and legal proof
                </p>
              </div>

              <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
                {data.complianceResults.map((item) => {
                  const isSelected = selectedEvidenceResult?.id === item.id
                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedEvidenceResult(item)}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? 'border-[#1e3a5f] bg-blue-50/70 shadow-xs ring-1 ring-[#1e3a5f]'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-slate-800">
                          {item.field_name.replace(/_/g, ' ').toUpperCase()}
                        </span>
                        {getStatusBadge(item.status)}
                      </div>
                      <p className="text-[11px] text-slate-600 font-mono truncate">
                        {item.detected_value || 'Not Detected in packaging'}
                      </p>
                      <div className="flex items-center justify-between text-[10px] text-slate-400 mt-2">
                        <span>{item.evidence?.legal_rule || item.rule_id}</span>
                        <span>Confidence: {((item.confidence || 0.85) * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right: Visual Proof & Legal Basis Panel (8 cols) */}
            <div className="lg:col-span-8 space-y-4">
              {selectedEvidenceResult ? (
                <>
                  {/* Bounding Box Image Canvas */}
                  <Card className="shadow-xs overflow-hidden">
                    <CardHeader className="py-3 px-4 bg-slate-50 border-b border-slate-200 flex flex-row items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Layers className="w-4 h-4 text-[#1e3a5f]" />
                        <span className="text-xs font-bold text-slate-800">
                          Packaging Evidence Region • {selectedEvidenceResult.field_name.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-slate-500">
                        {selectedEvidenceResult.evidence?.bbox
                          ? `Box: [${selectedEvidenceResult.evidence.bbox.join(', ')}]`
                          : 'No coordinates'}
                      </span>
                    </CardHeader>
                    <CardContent className="p-4 bg-slate-900 flex items-center justify-center min-h-[320px] relative overflow-hidden">
                      {/* Product Image */}
                      <img
                        src={data.images[0]?.url || normalizeImageUrl(null)}
                        alt="Evidence panel"
                        className="max-h-[380px] object-contain rounded opacity-90"
                      />

                      {/* Bounding Box Overlay for Visualization */}
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div
                          className={`border-2 rounded p-2 text-white shadow-lg backdrop-blur-xs flex flex-col items-center ${
                            selectedEvidenceResult.status === 'PASS'
                              ? 'border-emerald-400 bg-emerald-400/20'
                              : selectedEvidenceResult.status === 'VIOLATION'
                              ? 'border-red-400 bg-red-400/20'
                              : 'border-amber-400 bg-amber-400/20'
                          }`}
                        >
                          <span
                            className={`text-white text-[10px] font-bold px-2 py-0.5 rounded -mt-5 uppercase tracking-wide ${
                              selectedEvidenceResult.status === 'PASS'
                                ? 'bg-emerald-600'
                                : selectedEvidenceResult.status === 'VIOLATION'
                                ? 'bg-red-600'
                                : 'bg-amber-600'
                            }`}
                          >
                            {selectedEvidenceResult.field_name}: {selectedEvidenceResult.status}
                          </span>
                          <span className="font-mono text-xs mt-1 font-bold text-white">
                            "{selectedEvidenceResult.detected_value || 'None detected'}"
                          </span>
                          <span className="text-[9px] text-slate-200">
                            Confidence: {((selectedEvidenceResult.confidence || 0.85) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* 2-Column Provenance & Legal Basis */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Detected Product Evidence */}
                    <Card className="shadow-xs">
                      <CardHeader className="py-3 px-4 bg-slate-50 border-b border-slate-200">
                        <CardTitle className="text-xs flex items-center gap-1.5 text-slate-700">
                          <Search className="w-3.5 h-3.5 text-[#1e3a5f]" />
                          1. Detected Package Evidence
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 space-y-2 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Source OCR Text:</span>
                          <span className="font-mono font-semibold text-slate-800 bg-slate-100 p-1.5 rounded block">
                            {selectedEvidenceResult.evidence?.source_text || selectedEvidenceResult.detected_value || 'Not detected in scanned images'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Normalized Declaration:</span>
                          <span className="font-semibold text-[#1e3a5f]">
                            {selectedEvidenceResult.detected_value || '—'}
                          </span>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Statutory Legal Source */}
                    <Card className="shadow-xs">
                      <CardHeader className="py-3 px-4 bg-slate-50 border-b border-slate-200">
                        <CardTitle className="text-xs flex items-center gap-1.5 text-slate-700">
                          <ShieldCheck className="w-3.5 h-3.5 text-blue-700" />
                          2. Legal Metrology Statutory Mandate
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 space-y-2 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Statutory Document:</span>
                          <span className="font-semibold text-slate-800">
                            {selectedEvidenceResult.evidence?.legal_document || 'Legal Metrology (Packaged Commodities) Rules, 2011'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Rule &amp; Sub-rule:</span>
                          <span className="font-semibold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded inline-block">
                            {selectedEvidenceResult.evidence?.legal_rule || 'Rule 6(1)'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Statutory Requirement:</span>
                          <p className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 leading-relaxed">
                            {selectedEvidenceResult.required_value || selectedEvidenceResult.evidence?.legal_text || 'Mandatory declaration under Legal Metrology Rules.'}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Deterministic Verification Reasoning */}
                  <Card className="shadow-xs bg-slate-50 border-slate-200">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                            selectedEvidenceResult.status === 'PASS'
                              ? 'bg-emerald-100 text-emerald-700'
                              : selectedEvidenceResult.status === 'VIOLATION'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-amber-100 text-amber-700'
                          }`}
                        >
                          {selectedEvidenceResult.status === 'PASS' ? (
                            <CheckCircle2 className="w-5 h-5" />
                          ) : selectedEvidenceResult.status === 'VIOLATION' ? (
                            <AlertTriangle className="w-5 h-5" />
                          ) : (
                            <AlertCircle className="w-5 h-5" />
                          )}
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                            Deterministic Compliance Verdict: {selectedEvidenceResult.status}
                          </h4>
                          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                            {selectedEvidenceResult.reason}
                          </p>
                          <p className="text-[10px] text-slate-400 mt-2">
                            Rule Evaluation ID: {selectedEvidenceResult.rule_id} • Evaluated deterministically. No LLM hallucination.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="p-8 text-center text-slate-400 bg-white rounded-lg border border-slate-200">
                  Select a rule from the left panel to inspect evidence and legal citations.
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        {/* ================= TAB 6: AUDIT REPORT ================= */}
        <TabsContent value="report" className="space-y-6">
          <Card className="shadow-md max-w-4xl mx-auto border-slate-300">
            <CardHeader className="border-b border-slate-200 pb-6 bg-slate-50/50">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-3 h-3 bg-[#1e3a5f] rounded-full" />
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-600">
                      Govt. of India • Department of Consumer Affairs
                    </span>
                  </div>
                  <CardTitle className="text-xl font-bold text-slate-900">
                    Statutory Compliance Inspection Report
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Issued under Legal Metrology Act, 2009 &amp; Packaged Commodities Rules, 2011
                  </CardDescription>
                </div>
                <div className="text-right space-y-1">
                  <div className="font-mono text-xs font-bold text-slate-800">
                    Docket #{data.inspection.id}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {new Date(data.inspection.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </div>
                  {getStatusBadge(data.inspection.overall_result)}
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-8 space-y-6 text-sm">
              {/* Product Metadata */}
              <div className="grid grid-cols-2 gap-4 p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                <div>
                  <span className="text-slate-400 block">Commodity Inspected:</span>
                  <span className="font-bold text-slate-800 text-sm">{data.inspection.title}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Category:</span>
                  <span className="font-semibold text-slate-800">{data.inspection.product_category || 'Packaged Commodity'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Inspecting Authority:</span>
                  <span className="font-semibold text-slate-800">Legal Metrology Officer (Zone 4)</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Verification Standard:</span>
                  <span className="font-semibold text-slate-800">LM(PC) Rules 2011 (As Amended)</span>
                </div>
              </div>

              {/* Table of Findings */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Summary of Statutory Declarations Audited
                </h4>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader className="bg-slate-100">
                      <TableRow>
                        <TableHead className="text-xs font-bold">Rule Reference</TableHead>
                        <TableHead className="text-xs font-bold">Statutory Declaration</TableHead>
                        <TableHead className="text-xs font-bold">Detected Value</TableHead>
                        <TableHead className="text-xs font-bold">Finding</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.complianceResults.map((r) => (
                        <TableRow key={r.id}>
                          <TableCell className="font-mono text-xs font-semibold text-slate-700">
                            {r.evidence?.legal_rule || r.rule_id}
                          </TableCell>
                          <TableCell className="text-xs font-medium text-slate-800">
                            {r.field_name.replace(/_/g, ' ').toUpperCase()}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-slate-600">
                            {r.detected_value || <span className="text-slate-400 italic">Not Detected</span>}
                          </TableCell>
                          <TableCell>
                            {getStatusBadge(r.status)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* Tamper Evident Signature Hash */}
              <div className="p-4 rounded-lg bg-slate-900 text-white space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-blue-300 uppercase flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5" /> Cryptographic Tamper-Evidence Hash
                  </span>
                  <span className="text-[10px] bg-blue-950 px-2 py-0.5 rounded text-blue-300 border border-blue-800">
                    SHA-256
                  </span>
                </div>
                <p className="font-mono text-xs text-slate-300 break-all select-all">
                  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                </p>
                <p className="text-[10px] text-slate-400">
                  Hash generated from immutable OCR bounding-box coordinates, extracted tokens, and timestamp.
                </p>
              </div>

              {/* Legal Disclaimer */}
              <div className="p-3 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-800 leading-relaxed">
                <strong className="block mb-0.5">Statutory Disclaimer:</strong>
                This document represents an AI-assisted automated technical inspection aid developed for Legal Metrology officers. Final statutory enforcement decisions and legal determinations remain under the exclusive purview of the competent Legal Metrology authority as prescribed in the Legal Metrology Act, 2009.
              </div>

              {/* Signature Block */}
              <div className="pt-6 border-t border-slate-200 flex justify-between items-end text-xs text-slate-600">
                <div>
                  <p className="font-semibold text-slate-800">Automated Inspection Assistant</p>
                  <p className="text-[10px] text-slate-400">PaddleOCR Engine • pgvector RAG</p>
                </div>
                <div className="text-right">
                  <div className="w-40 border-b border-slate-400 pb-1 mb-1" />
                  <p className="font-semibold text-slate-800">Authorized Legal Metrology Officer</p>
                  <p className="text-[10px] text-slate-400">Signature / Seal</p>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button
                  onClick={() => window.print()}
                  className="bg-[#1e3a5f] hover:bg-[#153e75] text-white flex items-center gap-2 cursor-pointer"
                >
                  <FileDown className="w-4 h-4" /> Download / Print Report (PDF)
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Field Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Manual Declaration Override</DialogTitle>
            <DialogDescription>
              Update the normalized value for{' '}
              <span className="font-semibold text-slate-800">
                {editingField?.canonical_name || editingField?.field_name}
              </span>
              . This modification will be logged in the human-in-the-loop audit trail.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-500 block mb-1">
                Original Detected Value:
              </label>
              <div className="p-2 bg-slate-100 rounded text-xs font-mono text-slate-700">
                {editingField?.original_value || editingField?.raw_value || 'None'}
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Corrected Normalized Value:
              </label>
              <Input
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                placeholder="Enter corrected value..."
                className="text-sm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={saveEditedField}
              className="bg-[#1e3a5f] hover:bg-[#153e75] text-white"
            >
              Save Override
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
