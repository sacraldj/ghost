'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Target,
  Shield,
  Play,
  Square,
  Loader2,
  BarChart3,
  Maximize2
} from 'lucide-react'

// Интерфейсы для данных
interface CandleData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  quote_volume?: number
}

interface SignalData {
  id: string
  symbol: string
  side: 'LONG' | 'SHORT'
  entry_min: number
  entry_max: number
  tp1: number
  tp2: number
  sl: number
  posted_ts: number
  status: string
}

interface ChartStats {
  total_candles: number
  time_range: {
    start: number
    end: number
    duration_hours: number
  }
  price_range: {
    min: number
    max: number
    first: number
    last: number
  }
}

interface SignalChartProps {
  signalId: string | null
  onTrackingToggle?: (signalId: string, isTracking: boolean) => void
}

export default function SignalChart({ signalId, onTrackingToggle }: SignalChartProps) {
  const [signalData, setSignalData] = useState<SignalData | null>(null)
  const [candles, setCandles] = useState<CandleData[]>([])
  const [stats, setStats] = useState<ChartStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [isTracking, setIsTracking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [timeframe, setTimeframe] = useState('1m')
  const [isFullscreen, setIsFullscreen] = useState(false)
  
  const chartRef = useRef<HTMLDivElement>(null)

  // Загрузка данных при изменении signalId
  useEffect(() => {
    if (signalId) {
      fetchSignalData(signalId)
    } else {
      resetChart()
    }
  }, [signalId, timeframe])

  const resetChart = () => {
    setSignalData(null)
    setCandles([])
    setStats(null)
    setError(null)
    setIsTracking(false)
  }

  const fetchSignalData = async (id: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`/api/signal-candles/${id}?interval=${timeframe}&limit=2000`)
      const result = await response.json()

      if (response.ok) {
        setSignalData(result.signal)
        setCandles(result.candles || [])
        setStats(result.stats)
        
        // Проверяем статус отслеживания
        await checkTrackingStatus(id)
      } else {
        setError(result.error || 'Ошибка загрузки данных')
      }
    } catch (err) {
      setError('Ошибка подключения к серверу')
      console.error('Fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const checkTrackingStatus = async (id: string) => {
    try {
      const response = await fetch('/api/signal-tracking')
      const result = await response.json()
      
      if (response.ok && result.subscriptions) {
        const subscription = result.subscriptions.find(
          (sub: any) => sub.signal_id === id && sub.status === 'active'
        )
        setIsTracking(!!subscription)
      }
    } catch (err) {
      console.error('Error checking tracking status:', err)
    }
  }

  const toggleTracking = async () => {
    if (!signalId) return

    try {
      const action = isTracking ? 'stop' : 'start'
      const response = await fetch('/api/signal-tracking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signal_id: signalId, action })
      })

      const result = await response.json()
      
      if (response.ok) {
        setIsTracking(!isTracking)
        onTrackingToggle?.(signalId, !isTracking)
        
        // Обновляем данные через несколько секунд
        setTimeout(() => fetchSignalData(signalId), 2000)
      } else {
        setError(result.error || 'Ошибка управления отслеживанием')
      }
    } catch (err) {
      setError('Ошибка подключения к серверу')
    }
  }

  // Расчет цветов и позиций для уровней
  const getLevelColor = (type: 'entry' | 'tp' | 'sl') => {
    switch (type) {
      case 'entry': return 'rgb(255, 193, 7)'  // yellow
      case 'tp': return 'rgb(34, 197, 94)'     // green
      case 'sl': return 'rgb(239, 68, 68)'     // red
      default: return 'rgb(156, 163, 175)'     // gray
    }
  }

  const formatPrice = (price: number) => {
    return price?.toFixed(4) || '0.0000'
  }

  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit', 
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Простая SVG визуализация графика
  const renderChart = () => {
    if (!candles.length || !stats) return null

    const width = 800
    const height = 400
    const padding = 60

    const { price_range } = stats
    const priceSpread = price_range.max - price_range.min
    const priceStep = priceSpread / (height - 2 * padding)
    const timeStep = (width - 2 * padding) / candles.length

    // Функция для получения Y координаты по цене
    const getY = (price: number) => {
      return height - padding - (price - price_range.min) / priceStep
    }

    // Функция для получения X координаты по индексу
    const getX = (index: number) => {
      return padding + index * timeStep
    }

    return (
      <svg width={width} height={height} className="w-full h-full">
        {/* Фон */}
        <rect width={width} height={height} fill="rgb(17, 24, 39)" />
        
        {/* Сетка */}
        {Array.from({ length: 5 }, (_, i) => {
          const y = padding + (i * (height - 2 * padding)) / 4
          const price = price_range.max - (i * priceSpread) / 4
          return (
            <g key={`grid-${i}`}>
              <line 
                x1={padding} 
                y1={y} 
                x2={width - padding} 
                y2={y} 
                stroke="rgb(55, 65, 81)" 
                strokeWidth={1}
                strokeDasharray="2,2"
              />
              <text 
                x={padding - 10} 
                y={y + 4} 
                fill="rgb(156, 163, 175)" 
                fontSize="10" 
                textAnchor="end"
              >
                {formatPrice(price)}
              </text>
            </g>
          )
        })}

        {/* Уровни сигнала */}
        {signalData && (
          <>
            {/* Entry зона */}
            {signalData.entry_min > 0 && signalData.entry_max > 0 && (
              <>
                <rect
                  x={padding}
                  y={getY(signalData.entry_max)}
                  width={width - 2 * padding}
                  height={getY(signalData.entry_min) - getY(signalData.entry_max)}
                  fill="rgba(255, 193, 7, 0.1)"
                  stroke="rgb(255, 193, 7)"
                  strokeWidth={1}
                  strokeDasharray="5,5"
                />
                <text
                  x={padding + 5}
                  y={getY((signalData.entry_min + signalData.entry_max) / 2) + 4}
                  fill="rgb(255, 193, 7)"
                  fontSize="11"
                  fontWeight="bold"
                >
                  ENTRY ZONE
                </text>
              </>
            )}

            {/* TP1 */}
            {signalData.tp1 > 0 && (
              <>
                <line 
                  x1={padding} 
                  y1={getY(signalData.tp1)} 
                  x2={width - padding} 
                  y2={getY(signalData.tp1)} 
                  stroke="rgb(34, 197, 94)" 
                  strokeWidth={2}
                />
                <text
                  x={padding + 5}
                  y={getY(signalData.tp1) - 5}
                  fill="rgb(34, 197, 94)"
                  fontSize="11"
                  fontWeight="bold"
                >
                  TP1: {formatPrice(signalData.tp1)}
                </text>
              </>
            )}

            {/* TP2 */}
            {signalData.tp2 > 0 && (
              <>
                <line 
                  x1={padding} 
                  y1={getY(signalData.tp2)} 
                  x2={width - padding} 
                  y2={getY(signalData.tp2)} 
                  stroke="rgb(34, 197, 94)" 
                  strokeWidth={2}
                  strokeDasharray="3,3"
                />
                <text
                  x={padding + 5}
                  y={getY(signalData.tp2) - 5}
                  fill="rgb(34, 197, 94)"
                  fontSize="11"
                  fontWeight="bold"
                >
                  TP2: {formatPrice(signalData.tp2)}
                </text>
              </>
            )}

            {/* Stop Loss */}
            {signalData.sl > 0 && (
              <>
                <line 
                  x1={padding} 
                  y1={getY(signalData.sl)} 
                  x2={width - padding} 
                  y2={getY(signalData.sl)} 
                  stroke="rgb(239, 68, 68)" 
                  strokeWidth={2}
                />
                <text
                  x={padding + 5}
                  y={getY(signalData.sl) + 15}
                  fill="rgb(239, 68, 68)"
                  fontSize="11"
                  fontWeight="bold"
                >
                  SL: {formatPrice(signalData.sl)}
                </text>
              </>
            )}
          </>
        )}

        {/* Candlesticks */}
        {candles.map((candle, index) => {
          const x = getX(index)
          const openY = getY(candle.open)
          const closeY = getY(candle.close)
          const highY = getY(candle.high)
          const lowY = getY(candle.low)
          
          const isGreen = candle.close > candle.open
          const color = isGreen ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
          const bodyHeight = Math.abs(closeY - openY)

          return (
            <g key={`candle-${index}`}>
              {/* Wick */}
              <line 
                x1={x} 
                y1={highY} 
                x2={x} 
                y2={lowY} 
                stroke={color} 
                strokeWidth={1}
              />
              
              {/* Body */}
              <rect
                x={x - 2}
                y={Math.min(openY, closeY)}
                width={4}
                height={Math.max(bodyHeight, 1)}
                fill={color}
                stroke={color}
              />
            </g>
          )
        })}

        {/* Временные метки */}
        {candles.length > 0 && Array.from({ length: 6 }, (_, i) => {
          const candleIndex = Math.floor(i * (candles.length - 1) / 5)
          const candle = candles[candleIndex]
          const x = getX(candleIndex)
          return (
            <text
              key={`time-${i}`}
              x={x}
              y={height - 10}
              fill="rgb(156, 163, 175)"
              fontSize="9"
              textAnchor="middle"
            >
              {formatTime(candle.timestamp)}
            </text>
          )
        })}
      </svg>
    )
  }

  return (
    <div className={`bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl border border-gray-800/50 shadow-2xl ${
      isFullscreen ? 'fixed inset-4 z-50' : ''
    }`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-semibold text-white">
                📊 Interactive Signal Chart
              </h3>
            </div>
            
            {signalData && (
              <div className="flex items-center gap-3">
                <div className="bg-blue-600/20 px-3 py-1 rounded-lg border border-blue-500/30">
                  <span className="text-blue-300 font-medium">{signalData.symbol}</span>
                </div>
                <div className={`px-3 py-1 rounded-lg font-medium ${
                  signalData.side === 'LONG' 
                    ? 'bg-green-600/20 text-green-300 border border-green-500/30'
                    : 'bg-red-600/20 text-red-300 border border-red-500/30'
                }`}>
                  {signalData.side === 'LONG' ? <TrendingUp className="w-4 h-4 inline mr-1" /> : <TrendingDown className="w-4 h-4 inline mr-1" />}
                  {signalData.side}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Timeframe selector */}
            <select 
              value={timeframe} 
              onChange={(e) => setTimeframe(e.target.value)}
              className="bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1s">1s</option>
              <option value="1m">1m</option>
              <option value="5m">5m</option>
              <option value="15m">15m</option>
              <option value="1h">1h</option>
            </select>

            {/* Tracking control */}
            {signalId && (
              <button
                onClick={toggleTracking}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  isTracking 
                    ? 'bg-red-600/20 text-red-300 border border-red-500/30 hover:bg-red-600/30'
                    : 'bg-green-600/20 text-green-300 border border-green-500/30 hover:bg-green-600/30'
                }`}
              >
                {isTracking ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {isTracking ? 'Stop Recording' : 'Start Recording'}
              </button>
            )}

            {/* Fullscreen toggle */}
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Status indicators */}
        <div className="flex items-center gap-4 mt-3">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-lg text-sm ${
            isTracking 
              ? 'bg-green-600/20 text-green-300 border border-green-500/30'
              : 'bg-gray-600/20 text-gray-400 border border-gray-600/30'
          }`}>
            <Activity className={`w-3 h-3 ${isTracking ? 'animate-pulse' : ''}`} />
            {isTracking ? '⚡ Recording' : '📊 Static View'}
          </div>

          {stats && (
            <>
              <div className="text-sm text-gray-400">
                <Clock className="w-3 h-3 inline mr-1" />
                {stats.total_candles} candles, {stats.time_range.duration_hours.toFixed(1)}h
              </div>
              <div className="text-sm text-gray-400">
                Range: {formatPrice(stats.price_range.min)} - {formatPrice(stats.price_range.max)}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Chart Content */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="flex items-center gap-3 text-gray-400">
              <Loader2 className="w-6 h-6 animate-spin" />
              <span>Loading chart data...</span>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-red-400">
              <div className="text-lg font-medium mb-2">❌ Error Loading Chart</div>
              <div className="text-sm">{error}</div>
            </div>
          </div>
        ) : !signalId ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-gray-400">
              <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <div className="text-lg font-medium mb-2">Select a Signal</div>
              <div className="text-sm">Choose a signal from the table below to view its chart</div>
            </div>
          </div>
        ) : candles.length === 0 ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-yellow-400">
              <div className="text-lg font-medium mb-2">📊 No Chart Data</div>
              <div className="text-sm mb-4">No candles recorded for this signal yet</div>
              {!isTracking && (
                <button
                  onClick={toggleTracking}
                  className="bg-green-600/20 text-green-300 border border-green-500/30 hover:bg-green-600/30 px-4 py-2 rounded-lg font-medium transition-all"
                >
                  <Play className="w-4 h-4 inline mr-2" />
                  Start Recording
                </button>
              )}
            </div>
          </div>
        ) : (
          <div ref={chartRef} className="w-full h-96 bg-gray-800/20 rounded-xl overflow-hidden">
            {renderChart()}
          </div>
        )}
      </div>

      {/* Signal levels summary */}
      {signalData && (
        <div className="p-4 border-t border-gray-800/50 bg-gray-950/50">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-yellow-400 text-lg font-bold">
                {formatPrice(signalData.entry_min)} - {formatPrice(signalData.entry_max)}
              </div>
              <div className="text-xs text-gray-400">Entry Zone</div>
            </div>
            <div className="text-center">
              <div className="text-green-400 text-lg font-bold">
                <Target className="w-4 h-4 inline mr-1" />
                {formatPrice(signalData.tp1)}
              </div>
              <div className="text-xs text-gray-400">TP1</div>
            </div>
            <div className="text-center">
              <div className="text-green-400 text-lg font-bold">
                <Target className="w-4 h-4 inline mr-1" />
                {formatPrice(signalData.tp2)}
              </div>
              <div className="text-xs text-gray-400">TP2</div>
            </div>
            <div className="text-center">
              <div className="text-red-400 text-lg font-bold">
                <Shield className="w-4 h-4 inline mr-1" />
                {formatPrice(signalData.sl)}
              </div>
              <div className="text-xs text-gray-400">Stop Loss</div>
            </div>
            <div className="text-center">
              <div className="text-blue-400 text-lg font-bold">
                {formatTime(signalData.posted_ts)}
              </div>
              <div className="text-xs text-gray-400">Signal Time</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
