'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface NewsItem {
  id: number
  item_type: string
  source_name: string
  author?: string
  title: string
  content?: string
  published_at: string
  url?: string
  influence: number
  sentiment: number
  urgency: number
  source_trust: number
  source_type: string
  is_important: boolean
  priority_level: number
}

interface NewsFeedProps {
  className?: string
}

const NewsFeed: React.FC<NewsFeedProps> = ({ className = '' }) => {
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    important: false,
    sentiment: '',
    influence: '',
    urgency: '',
    source: ''
  })
  const [stats, setStats] = useState({
    total: 0,
    important: 0,
    positive: 0,
    negative: 0,
    avgSentiment: 0,
    avgInfluence: 0
  })

  useEffect(() => {
    fetchNews()
    const interval = setInterval(fetchNews, 60000) // Обновление каждую минуту
    return () => clearInterval(interval)
  }, [filters])

  const fetchNews = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      
      if (filters.important) params.append('important', 'true')
      if (filters.sentiment) params.append('sentiment', filters.sentiment)
      if (filters.influence) params.append('influence', filters.influence)
      if (filters.urgency) params.append('urgency', filters.urgency)
      if (filters.source) params.append('source', filters.source)
      
      params.append('limit', '50')
      params.append('minutes', '60')

      const response = await fetch(`/api/news?${params}`)
      const data = await response.json()
      
      if (data.news && data.news.length > 0) {
        setNews(data.news)
        calculateStats(data.news)
      } else {
        // Fallback: mock данные если API не возвращает новости
        const mockNews: NewsItem[] = [
          {
            id: 1,
            item_type: 'news',
            source_name: 'CoinTelegraph',
            author: 'Crypto Reporter',
            title: 'Bitcoin reaches new all-time high as institutional adoption grows',
            content: 'Bitcoin has reached a new all-time high as institutional adoption continues to grow across major corporations...',
            published_at: new Date().toISOString(),
            url: 'https://example.com',
            influence: 0.85,
            sentiment: 0.7,
            urgency: 0.8,
            source_trust: 0.9,
            source_type: 'crypto_media',
            is_important: true,
            priority_level: 1
          },
          {
            id: 2,
            item_type: 'news',
            source_name: 'Reuters',
            author: 'Financial News',
            title: 'Ethereum upgrade boosts DeFi ecosystem development',
            content: 'The latest Ethereum upgrade has significantly boosted the DeFi ecosystem with improved scalability...',
            published_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
            url: 'https://example.com',
            influence: 0.75,
            sentiment: 0.6,
            urgency: 0.5,
            source_trust: 0.95,
            source_type: 'media',
            is_important: true,
            priority_level: 2
          },
          {
            id: 3,
            item_type: 'news',
            source_name: 'CryptoNews',
            author: 'Market Analyst',
            title: 'Regulatory clarity drives crypto market optimism',
            content: 'Recent regulatory announcements have brought much-needed clarity to the cryptocurrency market...',
            published_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
            url: 'https://example.com',
            influence: 0.6,
            sentiment: 0.4,
            urgency: 0.3,
            source_trust: 0.7,
            source_type: 'crypto_media',
            is_important: false,
            priority_level: 3
          }
        ]
        setNews(mockNews)
        calculateStats(mockNews)
      }
    } catch (error) {
      console.error('Error fetching news:', error)
      // При ошибке также показываем mock данные
      const mockNews: NewsItem[] = [
        {
          id: 999,
          item_type: 'news',
          source_name: 'Mock Data',
          author: 'Demo',
          title: 'Demo: Real-time crypto market analysis available',
          content: 'This is demonstration data. Connect to live news feeds for real-time market intelligence...',
          published_at: new Date().toISOString(),
          url: '#',
          influence: 0.5,
          sentiment: 0.0,
          urgency: 0.2,
          source_trust: 0.5,
          source_type: 'demo',
          is_important: false,
          priority_level: 5
        }
      ]
      setNews(mockNews)
      calculateStats(mockNews)
    } finally {
      setLoading(false)
    }
  }

  const calculateStats = (newsItems: NewsItem[]) => {
    const total = newsItems.length
    const important = newsItems.filter(item => item.is_important).length
    const positive = newsItems.filter(item => item.sentiment > 0.1).length
    const negative = newsItems.filter(item => item.sentiment < -0.1).length
    const avgSentiment = newsItems.reduce((sum, item) => sum + item.sentiment, 0) / total || 0
    const avgInfluence = newsItems.reduce((sum, item) => sum + item.influence, 0) / total || 0

    setStats({ total, important, positive, negative, avgSentiment, avgInfluence })
  }

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.3) return 'text-green-500'
    if (sentiment > 0.1) return 'text-green-400'
    if (sentiment < -0.3) return 'text-red-500'
    if (sentiment < -0.1) return 'text-red-400'
    return 'text-gray-400'
  }

  const getUrgencyColor = (urgency: number) => {
    if (urgency > 0.8) return 'text-red-500'
    if (urgency > 0.6) return 'text-orange-500'
    if (urgency > 0.4) return 'text-yellow-500'
    return 'text-gray-400'
  }

  const getInfluenceColor = (influence: number) => {
    if (influence > 0.8) return 'text-purple-500'
    if (influence > 0.6) return 'text-blue-500'
    if (influence > 0.4) return 'text-cyan-500'
    return 'text-gray-400'
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    
    if (diffMins < 1) return 'только что'
    if (diffMins < 60) return `${diffMins}м назад`
    if (diffHours < 24) return `${diffHours}ч назад`
    return date.toLocaleDateString()
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Статистика */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-white">{stats.total}</div>
          <div className="text-sm text-gray-300">Всего новостей</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{stats.important}</div>
          <div className="text-sm text-gray-300">Важных</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400">{stats.positive}</div>
          <div className="text-sm text-gray-300">Позитивных</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{stats.negative}</div>
          <div className="text-sm text-gray-300">Негативных</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-400">
            {(stats.avgSentiment * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-300">Ср. настроение</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-purple-400">
            {(stats.avgInfluence * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-300">Ср. влияние</div>
        </div>
      </div>

      {/* Фильтры */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Фильтры</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.important}
              onChange={(e) => setFilters(prev => ({ ...prev, important: e.target.checked }))}
              className="rounded"
            />
            <span className="text-white">Только важные</span>
          </label>
          
          <select
            value={filters.sentiment}
            onChange={(e) => setFilters(prev => ({ ...prev, sentiment: e.target.value }))}
            className="bg-gray-800 text-white rounded px-3 py-2"
          >
            <option value="">Все настроения</option>
            <option value="0.3">Позитивные</option>
            <option value="-0.3">Негативные</option>
          </select>
          
          <select
            value={filters.influence}
            onChange={(e) => setFilters(prev => ({ ...prev, influence: e.target.value }))}
            className="bg-gray-800 text-white rounded px-3 py-2"
          >
            <option value="">Все влияния</option>
            <option value="0.8">Высокое</option>
            <option value="0.6">Среднее</option>
          </select>
          
          <select
            value={filters.urgency}
            onChange={(e) => setFilters(prev => ({ ...prev, urgency: e.target.value }))}
            className="bg-gray-800 text-white rounded px-3 py-2"
          >
            <option value="">Все срочности</option>
            <option value="0.8">Срочные</option>
            <option value="0.6">Средние</option>
          </select>
          
          <select
            value={filters.source}
            onChange={(e) => setFilters(prev => ({ ...prev, source: e.target.value }))}
            className="bg-gray-800 text-white rounded px-3 py-2"
          >
            <option value="">Все источники</option>
            <option value="Reuters">Reuters</option>
            <option value="Bloomberg">Bloomberg</option>
            <option value="CoinTelegraph">CoinTelegraph</option>
            <option value="CoinDesk">CoinDesk</option>
          </select>
        </div>
      </div>

      {/* Список новостей */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto"></div>
            <p className="text-gray-400 mt-2">Загрузка новостей...</p>
          </div>
        ) : (
          <AnimatePresence>
            {news.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className={`glass rounded-xl p-6 ${
                  item.is_important ? 'ring-2 ring-red-500' : ''
                }`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-sm text-gray-400">{item.source_name}</span>
                      {item.is_important && (
                        <span className="px-2 py-1 bg-red-500 text-white text-xs rounded">
                          ВАЖНО
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {formatTime(item.published_at)}
                      </span>
                    </div>
                    <h4 className="text-lg font-semibold text-white mb-2">
                      {item.title}
                    </h4>
                    {item.content && (
                      <p className="text-gray-300 text-sm mb-3 line-clamp-2">
                        {item.content}
                      </p>
                    )}
                  </div>
                  
                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-sm ml-4"
                    >
                      Открыть →
                    </a>
                  )}
                </div>
                
                {/* Метрики */}
                <div className="flex items-center space-x-6 text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400">Настроение:</span>
                    <span className={getSentimentColor(item.sentiment)}>
                      {(item.sentiment * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400">Влияние:</span>
                    <span className={getInfluenceColor(item.influence)}>
                      {(item.influence * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400">Срочность:</span>
                    <span className={getUrgencyColor(item.urgency)}>
                      {(item.urgency * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400">Доверие:</span>
                    <span className="text-yellow-400">
                      {(item.source_trust * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400">Приоритет:</span>
                    <span className="text-purple-400">
                      {item.priority_level}/5
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        
        {!loading && news.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-400">Новости не найдены</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default NewsFeed
