import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Search,
  Filter,
  PlusCircle,
  Scan,
  Calendar,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  ArrowUpDown,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { Inspection } from '@/types'
import { getInspections } from '@/services/api'

const mockInspections: Inspection[] = [
  {
    id: 'INSP-2026-001',
    title: 'Britannia Good Day Butter Cookies 100g',
    description: 'Seized sample from superstore retail shelf',
    product_category: 'Food & Beverages',
    status: 'completed',
    overall_result: 'PASS',
    created_at: '2026-09-17T09:30:00Z',
  },
  {
    id: 'INSP-2026-002',
    title: 'Dabur Honey 250g Glass Jar',
    description: 'Consumer packaging inspection for Net Weight declarations',
    product_category: 'Food & Beverages',
    status: 'completed',
    overall_result: 'REVIEW',
    created_at: '2026-09-16T14:15:00Z',
  },
  {
    id: 'INSP-2026-003',
    title: 'Nivea Soft Moisturizer 50ml Plastic Tub',
    description: 'Missing Consumer Care phone number on outer carton',
    product_category: 'Cosmetics & Personal Care',
    status: 'completed',
    overall_result: 'VIOLATION',
    created_at: '2026-09-15T11:20:00Z',
  },
  {
    id: 'INSP-2026-004',
    title: 'Tata Salt Vacuum Evaporated 1kg Pouch',
    description: 'Mandatory declarations verification under Rule 6',
    product_category: 'Spices & Condiments',
    status: 'completed',
    overall_result: 'PASS',
    created_at: '2026-09-14T16:45:00Z',
  },
  {
    id: 'INSP-2026-005',
    title: 'Amul Pure Ghee 1L Tin Container',
    description: 'Checking font size compliance under Rule 9',
    product_category: 'Edible Oils & Fats',
    status: 'completed',
    overall_result: 'REVIEW',
    created_at: '2026-09-13T10:00:00Z',
  },
  {
    id: 'INSP-2026-006',
    title: 'Surf Excel Matic Liquid Detergent 1L Pouch',
    description: 'Country of Origin and Manufacturer address check',
    product_category: 'Detergents & Soaps',
    status: 'completed',
    overall_result: 'PASS',
    created_at: '2026-09-12T13:30:00Z',
  },
  {
    id: 'INSP-2026-007',
    title: 'Asian Paints Apex Ultima 4L Bucket',
    description: 'Verification of MRP inclusion of all taxes and metric volume',
    product_category: 'Paints & Varnishes',
    status: 'completed',
    overall_result: 'PASS',
    created_at: '2026-09-11T15:10:00Z',
  },
  {
    id: 'INSP-2026-008',
    title: 'Philips 9W LED Bulb 2-Pack Blister',
    description: 'Testing non-standard packaging font sizing',
    product_category: 'Hardware & Electrical',
    status: 'completed',
    overall_result: 'VIOLATION',
    created_at: '2026-09-10T09:40:00Z',
  },
]

export default function InspectionListPage() {
  const [inspections, setInspections] = useState<Inspection[]>(mockInspections)
  const [search, setSearch] = useState('')
  const [selectedResult, setSelectedResult] = useState<string>('ALL')
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [page, setPage] = useState(1)

  useEffect(() => {
    async function load() {
      try {
        const res = await getInspections()
        if (res?.items && res.items.length > 0) {
          setInspections(res.items)
        }
      } catch (err) {
        // use fallback mock data
      }
    }
    load()
  }, [])

  const filtered = inspections.filter((insp) => {
    const matchesSearch =
      insp.title.toLowerCase().includes(search.toLowerCase()) ||
      insp.id.toLowerCase().includes(search.toLowerCase()) ||
      (insp.description && insp.description.toLowerCase().includes(search.toLowerCase()))

    const matchesResult =
      selectedResult === 'ALL' || insp.overall_result === selectedResult

    const matchesCategory =
      selectedCategory === 'ALL' || insp.product_category === selectedCategory

    return matchesSearch && matchesResult && matchesCategory
  })

  const getResultBadge = (result?: string | null) => {
    switch (result) {
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

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Inspections Registry
          </h1>
          <p className="text-sm text-slate-500">
            Legal Metrology Act, 2009 &amp; Packaged Commodities Rules, 2011 compliance records
          </p>
        </div>
        <Link to="/inspections/new">
          <Button className="bg-[#1e3a5f] hover:bg-[#153e75] text-white flex items-center gap-2 cursor-pointer shadow-xs">
            <PlusCircle className="w-4 h-4" />
            New Inspection
          </Button>
        </Link>
      </div>

      {/* Filters Bar */}
      <Card className="shadow-xs">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="md:col-span-2 relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <Input
                placeholder="Search by commodity name, ID, or description..."
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div>
              <select
                value={selectedResult}
                onChange={(e) => setSelectedResult(e.target.value)}
                className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-xs focus:outline-none focus:ring-1 focus:ring-[#1e3a5f]"
              >
                <option value="ALL">All Results (Any Status)</option>
                <option value="PASS">PASS (Compliant)</option>
                <option value="REVIEW">REVIEW REQUIRED</option>
                <option value="VIOLATION">POTENTIAL VIOLATION</option>
              </select>
            </div>

            <div>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-xs focus:outline-none focus:ring-1 focus:ring-[#1e3a5f]"
              >
                <option value="ALL">All Categories</option>
                <option value="Food & Beverages">Food &amp; Beverages</option>
                <option value="Cosmetics & Personal Care">Cosmetics &amp; Personal Care</option>
                <option value="Edible Oils & Fats">Edible Oils &amp; Fats</option>
                <option value="Spices & Condiments">Spices &amp; Condiments</option>
                <option value="Detergents & Soaps">Detergents &amp; Soaps</option>
                <option value="Hardware & Electrical">Hardware &amp; Electrical</option>
                <option value="Paints & Varnishes">Paints &amp; Varnishes</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="shadow-xs">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[140px]">Inspection ID</TableHead>
                <TableHead>Packaged Commodity</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Legal Verdict</TableHead>
                <TableHead>Date / Timestamp</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-slate-500 text-sm">
                    No inspections match the selected filters.
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((insp) => (
                  <TableRow key={insp.id}>
                    <TableCell className="font-mono text-xs font-semibold text-slate-700">
                      {insp.id}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Scan className="w-4 h-4 text-slate-400 shrink-0" />
                        <div>
                          <p className="font-medium text-slate-900 leading-tight">
                            {insp.title}
                          </p>
                          {insp.description && (
                            <p className="text-xs text-slate-500 truncate max-w-xs mt-0.5">
                              {insp.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-slate-600">
                      {insp.product_category}
                    </TableCell>
                    <TableCell>{getResultBadge(insp.overall_result)}</TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {new Date(insp.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link to={`/inspections/${insp.id}`}>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 text-xs font-medium text-blue-700 border-blue-200 hover:bg-blue-50 cursor-pointer"
                        >
                          View Audit &amp; Evidence
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          {/* Pagination Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 text-xs text-slate-500">
            <span>
              Showing 1 to {filtered.length} of {filtered.length} entries
            </span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled className="h-8 w-8 p-0">
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" className="h-8 w-8 p-0 bg-blue-50 text-blue-700 font-semibold">
                1
              </Button>
              <Button variant="outline" size="sm" disabled className="h-8 w-8 p-0">
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
