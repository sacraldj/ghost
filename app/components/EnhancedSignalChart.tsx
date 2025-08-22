'use client'

import React, { useState, useEffect } from 'react'

// Простые UI компоненты без shadcn/ui
const Card = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 ${className}`}>
    {children}
  </div>
)

const CardHeader = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => (
  <div className={`p-6 border-b border-gray-200 dark:border-gray-700 ${className}`}>
    {children}
  </div>
)

const CardContent = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => (
  <div className={`p-6 ${className}`}>
    {children}
  </div>
)

const CardTitle = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => (
  <h3 className={`text-2xl font-semibold leading-none tracking-tight ${className}`}>
    {children}
  </h3>
)

const Badge = ({ children, variant = "default", className = "" }: { 
  children: React.ReactNode, 
  variant?: "default" | "secondary" | "outline", 
  className?: string 
}) => {
  const variants = {
    default: "bg-blue-600 text-white",
    secondary: "bg-gray-600 text-white",
    outline: "border border-gray-400 bg-transparent text-gray-700 dark:text-gray-300"
  }
  return (
    <div className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors ${variants[variant]} ${className}`}>
      {children}
    </div>
  )
}

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
  
  // Chart dimensions and zoom
  const [zoomLevel, setZoomLevel] = useState(1)
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })
  const chartWidth = 1000  // Увеличиваем размер для лучшего качества
  const chartHeight = 500  // Увеличиваем высоту
  const padding = 50

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
            📊
            {signalData ? `${signalData.symbol} ${signalData.side}` : `Signal #${signalId}`}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Badge variant={isRealtime ? "default" : "secondary"} className="flex items-center gap-1 bg-green-600 text-white">
              ⏱️ {isRealtime ? 'Live' : 'Static'}
            </Badge>
            
            {currentPrice && (
              <Badge variant="outline" className="flex items-center gap-1 border-yellow-400 text-yellow-400">
                💹 ${formatPrice(currentPrice)}
              </Badge>
            )}
          </div>
        </div>

                  {/* Professional Chart Controls - Bybit Style */}
        <div className="flex flex-col gap-4 mt-4">
          
          {/* Top Row - Timeframe Selection (Bybit Style) */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Timeframe</span>
              <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1 gap-1">
                {TIMEFRAME_OPTIONS.map((tf) => (
                  <button
                    key={tf.value}
                    onClick={() => setSelectedTimeframe(tf.value)}
                    className={`
                      px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200
                      ${selectedTimeframe === tf.value 
                        ? 'bg-blue-500 text-white shadow-sm' 
                        : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-700'
                      }
                    `}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Live Status Indicator */}
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${isRealtime ? 'bg-green-900/20 border border-green-500/30' : 'bg-gray-900/20 border border-gray-500/30'}`}>
                <div className={`w-2 h-2 rounded-full ${isRealtime ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
                <span className={`text-sm font-medium ${isRealtime ? 'text-green-400' : 'text-gray-400'}`}>
                  {isRealtime ? 'LIVE' : 'STATIC'}
                </span>
              </div>
              
              <button
                onClick={() => setIsRealtime(!isRealtime)}
                className="p-2 rounded-lg bg-gray-900/20 border border-gray-500/30 hover:bg-gray-900/40 transition-colors text-gray-400"
              >
                ⏰
              </button>
            </div>
          </div>

          {/* Bottom Row - Layer Controls (Professional Toggle Style) */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Chart Layers</span>
              
              {/* Candles Layer Toggle */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowCandlesLayer(!showCandlesLayer)}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${showCandlesLayer ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}
                  `}
                >
                  <span className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${showCandlesLayer ? 'translate-x-6' : 'translate-x-1'}
                  `} />
                </button>
                <span className={`text-sm font-medium ${showCandlesLayer ? 'text-blue-400' : 'text-gray-500'}`}>
                  📊 Candles
                </span>
              </div>

              {/* Trading Layer Toggle */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowTradingLayer(!showTradingLayer)}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${showTradingLayer ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-600'}
                  `}
                >
                  <span className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${showTradingLayer ? 'translate-x-6' : 'translate-x-1'}
                  `} />
                </button>
                <span className={`text-sm font-medium ${showTradingLayer ? 'text-green-400' : 'text-gray-500'}`}>
                  🎯 Signals
                </span>
              </div>
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Zoom</span>
              <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.25))}
                  className="px-2 py-1 text-sm hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  ➖
                </button>
                <button
                  onClick={() => {setZoomLevel(1); setPanOffset({ x: 0, y: 0 })}}
                  className="px-3 py-1 text-sm hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  {Math.round(zoomLevel * 100)}%
                </button>
                <button
                  onClick={() => setZoomLevel(Math.min(3, zoomLevel + 0.25))}
                  className="px-2 py-1 text-sm hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  ➕
                </button>
              </div>
            </div>
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
            {/* Professional Chart Container - Bybit Style */}
            <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
              
              {/* Chart Header with Symbol and Price */}
              <div className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700">
                <div className="flex items-center gap-4">
                  <h3 className="text-lg font-bold text-white">
                    {signalData ? signalData.symbol : `Signal #${signalId}`}
                  </h3>
                  {currentPrice && (
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-mono text-white">
                        {formatPrice(currentPrice)}
                      </span>
                      <Badge variant="outline" className="text-green-400 border-green-400">
                        {signalData?.side}
                      </Badge>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <span>📊 {candles.length} candles</span>
                  <span>•</span>
                  <span>⏱️ {selectedTimeframe.toUpperCase()}</span>
                </div>
              </div>

              {/* Main Chart SVG - Enhanced */}
              <svg 
                width={chartWidth} 
                height={chartHeight} 
                className="bg-gray-900"
                style={{ cursor: 'crosshair' }}
              >
                {/* Professional Grid */}
                <defs>
                  <pattern id="professionalGrid" width="50" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 50 0 L 0 0 0 40" fill="none" stroke="#374151" strokeWidth="0.5" opacity="0.3"/>
                  </pattern>
                  <linearGradient id="candleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style={{stopColor: '#10b981', stopOpacity: 0.8}} />
                    <stop offset="100%" style={{stopColor: '#059669', stopOpacity: 0.9}} />
                  </linearGradient>
                  <linearGradient id="bearGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style={{stopColor: '#ef4444', stopOpacity: 0.8}} />
                    <stop offset="100%" style={{stopColor: '#dc2626', stopOpacity: 0.9}} />
                  </linearGradient>
                </defs>
                <rect width="100%" height="100%" fill="url(#professionalGrid)" />

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

              {/* Layer 1: Professional Candlesticks - Bybit Style */}
              {showCandlesLayer && candles.map((candle, i) => {
                const x = timestampToX(candle.timestamp) * zoomLevel + panOffset.x
                const openY = priceToY(candle.open) * zoomLevel + panOffset.y
                const closeY = priceToY(candle.close) * zoomLevel + panOffset.y
                const highY = priceToY(candle.high) * zoomLevel + panOffset.y
                const lowY = priceToY(candle.low) * zoomLevel + panOffset.y
                
                const isGreen = candle.close > candle.open
                const isDoji = Math.abs(candle.close - candle.open) < (candle.high - candle.low) * 0.02
                
                const candleWidth = Math.max(3, (chartWidth - 2 * padding) / candles.length * 0.85 * zoomLevel)
                
                return (
                  <g key={i} className="candle-group">
                    {/* High-Low Wick */}
                    <line 
                      x1={x} y1={highY} x2={x} y2={lowY} 
                      stroke={isGreen ? '#10b981' : '#ef4444'} 
                      strokeWidth={Math.max(1, zoomLevel)} 
                      opacity="0.8"
                    />
                    
                    {/* Candle Body with Gradient */}
                    <rect 
                      x={x - candleWidth/2} 
                      y={Math.min(openY, closeY)} 
                      width={candleWidth}
                      height={Math.max(1, Math.abs(closeY - openY))}
                      fill={isDoji ? '#6b7280' : (isGreen ? 'url(#candleGradient)' : 'url(#bearGradient)')}
                      stroke={isGreen ? '#059669' : '#dc2626'}
                      strokeWidth="0.5"
                      rx="1"
                      className="transition-opacity hover:opacity-80"
                    />
                    
                    {/* Volume indicator at bottom */}
                    <rect 
                      x={x - candleWidth/2} 
                      y={chartHeight - padding - (candle.volume / Math.max(...candles.map(c => c.volume))) * 30}
                      width={candleWidth}
                      height={(candle.volume / Math.max(...candles.map(c => c.volume))) * 30}
                      fill={isGreen ? '#10b981' : '#ef4444'}
                      opacity="0.3"
                    />
                  </g>
                )
              })}

              {/* Layer 2: Professional Trading Markers - Styled as Bybit */}
              {showTradingLayer && markers.map((marker) => {
                const x = timestampToX(marker.timestamp) * zoomLevel + panOffset.x
                const y = priceToY(marker.price) * zoomLevel + panOffset.y
                
                // Icon styles for different marker types
                const getMarkerIcon = (type: string) => {
                  switch(type) {
                    case 'tp1': return '🎯'
                    case 'tp2': return '💎'
                    case 'tp3': return '🏆'
                    case 'sl': return '🛑'
                    case 'entry': return '📍'
                    default: return '📊'
                  }
                }
                
                return (
                  <g key={marker.id} className="trading-marker">
                    {/* Professional price line with shadow */}
                    <line 
                      x1={padding} y1={y+1} x2={chartWidth - padding} y2={y+1}
                      stroke="#000000" strokeWidth="3" opacity="0.2"
                    />
                    <line 
                      x1={padding} y1={y} x2={chartWidth - padding} y2={y}
                      stroke={marker.color}
                      strokeWidth="2"
                      strokeDasharray={marker.type === 'sl' ? "8,4" : marker.type === 'entry' ? "none" : "12,6"}
                      opacity="0.9"
                      className="animate-pulse"
                    />
                    
                    {/* Enhanced marker with glow effect */}
                    <circle 
                      cx={x} cy={y} r="8"
                      fill={marker.color} opacity="0.2"
                    />
                    <circle 
                      cx={x} cy={y} r="5"
                      fill={marker.color}
                      stroke="white"
                      strokeWidth="2"
                      className="shadow-lg"
                    />
                    
                    {/* Price label with professional styling */}
                    <g>
                      <rect 
                        x={chartWidth - padding + 5} 
                        y={y - 12} 
                        width="80" 
                        height="20"
                        fill={marker.color}
                        rx="4"
                        opacity="0.9"
                      />
                      <text 
                        x={chartWidth - padding + 10} 
                        y={y - 2} 
                        fontSize="11" 
                        fill="white"
                        fontWeight="bold"
                        fontFamily="monospace"
                      >
                        {getMarkerIcon(marker.type)} {formatPrice(marker.price)}
                      </text>
                    </g>

                    {/* Interactive hover area */}
                    <circle 
                      cx={x} cy={y} r="15"
                      fill="transparent"
                      className="cursor-pointer hover:fill-white hover:opacity-10"
                    />
                  </g>
                )
              })}
            </svg>
            </div>

            {/* Professional Chart Legend - Bybit Style */}
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

            {/* Professional Stats Panel - Bybit Style */}
            <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
              <div className="text-center">
                <p className="text-xs text-gray-400 uppercase tracking-wide">Timeframe</p>
                <p className="font-bold text-white text-lg">{selectedTimeframe.toUpperCase()}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-400 uppercase tracking-wide">Candles</p>
                <p className="font-bold text-blue-400 text-lg">{candles.length}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-400 uppercase tracking-wide">Price Range</p>
                <p className="font-bold text-yellow-400 text-sm font-mono">
                  {formatPrice(priceRange.min)}
                </p>
                <p className="font-bold text-yellow-400 text-sm font-mono">
                  {formatPrice(priceRange.max)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-400 uppercase tracking-wide">Signals</p>
                <p className="font-bold text-green-400 text-lg">{markers.length}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-400 uppercase tracking-wide">Zoom</p>
                <p className="font-bold text-purple-400 text-lg">{Math.round(zoomLevel * 100)}%</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
