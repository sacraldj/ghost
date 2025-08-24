'use client'

import { useState, useEffect } from 'react'
import UnifiedLayout from '@/app/components/UnifiedLayout'
import NewsAnalysisDashboard from '@/app/components/NewsAnalysisDashboard'

export default function NewsPage() {
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
              <h1 className="text-2xl font-bold text-white mb-2">🔔 News Analysis</h1>
              <p className="text-gray-400">AI-powered market news analysis and sentiment tracking</p>
            </div>
            <div className="bg-gradient-to-r from-orange-600 to-orange-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
              🤖 AI Analysis
            </div>
          </div>
        </div>

        {/* News Analysis Component */}
        <NewsAnalysisDashboard />
      </div>
    </UnifiedLayout>
  )
}
