"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'

interface TelegramSignal {
  id: string
  symbol: string
  direction: 'LONG' | 'SHORT'
  signalType: string
  entryPrice: number
  entryLevels: number[]
  stopLoss: number
  takeProfitLevels: number[]
  leverage: number
  confidenceScore: number
  signalTimestamp: string
  timeframe: string
  technicalReason: string
  tags: string[]
  validationStatus: 'valid' | 'suspicious' | 'invalid'
  parsingConfidence: number
  source: {
    name: string
    code: string
    reliabilityScore: number
  }
  instrument: {
    symbol: string
    name: string
    exchange: string
  }
  rawMessage: {
    text: string
    timestamp: string
    sentiment: number
  }
  potentialProfit: string
  potentialLoss: string
  ageMinutes: number
}

interface SignalStats {
  total: number
  byDirection: {
    LONG: number
    SHORT: number
  }
  byStatus: {
    valid: number
    suspicious: number
  }
  avgConfidence: string
  recentSignals: number
}

const TelegramSignalsDashboard: React.FC = () => {
  const [signals, setSignals] = useState<TelegramSignal[]>([])
  const [stats, setStats] = useState<SignalStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState({
    direction: 'all',
    status: 'all',
    hours: 24
  })

  const fetchSignals = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        limit: '50',
        hours: filter.hours.toString()
      })
      
      if (filter.direction !== 'all') params.set('direction', filter.direction)
      if (filter.status !== 'all') params.set('status', filter.status)
      
      const response = await fetch(`/api/telegram-signals?${params}`)
      const data = await response.json()
      
      if (data.error) {
        setError(data.error)
      } else {
        setSignals(data.signals || [])
        setStats(data.stats || null)
        setError(null)
      }
    } catch (err) {
      setError('Ошибка загрузки сигналов')
      console.error('Error fetching signals:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSignals()
    
    // Автообновление каждые 30 секунд
    const interval = setInterval(fetchSignals, 30000)
    return () => clearInterval(interval)
  }, [filter])

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatAge = (minutes: number) => {
    if (minutes < 60) return `${minutes}м назад`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}ч назад`
    return `${Math.floor(minutes / 1440)}д назад`
  }

  const getDirectionColor = (direction: string) => {
    return direction === 'LONG' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return 'bg-green-100 text-green-800'
      case 'suspicious': return 'bg-yellow-100 text-yellow-800'
      case 'invalid': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="space-y-3">
            {[1,2,3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-red-200">
          <CardContent className="p-6 text-center">
            <div className="text-red-600 text-lg font-semibold">⚠️ Ошибка загрузки</div>
            <div className="text-gray-600 mt-2">{error}</div>
            <button 
              onClick={fetchSignals}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Попробовать снова
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Заголовок */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">📱 Telegram Сигналы</h1>
          <p className="text-gray-600 mt-1">Реальные торговые сигналы из Telegram каналов</p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Обновлено: {formatTime(new Date().toISOString())}</span>
        </div>
      </div>

      {/* Фильтры */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-50 rounded-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Направление</label>
          <select 
            value={filter.direction}
            onChange={(e) => setFilter({...filter, direction: e.target.value})}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="all">Все</option>
            <option value="LONG">LONG</option>
            <option value="SHORT">SHORT</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
          <select 
            value={filter.status}
            onChange={(e) => setFilter({...filter, status: e.target.value})}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="all">Все</option>
            <option value="valid">Валидные</option>
            <option value="suspicious">Подозрительные</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Период</label>
          <select 
            value={filter.hours}
            onChange={(e) => setFilter({...filter, hours: parseInt(e.target.value)})}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value={1}>1 час</option>
            <option value={6}>6 часов</option>
            <option value={24}>24 часа</option>
            <option value={168}>7 дней</option>
          </select>
        </div>
      </div>

      {/* Статистика */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-gray-600">Всего сигналов</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-600">{stats.byDirection.LONG}</div>
              <div className="text-sm text-gray-600">LONG сигналов</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-red-600">{stats.byDirection.SHORT}</div>
              <div className="text-sm text-gray-600">SHORT сигналов</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-purple-600">{stats.avgConfidence}</div>
              <div className="text-sm text-gray-600">Средняя уверенность</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-orange-600">{stats.recentSignals}</div>
              <div className="text-sm text-gray-600">За последний час</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Список сигналов */}
      <div className="space-y-4">
        {signals.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <div className="text-gray-500 text-lg">📭 Сигналов не найдено</div>
              <div className="text-sm text-gray-400 mt-2">
                Попробуйте изменить фильтры или проверьте подключение к Telegram
              </div>
            </CardContent>
          </Card>
        ) : (
          signals.map((signal) => (
            <Card key={signal.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center space-x-3">
                    <Badge className={getDirectionColor(signal.direction)}>
                      {signal.direction}
                    </Badge>
                    <div className="text-xl font-bold text-gray-900">
                      {signal.symbol}
                    </div>
                    <Badge variant="outline">
                      {signal.instrument.exchange}
                    </Badge>
                    <Badge className={getStatusColor(signal.validationStatus)}>
                      {signal.validationStatus}
                    </Badge>
                  </div>
                  
                  <div className="text-right text-sm text-gray-500">
                    <div>{formatTime(signal.signalTimestamp)}</div>
                    <div>{formatAge(signal.ageMinutes)}</div>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Цены и уровни */}
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">💰 Уровни</h4>
                    <div className="space-y-1 text-sm">
                      {signal.entryPrice && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Вход:</span>
                          <span className="font-mono">{signal.entryPrice}</span>
                        </div>
                      )}
                      {signal.entryLevels.length > 0 && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Уровни:</span>
                          <span className="font-mono text-xs">
                            {signal.entryLevels.slice(0, 3).join(', ')}
                            {signal.entryLevels.length > 3 && '...'}
                          </span>
                        </div>
                      )}
                      {signal.stopLoss && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Стоп:</span>
                          <span className="font-mono text-red-600">{signal.stopLoss}</span>
                        </div>
                      )}
                      {signal.takeProfitLevels.length > 0 && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Цели:</span>
                          <span className="font-mono text-green-600 text-xs">
                            {signal.takeProfitLevels.slice(0, 3).join(', ')}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Риск и потенциал */}
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">📊 Анализ</h4>
                    <div className="space-y-1 text-sm">
                      {signal.leverage && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Плечо:</span>
                          <span className="font-semibold">{signal.leverage}x</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-gray-600">Уверенность:</span>
                        <span className={`font-semibold ${getConfidenceColor(signal.confidenceScore)}`}>
                          {(signal.confidenceScore * 100).toFixed(0)}%
                        </span>
                      </div>
                      {signal.potentialProfit && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Потенциал:</span>
                          <span className="text-green-600 font-semibold">
                            +{signal.potentialProfit}%
                          </span>
                        </div>
                      )}
                      {signal.potentialLoss && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Риск:</span>
                          <span className="text-red-600 font-semibold">
                            -{signal.potentialLoss}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Источник и детали */}
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">📡 Источник</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Канал:</span>
                        <span className="font-semibold">{signal.source.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Надежность:</span>
                        <span className="font-semibold">
                          {(signal.source.reliabilityScore * 100).toFixed(0)}%
                        </span>
                      </div>
                      {signal.timeframe && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Таймфрейм:</span>
                          <span className="font-mono">{signal.timeframe}</span>
                        </div>
                      )}
                      {signal.tags.length > 0 && (
                        <div className="mt-2">
                          <div className="flex flex-wrap gap-1">
                            {signal.tags.slice(0, 3).map(tag => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Техническое обоснование */}
                {signal.technicalReason && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <div className="text-sm text-blue-800">
                      <strong>Техническое обоснование:</strong> {signal.technicalReason}
                    </div>
                  </div>
                )}
                
                {/* Сырое сообщение */}
                {signal.rawMessage.text && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-600 mb-1">Оригинальное сообщение:</div>
                    <div className="text-sm text-gray-800 font-mono">
                      {signal.rawMessage.text}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}

export default TelegramSignalsDashboard
