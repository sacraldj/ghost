'use client'

import React, { useState, useEffect } from 'react'
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
  TestTube
} from 'lucide-react'
import SystemStatusIndicator from '@/app/components/SystemStatusIndicator'

const navigationItems = [
  { name: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { name: 'Traders', icon: Users, path: '/traders' },
  { name: 'Trading', icon: TrendingUp, path: '/trading' },
  { name: 'Signals', icon: Activity, path: '/signals' },
  { name: 'Analytics', icon: BarChart3, path: '/analytics' },
  { name: 'Test Table', icon: TestTube, path: '/test-table' },
  { name: 'News', icon: Bell, path: '/news' },
  { name: 'Chat', icon: MessageSquare, path: '/chat' },
  { name: 'Settings', icon: Settings, path: '/settings' },
]

interface NavigationSidebarProps {
  sidebarOpen?: boolean
  setSidebarOpen?: (open: boolean) => void
}

export default function NavigationSidebar({ sidebarOpen = false, setSidebarOpen }: NavigationSidebarProps) {
  const pathname = usePathname()
  const [currentTime, setCurrentTime] = useState('')

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // Close sidebar when route changes
  useEffect(() => {
    if (setSidebarOpen) {
      setSidebarOpen(false)
    }
  }, [pathname, setSidebarOpen])

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
    <>
      {/* Mobile menu overlay */}
      {sidebarOpen && setSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden backdrop-blur-md bg-black/50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Desktop Sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-80 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gradient-to-b from-gray-900/95 via-gray-950/95 to-black/95 backdrop-blur-xl px-6 pb-4 border-r border-gray-800/50 shadow-2xl">
          {/* Logo */}
          <div className="flex h-16 shrink-0 items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <div className="flex flex-col">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-white via-blue-100 to-gray-300 bg-clip-text text-transparent">
                  GHOST Trading
                </h1>
                <span className="text-sm text-gray-400">Pro Dashboard</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-2">
              {navigationItems.map((item, index) => {
                const isActive = pathname === item.path
                return (
                  <li key={item.name}>
                    <Link
                      href={item.path}
                      className={`
                        group flex gap-x-4 rounded-2xl p-4 text-sm leading-6 font-medium transition-all duration-300 ease-out
                        ${isActive
                          ? 'bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-blue-700/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20 transform scale-105'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/40 hover:scale-102 hover:shadow-md'
                        }
                      `}
                    >
                      <item.icon className={`h-6 w-6 shrink-0 transition-all duration-300 ${
                        isActive ? 'text-blue-400 drop-shadow-sm' : 'group-hover:text-blue-300'
                      }`} />
                      <span className="flex-1 text-base">{item.name}</span>
                      {isActive && (
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                        </div>
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </nav>
          
          {/* System Status */}
          <div className="space-y-4">
            <SystemStatusIndicator className="w-full" />
            
            {/* Time display */}
            <div className="text-center">
              <div className="text-xs text-gray-500 font-mono">{currentTime}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Sidebar */}
      <div className={`
        fixed inset-y-0 z-50 flex w-80 flex-col transition-all duration-300 ease-out lg:hidden
        ${sidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'}
      `}>
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gradient-to-b from-gray-900/98 via-gray-950/98 to-black/98 backdrop-blur-xl px-6 pb-4 border-r border-gray-700/50">
          {/* Mobile Header */}
          <div className="flex h-16 shrink-0 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 rounded-2xl flex items-center justify-center shadow-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div className="flex flex-col">
                <h1 className="text-lg font-bold bg-gradient-to-r from-white via-blue-100 to-gray-300 bg-clip-text text-transparent">
                  GHOST Trading
                </h1>
                <span className="text-xs text-gray-500">Mobile Dashboard</span>
              </div>
            </div>
            {setSidebarOpen && (
              <button
                type="button"
                className="text-gray-400 hover:text-white p-2 rounded-xl hover:bg-gray-800/50 transition-all duration-200 active:scale-95"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-6 w-6" />
              </button>
            )}
          </div>
          
          {/* Mobile Navigation */}
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-3">
              {navigationItems.map((item, index) => {
                const isActive = pathname === item.path
                return (
                  <li key={item.name} 
                      className={`transform transition-all duration-500 ${
                        sidebarOpen ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'
                      }`}
                      style={{ transitionDelay: `${index * 75}ms` }}>
                    <Link
                      href={item.path}
                      onClick={() => setSidebarOpen && setSidebarOpen(false)}
                      className={`
                        group flex gap-x-4 rounded-2xl p-4 text-base leading-6 font-medium transition-all duration-300 active:scale-95
                        ${isActive
                          ? 'bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-blue-700/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20 scale-105'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/40 hover:scale-102'
                        }
                      `}
                    >
                      <item.icon className={`h-6 w-6 shrink-0 transition-all duration-300 ${
                        isActive ? 'text-blue-400' : 'group-hover:text-blue-300'
                      }`} />
                      <span className="flex-1">{item.name}</span>
                      {isActive && (
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </nav>
          
          {/* Mobile System Status */}
          <div className="space-y-4">
            <SystemStatusIndicator className="w-full" />
            
            {/* Time display */}
            <div className="text-center">
              <div className="text-xs text-gray-500 font-mono">{currentTime}</div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
