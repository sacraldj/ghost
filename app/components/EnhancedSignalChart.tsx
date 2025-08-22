'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Eye, EyeOff, BarChart3, TrendingUp, Clock, Layers } from 'lucide-react'

interface CandleData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface TradeMarker {
  id: string
  type: 'entry' | 'tp1' | 'tp2' | 'tp3' | 'sl' | 'current'
  price: number
  timestamp: number
  label: string
  color: string
}

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

interface Props {
  signalId: string
  signalData?: SignalData
}

const TIMEFRAME_OPTIONS = [
  { value: '1s', label: '1s', minutes: 0.0167 },
  { value: '1m', label: '1m', minutes: 1 },
  { value: '3m', label: '3m', minutes: 3 },
  { value: '5m', label: '5m', minutes: 5 },
  { value: '15m', label: '15m', minutes: 15 },
  { value: '30m', label: '30m', minutes: 30 },
  { value: '1h', label: '1h', minutes: 60 },
  { value: '4h', label: '4h', minutes: 240 },
  { value: '1d', label: '1d', minutes: 1440 }
]

export default function EnhancedSignalChart({ signalId, signalData }: Props) {
  // States
  const [candles, setCandles] = useState<CandleData[]>([])
  const [markers, setMarkers] = useState<TradeMarker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPrice, setCurrentPrice] = useState<number | null>(null)
  
  // Layer visibility
  const [showCandlesLayer, setShowCandlesLayer] = useState(true)
  const [showTradingLayer, setShowTradingLayer] = useState(true)
  
  // Time controls
  const [selectedTimeframe, setSelectedTimeframe] = useState('5m')
  const [isRealtime, setIsRealtime] = useState(true)
  
  // Chart dimensions
  const chartWidth = 800
  const chartHeight = 400
  const padding = 40

  // Fetch chart data
  const fetchChartData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`/api/signal-candles/${signalId}?interval=${selectedTimeframe}`)
      const data = await response.json()
      
      if (data.error) {
        setError(data.error)
        return
      }
      
      setCandles(data.candles || [])
      
      // Create trading markers if signal data exists
      if (data.signal) {
        const signal = data.signal
        const markers: TradeMarker[] = []
        
        // Entry zone
        if (signal.entry_min && signal.entry_max) {
          markers.push({
            id: 'entry_zone',
            type: 'entry',
            price: (signal.entry_min + signal.entry_max) / 2,
            timestamp: new Date(signal.posted_ts || signal.created_at).getTime() / 1000,
            label: `Entry: ${signal.entry_min}-${signal.entry_max}`,
            color: '#3B82F6'
          })
        }
        
        // Take profits
        if (signal.tp1) {
          markers.push({
            id: 'tp1',
            type: 'tp1', 
            price: signal.tp1,
            timestamp: new Date(signal.posted_ts || signal.created_at).getTime() / 1000,
            label: `TP1: ${signal.tp1}`,
            color: '#10B981'
          })
        }
        
        if (signal.tp2) {
          markers.push({
            id: 'tp2',
            type: 'tp2',
            price: signal.tp2,
            timestamp: new Date(signal.posted_ts || signal.created_at).getTime() / 1000,
            label: `TP2: ${signal.tp2}`,
            color: '#059669'
          })
        }
        
        if (signal.tp3) {
          markers.push({
            id: 'tp3',
            type: 'tp3',
            price: signal.tp3,
            timestamp: new Date(signal.posted_ts || signal.created_at).getTime() / 1000,
            label: `TP3: ${signal.tp3}`,
            color: '#047857'
          })
        }
        
        // Stop loss
        if (signal.sl) {
          markers.push({
            id: 'sl',
            type: 'sl',
            price: signal.sl,
            timestamp: new Date(signal.posted_ts || signal.created_at).getTime() / 1000,
            label: `SL: ${signal.sl}`,
            color: '#EF4444'
          })
        }
        
        setMarkers(markers)
      }
      
    } catch (error) {
      console.error('Error fetching chart data:', error)
      setError('Failed to load chart data')
    } finally {
      setLoading(false)
    }
  }

  // Calculate price range
  const getPriceRange = () => {
    if (!candles.length && !markers.length) return { min: 0, max: 100 }
    
    let allPrices: number[] = []
    
    // Add candle prices
    if (showCandlesLayer && candles.length) {
      candles.forEach(candle => {
        allPrices.push(candle.high, candle.low, candle.open, candle.close)
      })
    }
    
    // Add marker prices
    if (showTradingLayer) {
      allPrices.push(...markers.map(m => m.price))
    }
    
    if (allPrices.length === 0) return { min: 0, max: 100 }
    
    const min = Math.min(...allPrices)
    const max = Math.max(...allPrices)
    const padding = (max - min) * 0.1
    
    return { 
      min: min - padding,
      max: max + padding
    }
  }

  // Calculate time range
  const getTimeRange = () => {
    if (!candles.length) {
      const now = Date.now() / 1000
      return { min: now - 3600, max: now } // 1 hour default
    }
    
    const min = Math.min(...candles.map(c => c.timestamp))
    const max = Math.max(...candles.map(c => c.timestamp))
    
    return { min, max }
  }

  // Convert price to Y coordinate
  const priceToY = (price: number) => {
    const { min, max } = getPriceRange()
    return padding + (max - price) / (max - min) * (chartHeight - 2 * padding)
  }

  // Convert timestamp to X coordinate
  const timestampToX = (timestamp: number) => {
    const { min, max } = getTimeRange()
    if (max === min) return padding
    return padding + (timestamp - min) / (max - min) * (chartWidth - 2 * padding)
  }

  // Format price for display
  const formatPrice = (price: number) => {
    if (price < 1) return price.toFixed(6)
    if (price < 100) return price.toFixed(4)
    return price.toFixed(2)
  }

  // Format time for display
  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('ru-RU', {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  useEffect(() => {
    fetchChartData()
  }, [signalId, selectedTimeframe])

  useEffect(() => {
    if (!isRealtime) return
    
    const interval = setInterval(fetchChartData, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [isRealtime, signalId, selectedTimeframe])

  const priceRange = getPriceRange()
  const timeRange = getTimeRange()

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            {signalData ? `${signalData.symbol} ${signalData.side}` : `Signal #${signalId}`}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Badge variant={isRealtime ? "default" : "secondary"} className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {isRealtime ? 'Live' : 'Static'}
            </Badge>
            
            {currentPrice && (
              <Badge variant="outline" className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                ${formatPrice(currentPrice)}
              </Badge>
            )}
          </div>
        </div>

        {/* Chart Controls */}
        <div className="flex flex-wrap items-center gap-4 mt-4">
          {/* Timeframe Selection */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Timeframe:</label>
            <div className="flex flex-wrap gap-1">
              {TIMEFRAME_OPTIONS.map((tf) => (
                <Button
                  key={tf.value}
                  variant={selectedTimeframe === tf.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedTimeframe(tf.value)}
                >
                  {tf.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Layer Controls */}
          <div className="flex items-center gap-4 ml-auto">
            <Button
              variant={showCandlesLayer ? "default" : "outline"}
              size="sm"
              onClick={() => setShowCandlesLayer(!showCandlesLayer)}
              className="flex items-center gap-2"
            >
              {showCandlesLayer ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
              Candles
            </Button>
            
            <Button
              variant={showTradingLayer ? "default" : "outline"}
              size="sm"
              onClick={() => setShowTradingLayer(!showTradingLayer)}
              className="flex items-center gap-2"
            >
              {showTradingLayer ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
              Trading
            </Button>
            
            <Button
              variant={isRealtime ? "default" : "outline"}
              size="sm"
              onClick={() => setIsRealtime(!isRealtime)}
              className="flex items-center gap-2"
            >
              <Clock className="h-4 w-4" />
              {isRealtime ? 'Live' : 'Paused'}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-[400px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-[400px] text-red-500">
            <p>❌ {error}</p>
          </div>
        ) : (
          <div className="relative">
            {/* Main Chart SVG */}
            <svg width={chartWidth} height={chartHeight} className="border rounded-lg bg-gray-50 dark:bg-gray-900">
              {/* Grid Lines */}
              <defs>
                <pattern id="grid" width="50" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 50 0 L 0 0 0 30" fill="none" stroke="#e5e7eb" strokeWidth="0.5"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />

              {/* Price Axis */}
              {Array.from({ length: 6 }, (_, i) => {
                const price = priceRange.min + (priceRange.max - priceRange.min) * i / 5
                const y = priceToY(price)
                return (
                  <g key={i}>
                    <line x1={padding} y1={y} x2={chartWidth - padding} y2={y} 
                          stroke="#d1d5db" strokeWidth="0.5" strokeDasharray="3,3" />
                    <text x={padding - 5} y={y + 4} textAnchor="end" fontSize="10" fill="#6b7280">
                      {formatPrice(price)}
                    </text>
                  </g>
                )
              })}

              {/* Time Axis */}
              {Array.from({ length: 6 }, (_, i) => {
                const timestamp = timeRange.min + (timeRange.max - timeRange.min) * i / 5
                const x = timestampToX(timestamp)
                return (
                  <g key={i}>
                    <line x1={x} y1={padding} x2={x} y2={chartHeight - padding} 
                          stroke="#d1d5db" strokeWidth="0.5" strokeDasharray="3,3" />
                    <text x={x} y={chartHeight - padding + 15} textAnchor="middle" fontSize="9" fill="#6b7280">
                      {formatTime(timestamp)}
                    </text>
                  </g>
                )
              })}

              {/* Layer 1: Candlesticks */}
              {showCandlesLayer && candles.map((candle, i) => {
                const x = timestampToX(candle.timestamp)
                const openY = priceToY(candle.open)
                const closeY = priceToY(candle.close)
                const highY = priceToY(candle.high)
                const lowY = priceToY(candle.low)
                
                const isGreen = candle.close > candle.open
                const bodyColor = isGreen ? '#10b981' : '#ef4444'
                const wickColor = isGreen ? '#065f46' : '#991b1b'
                
                const candleWidth = Math.max(2, (chartWidth - 2 * padding) / candles.length * 0.8)
                
                return (
                  <g key={i}>
                    {/* Wick */}
                    <line x1={x} y1={highY} x2={x} y2={lowY} 
                          stroke={wickColor} strokeWidth="1" />
                    
                    {/* Body */}
                    <rect 
                      x={x - candleWidth/2} 
                      y={Math.min(openY, closeY)} 
                      width={candleWidth}
                      height={Math.abs(closeY - openY) || 1}
                      fill={bodyColor}
                      stroke={wickColor}
                      strokeWidth="1"
                    />
                  </g>
                )
              })}

              {/* Layer 2: Trading Markers */}
              {showTradingLayer && markers.map((marker) => {
                const x = timestampToX(marker.timestamp)
                const y = priceToY(marker.price)
                
                return (
                  <g key={marker.id}>
                    {/* Horizontal price line */}
                    <line 
                      x1={padding} 
                      y1={y} 
                      x2={chartWidth - padding} 
                      y2={y}
                      stroke={marker.color}
                      strokeWidth="2"
                      strokeDasharray={marker.type === 'sl' ? "5,5" : "none"}
                      opacity="0.8"
                    />
                    
                    {/* Price marker circle */}
                    <circle 
                      cx={x} 
                      cy={y} 
                      r="4"
                      fill={marker.color}
                      stroke="white"
                      strokeWidth="2"
                    />
                    
                    {/* Price label */}
                    <text 
                      x={chartWidth - padding + 5} 
                      y={y + 4} 
                      fontSize="10" 
                      fill={marker.color}
                      fontWeight="bold"
                    >
                      {marker.label}
                    </text>
                  </g>
                )
              })}
            </svg>

            {/* Chart Legend */}
            <div className="mt-4 flex flex-wrap gap-4 text-sm">
              {showTradingLayer && markers.map((marker) => (
                <div key={marker.id} className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full border border-white"
                    style={{ backgroundColor: marker.color }}
                  />
                  <span className="text-gray-600 dark:text-gray-300">
                    {marker.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Chart Stats */}
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-500">Timeframe</p>
                <p className="font-semibold">{selectedTimeframe.toUpperCase()}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">Candles</p>
                <p className="font-semibold">{candles.length}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">Price Range</p>
                <p className="font-semibold text-xs">
                  {formatPrice(priceRange.min)} - {formatPrice(priceRange.max)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">Markers</p>
                <p className="font-semibold">{markers.length}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
