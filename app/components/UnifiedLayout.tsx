'use client'

import React, { useState } from 'react'
import NavigationSidebar from './NavigationSidebar'
import { Menu } from 'lucide-react'

interface UnifiedLayoutProps {
  children: React.ReactNode
}

export default function UnifiedLayout({ children }: UnifiedLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-900 text-white">
      {/* Единая адаптивная левая навигационная панель */}
      <NavigationSidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      
      {/* Mobile menu button */}
      <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-800/50 bg-black/80 backdrop-blur-xl px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:hidden">
        <button
          type="button"
          className="-m-2.5 p-2.5 text-gray-400 hover:text-white transition-colors duration-200"
          onClick={() => setSidebarOpen(true)}
        >
          <span className="sr-only">Open sidebar</span>
          <Menu className="h-6 w-6" aria-hidden="true" />
        </button>
        
        {/* Mobile header */}
        <div className="flex-1 text-sm font-semibold leading-6 text-white">
          GHOST Trading
        </div>
      </div>
      
      {/* Main content */}
      <main className="lg:pl-80">
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
