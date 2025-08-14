'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface PriceData {
  symbol: string
  price: number
  change24h: number
  volume: number
  timestamp: number
}

interface CandleData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export default function RealtimeChart() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [priceData, setPriceData] = useState<PriceData | null>(null)
  const [candleData, setCandleData] = useState<CandleData[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']

  // WebSocket подключение
  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [selectedSymbol])

  const connectWebSocket = () => {
    try {
      // Используем Binance WebSocket для реальных данных
      const wsUrl = `wss://stream.binance.com:9443/ws/${selectedSymbol.toLowerCase()}@ticker`
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        setError(null)
        console.log(`WebSocket connected to ${selectedSymbol}`)
      }

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          const newPriceData: PriceData = {
            symbol: data.s,
            price: parseFloat(data.c),
            change24h: parseFloat(data.P),
            volume: parseFloat(data.v),
            timestamp: Date.now()
          }

          setPriceData(newPriceData)
          
          // Добавляем новую свечу каждые 5 секунд (упрощенно)
          const newCandle: CandleData = {
            timestamp: Date.now(),
            open: parseFloat(data.o),
            high: parseFloat(data.h),
            low: parseFloat(data.l),
            close: parseFloat(data.c),
            volume: parseFloat(data.v)
          }

          setCandleData(prev => {
            const updated = [...prev, newCandle]
            // Оставляем только последние 100 свечей
            return updated.slice(-100)
          })

        } catch (err) {
          console.error('Error parsing WebSocket data:', err)
        }
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected')
        
        // Переподключение через 3 секунды
        setTimeout(() => {
          if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
            connectWebSocket()
          }
        }, 3000)
      }

      wsRef.current.onerror = (error) => {
        setError('WebSocket connection failed')
        setIsConnected(false)
        console.error('WebSocket error:', error?.message || 'Unknown WebSocket error')
      }

    } catch (err) {
      setError('Failed to establish WebSocket connection')
      console.error('WebSocket setup error:', err)
    }
  }

  // Рисование графика на canvas
  useEffect(() => {
    if (candleData.length > 0 && canvasRef.current) {
      drawChart()
    }
  }, [candleData])

  const drawChart = () => {
    const canvas = canvasRef.current
    if (!canvas || candleData.length === 0) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Настройка canvas
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    const width = rect.width
    const height = rect.height
    const padding = 40

    // Очистка canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'
    ctx.fillRect(0, 0, width, height)

    if (candleData.length < 2) return

    // Вычисление диапазона цен
    const prices = candleData.flatMap(candle => [candle.high, candle.low])
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)
    const priceRange = maxPrice - minPrice

    // Функции для преобразования координат
    const xScale = (index: number) => padding + (index / (candleData.length - 1)) * (width - 2 * padding)
    const yScale = (price: number) => height - padding - ((price - minPrice) / priceRange) * (height - 2 * padding)

    // Рисование сетки
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
    ctx.lineWidth = 1

    // Горизонтальные линии
    for (let i = 0; i <= 5; i++) {
      const y = padding + (i / 5) * (height - 2 * padding)
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(width - padding, y)
      ctx.stroke()
    }

    // Вертикальные линии
    for (let i = 0; i <= 10; i++) {
      const x = padding + (i / 10) * (width - 2 * padding)
      ctx.beginPath()
      ctx.moveTo(x, padding)
      ctx.lineTo(x, height - padding)
      ctx.stroke()
    }

    // Рисование линии цены
    ctx.strokeStyle = '#667eea'
    ctx.lineWidth = 2
    ctx.beginPath()

    candleData.forEach((candle, index) => {
      const x = xScale(index)
      const y = yScale(candle.close)
      
      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })

    ctx.stroke()

    // Рисование свечей (упрощенно - только линии)
    candleData.forEach((candle, index) => {
      const x = xScale(index)
      const yHigh = yScale(candle.high)
      const yLow = yScale(candle.low)
      const yOpen = yScale(candle.open)
      const yClose = yScale(candle.close)

      // Цвет свечи
      const isGreen = candle.close > candle.open
      ctx.strokeStyle = isGreen ? '#10b981' : '#ef4444'
      ctx.lineWidth = 1

      // Тень свечи
      ctx.beginPath()
      ctx.moveTo(x, yHigh)
      ctx.lineTo(x, yLow)
      ctx.stroke()

      // Тело свечи
      const bodyTop = Math.min(yOpen, yClose)
      const bodyBottom = Math.max(yOpen, yClose)
      const candleWidth = Math.max(2, (width - 2 * padding) / candleData.length * 0.8)

      ctx.fillStyle = isGreen ? '#10b981' : '#ef4444'
      ctx.fillRect(x - candleWidth/2, bodyTop, candleWidth, bodyBottom - bodyTop)
    })

    // Подписи осей
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
    ctx.font = '12px Arial'
    ctx.textAlign = 'right'

    // Цены на оси Y
    for (let i = 0; i <= 5; i++) {
      const price = minPrice + (priceRange * i / 5)
      const y = height - padding - (i / 5) * (height - 2 * padding)
      ctx.fillText(price.toFixed(2), padding - 5, y + 4)
    }

    // Текущая цена
    if (priceData) {
      const currentY = yScale(priceData.price)
      ctx.strokeStyle = '#fbbf24'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      ctx.moveTo(padding, currentY)
      ctx.lineTo(width - padding, currentY)
      ctx.stroke()
      ctx.setLineDash([])

      // Подпись текущей цены
      ctx.fillStyle = '#fbbf24'
      ctx.textAlign = 'left'
      ctx.fillText(`$${priceData.price.toFixed(2)}`, width - padding + 5, currentY + 4)
    }
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(price)
  }

  const formatPercentage = (percentage: number) => {
    const sign = percentage >= 0 ? '+' : ''
    return `${sign}${percentage.toFixed(2)}%`
  }

  return (
    <Card className="glass border-white/10">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-4">
            <CardTitle className="text-white flex items-center space-x-2">
              <span>📈 Real-time Chart</span>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            </CardTitle>
            {error && (
              <span className="text-red-400 text-sm">⚠️ {error}</span>
            )}
          </div>
          
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {symbols.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
        </div>

        {priceData && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="text-center">
              <p className="text-gray-400 text-sm">Price</p>
              <p className="text-white font-bold text-lg">{formatPrice(priceData.price)}</p>
            </div>
            <div className="text-center">
              <p className="text-gray-400 text-sm">24h Change</p>
              <p className={`font-bold text-lg ${priceData.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {formatPercentage(priceData.change24h)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-gray-400 text-sm">Volume</p>
              <p className="text-white font-bold text-lg">{(priceData.volume / 1000000).toFixed(1)}M</p>
            </div>
            <div className="text-center">
              <p className="text-gray-400 text-sm">Status</p>
              <p className={`font-bold text-lg ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                {isConnected ? 'LIVE' : 'OFFLINE'}
              </p>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent>
        <div className="relative">
          <canvas
            ref={canvasRef}
            className="w-full h-80 bg-gray-900/20 rounded-lg"
            style={{ width: '100%', height: '320px' }}
          />
          
          {candleData.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-400">Loading chart data...</p>
              </div>
            </div>
          )}
        </div>

        {/* Chart Controls */}
        <div className="flex justify-center space-x-2 mt-4">
          {['1m', '5m', '15m', '1h', '4h', '1d'].map((timeframe) => (
            <button
              key={timeframe}
              className="px-3 py-1 text-sm bg-gray-800 text-gray-400 rounded hover:bg-gray-700 hover:text-white transition-colors"
            >
              {timeframe}
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
