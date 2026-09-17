import React, { useState } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import {
  Shield,
  LayoutDashboard,
  PlusCircle,
  ClipboardList,
  BookOpen,
  Settings,
  Menu,
  Bell,
  User,
  ChevronRight,
  ExternalLink,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface NavItem {
  label: string
  href: string
  icon: React.ElementType
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'New Inspection', href: '/inspections/new', icon: PlusCircle },
  { label: 'All Inspections', href: '/inspections', icon: ClipboardList },
  { label: 'Knowledge Base', href: '/regulations', icon: BookOpen },
]

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()

  const getPageTitle = () => {
    const path = location.pathname
    if (path === '/') return 'Inspection Dashboard'
    if (path === '/inspections/new') return 'New Product Inspection'
    if (path === '/inspections') return 'Inspections Registry'
    if (path.includes('/processing')) return 'Inspection Pipeline Processing'
    if (path.startsWith('/inspections/')) return 'Inspection Review & Evidence'
    if (path === '/regulations') return 'Legal Knowledge Base & Regulations'
    return 'Legal Metrology Compliance System'
  }

  return (
    <div className="flex h-screen bg-[#f7fafc] overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col bg-[#1e3a5f] text-white transition-all duration-300 z-30 shadow-xl',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        {/* Logo / Header */}
        <div className="flex items-center h-16 px-4 border-b border-white/10 gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-[#3182ce] text-white shadow-md shrink-0">
            <Shield className="w-6 h-6" />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <h1 className="font-bold text-sm leading-tight text-white tracking-wide uppercase">
                Legal Metrology
              </h1>
              <p className="text-[11px] text-blue-200 tracking-wider">
                COMPLIANCE SYSTEM
              </p>
            </div>
          )}
        </div>

        {/* Sub-label banner */}
        {sidebarOpen && (
          <div className="px-4 py-2 bg-[#153e75]/60 border-b border-white/5 text-[10px] text-blue-200 uppercase tracking-widest font-semibold flex items-center justify-between">
            <span>Govt. of India</span>
            <span className="bg-blue-400/20 text-blue-300 px-1.5 py-0.5 rounded text-[9px]">SIH 26034</span>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive =
              item.href === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.href)

            return (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group cursor-pointer',
                  isActive
                    ? 'bg-[#3182ce] text-white shadow-sm'
                    : 'text-blue-100/80 hover:bg-white/10 hover:text-white'
                )}
                title={!sidebarOpen ? item.label : undefined}
              >
                <Icon className={cn('w-5 h-5 shrink-0', isActive ? 'text-white' : 'text-blue-200')} />
                {sidebarOpen && (
                  <span className="truncate">{item.label}</span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Rule reference box */}
        {sidebarOpen && (
          <div className="m-3 p-3 rounded-lg bg-white/5 border border-white/10 text-xs text-blue-200">
            <p className="font-semibold text-white mb-1">Standard: LM(PC) Rules, 2011</p>
            <p className="text-[11px] text-blue-300/80 leading-relaxed">
              Rules 6, 7, 8, 9, 10 &amp; 18 enforcement for packaged commodities.
            </p>
          </div>
        )}

        {/* Footer info */}
        <div className="p-4 border-t border-white/10 flex items-center justify-between text-xs text-blue-300/60">
          {sidebarOpen ? (
            <div>
              <p className="font-medium text-blue-200">Inspector Terminal</p>
              <p className="text-[10px]">v1.0.0-SIH26034</p>
            </div>
          ) : (
            <div className="w-full text-center text-[10px]">v1.0</div>
          )}
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-20 shrink-0 shadow-xs">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-slate-600 hover:text-slate-900"
              aria-label="Toggle Sidebar"
            >
              <Menu className="w-5 h-5" />
            </Button>
            <div>
              <h2 className="text-base font-semibold text-slate-800 leading-tight">
                {getPageTitle()}
              </h2>
              <p className="text-xs text-slate-500">
                Department of Consumer Affairs • Legal Metrology Division
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-xs px-2.5 py-1 rounded-md">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <span>AI-Assisted Human-in-the-Loop Mode</span>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="text-slate-500 hover:text-slate-800 relative"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-blue-600 rounded-full" />
            </Button>

            <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
              <div className="w-8 h-8 rounded-full bg-[#1e3a5f] text-white flex items-center justify-center font-medium text-xs">
                IN
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-xs font-semibold text-slate-800 leading-none">Inspector 104</p>
                <p className="text-[10px] text-slate-500 leading-tight">Legal Metrology Officer</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#f7fafc]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
