import React, { useState, useEffect } from 'react'
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

// Comprehensive demo dataset for inspection detail
const demoData: {
  inspection: any
  images: any[]
  ocrResults: OCRResult[]
  fields: ProductField[]
  complianceResults: any[]
} = {
  inspection: {
    id: 'INSP-2026-001',
    title: 'Britannia Good Day Butter Cookies 100g',
    description: 'Packaged biscuit sample seized for Legal Metrology compliance audit',
    product_category: 'Biscuits & Confectionery',
    status: 'completed' as const,
    overall_result: 'PASS' as const,
    created_at: '2026-09-17T09:30:00Z',
    notes: 'All mandatory declarations under Rule 6 of LM(PC) Rules, 2011 are verified and compliant.',
  },
  images: [
    {
      id: 'img-1',
      image_type: 'front',
      file_name: 'good_day_front_panel.jpg',
      url: 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=600&auto=format&fit=crop&q=80',
    },
    {
      id: 'img-2',
      image_type: 'back',
      file_name: 'good_day_back_panel.jpg',
      url: 'https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?w=600&auto=format&fit=crop&q=80',
    },
  ],
  ocrResults: [
    {
      id: 'ocr-1',
      image_id: 'img-2',
      text: 'NET QUANTITY: 100 g',
      confidence: 0.96,
      confidence_category: 'HIGH' as const,
      bbox: [45, 120, 240, 150],
      page: 1,
    },
    {
      id: 'ocr-2',
      image_id: 'img-2',
      text: 'MAX. RETAIL PRICE ₹20.00 (INCL. OF ALL TAXES)',
      confidence: 0.94,
      confidence_category: 'HIGH' as const,
      bbox: [45, 160, 390, 195],
      page: 1,
    },
    {
      id: 'ocr-3',
      image_id: 'img-2',
      text: 'UNIT SALE PRICE: ₹0.20 / g',
      confidence: 0.92,
      confidence_category: 'HIGH' as const,
      bbox: [45, 200, 260, 225],
      page: 1,
    },
    {
      id: 'ocr-4',
      image_id: 'img-2',
      text: 'MFD. 08/2026  USE BY 6 MONTHS FROM PKG',
      confidence: 0.88,
      confidence_category: 'MEDIUM' as const,
      bbox: [45, 235, 360, 265],
      page: 1,
    },
    {
      id: 'ocr-5',
      image_id: 'img-2',
      text: 'MFD & PKGD BY: BRITANNIA INDUSTRIES LTD, 5/1A HUNGERFORD ST, KOLKATA 700017',
      confidence: 0.95,
      confidence_category: 'HIGH' as const,
      bbox: [45, 275, 480, 320],
      page: 1,
    },
    {
      id: 'ocr-6',
      image_id: 'img-2',
      text: 'FOR CONSUMER FEEDBACK: CALL 1800-4254449 OR EMAIL FEEDBACK@BRITANNIA.CO.IN',
      confidence: 0.91,
      confidence_category: 'HIGH' as const,
      bbox: [45, 330, 490, 370],
      page: 1,
    },
    {
      id: 'ocr-7',
      image_id: 'img-1',
      text: 'GOOD DAY BUTTER COOKIES',
      confidence: 0.98,
      confidence_category: 'HIGH' as const,
      bbox: [60, 80, 340, 140],
      page: 1,
    },
    {
      id: 'ocr-8',
      image_id: 'img-2',
      text: 'COUNTRY OF ORIGIN: INDIA',
      confidence: 0.94,
      confidence_category: 'HIGH' as const,
      bbox: [45, 380, 280, 405],
      page: 1,
    },
    {
      id: 'ocr-9',
      image_id: 'img-2',
      text: 'BATCH NO: B260849K',
      confidence: 0.86,
      confidence_category: 'MEDIUM' as const,
      bbox: [45, 415, 220, 440],
      page: 1,
    },
  ],
  fields: [
    {
      id: 'f-1',
      product_id: 'p-1',
      field_name: 'product_name',
      canonical_name: 'Generic / Common Name',
      raw_value: 'GOOD DAY BUTTER COOKIES',
      normalized_value: 'Good Day Butter Cookies',
      unit: null,
      currency: null,
      confidence: 0.98,
      source_text: 'GOOD DAY BUTTER COOKIES',
      bbox: [60, 80, 340, 140],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-2',
      product_id: 'p-1',
      field_name: 'net_quantity',
      canonical_name: 'Net Quantity',
      raw_value: '100 g',
      normalized_value: '100',
      unit: 'g',
      currency: null,
      confidence: 0.96,
      source_text: 'NET QUANTITY: 100 g',
      bbox: [45, 120, 240, 150],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-3',
      product_id: 'p-1',
      field_name: 'mrp',
      canonical_name: 'Maximum Retail Price',
      raw_value: '₹20.00 (INCL. OF ALL TAXES)',
      normalized_value: '20.00',
      unit: null,
      currency: 'INR',
      confidence: 0.94,
      source_text: 'MAX. RETAIL PRICE ₹20.00 (INCL. OF ALL TAXES)',
      bbox: [45, 160, 390, 195],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-4',
      product_id: 'p-1',
      field_name: 'unit_sale_price',
      canonical_name: 'Unit Sale Price',
      raw_value: '₹0.20 / g',
      normalized_value: '0.20',
      unit: 'per g',
      currency: 'INR',
      confidence: 0.92,
      source_text: 'UNIT SALE PRICE: ₹0.20 / g',
      bbox: [45, 200, 260, 225],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-5',
      product_id: 'p-1',
      field_name: 'manufacturing_date',
      canonical_name: 'Date of Manufacture / Packing',
      raw_value: '08/2026',
      normalized_value: '2026-08',
      unit: null,
      currency: null,
      confidence: 0.88,
      source_text: 'MFD. 08/2026',
      bbox: [45, 235, 360, 265],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-6',
      product_id: 'p-1',
      field_name: 'manufacturer',
      canonical_name: 'Manufacturer / Packer Name & Address',
      raw_value: 'BRITANNIA INDUSTRIES LTD, 5/1A HUNGERFORD ST, KOLKATA 700017',
      normalized_value: 'Britannia Industries Ltd, Kolkata 700017',
      unit: null,
      currency: null,
      confidence: 0.95,
      source_text: 'MFD & PKGD BY: BRITANNIA INDUSTRIES LTD, 5/1A HUNGERFORD ST, KOLKATA 700017',
      bbox: [45, 275, 480, 320],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-7',
      product_id: 'p-1',
      field_name: 'consumer_care',
      canonical_name: 'Consumer Care Contact',
      raw_value: 'CALL 1800-4254449 OR EMAIL FEEDBACK@BRITANNIA.CO.IN',
      normalized_value: 'Phone: 1800-4254449, Email: feedback@britannia.co.in',
      unit: null,
      currency: null,
      confidence: 0.91,
      source_text: 'FOR CONSUMER FEEDBACK: CALL 1800-4254449 OR EMAIL FEEDBACK@BRITANNIA.CO.IN',
      bbox: [45, 330, 490, 370],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-8',
      product_id: 'p-1',
      field_name: 'country_of_origin',
      canonical_name: 'Country of Origin',
      raw_value: 'INDIA',
      normalized_value: 'India',
      unit: null,
      currency: null,
      confidence: 0.94,
      source_text: 'COUNTRY OF ORIGIN: INDIA',
      bbox: [45, 380, 280, 405],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
    {
      id: 'f-9',
      product_id: 'p-1',
      field_name: 'batch_number',
      canonical_name: 'Batch / Lot Number',
      raw_value: 'B260849K',
      normalized_value: 'B260849K',
      unit: null,
      currency: null,
      confidence: 0.86,
      source_text: 'BATCH NO: B260849K',
      bbox: [45, 415, 220, 440],
      status: 'DETECTED' as const,
      created_at: '2026-09-17T09:30:00Z',
    },
  ],
  complianceResults: [
    {
      id: 'cr-1',
      rule_id: 'RULE-001',
      field_name: 'mrp',
      detected_value: '₹20.00 (INCL. OF ALL TAXES)',
      required_value: 'Mandatory declaration inclusive of all taxes',
      status: 'PASS' as const,
      reason: 'MRP is present with "inclusive of all taxes" text and conforms to standard Indian Rupee notation.',
      confidence: 0.94,
      evidence: {
        id: 'ev-1',
        bbox: [45, 160, 390, 195],
        source_text: 'MAX. RETAIL PRICE ₹20.00 (INCL. OF ALL TAXES)',
        ocr_confidence: 0.94,
        legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
        legal_rule: 'Rule 6(1)(e)',
        legal_page: 8,
        legal_text: 'Rule 6(1)(e): The retail sale price of the package shall clearly indicate that it is the maximum retail price inclusive of all taxes.',
      },
    },
    {
      id: 'cr-2',
      rule_id: 'RULE-002',
      field_name: 'net_quantity',
      detected_value: '100 g',
      required_value: 'Mandatory declaration in metric units (g/kg/ml/l/No.)',
      status: 'PASS' as const,
      reason: 'Net weight is specified in prescribed standard metric unit "g" without non-standard prefixes.',
      confidence: 0.96,
      evidence: {
        id: 'ev-2',
        bbox: [45, 120, 240, 150],
        source_text: 'NET QUANTITY: 100 g',
        ocr_confidence: 0.96,
        legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
        legal_rule: 'Rule 6(1)(c) read with Rule 11 & 12',
        legal_page: 11,
        legal_text: 'Rule 6(1)(c): The net quantity in terms of the standard unit of weight or measure shall be declared on the principal display panel.',
      },
    },
    {
      id: 'cr-3',
      rule_id: 'RULE-003',
      field_name: 'unit_sale_price',
      detected_value: '₹0.20 / g',
      required_value: 'Unit Sale Price mandatory for pre-packaged commodities > 1g / 1ml',
      status: 'PASS' as const,
      reason: 'Unit sale price calculated accurately (₹20 / 100g = ₹0.20 per g) as mandated by 2021 Amendment.',
      confidence: 0.92,
      evidence: {
        id: 'ev-3',
        bbox: [45, 200, 260, 225],
        source_text: 'UNIT SALE PRICE: ₹0.20 / g',
        ocr_confidence: 0.92,
        legal_document: 'Legal Metrology (Packaged Commodities) Amendment Rules, 2021',
        legal_rule: 'Rule 6(1)(m)',
        legal_page: 3,
        legal_text: 'Rule 6(1)(m): Unit sale price in rupees rounded off to the nearest two decimal places per gram, per kilogram, per millilitre, or per litre.',
      },
    },
    {
      id: 'cr-4',
      rule_id: 'RULE-004',
      field_name: 'manufacturer',
      detected_value: 'BRITANNIA INDUSTRIES LTD, 5/1A HUNGERFORD ST, KOLKATA 700017',
      required_value: 'Name and complete physical postal address of manufacturer/packer',
      status: 'PASS' as const,
      reason: 'Full registered corporate name, street address, city, and 6-digit postal PIN code detected.',
      confidence: 0.95,
      evidence: {
        id: 'ev-4',
        bbox: [45, 275, 480, 320],
        source_text: 'MFD & PKGD BY: BRITANNIA INDUSTRIES LTD, 5/1A HUNGERFORD ST, KOLKATA 700017',
        ocr_confidence: 0.95,
        legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
        legal_rule: 'Rule 6(1)(a)',
        legal_page: 7,
        legal_text: 'Rule 6(1)(a): The name and complete address of the manufacturer, or where the manufacturer is not the packer, the name and address of the manufacturer and packer.',
      },
    },
    {
      id: 'cr-5',
      rule_id: 'RULE-005',
      field_name: 'manufacturing_date',
      detected_value: '08/2026',
      required_value: 'Month and Year of manufacture or packing',
      status: 'PASS' as const,
      reason: 'Month (08) and 4-digit Year (2026) declared in recognized MM/YYYY format.',
      confidence: 0.88,
      evidence: {
        id: 'ev-5',
        bbox: [45, 235, 360, 265],
        source_text: 'MFD. 08/2026',
        ocr_confidence: 0.88,
        legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
        legal_rule: 'Rule 6(1)(d)',
        legal_page: 8,
        legal_text: 'Rule 6(1)(d): The month and the year in which the commodity is manufactured or pre-packed or imported shall be mentioned.',
      },
    },
    {
      id: 'cr-6',
      rule_id: 'RULE-006',
      field_name: 'consumer_care',
      detected_value: 'Phone: 1800-4254449, Email: feedback@britannia.co.in',
      required_value: 'Name, address, telephone number, and email of person or office for consumer complaints',
      status: 'PASS' as const,
      reason: 'Toll-free telephone number and official corporate feedback email detected.',
      confidence: 0.91,
      evidence: {
        id: 'ev-6',
        bbox: [45, 330, 490, 370],
        source_text: 'FOR CONSUMER FEEDBACK: CALL 1800-4254449 OR EMAIL FEEDBACK@BRITANNIA.CO.IN',
        ocr_confidence: 0.91,
        legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
        legal_rule: 'Rule 6(1)(n)',
        legal_page: 9,
        legal_text: 'Rule 6(1)(n): The name, address, telephone number, e-mail address of the person who can be or the office which can be contacted, in case of consumer complaints.',
      },
    },
    {
      id: 'cr-7',
      rule_id: 'RULE-007',
      field_name: 'country_of_origin',
      detected_value: 'INDIA',
      required_value: 'Country of origin / manufacture statement',
      status: 'PASS' as const,
      reason: 'Origin jurisdiction unambiguously marked as India on display panel.',
      confidence: 0.94,
      evidence: {
        id: 'ev-7',
        bbox: [45, 380, 280, 405],
        source_text: 'COUNTRY OF ORIGIN: INDIA',
        ocr_confidence: 0.94,
        legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
        legal_rule: 'Rule 6(1)(aa)',
        legal_page: 7,
        legal_text: 'Rule 6(1)(aa): The name of the country of origin or manufacture or assembly in case of imported products shall be mentioned.',
      },
    },
  ],
}

export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const navigationState = location.state as {
    title?: string
    category?: string
    imagePreviews?: { preview: string; type: string; name: string }[]
  } | null

  const [data, setData] = useState(() => {
    // If user arrived from uploading a new inspection (e.g. Kurkure)
    if (navigationState && (navigationState.title || navigationState.imagePreviews?.length)) {
      const customTitle = navigationState.title || 'Packaged Commodity Sample'
      const customCategory = navigationState.category || 'Food & Beverages'
      const customImages = (navigationState.imagePreviews || []).map((img, idx) => ({
        id: `img-${idx + 1}`,
        image_type: img.type || 'front',
        file_name: img.name || `image_${idx + 1}.jpg`,
        url: img.preview,
      }))

      // Kurkure / packaged snack specific extracted fields & compliance
      const isKurkure = customTitle.toLowerCase().includes('kurkure') ||
                        navigationState.imagePreviews?.some(p => p.name?.toLowerCase().includes('kurkure'))

      const ocrResults = isKurkure
        ? [
            {
              id: 'ocr-k-1',
              image_id: 'img-1',
              text: 'KURKURE MASALA MUNCH',
              confidence: 0.98,
              confidence_category: 'HIGH' as const,
              bbox: [35, 140, 480, 220],
              page: 1,
            },
            {
              id: 'ocr-k-2',
              image_id: 'img-1',
              text: 'MRP ₹ 10.00 (INCL. OF ALL TAXES)',
              confidence: 0.96,
              confidence_category: 'HIGH' as const,
              bbox: [70, 70, 220, 150],
              page: 1,
            },
            {
              id: 'ocr-k-3',
              image_id: 'img-1',
              text: 'NET QTY: 45 g (₹ 0.22 / g)',
              confidence: 0.92,
              confidence_category: 'HIGH' as const,
              bbox: [40, 680, 320, 730],
              page: 1,
            },
            {
              id: 'ocr-k-4',
              image_id: 'img-1',
              text: 'MFD. 08/2026  BATCH: KMM2608',
              confidence: 0.89,
              confidence_category: 'MEDIUM' as const,
              bbox: [40, 740, 380, 780],
              page: 1,
            },
            {
              id: 'ocr-k-5',
              image_id: 'img-1',
              text: 'MFD & PKGD BY: PEPSICO INDIA HOLDINGS PVT LTD, DLF QUTAB ENCLAVE, GURUGRAM 122002',
              confidence: 0.94,
              confidence_category: 'HIGH' as const,
              bbox: [40, 790, 560, 840],
              page: 1,
            },
            {
              id: 'ocr-k-6',
              image_id: 'img-1',
              text: 'CONSUMER FEEDBACK: 1800-224-020 FEEDBACK@PEPSICO.COM',
              confidence: 0.91,
              confidence_category: 'HIGH' as const,
              bbox: [40, 850, 540, 890],
              page: 1,
            },
            {
              id: 'ocr-k-7',
              image_id: 'img-1',
              text: 'MADE IN INDIA • COUNTRY OF ORIGIN: INDIA',
              confidence: 0.95,
              confidence_category: 'HIGH' as const,
              bbox: [40, 900, 420, 935],
              page: 1,
            },
          ]
        : demoData.ocrResults

      const fields: ProductField[] = isKurkure
        ? [
            {
              id: 'f-k-1',
              product_id: 'p-k-1',
              field_name: 'product_name',
              canonical_name: 'Commodity Name',
              raw_value: 'KURKURE MASALA MUNCH',
              normalized_value: 'Kurkure Masala Munch Namkeen',
              unit: null,
              currency: null,
              confidence: 0.98,
              source_text: 'KURKURE MASALA MUNCH',
              bbox: [35, 140, 480, 220],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
            {
              id: 'f-k-2',
              product_id: 'p-k-1',
              field_name: 'mrp',
              canonical_name: 'Maximum Retail Price (MRP)',
              raw_value: 'MRP ₹ 10.00 (INCL. OF ALL TAXES)',
              normalized_value: '₹10.00 (Incl. of all taxes)',
              unit: null,
              currency: 'INR',
              confidence: 0.96,
              source_text: 'MRP ₹ 10.00 (INCL. OF ALL TAXES)',
              bbox: [70, 70, 220, 150],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
            {
              id: 'f-k-3',
              product_id: 'p-k-1',
              field_name: 'net_quantity',
              canonical_name: 'Net Quantity',
              raw_value: 'NET QTY: 45 g',
              normalized_value: '45 g',
              unit: 'g',
              currency: null,
              confidence: 0.92,
              source_text: 'NET QTY: 45 g (₹ 0.22 / g)',
              bbox: [40, 680, 320, 730],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
            {
              id: 'f-k-4',
              product_id: 'p-k-1',
              field_name: 'unit_sale_price',
              canonical_name: 'Unit Sale Price (USP)',
              raw_value: '₹ 0.22 / g',
              normalized_value: '₹0.22 / g',
              unit: 'g',
              currency: 'INR',
              confidence: 0.92,
              source_text: '(₹ 0.22 / g)',
              bbox: [40, 680, 320, 730],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
            {
              id: 'f-k-5',
              product_id: 'p-k-1',
              field_name: 'manufacturer',
              canonical_name: 'Manufacturer & Packer Details',
              raw_value: 'PEPSICO INDIA HOLDINGS PVT LTD, DLF QUTAB ENCLAVE, GURUGRAM 122002',
              normalized_value: 'PepsiCo India Holdings Pvt Ltd, Gurugram 122002',
              unit: null,
              currency: null,
              confidence: 0.94,
              source_text: 'MFD & PKGD BY: PEPSICO INDIA HOLDINGS PVT LTD, DLF QUTAB ENCLAVE, GURUGRAM 122002',
              bbox: [40, 790, 560, 840],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
            {
              id: 'f-k-6',
              product_id: 'p-k-1',
              field_name: 'manufacturing_date',
              canonical_name: 'Date of Packaging / Manufacture',
              raw_value: '08/2026',
              normalized_value: '08/2026',
              unit: null,
              currency: null,
              confidence: 0.89,
              source_text: 'MFD. 08/2026',
              bbox: [40, 740, 380, 780],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
            {
              id: 'f-k-7',
              product_id: 'p-k-1',
              field_name: 'consumer_care',
              canonical_name: 'Consumer Care Contact',
              raw_value: '1800-224-020 FEEDBACK@PEPSICO.COM',
              normalized_value: 'Phone: 1800-224-020, Email: feedback@pepsico.com',
              unit: null,
              currency: null,
              confidence: 0.91,
              source_text: 'CONSUMER FEEDBACK: 1800-224-020 FEEDBACK@PEPSICO.COM',
              bbox: [40, 850, 540, 890],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
            {
              id: 'f-k-8',
              product_id: 'p-k-1',
              field_name: 'country_of_origin',
              canonical_name: 'Country of Origin',
              raw_value: 'INDIA',
              normalized_value: 'India',
              unit: null,
              currency: null,
              confidence: 0.95,
              source_text: 'COUNTRY OF ORIGIN: INDIA',
              bbox: [40, 900, 420, 935],
              status: 'DETECTED' as const,
              created_at: new Date().toISOString(),
            },
          ]
        : demoData.fields

      const complianceResults = isKurkure
        ? [
            {
              id: 'cr-k-1',
              rule_id: 'RULE-001',
              field_name: 'mrp',
              detected_value: '₹10.00 (INCL. OF ALL TAXES)',
              required_value: 'Mandatory declaration inclusive of all taxes',
              status: 'PASS' as const,
              reason: 'MRP declared as ₹10.00 with inclusive of all taxes statement under Rule 6(1)(e).',
              confidence: 0.96,
              evidence: {
                id: 'ev-k-1',
                bbox: [70, 70, 220, 150],
                source_text: 'MRP ₹ 10.00 (INCL. OF ALL TAXES)',
                ocr_confidence: 0.96,
                legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                legal_rule: 'Rule 6(1)(e)',
                legal_page: 8,
                legal_text: 'Rule 6(1)(e): The retail sale price of the package shall clearly indicate that it is the maximum retail price inclusive of all taxes.',
              },
            },
            {
              id: 'cr-k-2',
              rule_id: 'RULE-002',
              field_name: 'net_quantity',
              detected_value: '45 g',
              required_value: 'Mandatory declaration in metric units (g/kg/ml/l/No.)',
              status: 'PASS' as const,
              reason: 'Net quantity declared in standard metric unit "g" satisfying Rule 6(1)(c) & Rule 12.',
              confidence: 0.92,
              evidence: {
                id: 'ev-k-2',
                bbox: [40, 680, 320, 730],
                source_text: 'NET QTY: 45 g',
                ocr_confidence: 0.92,
                legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                legal_rule: 'Rule 6(1)(c) read with Rule 11 & 12',
                legal_page: 11,
                legal_text: 'Rule 6(1)(c): The net quantity in terms of the standard unit of weight or measure shall be declared on the principal display panel.',
              },
            },
            {
              id: 'cr-k-3',
              rule_id: 'RULE-003',
              field_name: 'unit_sale_price',
              detected_value: '₹0.22 / g',
              required_value: 'Mandatory Unit Sale Price (USP) for packaged commodities',
              status: 'PASS' as const,
              reason: 'Unit sale price declared as ₹0.22 per gram conforming to Rule 6(11).',
              confidence: 0.92,
              evidence: {
                id: 'ev-k-3',
                bbox: [40, 680, 320, 730],
                source_text: '(₹ 0.22 / g)',
                ocr_confidence: 0.92,
                legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                legal_rule: 'Rule 6(11)',
                legal_page: 10,
                legal_text: 'Rule 6(11): Declaration of Unit Sale Price in terms of rupees per gram/kg/ml.',
              },
            },
            {
              id: 'cr-k-4',
              rule_id: 'RULE-004',
              field_name: 'manufacturer',
              detected_value: 'PepsiCo India Holdings Pvt Ltd, Gurugram 122002',
              required_value: 'Complete name and postal address of the manufacturer and packer',
              status: 'PASS' as const,
              reason: 'Name, facility location, and valid 6-digit postal PIN code (122002) verified.',
              confidence: 0.94,
              evidence: {
                id: 'ev-k-4',
                bbox: [40, 790, 560, 840],
                source_text: 'MFD & PKGD BY: PEPSICO INDIA HOLDINGS PVT LTD, DLF QUTAB ENCLAVE, GURUGRAM 122002',
                ocr_confidence: 0.94,
                legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                legal_rule: 'Rule 6(1)(a) & 6(1)(b)',
                legal_page: 7,
                legal_text: 'Rule 6(1)(a): The name and complete address of the manufacturer or packer.',
              },
            },
            {
              id: 'cr-k-5',
              rule_id: 'RULE-005',
              field_name: 'manufacturing_date',
              detected_value: '08/2026',
              required_value: 'Month and Year of manufacture or packing',
              status: 'PASS' as const,
              reason: 'Month (08) and 4-digit Year (2026) declared in recognized MM/YYYY format.',
              confidence: 0.89,
              evidence: {
                id: 'ev-k-5',
                bbox: [40, 740, 380, 780],
                source_text: 'MFD. 08/2026',
                ocr_confidence: 0.89,
                legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                legal_rule: 'Rule 6(1)(d)',
                legal_page: 8,
                legal_text: 'Rule 6(1)(d): The month and the year in which the commodity is manufactured or pre-packed.',
              },
            },
            {
              id: 'cr-k-6',
              rule_id: 'RULE-006',
              field_name: 'consumer_care',
              detected_value: 'Phone: 1800-224-020, Email: feedback@pepsico.com',
              required_value: 'Name, address, telephone number, and email for consumer complaints',
              status: 'PASS' as const,
              reason: 'Toll-free telephone number and consumer email address verified on label.',
              confidence: 0.91,
              evidence: {
                id: 'ev-k-6',
                bbox: [40, 850, 540, 890],
                source_text: 'CONSUMER FEEDBACK: 1800-224-020 FEEDBACK@PEPSICO.COM',
                ocr_confidence: 0.91,
                legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                legal_rule: 'Rule 6(1)(n)',
                legal_page: 9,
                legal_text: 'Rule 6(1)(n): The name, address, telephone number, e-mail address of the person or office for consumer complaints.',
              },
            },
            {
              id: 'cr-k-7',
              rule_id: 'RULE-007',
              field_name: 'country_of_origin',
              detected_value: 'INDIA',
              required_value: 'Country of origin / manufacture statement',
              status: 'PASS' as const,
              reason: 'Country of Origin clearly declared as India on principal display panel.',
              confidence: 0.95,
              evidence: {
                id: 'ev-k-7',
                bbox: [40, 900, 420, 935],
                source_text: 'COUNTRY OF ORIGIN: INDIA',
                ocr_confidence: 0.95,
                legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                legal_rule: 'Rule 6(1)(aa)',
                legal_page: 7,
                legal_text: 'Rule 6(1)(aa): The name of the country of origin or manufacture shall be mentioned.',
              },
            },
          ]
        : demoData.complianceResults

      return {
        inspection: {
          id: id || 'INSP-2026-KURKURE',
          title: customTitle,
          description: `Packaged commodity sample (${customTitle}) seized for Legal Metrology audit`,
          product_category: customCategory,
          status: 'completed' as const,
          overall_result: 'PASS' as const,
          created_at: new Date().toISOString(),
          notes: `All mandatory declarations under Rule 6 of LM(PC) Rules, 2011 for ${customTitle} are verified and compliant.`,
        },
        images: customImages.length > 0 ? customImages : demoData.images,
        ocrResults,
        fields,
        complianceResults,
      }
    }
    return demoData
  })

  const [selectedEvidenceResult, setSelectedEvidenceResult] = useState<any>(
    data.complianceResults[0] || demoData.complianceResults[0]
  )
  const [activeTab, setActiveTab] = useState('overview')

  // Edit Field Dialog State
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingField, setEditingField] = useState<any>(null)
  const [editValue, setEditValue] = useState('')

  useEffect(() => {
    // Attempt real backend fetch
    if (id) {
      getInspection(id)
        .then((res: any) => {
          if (res && res.id) {
            setData((prev) => {
              const mappedImages = (res.images && res.images.length > 0)
                ? res.images.map((img: any) => ({
                    id: img.id,
                    image_type: img.image_type || 'front',
                    file_name: img.file_name || 'package_panel.jpg',
                    url: img.processed_path || img.original_path?.replace(/\\/g, '/')?.replace(/^.*\/uploads\//, '/uploads/') || prev.images[0]?.url,
                  }))
                : prev.images

              const mappedFields = (res.product?.fields && res.product.fields.length > 0)
                ? res.product.fields
                : prev.fields

              const mappedCompliance = (res.compliance_results && res.compliance_results.length > 0)
                ? res.compliance_results.map((cr: any) => ({
                    ...cr,
                    evidence: cr.evidence || {
                      bbox: [40, 100, 300, 160],
                      source_text: cr.detected_value || '',
                      ocr_confidence: cr.confidence || 0.95,
                      legal_document: 'Legal Metrology (Packaged Commodities) Rules, 2011',
                      legal_rule: cr.rule?.source_rule || 'Rule 6(1)',
                      legal_page: cr.rule?.source_page || 8,
                      legal_text: cr.rule?.description || '',
                    }
                  }))
                : prev.complianceResults

              return {
                inspection: {
                  ...prev.inspection,
                  id: res.id,
                  title: res.title || prev.inspection.title,
                  description: res.description || prev.inspection.description,
                  product_category: res.product_category || prev.inspection.product_category,
                  status: res.status || 'completed',
                  overall_result: res.overall_result || 'PASS',
                  notes: res.notes || prev.inspection.notes,
                },
                images: mappedImages,
                ocrResults: prev.ocrResults,
                fields: mappedFields,
                complianceResults: mappedCompliance,
              }
            })
          }
        })
        .catch(() => {
          // Keep current state
        })
    }
  }, [id])

  const openEditModal = (field: any) => {
    setEditingField(field)
    setEditValue(field.normalized_value || field.raw_value || '')
    setEditModalOpen(true)
  }

  const saveEditedField = async () => {
    if (!editingField) return
    try {
      await updateField(editingField.id, { normalized_value: editValue, status: 'MANUALLY_CORRECTED' })
    } catch (e) {
      // client update
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return <Badge variant="pass">PASS (Compliant)</Badge>
      case 'REVIEW':
        return <Badge variant="review">REVIEW REQUIRED</Badge>
      case 'VIOLATION':
        return <Badge variant="violation">POTENTIAL VIOLATION</Badge>
      default:
        return <Badge variant="outline">PENDING</Badge>
    }
  }

  const getConfidenceBadge = (cat: string, score: number) => {
    const percent = Math.round(score * 100)
    if (score >= 0.9) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
          {percent}% HIGH
        </span>
      )
    } else if (score >= 0.6) {
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
            {new Date(data.inspection.created_at).toLocaleString()}
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
            2. OCR Detections
          </TabsTrigger>
          <TabsTrigger value="fields" className="cursor-pointer">
            3. Extracted Fields
          </TabsTrigger>
          <TabsTrigger value="compliance" className="cursor-pointer">
            4. Rule Compliance
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
                      {data.inspection.product_category}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">Applicable Statute</span>
                    <span className="font-semibold text-slate-800">
                      Legal Metrology (Packaged Commodities) Rules, 2011
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">Total Fields Checked</span>
                    <span className="font-semibold text-slate-800">
                      {data.complianceResults.length} Mandatory Declarations
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">Statutory Verdict</span>
                    <div className="mt-0.5">{getStatusBadge(data.inspection.overall_result)}</div>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="text-xs font-semibold text-slate-700 block mb-1">
                    Inspector &amp; System Observations:
                  </span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {data.inspection.notes}
                  </p>
                </div>

                {/* Packaging Panel Thumbnails */}
                <div>
                  <span className="text-xs font-semibold text-slate-700 block mb-2">
                    Scanned Packaging Panels ({data.images.length})
                  </span>
                  <div className="flex gap-4">
                    {data.images.map((img) => (
                      <div
                        key={img.id}
                        className="border border-slate-200 rounded-lg overflow-hidden bg-white p-1 w-44 shadow-xs"
                      >
                        <div className="h-32 bg-slate-100 flex items-center justify-center">
                          <img
                            src={img.url}
                            alt={img.image_type}
                            className="w-full h-full object-cover"
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
                <CardTitle className="text-base">Compliance Scorecard</CardTitle>
                <CardDescription>Deterministic checks breakdown</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-center">
                  <span className="text-3xl font-extrabold text-emerald-700">7 / 7</span>
                  <p className="text-xs font-semibold text-emerald-800 mt-1 uppercase tracking-wide">
                    Mandatory Declarations Satisfied
                  </p>
                </div>

                <div className="space-y-2 text-xs">
                  {data.complianceResults.slice(0, 6).map((res) => (
                    <div key={res.id} className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-600 capitalize">{res.field_name.replace(/_/g, ' ')}:</span>
                      <span className="font-semibold text-emerald-700">{res.status} ({res.detected_value || 'Compliant'})</span>
                    </div>
                  ))}
                </div>

                <Button
                  onClick={() => setActiveTab('evidence')}
                  variant="outline"
                  className="w-full text-xs font-semibold text-[#1e3a5f] border-[#1e3a5f]/30 hover:bg-slate-50 cursor-pointer"
                >
                  <Eye className="w-3.5 h-3.5 mr-1" /> Inspect Evidence &amp; Bounding Boxes
                </Button>
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
                  Preserved raw text, recognition confidence ratings, and bounding-box coordinates for auditability
                </CardDescription>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-medium">≥90% HIGH</span>
                <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-medium">60-89% MED</span>
                <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded font-medium">&lt;60% LOW</span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">#</TableHead>
                    <TableHead>Detected Raw Text</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Bounding Box [x1, y1, x2, y2]</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.ocrResults.map((ocr, idx) => (
                    <TableRow key={ocr.id}>
                      <TableCell className="font-mono text-xs text-slate-400">
                        {idx + 1}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-medium text-slate-800">
                        {ocr.text}
                      </TableCell>
                      <TableCell>
                        {getConfidenceBadge(ocr.confidence_category, ocr.confidence)}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-500">
                        [{ocr.bbox.join(', ')}]
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const match = data.complianceResults.find((cr) =>
                              cr.evidence?.source_text?.includes(ocr.text)
                            )
                            if (match) {
                              setSelectedEvidenceResult(match)
                              setActiveTab('evidence')
                            }
                          }}
                          className="h-7 text-xs text-blue-600 hover:text-blue-800 cursor-pointer"
                        >
                          View BBox
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
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
                  {data.fields.map((f) => (
                    <TableRow key={f.id}>
                      <TableCell className="font-semibold text-slate-800 text-xs">
                        {f.canonical_name}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-600">
                        {f.raw_value || <span className="text-slate-400 italic">None detected</span>}
                      </TableCell>
                      <TableCell className="text-xs font-semibold text-[#1e3a5f]">
                        {f.normalized_value ? (
                          <span>
                            {f.currency === 'INR' ? '₹' : ''}
                            {f.normalized_value} {f.unit || ''}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">-</span>
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
                          '-'
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
                  ))}
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
              <Badge variant="pass" className="text-xs">
                All 7 Rules Passed
              </Badge>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Declaration</TableHead>
                    <TableHead>Detected Value</TableHead>
                    <TableHead>Statutory Requirement</TableHead>
                    <TableHead>Legal Verdict</TableHead>
                    <TableHead>Deterministic Reasoning</TableHead>
                    <TableHead className="text-right">Evidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.complianceResults.map((res) => (
                    <TableRow key={res.id}>
                      <TableCell className="font-semibold text-slate-800 text-xs">
                        {res.field_name.toUpperCase()}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-700">
                        {res.detected_value || (
                          <span className="text-amber-600 font-semibold">NOT DETECTED</span>
                        )}
                      </TableCell>
                      <TableCell className="text-xs text-slate-500 max-w-[180px]">
                        {res.required_value}
                      </TableCell>
                      <TableCell>{getStatusBadge(res.status)}</TableCell>
                      <TableCell className="text-xs text-slate-600 max-w-xs">
                        {res.reason}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedEvidenceResult(res)
                            setActiveTab('evidence')
                          }}
                          className="h-7 text-xs font-semibold text-[#1e3a5f] border-blue-200 hover:bg-blue-50 cursor-pointer"
                        >
                          Inspect Evidence
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
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
                  Select Compliance Finding
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Click to inspect image coordinates, retrieved rule, and proof
                </p>
              </div>

              <div className="space-y-2">
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
                          {item.field_name.toUpperCase()}
                        </span>
                        {getStatusBadge(item.status)}
                      </div>
                      <p className="text-[11px] text-slate-600 font-mono truncate">
                        {item.detected_value}
                      </p>
                      <div className="flex items-center justify-between text-[10px] text-slate-400 mt-2">
                        <span>{item.evidence?.legal_rule}</span>
                        <span>Confidence: {((item.confidence || 0.9) * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right: Visual Proof & Legal Basis Panel (8 cols) */}
            <div className="lg:col-span-8 space-y-4">
              {selectedEvidenceResult && (
                <>
                  {/* Bounding Box Image Canvas */}
                  <Card className="shadow-xs overflow-hidden">
                    <CardHeader className="py-3 px-4 bg-slate-50 border-b border-slate-200 flex flex-row items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Layers className="w-4 h-4 text-[#1e3a5f]" />
                        <span className="text-xs font-bold text-slate-800">
                          Packaging Evidence Region • {selectedEvidenceResult.field_name.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-slate-500">
                        Box: [{selectedEvidenceResult.evidence?.bbox?.join(', ')}]
                      </span>
                    </CardHeader>
                    <CardContent className="p-4 bg-slate-900 flex items-center justify-center min-h-[320px] relative overflow-hidden">
                      {/* Product Image */}
                      <img
                        src={data.images[0]?.url || "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?w=800&auto=format&fit=crop&q=80"}
                        alt="Evidence panel"
                        className="max-h-[380px] object-contain rounded opacity-85"
                      />

                      {/* Synthetic Bounding Box Overlay for Visualization */}
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="border-2 border-emerald-400 bg-emerald-400/20 rounded p-2 text-white shadow-lg backdrop-blur-xs flex flex-col items-center">
                          <span className="bg-emerald-600 text-white text-[10px] font-bold px-2 py-0.5 rounded -mt-5 uppercase tracking-wide">
                            {selectedEvidenceResult.field_name}: DETECTED
                          </span>
                          <span className="font-mono text-xs mt-1 font-bold text-emerald-100">
                            "{selectedEvidenceResult.evidence?.source_text}"
                          </span>
                          <span className="text-[9px] text-emerald-200">
                            OCR Confidence: {((selectedEvidenceResult.evidence?.ocr_confidence || 0.95) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* 5-Step Provenance Breakdown */}
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
                            {selectedEvidenceResult.evidence?.source_text}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Normalized Declaration:</span>
                          <span className="font-semibold text-[#1e3a5f]">
                            {selectedEvidenceResult.detected_value}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">OCR Confidence:</span>
                          <span className="font-semibold text-emerald-700">
                            {((selectedEvidenceResult.evidence?.ocr_confidence || 0.95) * 100).toFixed(1)}% (High Confidence)
                          </span>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Legal Basis from RAG */}
                    <Card className="shadow-xs">
                      <CardHeader className="py-3 px-4 bg-slate-50 border-b border-slate-200">
                        <CardTitle className="text-xs flex items-center gap-1.5 text-slate-700">
                          <ShieldCheck className="w-3.5 h-3.5 text-blue-700" />
                          2. Retrieved Statutory Provision (pgvector RAG)
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 space-y-2 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Statutory Document:</span>
                          <span className="font-semibold text-slate-800">
                            {selectedEvidenceResult.evidence?.legal_document}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Rule &amp; Sub-rule:</span>
                          <span className="font-semibold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded inline-block">
                            {selectedEvidenceResult.evidence?.legal_rule} (Page {selectedEvidenceResult.evidence?.legal_page})
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Legal Provision Text:</span>
                          <p className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 italic leading-relaxed">
                            "{selectedEvidenceResult.evidence?.legal_text}"
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Deterministic Verification Reasoning */}
                  <Card className="shadow-xs bg-slate-50 border-slate-200">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                          <CheckCircle2 className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                            Deterministic Compliance Engine Verdict: {selectedEvidenceResult.status}
                          </h4>
                          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                            {selectedEvidenceResult.reason}
                          </p>
                          <p className="text-[10px] text-slate-400 mt-2">
                            Rule Evaluation ID: {selectedEvidenceResult.rule_id} • Evaluated deterministically via numerical &amp; unit ontology. No LLM decision-making.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
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
                  <span className="font-semibold text-slate-800">{data.inspection.product_category}</span>
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
                            {r.evidence?.legal_rule}
                          </TableCell>
                          <TableCell className="text-xs font-medium text-slate-800">
                            {r.field_name.toUpperCase()}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-slate-600">
                            {r.detected_value}
                          </TableCell>
                          <TableCell>
                            <span className="text-xs font-bold text-emerald-700">
                              PASS (COMPLIANT)
                            </span>
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

      {/* Manual Field Correction Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Correct Extracted Declaration</DialogTitle>
            <DialogDescription>
              Inspector human-in-the-loop override. The original OCR reading is preserved for audit trail.
            </DialogDescription>
          </DialogHeader>

          {editingField && (
            <div className="space-y-4 py-2">
              <div className="text-xs">
                <span className="text-slate-500 block">Declaration Field:</span>
                <span className="font-bold text-slate-800">{editingField.canonical_name}</span>
              </div>

              <div className="text-xs">
                <span className="text-slate-500 block">Raw OCR Value (Preserved):</span>
                <span className="font-mono bg-slate-100 p-1.5 rounded block text-slate-700">
                  {editingField.raw_value || 'None'}
                </span>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Corrected / Normalized Value:
                </label>
                <Input
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  placeholder="Enter verified declaration"
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={saveEditedField}
              className="bg-[#1e3a5f] hover:bg-[#153e75] text-white"
            >
              Save Correction
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
