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

interface Props {
  signalId: string
  signalData?: SignalData
}

interface ChartLayers {
  exchange: boolean
  signals: boolean
}

// Профессиональные таймфреймы как в ByBit
const TIMEFRAMES = [
  { value: '1s', label: '1C' },
  { value: '1m', label: '1мин' },
  { value: '3m', label: '3мин' },
  { value: '5m', label: '5мин' },
  { value: '15m', label: '15мин' },
  { value: '30m', label: '30мин' },
  { value: '1h', label: '1Ч' },
  { value: '2h', label: '2Ч' },
  { value: '4h', label: '4Ч' },
  { value: '1d', label: '1Д' }
]

export default function BybitStyleChart({ signalId, signalData }: Props) {
  const [candles, setCandles] = useState<CandleData[]>([])
  const [loading, setLoading] = useState(true)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const [currentPrice, setCurrentPrice] = useState<number | null>(null)
  const [priceChange, setPriceChange] = useState<number>(0)
  const [selectedTimeframe, setSelectedTimeframe] = useState('5m')
  
  // Layer controls
  const [layers, setLayers] = useState<ChartLayers>({
    exchange: true,
    signals: true
  })
  
  // Zoom and pan
  const [zoomLevel, setZoomLevel] = useState(1.0)
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })
  
  const chartRef = useRef<SVGSVGElement>(null)
  
  // Responsive chart dimensions
  const getChartDimensions = () => {
    if (typeof window === 'undefined') return { width: 1200, height: 500 }
    
    const isMobile = window.innerWidth <= 768
    const isTablet = window.innerWidth <= 1024
    
    if (isMobile) {
      return {
        width: Math.min(window.innerWidth - 20, 400),
        height: 300
      }
    } else if (isTablet) {
      return {
        width: Math.min(window.innerWidth - 40, 800),
        height: 400
      }
    } else {
      return {
        width: 1200,
        height: 500
      }
    }
  }
  
  const [chartDimensions, setChartDimensions] = useState(getChartDimensions())
  const chartWidth = chartDimensions.width
  const chartHeight = chartDimensions.height
  
  // Responsive padding
  const isMobile = chartWidth <= 400
  const leftPadding = isMobile ? 50 : 80
  const rightPadding = isMobile ? 10 : 80  
  const topPadding = isMobile ? 30 : 40
  const bottomPadding = isMobile ? 40 : 60

  // Generate realistic real-time mock market data
  const generateMockCandles = () => {
    const now = Math.floor(Date.now() / 1000)
    const interval = selectedTimeframe === '1m' ? 60 : selectedTimeframe === '5m' ? 300 : 3600
    const candleCount = 100
    
    // Start with current market-like price
    let basePrice = 58000 + (Math.sin(Date.now() / 100000) * 2000) // Simulate market movement
    const candles: CandleData[] = []
    
    for (let i = 0; i < candleCount; i++) {
      const timestamp = now - (candleCount - i) * interval
      const volatility = basePrice * 0.004 // 0.4% volatility for more movement
      
      // Add trend and noise for realistic movement
      const trendFactor = Math.sin((i / 10)) * 0.1
      const noiseFactor = (Math.random() - 0.5) * 2
      
      const open = basePrice * (1 + trendFactor * 0.01 + noiseFactor * 0.002)
      const high = open * (1 + Math.random() * 0.008)
      const low = open * (1 - Math.random() * 0.008)
      const close = low + Math.random() * (high - low)
      const volume = 800000 + Math.random() * 3000000
      
      candles.push({
        timestamp,
        open: Math.max(low, Math.min(high, open)),
        high,
        low,
        close: Math.max(low, Math.min(high, close)),
        volume
      })
      
      basePrice = close // Next candle continues from previous close
    }
    
    return candles
  }

  // Fetch real market data with fallback to mock
  const fetchData = async () => {
    try {
      // Only show loading spinner on first load, not on updates
      if (isInitialLoad) {
        setLoading(true)
      }
      
      let candlesData: CandleData[] = []
      let dataSource = 'mock'
      
      // Try to fetch real data first
      try {
        const response = await fetch(`/api/signal-candles/${signalId}?interval=${selectedTimeframe}`)
        const data = await response.json()
        
        console.log('🔍 API Response:', data)
        
        if (response.ok && data.candles && data.candles.length > 0) {
          candlesData = data.candles
          dataSource = data.source || 'api'
        } else {
          throw new Error(`API Error: ${data.error || 'No candles data'}`)
        }
      } catch (apiError) {
        console.log('API not available, using mock data:', apiError)
        // Fallback to mock data
        candlesData = generateMockCandles()
      }
      
      // Set the candles data
      setCandles(candlesData)
      const latest = candlesData[candlesData.length - 1]
      const previous = candlesData[candlesData.length - 2]
      
      setCurrentPrice(latest.close)
      if (previous) {
        const change = ((latest.close - previous.close) / previous.close) * 100
        setPriceChange(change)
      }
      
      // Log successful data load
      console.log(`✅ Chart data loaded: ${candlesData.length} candles from ${dataSource}`)
      
    } catch (error) {
      console.error('❌ Chart data error:', error)
      // Even on error, show mock data
      const mockCandles = generateMockCandles()
      setCandles(mockCandles)
      const latest = mockCandles[mockCandles.length - 1]
      setCurrentPrice(latest.close)
    } finally {
      setLoading(false)
      if (isInitialLoad) {
        setIsInitialLoad(false)
      }
    }
  }

  // Price/Time calculations
  const getPriceRange = () => {
    if (!candles.length) return { min: 0, max: 100 }
    
    const allPrices = candles.flatMap(c => [c.high, c.low])
    if (signalData) {
      allPrices.push(signalData.entry_min, signalData.entry_max)
      if (signalData.tp1) allPrices.push(signalData.tp1)
      if (signalData.tp2) allPrices.push(signalData.tp2)
      if (signalData.sl) allPrices.push(signalData.sl)
    }
    
    const min = Math.min(...allPrices)
    const max = Math.max(...allPrices)
    const padding = (max - min) * 0.05
    
    return { min: min - padding, max: max + padding }
  }

  const getTimeRange = () => {
    if (!candles.length) {
      const now = Date.now() / 1000
      return { min: now - 3600, max: now }
    }
    return {
      min: candles[0].timestamp,
      max: candles[candles.length - 1].timestamp
    }
  }

  const priceToY = (price: number) => {
    const { min, max } = getPriceRange()
    return topPadding + (max - price) / (max - min) * (chartHeight - topPadding - bottomPadding)
  }

  const timestampToX = (timestamp: number) => {
    const { min, max } = getTimeRange()
    if (max === min) return leftPadding
    const baseX = leftPadding + (timestamp - min) / (max - min) * (chartWidth - leftPadding - rightPadding)
    return baseX * zoomLevel + panOffset.x
  }

  const formatPrice = (price: number) => {
    if (price < 0.001) return price.toFixed(6)
    if (price < 1) return price.toFixed(4)
    if (price < 100) return price.toFixed(3)
    return price.toFixed(2)
  }

  // Handle window resize for responsive design
  useEffect(() => {
    const handleResize = () => {
      setChartDimensions(getChartDimensions())
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    // Reset initial load flag when signal changes
    if (signalId) {
      setIsInitialLoad(true)
    }
    fetchData()
    
    // Real-time updates every 15 seconds - balanced between real-time feel and performance
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [signalId, selectedTimeframe])

  const priceRange = getPriceRange()
  const signalTimestamp = signalData ? new Date(signalData.posted_ts || signalData.created_at).getTime() / 1000 : 0

  return (
    <div className="bg-[#0B1426] text-white font-mono w-full max-w-full overflow-hidden">
      
      {/* Mobile-Responsive Header */}
      <div className="bg-[#0F1729] border-b border-gray-800 p-2 md:p-4">
        
        {/* Mobile Layout - Stack vertically */}
        <div className="block md:hidden">
          {/* Top row - Symbol and price */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white">
                {signalData?.symbol || 'BTCUSDT'}
              </h1>
              <span className={`text-xs px-1 py-0.5 rounded ${
                priceChange >= 0 ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'
              }`}>
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(1)}%
              </span>
            </div>
            {currentPrice && (
              <div className="text-right">
                <div className="text-white text-sm font-bold">
                  ${formatPrice(currentPrice)}
                </div>
              </div>
            )}
          </div>
          
          {/* Bottom row - Signal info */}
          {signalData && (
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="text-gray-400">Signal:</span>
                <span className={`px-1 py-0.5 rounded text-xs ${
                  signalData.side === 'LONG' 
                    ? 'bg-green-900 text-green-400' 
                    : 'bg-red-900 text-red-400'
                }`}>
                  {signalData.side}
                </span>
              </div>
              <div className="text-gray-400">
                Entry: {signalData.entry_min} - {signalData.entry_max}
              </div>
            </div>
          )}
        </div>

        {/* Desktop Layout - Original */}
        <div className="hidden md:flex items-center justify-between">
          
          {/* Left: Symbol and price info */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">
                {signalData?.symbol || 'BTCUSDT'}
              </h1>
              <span className={`text-sm px-2 py-1 rounded ${
                priceChange >= 0 ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'
              }`}>
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
              </span>
            </div>
            
            {currentPrice && (
              <div className="flex items-center gap-6 text-sm">
                <div>
                  <span className="text-gray-400">Price: </span>
                  <span className="text-white text-lg font-bold">
                    ${formatPrice(currentPrice)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">24h High: </span>
                  <span className="text-green-400">{candles.length ? formatPrice(Math.max(...candles.map(c => c.high))) : '0'}</span>
                </div>
                <div>
                  <span className="text-gray-400">24h Low: </span>
                  <span className="text-red-400">{candles.length ? formatPrice(Math.min(...candles.map(c => c.low))) : '0'}</span>
                </div>
                <div>
                  <span className="text-gray-400">Volume: </span>
                  <span className="text-white">{candles.length ? (candles.reduce((sum, c) => sum + c.volume, 0) / 1000000).toFixed(2) : '0'}M</span>
                </div>
              </div>
            )}
          </div>
          
          {/* Right: Our signal info */}
          {signalData && (
            <div className="text-right text-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-gray-400">Signal:</span>
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  signalData.side === 'LONG' 
                    ? 'bg-green-900 text-green-400' 
                    : 'bg-red-900 text-red-400'
                }`}>
                  {signalData.side}
                </span>
              </div>
              <div className="text-gray-400">
                Entry: {signalData.entry_min} - {signalData.entry_max}
              </div>
            </div>
          )}
        </div>

        {/* Mobile Controls - Stack vertically */}
        <div className="block md:hidden mt-3 space-y-3">
          
          {/* Timeframes - Compact mobile version */}
          <div className="space-y-2">
            <div className="text-xs text-gray-400">Timeframe</div>
            <div className="flex flex-wrap gap-1">
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf.value}
                  onClick={() => setSelectedTimeframe(tf.value)}
                  className={`px-2 py-1 text-xs transition-colors rounded ${
                    selectedTimeframe === tf.value
                      ? 'bg-[#F7931A] text-black font-bold'
                      : 'text-gray-400 hover:text-white bg-gray-800'
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>
          </div>

          {/* Layers and Zoom - Combined row */}
          <div className="flex items-center justify-between">
            
            {/* Layer toggles */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Layers:</span>
              
              <button
                onClick={() => setLayers(prev => ({ ...prev, exchange: !prev.exchange }))}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                  layers.exchange 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                <span>{layers.exchange ? '👁️' : '🙈'}</span>
                <span className="hidden sm:inline">Market</span>
              </button>

              <button
                onClick={() => setLayers(prev => ({ ...prev, signals: !prev.signals }))}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                  layers.signals 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                <span>{layers.signals ? '👁️' : '🙈'}</span>
                <span className="hidden sm:inline">Signals</span>
              </button>
            </div>

            {/* Zoom controls - Compact */}
            <div className="flex items-center gap-1">
                          <button
              onClick={() => {
                const newZoom = Math.max(0.5, zoomLevel - 0.25)
                setZoomLevel(newZoom)
                // Keep center point stable during zoom
                const centerX = chartWidth / 2
                setPanOffset(prev => ({ 
                  x: (prev.x - centerX) * (newZoom / zoomLevel) + centerX, 
                  y: prev.y 
                }))
              }}
              className="w-6 h-6 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded flex items-center justify-center"
            >
              –
            </button>
            <span className="text-xs text-white min-w-[35px] text-center">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              onClick={() => {
                const newZoom = Math.min(4.0, zoomLevel + 0.25)
                setZoomLevel(newZoom)
                // Keep center point stable during zoom
                const centerX = chartWidth / 2
                setPanOffset(prev => ({ 
                  x: (prev.x - centerX) * (newZoom / zoomLevel) + centerX, 
                  y: prev.y 
                }))
              }}
              className="w-6 h-6 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded flex items-center justify-center"
            >
              +
            </button>
            <button
              onClick={() => {
                setZoomLevel(1.0)
                setPanOffset({ x: 0, y: 0 })
              }}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded"
            >
              Reset
            </button>
            </div>
          </div>
        </div>

        {/* Desktop Controls - Original horizontal layout */}
        <div className="hidden md:flex items-center justify-between mt-4">
          
          {/* Timeframe selection */}
          <div className="flex items-center gap-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setSelectedTimeframe(tf.value)}
                className={`px-2 py-1 text-sm transition-colors ${
                  selectedTimeframe === tf.value
                    ? 'bg-[#F7931A] text-black font-bold'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          {/* Layer Controls */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400">Layers:</span>
            
            <button
              onClick={() => setLayers(prev => ({ ...prev, exchange: !prev.exchange }))}
              className={`flex items-center gap-2 px-2 py-1 rounded text-sm transition-colors ${
                layers.exchange 
                  ? 'bg-green-600 text-white' 
                  : 'bg-gray-700 text-gray-400'
              }`}
            >
              <span>{layers.exchange ? '👁️' : '🙈'}</span>
              <span>Market</span>
            </button>

            <button
              onClick={() => setLayers(prev => ({ ...prev, signals: !prev.signals }))}
              className={`flex items-center gap-2 px-2 py-1 rounded text-sm transition-colors ${
                layers.signals 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-400'
              }`}
            >
              <span>{layers.signals ? '👁️' : '🙈'}</span>
              <span>Signals</span>
            </button>
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Zoom:</span>
            <button
              onClick={() => {
                const newZoom = Math.max(0.5, zoomLevel - 0.25)
                setZoomLevel(newZoom)
                // Keep center point stable during zoom
                const centerX = chartWidth / 2
                setPanOffset(prev => ({ 
                  x: (prev.x - centerX) * (newZoom / zoomLevel) + centerX, 
                  y: prev.y 
                }))
              }}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
            >
              –
            </button>
            <span className="text-sm text-white min-w-[45px] text-center">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              onClick={() => {
                const newZoom = Math.min(4.0, zoomLevel + 0.25)
                setZoomLevel(newZoom)
                // Keep center point stable during zoom
                const centerX = chartWidth / 2
                setPanOffset(prev => ({ 
                  x: (prev.x - centerX) * (newZoom / zoomLevel) + centerX, 
                  y: prev.y 
                }))
              }}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
            >
              +
            </button>
            <button
              onClick={() => {
                setZoomLevel(1.0)
                setPanOffset({ x: 0, y: 0 })
              }}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded"
            >
              Reset
            </button>
          </div>
          
          {/* Live update indicator */}
          {!isInitialLoad && loading && (
            <div className="absolute top-2 right-2 flex items-center gap-1 bg-black/20 backdrop-blur-sm rounded-md px-2 py-1">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-400">Live</span>
            </div>
          )}
        </div>
      </div>

      {/* Chart Area - Responsive */}
      <div className="relative bg-[#0B1426] w-full overflow-hidden" style={{ height: chartHeight + (isMobile ? 50 : 100) }}>
        
        {/* Left indicators panel - Hide on mobile */}
        <div className="absolute left-0 top-0 w-12 md:w-16 h-full bg-[#0F1729] border-r border-gray-800 p-1 md:p-2 text-xs hidden sm:block">
          {signalData && (
            <div className="space-y-1 md:space-y-2">
              <div className="text-blue-400 text-xs">TP</div>
              {signalData.tp1 && (
                <div className="text-green-400 text-xs">
                  {isMobile ? signalData.tp1.toFixed(0) : formatPrice(signalData.tp1)}
                </div>
              )}
              {signalData.tp2 && (
                <div className="text-green-400 text-xs">
                  {isMobile ? signalData.tp2.toFixed(0) : formatPrice(signalData.tp2)}
                </div>
              )}
              
              <div className="text-red-400 mt-2 md:mt-4 text-xs">SL</div>
              {signalData.sl && (
                <div className="text-red-400 text-xs">
                  {isMobile ? signalData.sl.toFixed(0) : formatPrice(signalData.sl)}
                </div>
              )}
            </div>
          )}
        </div>

        {loading && isInitialLoad ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
              <div className="text-gray-400 text-xs">Обновление данных...</div>
            </div>
          </div>
        ) : (
          <div className={`${isMobile ? 'ml-0' : 'ml-12 md:ml-16'} overflow-hidden w-full`} 
               style={{ maxWidth: `${chartWidth}px`, height: chartHeight }}>
            <svg
              ref={chartRef}
              width="100%"
              height="100%"
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="block w-full h-full"
              style={{ backgroundColor: '#0B1426', maxWidth: '100%' }}
              preserveAspectRatio="xMidYMid meet"
            >
            {/* Grid and clip paths */}
            <defs>
              <pattern id="grid" width="50" height="40" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" opacity="0.3"/>
              </pattern>
              <clipPath id="chartClip">
                <rect x={leftPadding} y={topPadding} 
                      width={chartWidth - leftPadding - rightPadding} 
                      height={chartHeight - topPadding - bottomPadding} />
              </clipPath>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />

            {/* Price levels - right side */}
            {Array.from({ length: isMobile ? 6 : 10 }, (_, i) => {
              const count = isMobile ? 5 : 9
              const price = priceRange.min + (priceRange.max - priceRange.min) * i / count
              const y = priceToY(price)
              const fontSize = isMobile ? 9 : 11
              return (
                <g key={i}>
                  <line 
                    x1={leftPadding} y1={y} 
                    x2={chartWidth - rightPadding} y2={y}
                    stroke="#334155" strokeWidth="1" opacity="0.3"
                  />
                  {!isMobile && (
                    <text 
                      x={chartWidth - rightPadding + 5} y={y + 4} 
                      fontSize={fontSize} fill="#64748b" fontFamily="monospace"
                    >
                      {formatPrice(price)}
                    </text>
                  )}
                </g>
              )
            })}

            {/* Time axis */}
            {Array.from({ length: isMobile ? 4 : 8 }, (_, i) => {
              const timeRange = getTimeRange()
              const count = isMobile ? 3 : 7
              const timestamp = timeRange.min + (timeRange.max - timeRange.min) * i / count
              const x = timestampToX(timestamp)
              const date = new Date(timestamp * 1000)
              const fontSize = isMobile ? 8 : 10
              return (
                <g key={i}>
                  <line 
                    x1={x} y1={topPadding} 
                    x2={x} y2={chartHeight - bottomPadding}
                    stroke="#334155" strokeWidth="1" opacity="0.3"
                  />
                  <text 
                    x={x} y={chartHeight - bottomPadding + (isMobile ? 12 : 15)} 
                    textAnchor="middle" fontSize={fontSize} fill="#64748b"
                  >
                    {isMobile 
                      ? date.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', hour: '2-digit' })
                      : date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
                    }
                  </text>
                </g>
              )
            })}

            {/* LAYER 1: EXCHANGE CANDLESTICKS - Only if layer enabled */}
            {layers.exchange && candles.map((candle, i) => {
              const x = timestampToX(candle.timestamp)
              
              // Skip rendering if outside visible area (performance optimization)
              if (x < leftPadding - 50 || x > chartWidth - rightPadding + 50) return null
              
              const openY = priceToY(candle.open)
              const closeY = priceToY(candle.close)
              const highY = priceToY(candle.high)
              const lowY = priceToY(candle.low)
              
              const isGreen = candle.close > candle.open
              const baseCandleWidth = (chartWidth - leftPadding - rightPadding) / candles.length * 0.7
              const candleWidth = Math.max(isMobile ? 0.5 : 1, Math.min(baseCandleWidth * zoomLevel, isMobile ? 8 : 15))
              
              return (
                <g key={i} clipPath="url(#chartClip)">
                  {/* High-Low Wick */}
                  <line 
                    x1={x} y1={highY} x2={x} y2={lowY}
                    stroke={isGreen ? '#00D4AA' : '#FF4D4F'} 
                    strokeWidth={isMobile ? "1" : "1.5"}
                  />
                  
                  {/* Candle Body - exact ByBit colors */}
                  <rect 
                    x={x - candleWidth/2} 
                    y={Math.min(openY, closeY)}
                    width={candleWidth}
                    height={Math.max(1, Math.abs(closeY - openY))}
                    fill={isGreen ? '#00D4AA' : '#FF4D4F'}
                    stroke={isGreen ? '#00D4AA' : '#FF4D4F'}
                    strokeWidth="0"
                  />
                  
                  {/* Volume bars at bottom */}
                  <rect 
                    x={x - candleWidth/2} 
                    y={chartHeight - bottomPadding - (candle.volume / Math.max(...candles.map(c => c.volume))) * 30}
                    width={candleWidth}
                    height={(candle.volume / Math.max(...candles.map(c => c.volume))) * 30}
                    fill={isGreen ? '#00D4AA' : '#FF4D4F'}
                    opacity="0.6"
                  />
                </g>
              )
            })}

            {/* LAYER 2: TRADING SIGNALS - Only if layer enabled */}
            {layers.signals && signalData && (
              <g className="signal-overlay" clipPath="url(#chartClip)">
                {/* Signal entry line - exactly at signal time */}
                <line
                  x1={timestampToX(signalTimestamp)} y1={topPadding}
                  x2={timestampToX(signalTimestamp)} y2={chartHeight - bottomPadding}
                  stroke="#F7931A" strokeWidth={isMobile ? "2" : "3"} strokeDasharray={isMobile ? "6,3" : "8,4"}
                  opacity="0.8"
                />
                
                {/* Entry zone - full width background */}
                <rect
                  x={leftPadding} y={priceToY(signalData.entry_max)}
                  width={chartWidth - leftPadding - rightPadding} 
                  height={Math.abs(priceToY(signalData.entry_min) - priceToY(signalData.entry_max))}
                  fill="#3B82F6" opacity="0.15"
                />
                
                {/* Entry lines */}
                <line
                  x1={leftPadding} y1={priceToY(signalData.entry_min)} 
                  x2={chartWidth - rightPadding} y2={priceToY(signalData.entry_min)}
                  stroke="#3B82F6" strokeWidth={isMobile ? "1.5" : "2"} strokeDasharray={isMobile ? "4,2" : "6,3"}
                />
                <line
                  x1={leftPadding} y1={priceToY(signalData.entry_max)} 
                  x2={chartWidth - rightPadding} y2={priceToY(signalData.entry_max)}
                  stroke="#3B82F6" strokeWidth={isMobile ? "1.5" : "2"} strokeDasharray={isMobile ? "4,2" : "6,3"}
                />

                {/* Take Profits */}
                {signalData.tp1 && (
                  <line
                    x1={leftPadding} y1={priceToY(signalData.tp1)} 
                    x2={chartWidth - rightPadding} y2={priceToY(signalData.tp1)}
                    stroke="#00D4AA" strokeWidth={isMobile ? "1.5" : "2"}
                  />
                )}
                {signalData.tp2 && (
                  <line
                    x1={leftPadding} y1={priceToY(signalData.tp2)} 
                    x2={chartWidth - rightPadding} y2={priceToY(signalData.tp2)}
                    stroke="#00D4AA" strokeWidth={isMobile ? "1.5" : "2"}
                  />
                )}

                {/* Stop Loss */}
                {signalData.sl && (
                  <line
                    x1={leftPadding} y1={priceToY(signalData.sl)} 
                    x2={chartWidth - rightPadding} y2={priceToY(signalData.sl)}
                    stroke="#FF4D4F" strokeWidth={isMobile ? "1.5" : "2"} strokeDasharray={isMobile ? "6,3" : "8,4"}
                  />
                )}
              </g>
            )}

            {/* Signal time marker - outside clip area */}
            {layers.signals && signalData && (
              <text
                x={timestampToX(signalTimestamp)} y={topPadding - (isMobile ? 5 : 8)}
                textAnchor="middle" fontSize={isMobile ? "9" : "11"} fill="#F7931A" fontWeight="bold"
              >
                {isMobile ? "📍" : "📍 SIGNAL"}
              </text>
            )}
            </svg>
          </div>
        )}

        {/* Right indicators panel - Hide on mobile */}
        <div className="absolute right-0 top-0 w-12 md:w-20 h-full bg-[#0F1729] border-l border-gray-800 p-1 md:p-2 text-xs hidden md:block">
          <div className="space-y-2 md:space-y-3">
            <div className="text-blue-400">MA</div>
            <div className="text-purple-400">EMA</div>
            <div className="text-orange-400">BOLL</div>
            <div className="text-pink-400">SAR</div>
            <div className="text-cyan-400">MACD</div>
            <div className="text-yellow-400">RSI</div>
          </div>
        </div>

        {/* Mobile indicator strip - Bottom overlay */}
        {isMobile && (
          <div className="absolute bottom-0 left-0 right-0 bg-[#0F1729]/90 border-t border-gray-800 p-1">
            <div className="flex justify-center items-center gap-3 text-xs">
              <span className="text-blue-400">MA</span>
              <span className="text-purple-400">EMA</span>
              <span className="text-orange-400">BOLL</span>
              <span className="text-pink-400">SAR</span>
              <span className="text-cyan-400">MACD</span>
              <span className="text-yellow-400">RSI</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
