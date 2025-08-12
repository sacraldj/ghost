'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  MessageCircle, 
  Radio, 
  Clock, 
  TrendingUp, 
  AlertTriangle,
  RefreshCw
} from 'lucide-react'

interface TelegramSignal {
  timestamp: string
  source: string
  chat_id: number
  text: string
  type: string
  trigger?: string
}

interface RawMessage {
  timestamp: string
  chat_id: number
  channel_name: string
  message_id: number
  text: string
  from_user?: string
}

interface TelegramData {
  signals: TelegramSignal[]
  raw_messages: RawMessage[]
  stats: {
    total_signals: number
    total_raw: number
    last_activity: string | null
    channels_active: number
    signal_types: string[]
  }
}

export default function TelegramSignals() {
  const [data, setData] = useState<TelegramData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'signals' | 'raw'>('signals')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchData = async () => {
    try {
      const response = await fetch('/api/telegram-signals?limit=20&hours=24')
      const result = await response.json()
      
      if (result.success) {
        setData(result.data)
      }
    } catch (error) {
      console.error('Error fetching Telegram data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSignalIcon = (type: string) => {
    switch (type) {
      case 'trade': return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'news': return <Radio className="w-4 h-4 text-blue-500" />
      case 'test': return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      default: return <MessageCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const detectSignalType = (text: string) => {
    const upperText = text.toUpperCase()
    if (upperText.includes('LONG') || upperText.includes('SHORT')) {
      return 'trade'
    }
    if (upperText.includes('NEWS') || upperText.includes('BREAKING')) {
      return 'news'
    }
    return 'message'
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Radio className="w-6 h-6 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Telegram Сигналы
            </h2>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1 rounded text-sm ${
                autoRefresh 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
              }`}
            >
              {autoRefresh ? 'Auto' : 'Manual'}
            </button>
            
            <button
              onClick={fetchData}
              className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Stats */}
        {data && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{data.stats.total_signals}</div>
              <div className="text-sm text-gray-500">Сигналы</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{data.stats.total_raw}</div>
              <div className="text-sm text-gray-500">Сообщения</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{data.stats.channels_active}</div>
              <div className="text-sm text-gray-500">Каналы</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{data.stats.signal_types.length}</div>
              <div className="text-sm text-gray-500">Типы</div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex">
          <button
            onClick={() => setActiveTab('signals')}
            className={`px-6 py-3 text-sm font-medium border-b-2 ${
              activeTab === 'signals'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Сигналы ({data?.stats.total_signals || 0})
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`px-6 py-3 text-sm font-medium border-b-2 ${
              activeTab === 'raw'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Все сообщения ({data?.stats.total_raw || 0})
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {!data ? (
          <div className="text-center py-8 text-gray-500">
            Нет данных
          </div>
        ) : (
          <div className="space-y-4">
            {activeTab === 'signals' ? (
              data.signals.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  Сигналы не найдены
                </div>
              ) : (
                data.signals.map((signal, index) => (
                  <motion.div
                    key={`${signal.timestamp}-${index}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getSignalIcon(signal.type)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {signal.source}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              signal.type === 'trade' ? 'bg-green-100 text-green-800' :
                              signal.type === 'news' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {signal.type}
                            </span>
                          </div>
                          <p className="text-gray-700 dark:text-gray-300 text-sm">
                            {signal.text}
                          </p>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatTime(signal.timestamp)}
                      </div>
                    </div>
                  </motion.div>
                ))
              )
            ) : (
              data.raw_messages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  Сообщения не найдены
                </div>
              ) : (
                data.raw_messages.map((message, index) => (
                  <motion.div
                    key={`${message.timestamp}-${index}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getSignalIcon(detectSignalType(message.text))}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {message.channel_name}
                            </span>
                            {message.from_user && (
                              <span className="text-xs text-gray-500">
                                @{message.from_user}
                              </span>
                            )}
                          </div>
                          <p className="text-gray-700 dark:text-gray-300 text-sm">
                            {message.text}
                          </p>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatTime(message.timestamp)}
                      </div>
                    </div>
                  </motion.div>
                ))
              )
            )}
          </div>
        )}
      </div>
    </div>
  )
}
