'use client'

import { ReactNode, useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  Users, 
  TrendingUp, 
  MessageSquare, 
  Settings, 
  BarChart3,
  Activity,
  Bell,
  Menu,
  X,
  ChevronDown,
  Search,
  Wifi,
  WifiOff
} from 'lucide-react'

interface GhostLayoutExactProps {
  children: ReactNode
  currentPage?: string
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Traders', href: '/traders', icon: Users },
  { name: 'Trading', href: '/dashboard', icon: TrendingUp },
  { name: 'Signals', href: '/signals', icon: Activity },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'News', href: '/news', icon: Bell },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function GhostLayoutExact({ children, currentPage }: GhostLayoutExactProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [systemOnline, setSystemOnline] = useState(true)
  const [currentTime, setCurrentTime] = useState('')
  const pathname = usePathname()

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // Close sidebar when route changes
  useEffect(() => {
    setSidebarOpen(false)
  }, [pathname])

  // Prevent body scroll when sidebar is open on mobile
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [sidebarOpen])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-900 text-white">
      {/* Mobile menu overlay with enhanced blur */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden backdrop-blur-md bg-black/50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Desktop Sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gradient-to-b from-gray-900/95 via-gray-950/95 to-black/95 backdrop-blur-xl px-6 pb-4 border-r border-gray-800/50 shadow-2xl">
          {/* Logo */}
          <div className="flex h-16 shrink-0 items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div className="flex flex-col">
                <h1 className="text-xl font-bold bg-gradient-to-r from-white via-blue-100 to-gray-300 bg-clip-text text-transparent">
                  GHOST Trading
                </h1>
                <span className="text-xs text-gray-500">Pro Dashboard</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul role="list" className="-mx-2 space-y-2">
                  {navigation.map((item, index) => {
                    const isActive = pathname === item.href
                    return (
                      <li key={item.name}>
                        <Link
                          href={item.href}
                          className={`
                            group flex gap-x-3 rounded-xl p-3 text-sm leading-6 font-medium transition-all duration-300 ease-out
                            ${isActive
                              ? 'bg-gradient-to-r from-emerald-600/20 via-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20 transform scale-105'
                              : 'text-gray-400 hover:text-white hover:bg-gray-800/40 hover:scale-102 hover:shadow-md'
                            }
                          `}
                        >
                          <item.icon className={`h-5 w-5 shrink-0 transition-all duration-300 ${
                            isActive ? 'text-blue-400 drop-shadow-sm' : 'group-hover:text-blue-300'
                          }`} />
                          <span className="flex-1">{item.name}</span>
                          {isActive && (
                            <div className="flex items-center gap-1">
                              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                            </div>
                          )}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </li>
            </ul>
          </nav>
          
          {/* Enhanced System Status */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-emerald-600/10 via-green-600/10 to-teal-600/10 border border-emerald-500/20 rounded-xl backdrop-blur-sm">
              <div className="relative">
                <div className="h-3 w-3 bg-emerald-500 rounded-full animate-pulse shadow-lg shadow-emerald-500/50" />
                <div className="absolute inset-0 h-3 w-3 bg-emerald-400 rounded-full animate-ping opacity-75" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-emerald-400">System Online</span>
                <span className="text-xs text-gray-500">All services operational</span>
              </div>
              <Wifi className="ml-auto w-4 h-4 text-emerald-400" />
            </div>
            
            {/* Time display */}
            <div className="text-center">
              <div className="text-xs text-gray-500 font-mono">{currentTime}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Mobile Sidebar */}
      <div className={`
        fixed inset-y-0 z-50 flex w-80 flex-col transition-all duration-300 ease-out lg:hidden
        ${sidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'}
      `}>
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gradient-to-b from-gray-900/98 via-gray-950/98 to-black/98 backdrop-blur-xl px-6 pb-4 border-r border-gray-700/50">
          {/* Mobile Header */}
          <div className="flex h-16 shrink-0 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <h1 className="text-lg font-bold bg-gradient-to-r from-white via-blue-100 to-gray-300 bg-clip-text text-transparent">
                  GHOST Trading
                </h1>
                <span className="text-xs text-gray-500">Mobile Dashboard</span>
              </div>
            </div>
            <button
              type="button"
              className="text-gray-400 hover:text-white p-2 rounded-xl hover:bg-gray-800/50 transition-all duration-200 active:scale-95"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          {/* Mobile Navigation with staggered animations */}
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul role="list" className="-mx-2 space-y-3">
                  {navigation.map((item, index) => {
                    const isActive = pathname === item.href
                    return (
                      <li key={item.name} 
                          className={`transform transition-all duration-500 ${
                            sidebarOpen ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'
                          }`}
                          style={{ transitionDelay: `${index * 75}ms` }}>
                        <Link
                          href={item.href}
                          onClick={() => setSidebarOpen(false)}
                          className={`
                            group flex gap-x-4 rounded-xl p-4 text-base leading-6 font-medium transition-all duration-300 active:scale-95
                            ${isActive
                              ? 'bg-gradient-to-r from-emerald-600/20 via-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20 scale-105'
                              : 'text-gray-400 hover:text-white hover:bg-gray-800/40 hover:scale-102'
                            }
                          `}
                        >
                          <item.icon className={`h-6 w-6 shrink-0 transition-all duration-300 ${
                            isActive ? 'text-blue-400' : 'group-hover:text-blue-300'
                          }`} />
                          <div className="flex flex-col flex-1">
                            <span className="font-semibold">{item.name}</span>
                            {isActive && <span className="text-xs text-blue-400/70 mt-0.5">Currently active</span>}
                          </div>
                          {isActive && (
                            <div className="flex items-center">
                              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                            </div>
                          )}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </li>
            </ul>
          </nav>
          
          {/* Mobile System Status */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-emerald-600/10 to-teal-600/10 border border-emerald-500/20 rounded-xl">
              <div className="relative">
                <div className="h-3 w-3 bg-emerald-500 rounded-full animate-pulse" />
                <div className="absolute inset-0 h-3 w-3 bg-emerald-400 rounded-full animate-ping opacity-75" />
              </div>
              <div className="flex flex-col flex-1">
                <span className="text-sm font-semibold text-emerald-400">System Online</span>
                <span className="text-xs text-gray-500">All services operational</span>
              </div>
              <Wifi className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="lg:pl-72">
        {/* Enhanced Mobile Header with glassmorphism */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 backdrop-blur-xl bg-gray-900/80 border-b border-gray-800/30 px-4 shadow-lg sm:gap-x-6 sm:px-6 lg:hidden">
          <button
            type="button"
            className="text-gray-400 hover:text-white p-2 rounded-xl hover:bg-gray-800/50 transition-all duration-200 active:scale-95 touch-manipulation"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <div className="h-6 w-px bg-gray-700/50" />
          
          <div className="flex flex-1 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <div className="flex flex-col">
                <h1 className="text-lg font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  GHOST
                </h1>
              </div>
            </div>
            
            {/* Mobile status and time */}
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2">
                <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-xs text-gray-400">Online</span>
              </div>
              <div className="text-xs text-gray-500 font-mono hidden sm:block">
                {currentTime}
              </div>
            </div>
          </div>
        </div>

        {/* Page Content with responsive padding and smooth transitions */}
        <main className="py-4 sm:py-6 lg:py-8 xl:py-10 transition-all duration-300">
          <div className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}