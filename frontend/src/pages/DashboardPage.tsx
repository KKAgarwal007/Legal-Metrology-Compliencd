import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ClipboardCheck,
  AlertTriangle,
  AlertCircle,
  FileText,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  CheckCircle2,
  Clock,
  Scan,
  ShieldCheck,
  Inbox,
  Loader2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { DashboardStats } from '@/types'
import { getDashboardStats } from '@/services/api'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true
    async function loadStats() {
      setLoading(true)
      try {
        const data = await getDashboardStats()
        if (isMounted) {
          setStats(data)
        }
      } catch (err) {
        console.warn('Backend stats not available, using default view:', err)
        if (isMounted) {
          setStats({
            total_inspections: 0,
            compliant: 0,
            review_required: 0,
            violations: 0,
            recent_inspections: [],
          })
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }
    loadStats()
    return () => {
      isMounted = false
    }
  }, [])

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

  const currentStats = stats || {
    total_inspections: 0,
    compliant: 0,
    review_required: 0,
    violations: 0,
    recent_inspections: [],
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#1e3a5f] to-[#2c5282] rounded-xl p-6 text-white shadow-md flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-blue-400/20 px-3 py-1 rounded-full text-xs font-semibold text-blue-200 mb-2">
            <ShieldCheck className="w-4 h-4" /> Legal Metrology (Packaged Commodities) Rules, 2011
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            Compliance Inspection Terminal
          </h1>
          <p className="text-blue-100 text-sm mt-1 max-w-2xl">
            Automated verification of mandatory packaging declarations: MRP, Net Quantity, Manufacturer/Packer,
            Consumer Care, Country of Origin, and Dates with full deterministic audit trails.
          </p>
        </div>
        <Link to="/inspections/new">
          <Button className="bg-[#38a169] hover:bg-[#2f855a] text-white shadow-lg flex items-center gap-2 text-sm px-5 py-2.5 cursor-pointer">
            <PlusCircle className="w-4 h-4" />
            New Inspection
          </Button>
        </Link>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="border-l-4 border-l-[#1e3a5f] shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Total Inspections
            </CardTitle>
            <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-700">
              <FileText className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-800">
              {loading ? <Loader2 className="w-6 h-6 animate-spin text-slate-400" /> : currentStats.total_inspections}
            </div>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-600" />
              <span>Live records in system</span>
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-emerald-500 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Compliant (PASS)
            </CardTitle>
            <div className="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-700">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-700">
              {loading ? <Loader2 className="w-6 h-6 animate-spin text-emerald-400" /> : currentStats.compliant}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {currentStats.total_inspections > 0
                ? `${Math.round((currentStats.compliant / currentStats.total_inspections) * 100)}% compliance rate`
                : 'No inspection records yet'}
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Review Required
            </CardTitle>
            <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center text-amber-700">
              <AlertCircle className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-700">
              {loading ? <Loader2 className="w-6 h-6 animate-spin text-amber-400" /> : currentStats.review_required}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Missing or ambiguous declarations
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-red-500 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Potential Violations
            </CardTitle>
            <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center text-red-700">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-700">
              {loading ? <Loader2 className="w-6 h-6 animate-spin text-red-400" /> : currentStats.violations}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Statutory non-compliance identified
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Rules Information Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Rules Checklist */}
        <Card className="lg:col-span-1 shadow-xs">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-[#1e3a5f]" />
              Mandatory Declarations Rule 6
            </CardTitle>
            <CardDescription>
              Legal Metrology (Packaged Commodities) Rules, 2011
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { rule: 'Rule 6(1)(a)', name: 'Name & Address of Manufacturer/Packer' },
              { rule: 'Rule 6(1)(aa)', name: 'Country of Origin for imported goods' },
              { rule: 'Rule 6(1)(b)', name: 'Generic or Common Name of Commodity' },
              { rule: 'Rule 6(1)(c)', name: 'Net Quantity in standard metric units' },
              { rule: 'Rule 6(1)(d)', name: 'Month & Year of Manufacture/Packing' },
              { rule: 'Rule 6(1)(e)', name: 'Maximum Retail Price (MRP incl. taxes)' },
              { rule: 'Rule 6(1)(h)', name: 'Consumer Care Contact Details' },
              { rule: 'Rule 5 / Sched. 2', name: 'Standard Metric Units of Weight/Measure' },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded-md bg-slate-50 border border-slate-100 text-xs">
                <span className="font-semibold text-slate-800">{item.rule}</span>
                <span className="text-slate-600 truncate ml-2">{item.name}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Inspections Table */}
        <Card className="lg:col-span-2 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">Recent Inspections</CardTitle>
              <CardDescription>Live log of scanned packaged commodities</CardDescription>
            </div>
            <Link to="/inspections">
              <Button variant="outline" size="sm" className="gap-1 text-xs cursor-pointer">
                View Registry <ArrowRight className="w-3 h-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <span className="text-xs">Loading inspection records...</span>
              </div>
            ) : currentStats.recent_inspections.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-slate-500 gap-3">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                  <Inbox className="w-6 h-6" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-700">No inspections recorded yet</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Perform a new inspection to run OCR analysis and statutory compliance checks.
                  </p>
                </div>
                <Link to="/inspections/new">
                  <Button size="sm" className="bg-[#1e3a5f] hover:bg-[#153e75] text-white mt-1 cursor-pointer">
                    <PlusCircle className="w-4 h-4 mr-1.5" />
                    Start New Inspection
                  </Button>
                </Link>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product / Commodity</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Legal Verdict</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentStats.recent_inspections.map((insp) => (
                    <TableRow key={insp.id}>
                      <TableCell className="font-medium text-slate-900">
                        <div className="flex items-center gap-2">
                          <Scan className="w-4 h-4 text-slate-400 shrink-0" />
                          <div>
                            <p className="leading-tight text-xs font-semibold">{insp.title}</p>
                            <span className="text-[10px] text-slate-400 font-mono">{insp.id}</span>
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
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link to={`/inspections/${insp.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs text-blue-600 hover:text-blue-800 cursor-pointer">
                            Inspect
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
