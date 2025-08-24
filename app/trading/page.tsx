'use client'

import { useState, useEffect } from 'react'
import UnifiedLayout from '@/app/components/UnifiedLayout'
import TradingDashboard from '@/app/components/TradingDashboard'

export default function TradingPage() {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return <div className="min-h-screen bg-black" />
  }

  return (
    <UnifiedLayout>
      <div className="space-y-6">
        {/* Header in Test Table style */}
        <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">📈 Live Trading Dashboard</h1>
              <p className="text-gray-400">Real-time portfolio monitoring and active positions</p>
            </div>
            <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
              💹 Live Trading
            </div>
          </div>
        </div>

        {/* Trading Dashboard Component */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl border border-gray-700/50 shadow-lg">
          <TradingDashboard />
        </div>
      </div>
    </UnifiedLayout>
  )
}
