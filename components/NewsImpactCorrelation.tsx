'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Bar,
  BarChart,
  Legend
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Newspaper,
  Target,
  Zap,
  Brain,
  AlertCircle
} from 'lucide-react'

interface NewsImpactData {
  id: string
  title: string
  timestamp: string
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  impact: 'HIGH' | 'MEDIUM' | 'LOW'
  predicted_impact: number // Предсказанное влияние AI
  actual_impact: number    // Фактическое влияние на цену
  accuracy_score: number   // Точность предсказания
  keywords: string[]
  source: string
  price_before: number
  price_after: number
  time_to_impact: number   // Время до влияния в минутах
  volume_spike: number     // Увеличение объёма торгов
}

interface CorrelationMetrics {
  ai_accuracy: number
  sentiment_correlation: number
  impact_prediction_rate: number
  average_reaction_time: number
  false_positive_rate: number
  high_impact_detection_rate: number
}

export default function NewsImpactCorrelation() {
  const [newsData, setNewsData] = useState<NewsImpactData[]>([])
  const [metrics, setMetrics] = useState<CorrelationMetrics | null>(null)
  const [selectedTimeRange, setSelectedTimeRange] = useState('24H')
  const [selectedFilter, setSelectedFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)

  // Генерация демо данных для корреляции
  const generateCorrelationData = () => {
    const data: NewsImpactData[] = []
    const now = new Date()
    
    const newsTemplates = [
      {
        title: "LayerZero Foundation предложил приобрести Stargate",
        keywords: ["LayerZero", "STG", "ZRO", "DeFi"],
        source: "CryptoAttack",
        baseImpact: 12.5
      },
      {
        title: "Bitcoin ETF shows record institutional inflows",
        keywords: ["Bitcoin", "ETF", "Institutional"],
        source: "CoinDesk",
        baseImpact: 8.3
      },
      {
        title: "Major whale wallet moves 10,000 BTC",
        keywords: ["Bitcoin", "Whale", "Movement"],
        source: "WhaleAlert",
        baseImpact: -4.2
      },
      {
        title: "New DeFi protocol raises $50M funding",
        keywords: ["DeFi", "Funding", "Investment"],
        source: "TechCrunch",
        baseImpact: 6.7
      },
      {
        title: "Regulatory clarity boosts market confidence",
        keywords: ["Regulation", "Government", "Policy"],
        source: "Reuters",
        baseImpact: 15.2
      },
      {
        title: "Exchange hack affects $100M in assets",
        keywords: ["Security", "Hack", "Exchange"],
        source: "CoinTelegraph",
        baseImpact: -18.5
      }
    ]
    
    const timeRanges = {
      '24H': 24 * 60 * 60 * 1000,
      '7D': 7 * 24 * 60 * 60 * 1000,
      '30D': 30 * 24 * 60 * 60 * 1000
    }
    
    const timeRange = timeRanges[selectedTimeRange as keyof typeof timeRanges]
    const newsCount = selectedTimeRange === '24H' ? 8 : selectedTimeRange === '7D' ? 25 : 60
    
    for (let i = 0; i < newsCount; i++) {
      const template = newsTemplates[Math.floor(Math.random() * newsTemplates.length)]
      const timestamp = new Date(now.getTime() - Math.random() * timeRange).toISOString()
      
      // Определение сентимента на основе базового влияния
      const sentiment = template.baseImpact > 5 ? 'POSITIVE' : 
                       template.baseImpact < -5 ? 'NEGATIVE' : 'NEUTRAL'
      
      // Определение силы влияния
      const impact = Math.abs(template.baseImpact) > 10 ? 'HIGH' :
                    Math.abs(template.baseImpact) > 5 ? 'MEDIUM' : 'LOW'
      
      // AI предсказание (с некоторой погрешностью)
      const aiAccuracy = 0.7 + Math.random() * 0.25 // 70-95% точность
      const predicted_impact = template.baseImpact * (0.8 + Math.random() * 0.4) // ±20% погрешность
      
      // Фактическое влияние (более волатильное)
      const actual_impact = template.baseImpact * (0.5 + Math.random() * 1.0) // ±50% волатильность
      
      // Точность предсказания
      const accuracy_score = Math.max(0, 100 - Math.abs((predicted_impact - actual_impact) / actual_impact * 100))
      
      // Цены до и после
      const price_before = 43000 + (Math.random() - 0.5) * 2000
      const price_after = price_before * (1 + actual_impact / 100)
      
      data.push({
        id: `correlation_${i}`,
        title: template.title,
        timestamp,
        sentiment,
        impact,
        predicted_impact,
        actual_impact,
        accuracy_score,
        keywords: template.keywords,
        source: template.source,
        price_before,
        price_after,
        time_to_impact: Math.random() * 60 + 5, // 5-65 минут
        volume_spike: Math.random() * 300 + 50  // 50-350% увеличение объёма
      })
    }
    
    // Расчёт метрик
    const avgAccuracy = data.reduce((sum, item) => sum + item.accuracy_score, 0) / data.length
    
    const sentimentMatches = data.filter(item => 
      (item.sentiment === 'POSITIVE' && item.actual_impact > 0) ||
      (item.sentiment === 'NEGATIVE' && item.actual_impact < 0) ||
      (item.sentiment === 'NEUTRAL' && Math.abs(item.actual_impact) < 2)
    ).length
    
    const sentimentCorrelation = (sentimentMatches / data.length) * 100
    
    const highImpactNews = data.filter(item => item.impact === 'HIGH')
    const highImpactDetected = highImpactNews.filter(item => Math.abs(item.actual_impact) > 8).length
    const highImpactDetectionRate = highImpactNews.length > 0 ? (highImpactDetected / highImpactNews.length) * 100 : 0
    
    const avgReactionTime = data.reduce((sum, item) => sum + item.time_to_impact, 0) / data.length
    
    const falsePositives = data.filter(item => 
      (item.predicted_impact > 5 && item.actual_impact < 2) ||
      (item.predicted_impact < -5 && item.actual_impact > -2)
    ).length
    const falsePositiveRate = (falsePositives / data.length) * 100
    
    const correctPredictions = data.filter(item => 
      Math.abs(item.predicted_impact - item.actual_impact) < Math.abs(item.actual_impact) * 0.3
    ).length
    const impactPredictionRate = (correctPredictions / data.length) * 100
    
    setNewsData(data.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()))
    setMetrics({
      ai_accuracy: avgAccuracy,
      sentiment_correlation: sentimentCorrelation,
      impact_prediction_rate: impactPredictionRate,
      average_reaction_time: avgReactionTime,
      false_positive_rate: falsePositiveRate,
      high_impact_detection_rate: highImpactDetectionRate
    })
    setLoading(false)
  }

  useEffect(() => {
    generateCorrelationData()
  }, [selectedTimeRange, selectedFilter])

  const getFilteredData = () => {
    if (selectedFilter === 'ALL') return newsData
    if (selectedFilter === 'HIGH_IMPACT') return newsData.filter(item => item.impact === 'HIGH')
    if (selectedFilter === 'ACCURATE') return newsData.filter(item => item.accuracy_score > 80)
    if (selectedFilter === 'INACCURATE') return newsData.filter(item => item.accuracy_score < 50)
    return newsData
  }

  const filteredData = getFilteredData()

  const formatImpact = (impact: number) => {
    return `${impact > 0 ? '+' : ''}${impact.toFixed(1)}%`
  }

  const getImpactColor = (impact: number) => {
    if (impact > 5) return 'text-green-400'
    if (impact < -5) return 'text-red-400'
    return 'text-gray-400'
  }

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy > 80) return 'text-green-400'
    if (accuracy > 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const CustomScatterTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 shadow-xl max-w-xs">
          <p className="text-white font-semibold text-sm mb-2 line-clamp-2">{data.title}</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Predicted:</span>
              <span className={getImpactColor(data.predicted_impact)}>
                {formatImpact(data.predicted_impact)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Actual:</span>
              <span className={getImpactColor(data.actual_impact)}>
                {formatImpact(data.actual_impact)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Accuracy:</span>
              <span className={getAccuracyColor(data.accuracy_score)}>
                {data.accuracy_score.toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Source:</span>
              <span className="text-white">{data.source}</span>
            </div>
          </div>
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
            <Brain className="h-8 w-8 text-purple-500" />
          </motion.div>
          <span className="ml-2 text-gray-300">Analyzing news impact correlation...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Brain className="h-6 w-6 text-purple-400" />
          <h2 className="text-xl font-bold text-white">News Impact Analysis</h2>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Time Range Selector */}
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="bg-gray-700 text-white rounded px-3 py-1 text-sm border border-gray-600"
          >
            <option value="24H">Last 24H</option>
            <option value="7D">Last 7D</option>
            <option value="30D">Last 30D</option>
          </select>
          
          {/* Filter Selector */}
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="bg-gray-700 text-white rounded px-3 py-1 text-sm border border-gray-600"
          >
            <option value="ALL">All News</option>
            <option value="HIGH_IMPACT">High Impact</option>
            <option value="ACCURATE">Accurate Predictions</option>
            <option value="INACCURATE">Inaccurate Predictions</option>
          </select>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-700 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-green-400" />
              <span className="text-gray-300 text-xs">AI Accuracy</span>
            </div>
            <div className="text-lg font-bold text-white mt-1">
              {metrics.ai_accuracy.toFixed(1)}%
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-700 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-blue-400" />
              <span className="text-gray-300 text-xs">Sentiment Match</span>
            </div>
            <div className="text-lg font-bold text-white mt-1">
              {metrics.sentiment_correlation.toFixed(1)}%
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gray-700 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2">
              <Zap className="h-5 w-5 text-yellow-400" />
              <span className="text-gray-300 text-xs">Prediction Rate</span>
            </div>
            <div className="text-lg font-bold text-white mt-1">
              {metrics.impact_prediction_rate.toFixed(1)}%
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gray-700 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-purple-400" />
              <span className="text-gray-300 text-xs">High Impact Det.</span>
            </div>
            <div className="text-lg font-bold text-white mt-1">
              {metrics.high_impact_detection_rate.toFixed(1)}%
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-gray-700 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <span className="text-gray-300 text-xs">False Positives</span>
            </div>
            <div className="text-lg font-bold text-white mt-1">
              {metrics.false_positive_rate.toFixed(1)}%
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-gray-700 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-orange-400" />
              <span className="text-gray-300 text-xs">Avg Reaction</span>
            </div>
            <div className="text-lg font-bold text-white mt-1">
              {metrics.average_reaction_time.toFixed(0)}m
            </div>
          </motion.div>
        </div>
      )}

      {/* Correlation Chart */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Predicted vs Actual Impact</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              type="number"
              dataKey="predicted_impact"
              name="Predicted Impact"
              stroke="#9CA3AF"
              fontSize={12}
              tickFormatter={(value) => `${value.toFixed(1)}%`}
            />
            <YAxis
              type="number" 
              dataKey="actual_impact"
              name="Actual Impact"
              stroke="#9CA3AF"
              fontSize={12}
              tickFormatter={(value) => `${value.toFixed(1)}%`}
            />
            <Tooltip content={<CustomScatterTooltip />} />
            
            {/* Perfect correlation line */}
            <line 
              x1={0} y1={0} x2={100} y2={100} 
              stroke="#6B7280" 
              strokeDasharray="5 5"
              strokeWidth={1}
            />
            
            <Scatter data={filteredData} fill="#3B82F6">
              {filteredData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={
                    entry.impact === 'HIGH' ? '#EF4444' :
                    entry.impact === 'MEDIUM' ? '#F59E0B' : '#10B981'
                  }
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Recent News Analysis */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Newspaper className="h-5 w-5 mr-2 text-yellow-400" />
          Recent News Analysis ({filteredData.length})
        </h3>
        
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {filteredData.slice(0, 10).map((news) => (
            <motion.div
              key={news.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-gray-700 p-4 rounded-lg"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-white text-sm font-medium line-clamp-2 mb-2">
                    {news.title}
                  </p>
                  
                  <div className="flex items-center space-x-4 text-xs text-gray-400">
                    <span>{news.source}</span>
                    <span>{new Date(news.timestamp).toLocaleString()}</span>
                    <span className={`px-2 py-1 rounded ${
                      news.impact === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                      news.impact === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {news.impact}
                    </span>
                  </div>
                  
                  <div className="flex flex-wrap gap-1 mt-2">
                    {news.keywords.slice(0, 3).map((keyword, index) => (
                      <span
                        key={index}
                        className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded"
                      >
                        #{keyword}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="text-right ml-4 space-y-1">
                  <div>
                    <span className="text-xs text-gray-400">Predicted:</span>
                    <div className={`text-sm font-medium ${getImpactColor(news.predicted_impact)}`}>
                      {formatImpact(news.predicted_impact)}
                    </div>
                  </div>
                  
                  <div>
                    <span className="text-xs text-gray-400">Actual:</span>
                    <div className={`text-sm font-medium ${getImpactColor(news.actual_impact)}`}>
                      {formatImpact(news.actual_impact)}
                    </div>
                  </div>
                  
                  <div>
                    <span className="text-xs text-gray-400">Accuracy:</span>
                    <div className={`text-sm font-medium ${getAccuracyColor(news.accuracy_score)}`}>
                      {news.accuracy_score.toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Reaction Details */}
              <div className="mt-3 pt-3 border-t border-gray-600">
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-gray-400">Reaction Time:</span>
                    <div className="text-white">{news.time_to_impact.toFixed(0)} min</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Volume Spike:</span>
                    <div className="text-white">+{news.volume_spike.toFixed(0)}%</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Price Move:</span>
                    <div className="text-white">
                      ${news.price_before.toFixed(0)} → ${news.price_after.toFixed(0)}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
