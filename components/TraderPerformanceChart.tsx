"use client"

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'

interface TraderPerformanceChartProps {
  traderId: string
  data: Array<{
    date: string
    pnl: number
    cumulativePnl: number
  }>
  period: '7d' | '30d' | '90d'
}

const TraderPerformanceChart: React.FC<TraderPerformanceChartProps> = ({ 
  traderId, 
  data, 
  period 
}) => {
  // Генерируем примерные данные для графика P&L
  const generateMockData = () => {
    const points = period === '7d' ? 7 : period === '30d' ? 30 : 90
    const mockData = []
    let cumulativePnL = 0
    
    for (let i = 0; i < points; i++) {
      const date = new Date()
      date.setDate(date.getDate() - (points - i))
      
      // Генерируем случайное изменение P&L (-500 до +800)
      const dailyPnL = (Math.random() - 0.4) * 1300
      cumulativePnL += dailyPnL
      
      mockData.push({
        date: date.toISOString().split('T')[0],
        pnl: dailyPnL,
        cumulativePnl: cumulativePnL
      })
    }
    
    return mockData
  }

  const chartData = data.length > 0 ? data : generateMockData()
  
  // Находим min/max для масштабирования
  const minPnL = Math.min(...chartData.map(d => d.cumulativePnl))
  const maxPnL = Math.max(...chartData.map(d => d.cumulativePnl))
  const range = maxPnL - minPnL || 1000

  // Создаём SVG path для линии графика
  const createPath = (points: Array<{x: number, y: number}>) => {
    if (points.length < 2) return ''
    
    const pathData = points.map((point, index) => {
      const command = index === 0 ? 'M' : 'L'
      return `${command} ${point.x} ${point.y}`
    }).join(' ')
    
    return pathData
  }

  // Преобразуем данные в координаты SVG
  const svgPoints = chartData.map((item, index) => ({
    x: (index / (chartData.length - 1)) * 300, // Ширина графика 300px
    y: 120 - ((item.cumulativePnl - minPnL) / range) * 100 // Высота графика 100px, отступ 20px
  }))

  const pathD = createPath(svgPoints)
  const isProfit = chartData[chartData.length - 1]?.cumulativePnl >= 0

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white flex items-center justify-between">
          <span>График P&L</span>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-400">
              {new Date(chartData[0]?.date).toLocaleDateString('ru-RU')} - {new Date().toLocaleDateString('ru-RU')}
            </div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Общий P&L и Суточный P&L */}
          <div className="flex justify-between items-center">
            <div>
              <div className="text-sm text-gray-400">📉 Общий P&L</div>
              <div className={`text-lg font-bold ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
                {chartData[chartData.length - 1]?.cumulativePnl.toFixed(2)} USD
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400">📊 Суточный P&L</div>
              <div className="text-lg font-bold text-green-500">
                +{Math.abs(chartData[chartData.length - 1]?.pnl || 0).toFixed(2)} USD
              </div>
            </div>
          </div>

          {/* График */}
          <div className="relative bg-gray-800 rounded-lg p-4" style={{ height: '140px' }}>
            <svg width="100%" height="120" className="overflow-visible">
              {/* Сетка */}
              <defs>
                <pattern id="grid" width="30" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 30 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5" opacity="0.3"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
              
              {/* Градиент для заливки */}
              <defs>
                <linearGradient id={`gradient-${traderId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor={isProfit ? "#10b981" : "#ef4444"} stopOpacity="0.3"/>
                  <stop offset="100%" stopColor={isProfit ? "#10b981" : "#ef4444"} stopOpacity="0.0"/>
                </linearGradient>
              </defs>
              
              {/* Заливка под графиком */}
              {pathD && (
                <path
                  d={`${pathD} L 300 120 L 0 120 Z`}
                  fill={`url(#gradient-${traderId})`}
                />
              )}
              
              {/* Основная линия графика */}
              {pathD && (
                <path
                  d={pathD}
                  fill="none"
                  stroke={isProfit ? "#10b981" : "#ef4444"}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}
              
              {/* Точки на графике */}
              {svgPoints.map((point, index) => (
                <circle
                  key={index}
                  cx={point.x}
                  cy={point.y}
                  r="3"
                  fill={isProfit ? "#10b981" : "#ef4444"}
                  stroke="#1f2937"
                  strokeWidth="2"
                />
              ))}
            </svg>
            
            {/* Оси и подписи */}
            <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-500 px-2">
              <span>{new Date(chartData[0]?.date).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })}</span>
              <span>{new Date(chartData[Math.floor(chartData.length / 2)]?.date).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })}</span>
              <span>{new Date(chartData[chartData.length - 1]?.date).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })}</span>
            </div>
            
            {/* Y-axis labels */}
            <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-gray-500 py-2">
              <span>{maxPnL.toFixed(0)}</span>
              <span>0</span>
              <span>{minPnL.toFixed(0)}</span>
            </div>
          </div>

          {/* Статистика */}
          <div className="grid grid-cols-3 gap-4 pt-2 border-t border-gray-700">
            <div className="text-center">
              <div className="text-xs text-gray-400">Max Drawdown</div>
              <div className="text-sm font-medium text-red-400">
                -{Math.abs(minPnL).toFixed(0)} USD
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400">Max Profit</div>
              <div className="text-sm font-medium text-green-400">
                +{maxPnL.toFixed(0)} USD
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400">Volatility</div>
              <div className="text-sm font-medium text-yellow-400">
                {(range / chartData.length).toFixed(0)} USD
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default TraderPerformanceChart
