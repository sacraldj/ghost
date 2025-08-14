'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Eye, Play, Zap, Users, TrendingUp, TrendingDown, Clock, Target, BarChart3, Settings, Activity } from 'lucide-react'

interface TraderEnhanced {
  trader_id: string
  name: string
  source_type: string
  source_handle: string
  mode: 'observe' | 'paper' | 'live'
  is_active: boolean
  
  // Базовые счетчики (как у Дарена)
  total_signals: number
  valid_signals: number
  executed_signals: number
  
  // ЧЕСТНАЯ СТАТИСТИКА как у Дарена: "Вася дал 109 раз, из них 90 был TP1"
  tp1_count: number
  tp2_count: number
  sl_count: number
  be_count: number
  
  // Процентные показатели
  tp1_rate: number
  tp2_rate: number
  sl_rate: number
  winrate_30d: number
  
  // Финансовые показатели
  total_pnl: number
  avg_pnl: number
  pnl_30d: number
  avg_win: number
  avg_loss: number
  profit_factor: number
  
  // Временные показатели
  avg_time_to_tp1: number
  
  // Метаданные
  last_signal_at: string
  avg_confidence: number
  
  // Строка статистики как у Дарена
  stats_summary: string
  
  // Дополнительные показатели качества
  signal_quality: number
  execution_rate: number
}

interface Signal {
  signal_id: number
  trader_id: string
  symbol: string
  side: string
  entry: number
  tp1?: number
  tp2?: number
  sl?: number
  posted_at: string
  confidence: number
  is_valid: boolean
  outcome?: {
    final_result: string
    pnl_sim: number
    roi_sim: number
    duration_to_tp1_min?: number
  }
}

export default function TraderObservationEnhanced() {
  const [traders, setTraders] = useState<TraderEnhanced[]>([])
  const [recentSignals, setRecentSignals] = useState<Signal[]>([])
  const [overview, setOverview] = useState<any>({})
  const [selectedTrader, setSelectedTrader] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [sortBy, setSortBy] = useState<'tp1_rate' | 'total_pnl' | 'total_signals' | 'profit_factor'>('tp1_rate')

  useEffect(() => {
    fetchData()
    
    // Обновление каждые 30 секунд
    const interval = setInterval(fetchData, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Получаем трейдеров с детальной статистикой
      const tradersResponse = await fetch('/api/trader-observation?action=traders')
      const tradersData = await tradersResponse.json()
      
      if (tradersData.traders) {
        // Сортируем трейдеров
        const sortedTraders = tradersData.traders.sort((a: TraderEnhanced, b: TraderEnhanced) => {
          switch (sortBy) {
            case 'tp1_rate':
              return (b.tp1_rate || 0) - (a.tp1_rate || 0)
            case 'total_pnl':
              return (b.total_pnl || 0) - (a.total_pnl || 0)
            case 'total_signals':
              return (b.total_signals || 0) - (a.total_signals || 0)
            case 'profit_factor':
              return (b.profit_factor || 0) - (a.profit_factor || 0)
            default:
              return 0
          }
        })
        setTraders(sortedTraders)
      }
      
      // Получаем общую статистику
      const statsResponse = await fetch('/api/trader-observation?action=stats')
      const statsData = await statsResponse.json()
      setOverview(statsData.overview || {})
      
      // Получаем последние сигналы
      const signalsResponse = await fetch('/api/trader-observation?action=signals&limit=10')
      const signalsData = await signalsResponse.json()
      setRecentSignals(signalsData.signals || [])
      
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching trader data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const switchTraderMode = async (traderId: string, newMode: string) => {
    try {
      const response = await fetch('/api/trader-observation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'switch_mode',
          trader_id: traderId,
          mode: newMode
        })
      })
      
      if (response.ok) {
        await fetchData() // Refresh data
      }
    } catch (error) {
      console.error('Error switching trader mode:', error)
    }
  }

  // Utility functions
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600'
    if (pnl < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getModeVariant = (mode: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (mode) {
      case 'live': return 'destructive'
      case 'paper': return 'secondary'
      case 'observe': return 'outline'
      default: return 'default'
    }
  }

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'live': return 'bg-red-500'
      case 'paper': return 'bg-yellow-500'
      case 'observe': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  const getQualityColor = (quality: number) => {
    if (quality >= 80) return 'text-green-600'
    if (quality >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getTPRateColor = (rate: number) => {
    if (rate >= 70) return 'text-green-600 font-bold'
    if (rate >= 50) return 'text-yellow-600 font-semibold'
    if (rate >= 30) return 'text-orange-600'
    return 'text-red-600'
  }

  const formatTimeAgo = (dateString: string) => {
    if (!dateString) return 'Never'
    
    const now = new Date()
    const date = new Date(dateString)
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">📊 Честная Статистика Трейдеров</h1>
          <p className="text-gray-600 mt-1">Как у Дарена: полная статистика без фильтров</p>
        </div>
        <div className="text-sm text-gray-500">
          Last update: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex gap-2 mb-4">
        <span className="text-sm text-gray-600 flex items-center mr-4">Сортировать по:</span>
        {[
          { key: 'tp1_rate', label: 'TP1 Rate' },
          { key: 'total_pnl', label: 'Total P&L' },
          { key: 'profit_factor', label: 'Profit Factor' },
          { key: 'total_signals', label: 'Signals Count' }
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setSortBy(key as any)}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              sortBy === key 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Users className="w-4 h-4" />
              Active Traders
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {overview.active_traders || 0}
            </div>
            <div className="text-sm text-gray-600">
              of {overview.total_traders || 0} total
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Total Signals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {traders.reduce((sum, t) => sum + (t.total_signals || 0), 0)}
            </div>
            <div className="text-sm text-gray-600">
              Avg Quality: {Math.round(traders.reduce((sum, t) => sum + (t.signal_quality || 0), 0) / (traders.length || 1))}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Target className="w-4 h-4" />
              Total TP1 Hits
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {traders.reduce((sum, t) => sum + (t.tp1_count || 0), 0)}
            </div>
            <div className="text-sm text-gray-600">
              Avg Rate: {Math.round(traders.reduce((sum, t) => sum + (t.tp1_rate || 0), 0) / (traders.length || 1))}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Total P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getPnLColor(traders.reduce((sum, t) => sum + (t.total_pnl || 0), 0))}`}>
              {formatCurrency(traders.reduce((sum, t) => sum + (t.total_pnl || 0), 0))}
            </div>
            <div className="text-sm text-gray-600">
              Simulated
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Traders List with Enhanced Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Честная Статистика Трейдеров ({traders.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {traders.map((trader) => (
              <div
                key={trader.trader_id}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                  selectedTrader === trader.trader_id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
                onClick={() => setSelectedTrader(selectedTrader === trader.trader_id ? null : trader.trader_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${trader.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                    <div>
                      <div className="font-semibold">{trader.name}</div>
                      <div className="text-sm text-gray-600">{trader.source_handle}</div>
                      {/* ЧЕСТНАЯ СТАТИСТИКА КАК У ДАРЕНА */}
                      <div className="text-xs text-blue-600 font-mono mt-1 bg-blue-50 px-2 py-1 rounded">
                        📊 {trader.stats_summary || `${trader.executed_signals || trader.total_signals} сигналов: ${trader.tp1_count || 0} TP1 (${Math.round(trader.tp1_rate || 0)}%), ${trader.tp2_count || 0} TP2 (${Math.round(trader.tp2_rate || 0)}%), ${trader.sl_count || 0} SL (${Math.round(trader.sl_rate || 0)}%)`}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <Badge variant={getModeVariant(trader.mode)}>
                      {trader.mode}
                    </Badge>
                    
                    {/* Основные метрики */}
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {trader.total_signals} сигналов
                      </div>
                      <div className={`text-xs ${getQualityColor(trader.signal_quality || 0)}`}>
                        Качество: {trader.signal_quality || 0}%
                      </div>
                    </div>
                    
                    {/* TP1 Rate как основная метрика */}
                    <div className="text-right">
                      <div className={`text-lg font-bold ${getTPRateColor(trader.tp1_rate || 0)}`}>
                        {(trader.tp1_rate || 0).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">
                        TP1 Rate
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className={`text-sm font-medium ${getPnLColor(trader.total_pnl || 0)}`}>
                        {formatCurrency(trader.total_pnl || 0)}
                      </div>
                      <div className="text-xs text-gray-600">
                        PF: {(trader.profit_factor || 0).toFixed(2)}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-sm text-gray-600">
                        {formatTimeAgo(trader.last_signal_at)}
                      </div>
                      <div className="text-xs text-gray-600">
                        Conf: {(trader.avg_confidence || 0).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* РАСШИРЕННАЯ ДЕТАЛЬНАЯ СТАТИСТИКА КАК У ДАРЕНА */}
                {selectedTrader === trader.trader_id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    {/* Заголовок детальной статистики */}
                    <div className="mb-4">
                      <h4 className="font-semibold text-lg text-gray-800">📈 Детальная Статистика - {trader.name}</h4>
                      <p className="text-sm text-gray-600">Полный анализ как у Дарена без фильтров</p>
                    </div>
                    
                    {/* Базовые счетчики */}
                    <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm mb-4">
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="text-gray-600">Всего сигналов</div>
                        <div className="font-bold text-xl">{trader.total_signals}</div>
                        <div className="text-xs text-gray-500">Сырых сообщений</div>
                      </div>
                      <div className="bg-blue-50 p-3 rounded">
                        <div className="text-blue-600">Валидных</div>
                        <div className="font-bold text-xl text-blue-600">{trader.valid_signals || 0}</div>
                        <div className="text-xs text-gray-500">{trader.signal_quality || 0}% качества</div>
                      </div>
                      <div className="bg-purple-50 p-3 rounded">
                        <div className="text-purple-600">Исполнено</div>
                        <div className="font-bold text-xl text-purple-600">{trader.executed_signals || 0}</div>
                        <div className="text-xs text-gray-500">{trader.execution_rate || 0}% испол.</div>
                      </div>
                      
                      {/* Исходы как у Дарена */}
                      <div className="bg-green-50 p-3 rounded">
                        <div className="text-green-600">🎯 TP1 попаданий</div>
                        <div className="font-bold text-xl text-green-600">{trader.tp1_count || 0}</div>
                        <div className="text-xs text-gray-500">{(trader.tp1_rate || 0).toFixed(1)}%</div>
                      </div>
                      <div className="bg-blue-50 p-3 rounded">
                        <div className="text-blue-600">🎯🎯 TP2 попаданий</div>
                        <div className="font-bold text-xl text-blue-600">{trader.tp2_count || 0}</div>
                        <div className="text-xs text-gray-500">{(trader.tp2_rate || 0).toFixed(1)}%</div>
                      </div>
                      <div className="bg-red-50 p-3 rounded">
                        <div className="text-red-600">🛑 SL попаданий</div>
                        <div className="font-bold text-xl text-red-600">{trader.sl_count || 0}</div>
                        <div className="text-xs text-gray-500">{(trader.sl_rate || 0).toFixed(1)}%</div>
                      </div>
                    </div>
                    
                    {/* Финансовые показатели */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-t pt-4">
                      <div>
                        <div className="text-gray-600">💰 Общий P&L</div>
                        <div className={`font-bold text-lg ${getPnLColor(trader.total_pnl || 0)}`}>
                          {formatCurrency(trader.total_pnl || 0)}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">📊 Средний P&L</div>
                        <div className={`font-medium ${getPnLColor(trader.avg_pnl || 0)}`}>
                          {formatCurrency(trader.avg_pnl || 0)}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">📈 Средний выигрыш</div>
                        <div className="font-medium text-green-600">
                          {formatCurrency(trader.avg_win || 0)}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">📉 Средний проигрыш</div>
                        <div className="font-medium text-red-600">
                          -{formatCurrency(trader.avg_loss || 0)}
                        </div>
                      </div>
                    </div>
                    
                    {/* Временные показатели и качество */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-t pt-4 mt-4">
                      <div>
                        <div className="text-gray-600">⏱️ Время до TP1</div>
                        <div className="font-medium">
                          {trader.avg_time_to_tp1 ? `${trader.avg_time_to_tp1} мин` : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">⚖️ Profit Factor</div>
                        <div className={`font-bold ${(trader.profit_factor || 0) >= 1.5 ? 'text-green-600' : (trader.profit_factor || 0) >= 1.0 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {(trader.profit_factor || 0).toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">🕐 Последний сигнал</div>
                        <div className="font-medium">{formatTimeAgo(trader.last_signal_at)}</div>
                      </div>
                      <div>
                        <div className="text-gray-600">🎲 Avg Confidence</div>
                        <div className="font-medium">{(trader.avg_confidence || 0).toFixed(1)}%</div>
                      </div>
                    </div>
                    
                    {/* Действия */}
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          {['observe', 'paper', 'live'].map((mode) => (
                            <button
                              key={mode}
                              onClick={(e) => {
                                e.stopPropagation()
                                if (mode !== trader.mode) {
                                  switchTraderMode(trader.trader_id, mode)
                                }
                              }}
                              className={`px-3 py-2 text-xs rounded-md transition-colors font-medium ${
                                trader.mode === mode
                                  ? `${getModeColor(mode)} text-white`
                                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                              }`}
                              disabled={trader.mode === mode}
                            >
                              {mode.toUpperCase()}
                            </button>
                          ))}
                        </div>
                        
                        <div className="text-xs text-gray-600">
                          {trader.mode === 'live' && '🔴 LIVE TRADING ACTIVE'}
                          {trader.mode === 'paper' && '📝 Paper Trading'}
                          {trader.mode === 'observe' && '👁️ Observation Only'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
