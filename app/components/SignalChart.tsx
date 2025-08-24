'use client'

import React, { useState, useEffect } from 'react'
import BybitStyleChart from './BybitStyleChart'

interface SignalData {
  id: string
  symbol: string
  side: 'LONG' | 'SHORT'
  entry_min: number
  entry_max: number
  tp1: number
  tp2: number
  tp3: number
  sl: number
  posted_ts: string
  created_at: string
}

interface SignalChartProps {
  signalId: string | null
  onTrackingToggle?: (isTracking: boolean) => void
}

// 🚀 MODERN 2025 TRADING CHART - Revolutionary UX/UI
export default function SignalChart({ signalId, onTrackingToggle }: SignalChartProps) {
  const [signalData, setSignalData] = useState<SignalData | undefined>(undefined)
  const [loading, setLoading] = useState(false)

  // Fetch signal data for enhanced display
  const fetchSignalData = async (id: string) => {
    try {
      setLoading(true)
      const response = await fetch(`/api/test-table`)
      const data = await response.json()
      
      if (data.data) {
        const signal = data.data.find((s: any) => s.id === id)
        if (signal) {
          // Transform to expected format
          setSignalData({
            id: signal.id,
            symbol: signal.symbol,
            side: signal.side,
            entry_min: signal.entry_min,
            entry_max: signal.entry_max,
            tp1: signal.tp1,
            tp2: signal.tp2,
            tp3: signal.tp3,
            sl: signal.sl,
            posted_ts: signal.created_at,
            created_at: signal.created_at
          })
        }
      }
    } catch (error) {
      console.error('Error fetching signal data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (signalId) {
      fetchSignalData(signalId)
    }
  }, [signalId])
  
  if (!signalId) {
    return (
      <div className="bg-[#0B1426] text-white font-mono">
        {/* ByBit Style Empty Header */}
        <div className="bg-[#0F1729] border-b border-gray-800 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-white">BTCUSDT</h1>
                <span className="text-sm px-2 py-1 rounded bg-gray-700 text-gray-400">
                  Select Signal
                </span>
              </div>
            </div>
          </div>
          
          {/* Timeframe selection - disabled state */}
          <div className="flex items-center gap-1 mt-4">
            {['1C', '1мин', '3мин', '5мин', '15мин', '30мин', '1Ч', '2Ч', '4Ч', '1Д'].map((tf, i) => (
              <button
                key={i}
                disabled
                className="px-3 py-1.5 text-sm text-gray-500 cursor-not-allowed"
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Chart placeholder */}
        <div className="relative bg-[#0B1426] flex items-center justify-center" style={{ height: '500px' }}>
          <div className="text-center">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-bold text-white mb-2">Select Signal</h3>
            <p className="text-gray-400">Choose a signal from the list to view professional chart analysis</p>
          </div>
        </div>
      </div>
    )
  }

  // 🎯 BYBIT PROFESSIONAL TRADING INTERFACE
  return (
    <div className="w-full">
      {/* Pure ByBit Style Chart - No Extra Headers */}
      <BybitStyleChart 
        signalId={signalId}
        signalData={signalData}
      />
      
      {loading && (
        <div className="absolute inset-0 bg-black/80 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-4 border-orange-400/30 border-t-orange-400 rounded-full animate-spin" />
            <span className="text-gray-400 font-mono text-sm">Loading market data...</span>
          </div>
        </div>
      )}
    </div>
  )
}