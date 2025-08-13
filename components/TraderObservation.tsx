'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Eye, Play, Zap, Users, TrendingUp, TrendingDown, Clock, Target, BarChart3, Settings } from 'lucide-react'

interface Trader {
  trader_id: string
  name: string
  source_type: string
  source_handle: string
  mode: 'observe' | 'paper' | 'live'
  is_active: boolean
  total_signals: number
  winrate_30d: number
  pnl_30d: number
  last_signal_at: string
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

export default function TraderObservation() {
  const [traders, setTraders] = useState<Trader[]>([])
  const [recentSignals, setRecentSignals] = useState<Signal[]>([])
  const [overview, setOverview] = useState<any>({})
  const [selectedTrader, setSelectedTrader] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    fetchData()
    
    // Обновление каждые 30 секунд
    const interval = setInterval(fetchData, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      // Получаем трейдеров
      const tradersResponse = await fetch('/api/trader-observation?action=traders')
      const tradersData = await tradersResponse.json()
      setTraders(tradersData.traders || [])

      // Получаем общую статистику
      const statsResponse = await fetch('/api/trader-observation?action=stats')
      const statsData = await statsResponse.json()
      setOverview(statsData.overview || {})

      // Получаем последние сигналы
      const signalsResponse = await fetch('/api/trader-observation?action=signals&limit=10')
      const signalsData = await signalsResponse.json()
      setRecentSignals(signalsData.signals || [])

      setLastUpdate(new Date())
      setIsLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setIsLoading(false)
    }
  }

  const switchTraderMode = async (trader_id: string, mode: string) => {
    try {
      const response = await fetch('/api/trader-observation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'switch_mode',
          trader_id,
          mode
        })
      })

      if (response.ok) {
        // Обновляем данные
        fetchData()
      }
    } catch (error) {
      console.error('Error switching trader mode:', error)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(1)}%`
  }

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'observe': return <Eye className="w-4 h-4" />
      case 'paper': return <Play className="w-4 h-4" />
      case 'live': return <Zap className="w-4 h-4" />
      default: return <Eye className="w-4 h-4" />
    }
  }

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'observe': return 'bg-blue-500'
      case 'paper': return 'bg-yellow-500'
      case 'live': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getPnLColor = (value: number) => {
    if (value > 0) return 'text-green-600'
    if (value < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getOutcomeColor = (result: string) => {
    switch (result) {
      case 'TP1_ONLY':
      case 'TP2_FULL': return 'text-green-600'
      case 'SL': return 'text-red-600'
      case 'BE_EXIT': return 'text-yellow-600'
      default: return 'text-gray-600'
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Trader Observation System</h1>
        <div className="text-sm text-gray-500">
          Last update: {lastUpdate.toLocaleTimeString()}
        </div>
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
              <BarChart3 className="w-4 h-4" />
              Today's Signals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {overview.total_signals_today || 0}
            </div>
            <div className="text-sm text-gray-600">
              Avg WR: {formatPercentage(overview.avg_winrate || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Today's P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getPnLColor(overview.total_pnl_today || 0)}`}>
              {formatCurrency(overview.total_pnl_today || 0)}
            </div>
            <div className="text-sm text-gray-600">
              Simulated
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Target className="w-4 h-4" />
              Modes Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 text-sm">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                {overview.modes?.observe || 0}
              </span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                {overview.modes?.paper || 0}
              </span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                {overview.modes?.live || 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Traders Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Traders ({traders.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {traders.map((trader) => (
              <div 
                key={trader.trader_id} 
                className={`border rounded-lg p-4 transition-colors ${
                  selectedTrader === trader.trader_id ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedTrader(
                  selectedTrader === trader.trader_id ? null : trader.trader_id
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white ${
                      trader.is_active ? 'bg-green-500' : 'bg-gray-400'
                    }`}>
                      {getModeIcon(trader.mode)}
                    </div>
                    <div>
                      <h4 className="font-medium">{trader.name}</h4>
                      <p className="text-sm text-gray-600">{trader.source_handle}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className={`font-semibold ${getPnLColor(trader.pnl_30d)}`}>
                        {formatCurrency(trader.pnl_30d)}
                      </div>
                      <div className="text-sm text-gray-600">
                        WR: {formatPercentage(trader.winrate_30d)}
                      </div>
                    </div>
                    
                    <Badge className={`${getModeColor(trader.mode)} text-white`}>
                      {trader.mode.toUpperCase()}
                    </Badge>
                  </div>
                </div>
                
                <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Signals (30d):</span>
                    <span className="ml-2 font-medium">{trader.total_signals}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Source:</span>
                    <span className="ml-2 font-medium capitalize">{trader.source_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Status:</span>
                    <span className={`ml-2 font-medium ${trader.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                      {trader.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Last Signal:</span>
                    <span className="ml-2 font-medium">
                      {new Date(trader.last_signal_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                
                {/* Mode Switch Buttons */}
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
                          className={`px-3 py-1 text-xs rounded-md transition-colors ${
                            trader.mode === mode
                              ? `${getModeColor(mode)} text-white`
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {getModeIcon(mode)}
                          <span className="ml-1 capitalize">{mode}</span>
                        </button>
                      ))}
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        // Здесь можно открыть модальное окно настроек
                      }}
                      className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 transition-colors"
                    >
                      <Settings className="w-3 h-3 inline mr-1" />
                      Settings
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Signals */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Recent Signals ({recentSignals.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentSignals.map((signal) => (
              <div key={signal.signal_id} className="border rounded-lg p-3 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant={signal.side === 'BUY' ? 'default' : 'secondary'}>
                      {signal.symbol}
                    </Badge>
                    <Badge variant="outline">
                      {signal.side}
                    </Badge>
                    <span className="text-sm text-gray-600">
                      by {traders.find(t => t.trader_id === signal.trader_id)?.name}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      {signal.outcome && (
                        <>
                          <div className={`font-semibold ${getPnLColor(signal.outcome.pnl_sim)}`}>
                            {formatCurrency(signal.outcome.pnl_sim)}
                          </div>
                          <div className={`text-sm ${getOutcomeColor(signal.outcome.final_result)}`}>
                            {signal.outcome.final_result}
                          </div>
                        </>
                      )}
                    </div>
                    
                    <div className="text-right text-sm text-gray-600">
                      <div>Confidence: {signal.confidence.toFixed(1)}%</div>
                      <div>{new Date(signal.posted_at).toLocaleTimeString()}</div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-2 grid grid-cols-4 gap-4 text-xs text-gray-600">
                  <div>Entry: {signal.entry.toFixed(4)}</div>
                  {signal.tp1 && <div>TP1: {signal.tp1.toFixed(4)}</div>}
                  {signal.tp2 && <div>TP2: {signal.tp2.toFixed(4)}</div>}
                  {signal.sl && <div>SL: {signal.sl.toFixed(4)}</div>}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
