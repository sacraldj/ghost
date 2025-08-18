'use client'

import { useState, useEffect } from 'react'
import GhostLayoutExact from '@/app/components/GhostLayoutExact'
import TestTableComponent from '@/app/components/TestTableComponent'

export default function TestTablePage() {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return <div className="min-h-screen bg-black" />
  }

  return (
    <GhostLayoutExact currentPage="test-table">
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">🧪 v_trades Schema</h1>
              <p className="text-gray-400">Полная схема таблицы виртуальных сделок из Supabase</p>
            </div>
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
              📊 Database Schema
            </div>
          </div>
        </div>

        {/* Test Table Component */}
        <TestTableComponent />
      </div>
    </GhostLayoutExact>
  )
}
