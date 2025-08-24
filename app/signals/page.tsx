'use client'

import { useState, useEffect } from 'react'
import UnifiedLayout from '@/app/components/UnifiedLayout'
import SignalsMonitor from '@/app/components/SignalsMonitor'

export default function SignalsPage() {
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
              <h1 className="text-2xl font-bold text-white mb-2">📶 Signals Monitor</h1>
              <p className="text-gray-400">Real-time signal processing and validation</p>
            </div>
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
              🔄 Live Signals
            </div>
          </div>
        </div>

        {/* Signals Monitor Component */}
        <SignalsMonitor />
      </div>
    </UnifiedLayout>
  )
}
