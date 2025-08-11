'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceDot,
  Area,
  AreaChart
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Newspaper,
  Signal,
  Activity,
  DollarSign,
  BarChart3,
  Eye,
  Clock,
  Zap
} from 'lucide-react'

interface PricePoint {
  timestamp: string
  price: number
  volume: number
  ma20: number
  ma50: number
  rsi: number
  signal?: 'BUY' | 'SELL'
  signalStrength?: number
}

interface NewsEvent {
  id: string
  timestamp: string
  title: string
  impact: 'HIGH' | 'MEDIUM' | 'LOW'
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  price_impact: number
  keywords: string[]
  source: string
}

interface TradingSignal {
  id: string
  timestamp: string
  symbol: string
  direction: 'LONG' | 'SHORT'
  entry_price: number
  confidence: number
  trader: string
  status: 'ACTIVE' | 'FILLED' | 'CANCELLED'
}

export default function MarketAnalysisChart() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [timeframe, setTimeframe] = useState('1H')
  const [priceData, setPriceData] = useState<PricePoint[]>([])
  const [newsEvents, setNewsEvents] = useState<NewsEvent[]>([])
  const [tradingSignals, setTradingSignals] = useState<TradingSignal[]>([])
  const [selectedNews, setSelectedNews] = useState<NewsEvent | null>(null)
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Получение данных из API
  const fetchMarketData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/market-data?symbol=${selectedSymbol}&timeframe=${timeframe}&limit=100`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Преобразование данных API в формат компонента
      const transformedPriceData: PricePoint[] = data.price_data.map((point: any) => ({
        timestamp: point.timestamp,
        price: point.close,
        volume: point.volume,
        ma20: point.ma20 || 0,
        ma50: point.ma50 || 0,
        rsi: point.rsi || 50,
        signal: undefined,
        signalStrength: 0
      }))
      
      setPriceData(transformedPriceData)
      setNewsEvents(data.news_events || [])
      setTradingSignals(data.trading_signals || [])
      setLoading(false)
      
    } catch (error) {
      console.error('Failed to fetch market data:', error)
      setLoading(false)
      // Fallback to demo data if API fails
      generateFallbackData()
    }
  }

  // Fallback демо данные если API недоступен
  const generateFallbackData = () => {
    const now = new Date()
    const data: PricePoint[] = []
    
    let basePrice = selectedSymbol === 'BTCUSDT' ? 43000 : 
                   selectedSymbol === 'ETHUSDT' ? 2500 :
                   selectedSymbol === 'STGUSDT' ? 0.45 :
                   selectedSymbol === 'ZROUSDT' ? 4.2 : 100
    
    for (let i = 100; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60000).toISOString()
      
      const volatility = Math.random() * 0.02 - 0.01
      basePrice *= (1 + volatility)
      
      const volume = Math.random() * 1000000 + 500000
      const ma20 = basePrice * (1 + (Math.random() * 0.01 - 0.005))
      const ma50 = basePrice * (1 + (Math.random() * 0.02 - 0.01))
      const rsi = Math.random() * 40 + 30
      
      data.push({
        timestamp,
        price: basePrice,
        volume,
        ma20,
        ma50,
        rsi
      })
    }
    
    setPriceData(data)
    setNewsEvents([])
    setTradingSignals([])
    setLoading(false)
  }

  useEffect(() => {
    fetchMarketData()
  }, [selectedSymbol, timeframe])

  useEffect(() => {
    if (!autoRefresh) return
    
    const interval = setInterval(() => {
      fetchMarketData()
    }, 30000) // Обновление каждые 30 секунд
    
    return () => clearInterval(interval)
  }, [autoRefresh, selectedSymbol, timeframe])

  const currentPrice = priceData[priceData.length - 1]?.price || 0
  const priceChange = priceData.length > 1 
    ? ((currentPrice - priceData[priceData.length - 2].price) / priceData[priceData.length - 2].price) * 100
    : 0

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'HIGH': return 'text-red-400 bg-red-500/20'
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-500/20'
      case 'LOW': return 'text-green-400 bg-green-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'POSITIVE': return <TrendingUp className="h-4 w-4 text-green-400" />
      case 'NEGATIVE': return <TrendingDown className="h-4 w-4 text-red-400" />
      default: return <Activity className="h-4 w-4 text-gray-400" />
    }
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      const relatedNews = newsEvents.filter(news => 
        Math.abs(new Date(news.timestamp).getTime() - new Date(label).getTime()) < 300000 // 5 минут
      )
      
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 shadow-xl">
          <p className="text-white font-semibold">{formatTime(label)}</p>
          <p className="text-green-400">
            Price: {formatPrice(data.price)}
          </p>
          <p className="text-blue-400">
            Volume: {(data.volume / 1000000).toFixed(2)}M
          </p>
          <p className="text-yellow-400">
            RSI: {data.rsi.toFixed(1)}
          </p>
          
          {relatedNews.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-600">
              <p className="text-gray-300 text-sm font-medium">Related News:</p>
              {relatedNews.map(news => (
                <div key={news.id} className="mt-1">
                  <p className="text-xs text-gray-400 truncate">{news.title}</p>
                  <div className="flex items-center space-x-2">
                    {getSentimentIcon(news.sentiment)}
                    <span className={`text-xs px-2 py-1 rounded ${getImpactColor(news.impact)}`}>
                      {news.impact}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <BarChart3 className="h-8 w-8 text-blue-500" />
          </motion.div>
          <span className="ml-2 text-gray-300">Loading market data...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-6 w-6 text-blue-400" />
            <h2 className="text-xl font-bold text-white">Market Analysis</h2>
          </div>
          
          {/* Symbol Selector */}
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-gray-700 text-white rounded px-3 py-1 text-sm border border-gray-600 focus:border-blue-500"
          >
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="BNBUSDT">BNB/USDT</option>
            <option value="STGUSDT">STG/USDT</option>
            <option value="ZROUSDT">ZRO/USDT</option>
          </select>
          
          {/* Timeframe Selector */}
          <div className="flex space-x-1">
            {['1M', '5M', '15M', '1H', '4H', '1D'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2 py-1 text-xs rounded ${
                  timeframe === tf
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Price Display */}
          <div className="text-right">
            <div className="text-2xl font-bold text-white">
              {formatPrice(currentPrice)}
            </div>
            <div className={`text-sm flex items-center ${
              priceChange >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {priceChange >= 0 ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
              {priceChange.toFixed(2)}%
            </div>
          </div>
          
          {/* Auto Refresh Toggle */}
          <label className="flex items-center text-sm text-gray-300">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            Auto-refresh
          </label>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-700 rounded-lg p-4"
        >
          <div className="flex items-center space-x-2">
            <DollarSign className="h-5 w-5 text-green-400" />
            <span className="text-gray-300 text-sm">Volume 24h</span>
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {((priceData[priceData.length - 1]?.volume || 0) / 1000000).toFixed(1)}M
          </div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gray-700 rounded-lg p-4"
        >
          <div className="flex items-center space-x-2">
            <Signal className="h-5 w-5 text-blue-400" />
            <span className="text-gray-300 text-sm">Active Signals</span>
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {tradingSignals.filter(s => s.status === 'ACTIVE').length}
          </div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-700 rounded-lg p-4"
        >
          <div className="flex items-center space-x-2">
            <Newspaper className="h-5 w-5 text-yellow-400" />
            <span className="text-gray-300 text-sm">News Impact</span>
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {newsEvents.filter(n => n.impact === 'HIGH').length} High
          </div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gray-700 rounded-lg p-4"
        >
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-purple-400" />
            <span className="text-gray-300 text-sm">RSI</span>
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {(priceData[priceData.length - 1]?.rsi || 0).toFixed(0)}
          </div>
        </motion.div>
      </div>

      {/* Main Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={priceData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatTime}
              stroke="#9CA3AF"
              fontSize={12}
            />
            <YAxis 
              domain={['dataMin - 100', 'dataMax + 100']}
              tickFormatter={(value) => `$${value.toLocaleString()}`}
              stroke="#9CA3AF"
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Moving Averages */}
            <Line 
              type="monotone" 
              dataKey="ma20" 
              stroke="#FCD34D" 
              strokeWidth={1}
              dot={false}
              strokeDasharray="5 5"
            />
            <Line 
              type="monotone" 
              dataKey="ma50" 
              stroke="#F97316" 
              strokeWidth={1}
              dot={false}
              strokeDasharray="10 5"
            />
            
            {/* Price Line */}
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#3B82F6" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: '#3B82F6' }}
            />
            
            {/* News Events Markers */}
            {newsEvents.map((news, index) => {
              const dataPoint = priceData.find(p => 
                Math.abs(new Date(p.timestamp).getTime() - new Date(news.timestamp).getTime()) < 60000
              )
              if (!dataPoint) return null
              
              return (
                <ReferenceDot
                  key={news.id}
                  x={news.timestamp}
                  y={dataPoint.price}
                  r={6}
                  fill={news.impact === 'HIGH' ? '#EF4444' : news.impact === 'MEDIUM' ? '#F59E0B' : '#10B981'}
                  stroke="#ffffff"
                  strokeWidth={2}
                  onClick={() => setSelectedNews(news)}
                  style={{ cursor: 'pointer' }}
                />
              )
            })}
            
            {/* Trading Signals */}
            {tradingSignals.map((signal, index) => {
              const dataPoint = priceData.find(p => 
                Math.abs(new Date(p.timestamp).getTime() - new Date(signal.timestamp).getTime()) < 60000
              )
              if (!dataPoint) return null
              
              return (
                <ReferenceDot
                  key={signal.id}
                  x={signal.timestamp}
                  y={signal.entry_price}
                  r={4}
                  fill={signal.direction === 'LONG' ? '#10B981' : '#EF4444'}
                  stroke="#ffffff"
                  strokeWidth={1}
                />
              )
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* News Events Panel */}
      <div className="grid grid-cols-2 gap-6">
        {/* Recent News */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Newspaper className="h-5 w-5 mr-2 text-yellow-400" />
            Recent News Impact
          </h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {newsEvents.slice(-5).reverse().map((news) => (
              <motion.div
                key={news.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`p-3 rounded-lg border-l-4 cursor-pointer transition-all ${
                  selectedNews?.id === news.id
                    ? 'bg-gray-600 border-blue-500'
                    : 'bg-gray-700 border-gray-500 hover:bg-gray-600'
                } ${
                  news.impact === 'HIGH' ? 'border-l-red-500' :
                  news.impact === 'MEDIUM' ? 'border-l-yellow-500' : 'border-l-green-500'
                }`}
                onClick={() => setSelectedNews(news)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-white text-sm font-medium line-clamp-2">
                      {news.title}
                    </p>
                    <div className="flex items-center space-x-2 mt-2">
                      {getSentimentIcon(news.sentiment)}
                      <span className={`text-xs px-2 py-1 rounded ${getImpactColor(news.impact)}`}>
                        {news.impact}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatTime(news.timestamp)}
                      </span>
                    </div>
                  </div>
                  <div className="text-right ml-2">
                    <div className={`text-sm font-medium ${
                      news.price_impact > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {news.price_impact > 0 ? '+' : ''}{news.price_impact.toFixed(1)}%
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Trading Signals */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Signal className="h-5 w-5 mr-2 text-blue-400" />
            Recent Signals
          </h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {tradingSignals.slice(-5).reverse().map((signal) => (
              <motion.div
                key={signal.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-gray-700 p-3 rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      signal.direction === 'LONG' ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <span className="text-white font-medium">{signal.direction}</span>
                    <span className="text-gray-300">{signal.symbol}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-medium">
                      {formatPrice(signal.entry_price)}
                    </div>
                    <div className="text-xs text-gray-400">
                      {signal.confidence.toFixed(0)}% confidence
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-400">by {signal.trader}</span>
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs px-2 py-1 rounded ${
                      signal.status === 'ACTIVE' ? 'bg-blue-500/20 text-blue-400' : 
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {signal.status}
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatTime(signal.timestamp)}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Selected News Detail */}
      {selectedNews && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 bg-gray-700 rounded-lg p-4 border-l-4 border-blue-500"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="text-white font-semibold mb-2">{selectedNews.title}</h4>
              <div className="flex items-center space-x-4 text-sm text-gray-300">
                <div className="flex items-center space-x-1">
                  <Clock className="h-4 w-4" />
                  <span>{new Date(selectedNews.timestamp).toLocaleString()}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Eye className="h-4 w-4" />
                  <span>{selectedNews.source}</span>
                </div>
                <div className="flex items-center space-x-1">
                  {getSentimentIcon(selectedNews.sentiment)}
                  <span>{selectedNews.sentiment}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {selectedNews.keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded"
                  >
                    #{keyword}
                  </span>
                ))}
              </div>
            </div>
            <div className="text-right ml-4">
              <div className={`text-lg font-bold ${
                selectedNews.price_impact > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {selectedNews.price_impact > 0 ? '+' : ''}{selectedNews.price_impact.toFixed(2)}%
              </div>
              <span className={`text-xs px-2 py-1 rounded ${getImpactColor(selectedNews.impact)}`}>
                {selectedNews.impact} IMPACT
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
