'use client'

import React, { useState, useEffect, useRef } from 'react'

interface CandleData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
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

interface VirtualPrediction {
  timestamp: number
  predictedPrice: number
  confidence: number
  type: 'entry' | 'target' | 'stop'
  achieved?: boolean
}

interface Props {
  signalId: string
  signalData?: SignalData
}

const TIMEFRAMES = [
  { value: '1s', label: '1s' },
  { value: '1m', label: '1m' },
  { value: '3m', label: '3m' },
  { value: '5m', label: '5m', active: true },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1h' },
  { value: '4h', label: '4h' },
  { value: '1d', label: '1d' }
]

export default function ModernTradingChart({ signalId, signalData }: Props) {
  // States
  const [candles, setCandles] = useState<CandleData[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPrice, setCurrentPrice] = useState<number | null>(null)
  const [selectedTimeframe, setSelectedTimeframe] = useState('5m')
  const [predictions, setPredictions] = useState<VirtualPrediction[]>([])
  
  // Layer controls - modern toggle style
  const [showExchangeLayer, setShowExchangeLayer] = useState(true)
  const [showPredictionLayer, setShowPredictionLayer] = useState(true)
  const [showSignalMarkers, setShowSignalMarkers] = useState(true)
  
  // Chart settings
  const [zoom, setZoom] = useState(100)
  const [isLive, setIsLive] = useState(true)
  
  const chartRef = useRef<SVGSVGElement>(null)
  const chartWidth = 1200
  const chartHeight = 600
  const padding = 60

  // Fetch data
  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/signal-candles/${signalId}?interval=${selectedTimeframe}`)
      const data = await response.json()
      
      if (data.candles) {
        setCandles(data.candles)
        if (data.candles.length > 0) {
          setCurrentPrice(data.candles[data.candles.length - 1].close)
        }
      }
      
      // Generate virtual predictions based on signal
      if (data.signal && signalData) {
        const predictions = generateVirtualPredictions(data.signal, data.candles)
        setPredictions(predictions)
      }
      
    } catch (error) {
      console.error('Chart data error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Generate virtual price predictions based on signal data
  const generateVirtualPredictions = (signal: SignalData, candles: CandleData[]): VirtualPrediction[] => {
    if (!candles.length) return []
    
    const signalTime = new Date(signal.posted_ts || signal.created_at).getTime() / 1000
    const predictions: VirtualPrediction[] = []
    const startCandle = candles.find(c => c.timestamp >= signalTime) || candles[0]
    
    // Create prediction path from signal time
    const baseTimestamp = startCandle.timestamp
    const timeStep = 300 // 5 minutes
    
    // Entry zone prediction
    for (let i = 0; i < 20; i++) {
      const timestamp = baseTimestamp + (i * timeStep)
      const entryPrice = (signal.entry_min + signal.entry_max) / 2
      
      predictions.push({
        timestamp,
        predictedPrice: entryPrice + (Math.random() - 0.5) * (signal.entry_max - signal.entry_min) * 0.5,
        confidence: 0.8 - (i * 0.02),
        type: 'entry'
      })
    }
    
    // Target predictions
    if (signal.tp1) {
      for (let i = 10; i < 50; i++) {
        const timestamp = baseTimestamp + (i * timeStep)
        const progress = (i - 10) / 40
        const targetPrice = signal.entry_min + (signal.tp1 - signal.entry_min) * progress
        
        predictions.push({
          timestamp,
          predictedPrice: targetPrice,
          confidence: 0.7 - (i * 0.01),
          type: 'target'
        })
      }
    }
    
    return predictions.sort((a, b) => a.timestamp - b.timestamp)
  }

  // Price/time conversion functions
  const getPriceRange = () => {
    const allPrices = [
      ...candles.flatMap(c => [c.high, c.low, c.open, c.close]),
      ...predictions.map(p => p.predictedPrice),
      ...(signalData ? [signalData.entry_min, signalData.entry_max, signalData.tp1, signalData.tp2, signalData.sl].filter(p => p) : [])
    ]
    
    if (allPrices.length === 0) return { min: 0, max: 100 }
    
    const min = Math.min(...allPrices)
    const max = Math.max(...allPrices)
    const padding = (max - min) * 0.1
    
    return { min: min - padding, max: max + padding }
  }

  const getTimeRange = () => {
    if (!candles.length) {
      const now = Date.now() / 1000
      return { min: now - 3600, max: now }
    }
    
    const min = Math.min(...candles.map(c => c.timestamp))
    const max = Math.max(...candles.map(c => c.timestamp))
    return { min, max }
  }

  const priceToY = (price: number) => {
    const { min, max } = getPriceRange()
    return padding + (max - price) / (max - min) * (chartHeight - 2 * padding)
  }

  const timestampToX = (timestamp: number) => {
    const { min, max } = getTimeRange()
    if (max === min) return padding
    return padding + (timestamp - min) / (max - min) * (chartWidth - 2 * padding)
  }

  const formatPrice = (price: number) => {
    if (price < 1) return price.toFixed(6)
    if (price < 100) return price.toFixed(4)
    return price.toFixed(2)
  }

  useEffect(() => {
    fetchData()
    
    if (isLive) {
      const interval = setInterval(fetchData, 30000)
      return () => clearInterval(interval)
    }
  }, [signalId, selectedTimeframe, isLive])

  const priceRange = getPriceRange()
  const timeRange = getTimeRange()
  const signalTimestamp = signalData ? new Date(signalData.posted_ts || signalData.created_at).getTime() / 1000 : 0

  return (
    <div className="w-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-gray-700/50 overflow-hidden backdrop-blur-sm">
      
      {/* 🎯 MODERN HEADER - 2025 STYLE */}
      <div className="bg-gradient-to-r from-gray-800/90 to-gray-900/90 backdrop-blur-lg border-b border-gray-700/50">
        <div className="flex items-center justify-between p-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">📈</span>
              </div>
              <div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  {signalData?.symbol || `Signal #${signalId}`}
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  {signalData && (
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      signalData.side === 'LONG' 
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                      {signalData.side}
                    </span>
                  )}
                  {currentPrice && (
                    <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                      ${formatPrice(currentPrice)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
          
          {/* Live indicator */}
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl backdrop-blur-sm ${
              isLive 
                ? 'bg-green-500/20 border border-green-500/30' 
                : 'bg-gray-500/20 border border-gray-500/30'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`} />
              <span className={`text-sm font-semibold ${isLive ? 'text-green-400' : 'text-gray-400'}`}>
                {isLive ? 'LIVE' : 'STATIC'}
              </span>
            </div>
          </div>
        </div>

        {/* 🚀 MODERN CONTROLS - NO ROUND TOGGLES */}
        <div className="px-6 pb-6 space-y-4">
          
          {/* Timeframe Selection - Modern Pills */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-400 min-w-[80px]">Timeframe</span>
            <div className="flex gap-1 bg-gray-800/50 backdrop-blur-sm rounded-xl p-1 border border-gray-700/50">
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf.value}
                  onClick={() => setSelectedTimeframe(tf.value)}
                  className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                    selectedTimeframe === tf.value
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/25'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>
          </div>

          {/* Layer Controls - Modern Buttons Instead of Toggles */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-400 min-w-[80px]">Chart Layers</span>
              
              <div className="flex gap-2">
                {/* Exchange Data Layer */}
                <button
                  onClick={() => setShowExchangeLayer(!showExchangeLayer)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    showExchangeLayer
                      ? 'bg-gradient-to-r from-blue-500/20 to-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                      : 'bg-gray-700/30 text-gray-500 border border-gray-600/30 hover:bg-gray-700/50'
                  }`}
                >
                  <span className="text-lg">🕯️</span>
                  <span>Exchange</span>
                </button>

                {/* Prediction Layer */}
                <button
                  onClick={() => setShowPredictionLayer(!showPredictionLayer)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    showPredictionLayer
                      ? 'bg-gradient-to-r from-purple-500/20 to-pink-600/20 text-purple-400 border border-purple-500/30 shadow-lg shadow-purple-500/10'
                      : 'bg-gray-700/30 text-gray-500 border border-gray-600/30 hover:bg-gray-700/50'
                  }`}
                >
                  <span className="text-lg">🔮</span>
                  <span>AI Prediction</span>
                </button>

                {/* Signal Markers */}
                <button
                  onClick={() => setShowSignalMarkers(!showSignalMarkers)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    showSignalMarkers
                      ? 'bg-gradient-to-r from-green-500/20 to-emerald-600/20 text-green-400 border border-green-500/30 shadow-lg shadow-green-500/10'
                      : 'bg-gray-700/30 text-gray-500 border border-gray-600/30 hover:bg-gray-700/50'
                  }`}
                >
                  <span className="text-lg">🎯</span>
                  <span>Signals</span>
                </button>
              </div>
            </div>

            {/* Zoom & Controls */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-gray-800/50 backdrop-blur-sm rounded-xl p-1 border border-gray-700/50">
                <button
                  onClick={() => setZoom(Math.max(50, zoom - 25))}
                  className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all duration-200"
                >
                  ➖
                </button>
                <span className="text-sm font-mono font-semibold text-gray-300 min-w-[50px] text-center">
                  {zoom}%
                </span>
                <button
                  onClick={() => setZoom(Math.min(300, zoom + 25))}
                  className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all duration-200"
                >
                  ➕
                </button>
              </div>

              <button
                onClick={() => setIsLive(!isLive)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  isLive
                    ? 'bg-gradient-to-r from-green-500/20 to-emerald-600/20 text-green-400 border border-green-500/30'
                    : 'bg-gray-700/30 text-gray-500 border border-gray-600/30 hover:bg-gray-700/50'
                }`}
              >
                {isLive ? '⏸️ Pause' : '▶️ Resume'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 📊 MAIN CHART AREA */}
      <div className="relative bg-gradient-to-br from-gray-900 to-black">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
              <span className="text-gray-400 font-medium">Loading market data...</span>
            </div>
          </div>
        ) : (
          <svg
            ref={chartRef}
            width={chartWidth}
            height={chartHeight}
            className="w-full h-auto"
            style={{ cursor: 'crosshair' }}
          >
            {/* Professional Gradient Backgrounds */}
            <defs>
              <linearGradient id="chartBg" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style={{stopColor: '#1f2937', stopOpacity: 0.8}} />
                <stop offset="100%" style={{stopColor: '#111827', stopOpacity: 0.9}} />
              </linearGradient>
              
              <linearGradient id="bullCandle" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style={{stopColor: '#10b981', stopOpacity: 0.9}} />
                <stop offset="100%" style={{stopColor: '#059669', stopOpacity: 1}} />
              </linearGradient>
              
              <linearGradient id="bearCandle" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style={{stopColor: '#ef4444', stopOpacity: 0.9}} />
                <stop offset="100%" style={{stopColor: '#dc2626', stopOpacity: 1}} />
              </linearGradient>

              <linearGradient id="predictionGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style={{stopColor: '#8b5cf6', stopOpacity: 0.6}} />
                <stop offset="100%" style={{stopColor: '#a855f7', stopOpacity: 0.3}} />
              </linearGradient>
            </defs>

            <rect width="100%" height="100%" fill="url(#chartBg)" />

            {/* Enhanced Grid */}
            <defs>
              <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 30" fill="none" stroke="#374151" strokeWidth="0.5" opacity="0.2"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />

            {/* Price Axis - Enhanced */}
            {Array.from({ length: 8 }, (_, i) => {
              const price = priceRange.min + (priceRange.max - priceRange.min) * i / 7
              const y = priceToY(price)
              return (
                <g key={i}>
                  <line 
                    x1={padding} y1={y} x2={chartWidth - padding} y2={y}
                    stroke="#4b5563" strokeWidth="0.5" strokeDasharray="2,4" opacity="0.6"
                  />
                  <rect x={chartWidth - padding + 2} y={y - 10} width="80" height="20" fill="#374151" rx="4" opacity="0.8" />
                  <text x={chartWidth - padding + 8} y={y + 3} fontSize="11" fill="#d1d5db" fontFamily="monospace">
                    {formatPrice(price)}
                  </text>
                </g>
              )
            })}

            {/* Time Axis */}
            {Array.from({ length: 6 }, (_, i) => {
              const timestamp = timeRange.min + (timeRange.max - timeRange.min) * i / 5
              const x = timestampToX(timestamp)
              const date = new Date(timestamp * 1000)
              return (
                <g key={i}>
                  <line 
                    x1={x} y1={padding} x2={x} y2={chartHeight - padding}
                    stroke="#4b5563" strokeWidth="0.5" strokeDasharray="2,4" opacity="0.4"
                  />
                  <text x={x} y={chartHeight - 20} textAnchor="middle" fontSize="10" fill="#9ca3af">
                    {date.toLocaleDateString('ru-RU', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </text>
                </g>
              )
            })}

            {/* LAYER 1: EXCHANGE CANDLESTICKS - ULTRA HD QUALITY */}
            {showExchangeLayer && candles.map((candle, i) => {
              const x = timestampToX(candle.timestamp)
              const openY = priceToY(candle.open)
              const closeY = priceToY(candle.close)
              const highY = priceToY(candle.high)
              const lowY = priceToY(candle.low)
              
              const isGreen = candle.close > candle.open
              const candleWidth = Math.max(2, (chartWidth - 2 * padding) / candles.length * 0.8)
              
              return (
                <g key={i} className="candle-group">
                  {/* Shadow for depth */}
                  <line 
                    x1={x + 1} y1={highY + 1} x2={x + 1} y2={lowY + 1}
                    stroke="#000000" strokeWidth="2" opacity="0.3"
                  />
                  <rect 
                    x={x - candleWidth/2 + 1} y={Math.min(openY, closeY) + 1}
                    width={candleWidth} height={Math.max(1, Math.abs(closeY - openY))}
                    fill="#000000" opacity="0.3" rx="1"
                  />
                  
                  {/* High-Low Wick */}
                  <line 
                    x1={x} y1={highY} x2={x} y2={lowY}
                    stroke={isGreen ? '#10b981' : '#ef4444'} 
                    strokeWidth="1.5" opacity="0.9"
                  />
                  
                  {/* Candle Body */}
                  <rect 
                    x={x - candleWidth/2} y={Math.min(openY, closeY)}
                    width={candleWidth} height={Math.max(1, Math.abs(closeY - openY))}
                    fill={isGreen ? 'url(#bullCandle)' : 'url(#bearCandle)'}
                    stroke={isGreen ? '#059669' : '#dc2626'}
                    strokeWidth="0.5" rx="1"
                    className="transition-all duration-200 hover:brightness-110"
                  />
                  
                  {/* Volume bars at bottom */}
                  <rect 
                    x={x - candleWidth/2} 
                    y={chartHeight - padding - (candle.volume / Math.max(...candles.map(c => c.volume))) * 40}
                    width={candleWidth}
                    height={(candle.volume / Math.max(...candles.map(c => c.volume))) * 40}
                    fill={isGreen ? '#10b981' : '#ef4444'}
                    opacity="0.4" rx="1"
                  />
                </g>
              )
            })}

            {/* LAYER 2: AI PREDICTION OVERLAY - SEMI-TRANSPARENT */}
            {showPredictionLayer && predictions.length > 0 && (
              <g className="prediction-layer" opacity="0.7">
                {/* Prediction path */}
                <path
                  d={`M ${predictions.map(p => `${timestampToX(p.timestamp)},${priceToY(p.predictedPrice)}`).join(' L ')}`}
                  fill="none"
                  stroke="url(#predictionGradient)"
                  strokeWidth="3"
                  strokeDasharray="8,4"
                  className="animate-pulse"
                />
                
                {/* Confidence bands */}
                {predictions.map((pred, i) => {
                  const x = timestampToX(pred.timestamp)
                  const y = priceToY(pred.predictedPrice)
                  const confidenceHeight = pred.confidence * 20
                  
                  return (
                    <ellipse
                      key={i}
                      cx={x} cy={y}
                      rx="4" ry={confidenceHeight}
                      fill="#8b5cf6" opacity={pred.confidence * 0.3}
                      className="animate-pulse"
                    />
                  )
                })}
              </g>
            )}

            {/* LAYER 3: SIGNAL MARKERS - PRECISELY POSITIONED */}
            {showSignalMarkers && signalData && (
              <g className="signal-markers">
                {/* Signal Entry Point - Precisely at signal time */}
                <g>
                  <line
                    x1={timestampToX(signalTimestamp)} y1={padding}
                    x2={timestampToX(signalTimestamp)} y2={chartHeight - padding}
                    stroke="#fbbf24" strokeWidth="3" strokeDasharray="10,5"
                    opacity="0.8" className="animate-pulse"
                  />
                  <text
                    x={timestampToX(signalTimestamp)} y={padding - 10}
                    textAnchor="middle" fontSize="12" fill="#fbbf24" fontWeight="bold"
                  >
                    📍 SIGNAL
                  </text>
                </g>

                {/* Entry Zone */}
                <rect
                  x={padding} y={priceToY(signalData.entry_max)}
                  width={chartWidth - 2 * padding} height={priceToY(signalData.entry_min) - priceToY(signalData.entry_max)}
                  fill="#3b82f6" opacity="0.2" rx="4"
                />
                <line
                  x1={padding} y1={priceToY(signalData.entry_min)} x2={chartWidth - padding} y2={priceToY(signalData.entry_min)}
                  stroke="#3b82f6" strokeWidth="2" strokeDasharray="12,6"
                />
                <line
                  x1={padding} y1={priceToY(signalData.entry_max)} x2={chartWidth - padding} y2={priceToY(signalData.entry_max)}
                  stroke="#3b82f6" strokeWidth="2" strokeDasharray="12,6"
                />

                {/* Take Profits */}
                {signalData.tp1 && (
                  <g>
                    <line
                      x1={padding} y1={priceToY(signalData.tp1)} x2={chartWidth - padding} y2={priceToY(signalData.tp1)}
                      stroke="#10b981" strokeWidth="2"
                    />
                    <circle cx={chartWidth - padding - 20} cy={priceToY(signalData.tp1)} r="6" fill="#10b981" />
                    <text x={chartWidth - padding - 40} y={priceToY(signalData.tp1) - 10} fontSize="10" fill="#10b981" fontWeight="bold">
                      🎯 TP1: {formatPrice(signalData.tp1)}
                    </text>
                  </g>
                )}
                
                {signalData.tp2 && (
                  <g>
                    <line
                      x1={padding} y1={priceToY(signalData.tp2)} x2={chartWidth - padding} y2={priceToY(signalData.tp2)}
                      stroke="#059669" strokeWidth="2"
                    />
                    <circle cx={chartWidth - padding - 20} cy={priceToY(signalData.tp2)} r="6" fill="#059669" />
                    <text x={chartWidth - padding - 40} y={priceToY(signalData.tp2) - 10} fontSize="10" fill="#059669" fontWeight="bold">
                      💎 TP2: {formatPrice(signalData.tp2)}
                    </text>
                  </g>
                )}

                {/* Stop Loss */}
                {signalData.sl && (
                  <g>
                    <line
                      x1={padding} y1={priceToY(signalData.sl)} x2={chartWidth - padding} y2={priceToY(signalData.sl)}
                      stroke="#ef4444" strokeWidth="2" strokeDasharray="8,4"
                    />
                    <circle cx={chartWidth - padding - 20} cy={priceToY(signalData.sl)} r="6" fill="#ef4444" />
                    <text x={chartWidth - padding - 40} y={priceToY(signalData.sl) - 10} fontSize="10" fill="#ef4444" fontWeight="bold">
                      🛑 SL: {formatPrice(signalData.sl)}
                    </text>
                  </g>
                )}
              </g>
            )}
          </svg>
        )}

        {/* Modern Stats Panel - Bottom */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent backdrop-blur-sm p-4">
          <div className="grid grid-cols-5 gap-4 text-center">
            <div className="bg-gray-800/30 rounded-xl p-3 backdrop-blur-sm border border-gray-700/30">
              <p className="text-xs text-gray-400 mb-1">TIMEFRAME</p>
              <p className="text-lg font-bold text-white">{selectedTimeframe.toUpperCase()}</p>
            </div>
            <div className="bg-gray-800/30 rounded-xl p-3 backdrop-blur-sm border border-gray-700/30">
              <p className="text-xs text-gray-400 mb-1">CANDLES</p>
              <p className="text-lg font-bold text-blue-400">{candles.length}</p>
            </div>
            <div className="bg-gray-800/30 rounded-xl p-3 backdrop-blur-sm border border-gray-700/30">
              <p className="text-xs text-gray-400 mb-1">PREDICTIONS</p>
              <p className="text-lg font-bold text-purple-400">{predictions.length}</p>
            </div>
            <div className="bg-gray-800/30 rounded-xl p-3 backdrop-blur-sm border border-gray-700/30">
              <p className="text-xs text-gray-400 mb-1">PRICE RANGE</p>
              <p className="text-sm font-bold text-yellow-400">{formatPrice(priceRange.min)}</p>
              <p className="text-sm font-bold text-yellow-400">{formatPrice(priceRange.max)}</p>
            </div>
            <div className="bg-gray-800/30 rounded-xl p-3 backdrop-blur-sm border border-gray-700/30">
              <p className="text-xs text-gray-400 mb-1">ZOOM</p>
              <p className="text-lg font-bold text-green-400">{zoom}%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
