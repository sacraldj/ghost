"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'

interface NewsStatistics {
  total_news: number
  critical_news: number
  prediction_accuracy: string
  avg_market_impact: string
  sentiment_breakdown: {
    bullish: number
    bearish: number
    neutral: number
  }
  top_sources: Record<string, number>
  time_accuracy: {
    '1h_accuracy': string
    '4h_accuracy': string
    '24h_accuracy': string
  }
}

interface NewsItem {
  id: string
  title: string
  source: string
  sentiment: number
  urgency: number
  market_impact: number
  published_at: string
  filter_info?: {
    importance_score: number
    detected_categories: string[]
  }
}

interface NewsAnalysisData {
  enabled: boolean
  statistics?: NewsStatistics
  recent_news?: NewsItem[]
  integration_status?: {
    enabled: boolean
    components: Record<string, boolean>
    hooks_registered: number
  }
  error?: string
  message?: string
}

const NewsAnalysisDashboard: React.FC = () => {
  const [data, setData] = useState<NewsAnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'statistics' | 'recent'>('overview')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchData = async (action: string = 'overview') => {
    try {
      setLoading(true)
      const response = await fetch(`/api/news-analysis?action=${action}&days=7&limit=20`)
      const result = await response.json()
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to fetch news analysis')
      }
      
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      console.error('Error fetching news analysis:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(activeTab)
  }, [activeTab])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchData(activeTab)
    }, 60000) // Обновление каждую минуту

    return () => clearInterval(interval)
  }, [autoRefresh, activeTab])

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit'
    })
  }

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.1) return 'bg-green-500'
    if (sentiment < -0.1) return 'bg-red-500'
    return 'bg-gray-500'
  }

  const getSentimentEmoji = (sentiment: number) => {
    if (sentiment > 0.3) return '📈'
    if (sentiment < -0.3) return '📉'
    return '➡️'
  }

  const getUrgencyEmoji = (urgency: number) => {
    if (urgency > 0.7) return '🚨'
    if (urgency > 0.3) return '⏰'
    return '🕐'
  }

  const renderIntegrationStatus = () => {
    if (!data?.integration_status) return null

    const { enabled, components } = data.integration_status

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <span>{enabled ? '✅' : '❌'}</span>
            <span>News Integration Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!enabled ? (
            <div className="text-yellow-600 bg-yellow-50 p-4 rounded-lg">
              <p className="font-semibold">News integration is disabled</p>
              <p className="text-sm mt-1">
                Set GHOST_NEWS_INTEGRATION_ENABLED=true environment variable to enable
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(components).map(([component, status]) => (
                <div key={component} className="flex items-center space-x-2">
                  <span>{status ? '✅' : '❌'}</span>
                  <span className="text-sm capitalize">{component.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  const renderStatistics = () => {
    if (!data?.statistics) return null

    const stats = data.statistics

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Общая статистика */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total News</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_news}</div>
            <div className="text-xs text-gray-500">
              {stats.critical_news} critical
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Prediction Accuracy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.prediction_accuracy}</div>
            <div className="text-xs text-gray-500">
              Avg impact: {stats.avg_market_impact}
            </div>
          </CardContent>
        </Card>

        {/* Sentiment Breakdown */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Sentiment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Bullish
                </span>
                <span>{stats.sentiment_breakdown.bullish}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                  Bearish
                </span>
                <span>{stats.sentiment_breakdown.bearish}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-gray-500 rounded-full mr-2"></span>
                  Neutral
                </span>
                <span>{stats.sentiment_breakdown.neutral}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Time Accuracy */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Time Accuracy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>1h:</span>
                <span>{stats.time_accuracy['1h_accuracy']}</span>
              </div>
              <div className="flex justify-between">
                <span>4h:</span>
                <span>{stats.time_accuracy['4h_accuracy']}</span>
              </div>
              <div className="flex justify-between">
                <span>24h:</span>
                <span>{stats.time_accuracy['24h_accuracy']}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderRecentNews = () => {
    if (!data?.recent_news || data.recent_news.length === 0) {
      return (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-gray-500 text-lg">📰 No recent news</div>
            <div className="text-sm text-gray-400 mt-2">
              News analysis is {data?.enabled ? 'enabled' : 'disabled'}
            </div>
          </CardContent>
        </Card>
      )
    }

    return (
      <div className="space-y-4">
        {data.recent_news.map((news) => (
          <Card key={news.id} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-4">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center space-x-3 flex-1">
                  <div className="flex items-center space-x-1">
                    <span>{getSentimentEmoji(news.sentiment)}</span>
                    <span>{getUrgencyEmoji(news.urgency)}</span>
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 line-clamp-2">
                      {news.title}
                    </h3>
                    <div className="flex items-center space-x-3 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {news.source}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        Impact: {news.market_impact.toFixed(2)}
                      </span>
                      {news.filter_info && (
                        <span className="text-xs text-gray-500">
                          Score: {news.filter_info.importance_score.toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="text-right text-xs text-gray-500">
                  {formatTime(news.published_at)}
                </div>
              </div>

              {/* Sentiment и Urgency индикаторы */}
              <div className="flex items-center space-x-4 text-xs">
                <div className="flex items-center space-x-1">
                  <span>Sentiment:</span>
                  <div className={`w-12 h-2 rounded-full ${getSentimentColor(news.sentiment)}`}></div>
                  <span>{news.sentiment.toFixed(2)}</span>
                </div>
                
                <div className="flex items-center space-x-1">
                  <span>Urgency:</span>
                  <div className={`w-12 h-2 rounded-full ${
                    news.urgency > 0.7 ? 'bg-red-500' : 
                    news.urgency > 0.3 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}></div>
                  <span>{news.urgency.toFixed(2)}</span>
                </div>

                {news.filter_info?.detected_categories && news.filter_info.detected_categories.length > 0 && (
                  <div className="flex items-center space-x-1">
                    <span>Categories:</span>
                    {news.filter_info.detected_categories.map((category, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {category}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-red-500 text-lg">❌ Error</div>
            <div className="text-sm text-gray-600 mt-2">{error}</div>
            <Button 
              onClick={() => fetchData(activeTab)} 
              className="mt-4"
              variant="outline"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!data?.enabled) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-yellow-600 text-lg">📰 News Integration Disabled</div>
            <div className="text-sm text-gray-600 mt-2">
              {data?.message || 'News analysis is not enabled'}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📰 News Analysis</h1>
          <p className="text-gray-600">Real-time news impact analysis and filtering</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? "🔄 Auto" : "⏸️ Manual"}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchData(activeTab)}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Integration Status */}
      {renderIntegrationStatus()}

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        {(['overview', 'statistics', 'recent'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab === 'overview' && '📊 Overview'}
            {tab === 'statistics' && '📈 Statistics'}
            {tab === 'recent' && '📰 Recent News'}
          </button>
        ))}
      </div>

      {/* Content */}
      {(activeTab === 'overview' || activeTab === 'statistics') && renderStatistics()}
      {(activeTab === 'overview' || activeTab === 'recent') && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Recent News</h2>
          {renderRecentNews()}
        </div>
      )}
    </div>
  )
}

export default NewsAnalysisDashboard
