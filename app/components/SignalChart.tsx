'use client'

import React from 'react'
import EnhancedSignalChart from './EnhancedSignalChart'

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

// Новый график в стиле Bybit с двумя слоями
export default function SignalChart({ signalId, onTrackingToggle }: SignalChartProps) {
  
  if (!signalId) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg border border-gray-700">
        <p className="text-gray-400 text-lg">📊 Выберите сигнал для отображения графика</p>
      </div>
    )
  }

  // Используем новый профессиональный график
  return (
    <div className="w-full">
      <EnhancedSignalChart 
        signalId={signalId}
      />
    </div>
  )
}