'use client'

import React, { useState, useEffect } from 'react'

interface TraderAnalytics {
  trader_id: string
  trust_index: number
  winrate: number
  total_signals: number
  avg_roi: number
}

interface PerformanceData {
  date: string
  trust_index: number
  winrate: number
  signals_count: number
  roi: number
}

interface TraderPerformanceChartProps {
  trader: TraderAnalytics
}

export default function TraderPerformanceChart({ trader }: TraderPerformanceChartProps) {
  const [timeframe, setTimeframe] = useState<string>('1month')
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([])

  // Генерируем синтетические данные для демонстрации
  useEffect(() => {
    generatePerformanceData()
  }, [trader, timeframe])

  const generatePerformanceData = () => {
    const periods = {
      '1day': 24,
      '1week': 7, 
      '1month': 30,
      '6months': 180,
      'year': 365,
      '1year': 365,
      'all': 365
    }

    const period = periods[timeframe as keyof typeof periods] || 30
    const data: PerformanceData[] = []
    
    for (let i = period; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      
      // Генерируем реалистичные данные на основе текущих показателей трейдера
      const baseVariation = (Math.random() - 0.5) * 10
      const trendFactor = (period - i) / period * 5 // Показываем рост со временем
      
      data.push({
        date: date.toISOString().split('T')[0],
        trust_index: Math.max(0, Math.min(100, trader.trust_index + baseVariation + trendFactor)),
        winrate: Math.max(0, Math.min(100, trader.winrate + baseVariation * 0.5)),
        signals_count: Math.max(0, trader.total_signals + Math.floor(Math.random() * 10)),
        roi: trader.avg_roi + baseVariation * 2
      })
    }
    
    setPerformanceData(data)
  }

  const getChangePercentage = (current: number, previous: number) => {
    if (previous === 0) return 0
    return ((current - previous) / previous * 100)
  }

  const currentData = performanceData[performanceData.length - 1]
  const previousData = performanceData[performanceData.length - 8] || performanceData[0]

  const trustChange = currentData && previousData 
    ? getChangePercentage(currentData.trust_index, previousData.trust_index)
    : 0

  const winrateChange = currentData && previousData
    ? getChangePercentage(currentData.winrate, previousData.winrate) 
    : 0

  // Простой SVG график
  const chartWidth = 400
  const chartHeight = 200
  const padding = 40

  const createPath = (data: PerformanceData[], key: keyof PerformanceData, color: string) => {
    if (data.length < 2) return null
    
    const values = data.map(d => Number(d[key]))
    const minVal = Math.min(...values)
    const maxVal = Math.max(...values)
    const range = maxVal - minVal || 1
    
    let path = `M ${padding} ${chartHeight - padding - ((values[0] - minVal) / range) * (chartHeight - 2 * padding)}`
    
    for (let i = 1; i < data.length; i++) {
      const x = padding + (i / (data.length - 1)) * (chartWidth - 2 * padding)
      const y = chartHeight - padding - ((values[i] - minVal) / range) * (chartHeight - 2 * padding)
      path += ` L ${x} ${y}`
    }
    
    return (
      <path
        key={key as string}
        d={path}
        stroke={color}
        strokeWidth="2"
        fill="none"
      />
    )
  }

  return (
    <div className="bg-gray-700 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-md font-bold text-white">Performance Chart</h3>
        
        {/* Временные фреймы */}
        <div className="flex space-x-1 bg-gray-700 rounded p-1">
          {['1day', '1week', '1month', '6months', 'year', '1year', 'all'].map(tf => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                timeframe === tf
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-300 hover:text-white hover:bg-gray-600'
              }`}
            >
              {tf === 'all' ? 'All time' : tf}
            </button>
          ))}
        </div>
            </div>

      {/* Ключевые метрики */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-400">
            {currentData?.trust_index.toFixed(1) || trader.trust_index.toFixed(1)}
          </div>
          <div className="text-sm text-gray-400">Trust Index</div>
          <div className={`text-xs ${trustChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trustChange >= 0 ? '+' : ''}{trustChange.toFixed(1)}%
              </div>
            </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">
            {currentData?.winrate.toFixed(1) || trader.winrate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400">Winrate</div>
          <div className={`text-xs ${winrateChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {winrateChange >= 0 ? '+' : ''}{winrateChange.toFixed(1)}%
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-400">
            {currentData?.roi.toFixed(1) || trader.avg_roi.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400">ROI</div>
          <div className="text-xs text-gray-500">
            Average
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-400">
            {currentData?.signals_count || trader.total_signals}
          </div>
          <div className="text-sm text-gray-400">Signals</div>
          <div className="text-xs text-gray-500">
            Total
              </div>
            </div>
          </div>

          {/* График */}
      <div className="bg-gray-900 rounded-lg p-4">
        <svg width={chartWidth} height={chartHeight} className="w-full">
              {/* Сетка */}
              <defs>
            <pattern id="grid" width="50" height="40" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 40" fill="none" stroke="#374151" strokeWidth="1"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
              
          {/* Линии графика */}
          {performanceData.length > 1 && (
            <>
              {createPath(performanceData, 'trust_index', '#3B82F6')}
              {createPath(performanceData, 'winrate', '#10B981')} 
              {createPath(performanceData, 'roi', '#F59E0B')}
            </>
          )}
          
          {/* Оси */}
          <line x1={padding} y1={padding} x2={padding} y2={chartHeight - padding} stroke="#6B7280" strokeWidth="1"/>
          <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="#6B7280" strokeWidth="1"/>
            </svg>
            
        {/* Легенда */}
        <div className="flex justify-center space-x-6 mt-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-0.5 bg-blue-400"></div>
            <span className="text-xs text-gray-400">Trust Index</span>
            </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-0.5 bg-green-400"></div>
            <span className="text-xs text-gray-400">Winrate</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-0.5 bg-yellow-400"></div>
            <span className="text-xs text-gray-400">ROI</span>
              </div>
            </div>
          </div>
        </div>
  )
}