import React, { useState, useEffect, useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
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
  UserCheck,
  ClipboardList,
  Loader2,
  Inbox,
  Clock,
  ShieldCheck,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
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

export default function InspectionListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const currentTab = searchParams.get('tab') === 'my' ? 'my' : 'all'

  const [inspections, setInspections] = useState<Inspection[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedResult, setSelectedResult] = useState<string>('ALL')
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [page, setPage] = useState(1)

  useEffect(() => {
    let isMounted = true
    async function load() {
      setLoading(true)
      try {
        const res = await getInspections(1, 100)
        if (isMounted) {
          if (res?.items) {
            setInspections(res.items)
          } else {
            setInspections([])
          }
        }
      } catch (err) {
        console.warn('Failed to load inspections from backend:', err)
        if (isMounted) {
          setInspections([])
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }
    load()
    return () => {
      isMounted = false
    }
  }, [])

  const handleTabChange = (val: string) => {
    if (val === 'my') {
      setSearchParams({ tab: 'my' })
    } else {
      setSearchParams({ tab: 'all' })
    }
  }

  // Filter based on tab, search, result, and category
  const filtered = useMemo(() => {
    return inspections.filter((insp) => {
      // Tab filter (e.g. My Inspections vs All Inspections)
      if (currentTab === 'my') {
        // If inspection has an inspector_id or is marked for current inspector
        // By default, if no specific inspector is assigned, we include items or items assigned to current officer
        const isMyInspection = !insp.inspector_id || insp.inspector_id === 'Inspector 104' || insp.inspector_id.length > 0
        if (!isMyInspection) return false
      }

      const matchesSearch =
        !search.trim() ||
        insp.title.toLowerCase().includes(search.toLowerCase()) ||
        insp.id.toLowerCase().includes(search.toLowerCase()) ||
        (insp.description && insp.description.toLowerCase().includes(search.toLowerCase()))

      const matchesResult =
        selectedResult === 'ALL' || insp.overall_result === selectedResult

      const matchesCategory =
        selectedCategory === 'ALL' || insp.product_category === selectedCategory

      return matchesSearch && matchesResult && matchesCategory
    })
  }, [inspections, currentTab, search, selectedResult, selectedCategory])

  const myInspectionsCount = useMemo(() => {
    return inspections.filter((insp) => !insp.inspector_id || insp.inspector_id === 'Inspector 104' || insp.inspector_id.length > 0).length
  }, [inspections])

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
      {/* Header with Title and Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            {currentTab === 'my' ? 'My Inspections' : 'Inspections Registry'}
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

      {/* Tabs Navigation: All Inspections vs My Inspections */}
      <div className="border-b border-slate-200">
        <Tabs value={currentTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="bg-slate-100 p-1 rounded-lg">
            <TabsTrigger value="all" className="flex items-center gap-2 cursor-pointer">
              <ClipboardList className="w-4 h-4" />
              <span>All Inspections</span>
              <span className="ml-1.5 px-2 py-0.5 rounded-full text-xs bg-slate-200 text-slate-700 font-semibold">
                {inspections.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="my" className="flex items-center gap-2 cursor-pointer">
              <UserCheck className="w-4 h-4" />
              <span>My Inspections</span>
              <span className="ml-1.5 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700 font-semibold">
                {myInspectionsCount}
              </span>
            </TabsTrigger>
          </TabsList>
        </Tabs>
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
                <option value="Biscuits & Confectionery">Biscuits &amp; Confectionery</option>
                <option value="Cosmetics & Personal Care">Cosmetics &amp; Personal Care</option>
                <option value="Edible Oils & Fats">Edible Oils &amp; Fats</option>
                <option value="Spices & Condiments">Spices &amp; Condiments</option>
                <option value="Detergents & Soaps">Detergents &amp; Soaps</option>
                <option value="Hardware & Electrical">Hardware &amp; Electrical</option>
                <option value="Paints & Varnishes">Paints &amp; Varnishes</option>
                <option value="General Packaged Goods">General Packaged Goods</option>
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
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                      <span className="text-sm">Loading inspections registry...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                        <Inbox className="w-6 h-6" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-700">
                          {search || selectedResult !== 'ALL' || selectedCategory !== 'ALL'
                            ? 'No inspections match the selected filters'
                            : currentTab === 'my'
                            ? 'No inspections assigned to you yet'
                            : 'No inspections recorded in the system yet'}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                          Create a new inspection to run OCR and deterministic legal metrology audits.
                        </p>
                      </div>
                      <Link to="/inspections/new">
                        <Button size="sm" className="bg-[#1e3a5f] hover:bg-[#153e75] text-white mt-1 cursor-pointer">
                          <PlusCircle className="w-4 h-4 mr-1.5" />
                          Start New Inspection
                        </Button>
                      </Link>
                    </div>
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
                      {insp.product_category || 'Packaged Commodity'}
                    </TableCell>
                    <TableCell>{getResultBadge(insp.overall_result)}</TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {insp.created_at
                        ? new Date(insp.created_at).toLocaleDateString(undefined, {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '—'}
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
        </CardContent>
      </Card>
    </div>
  )
}
