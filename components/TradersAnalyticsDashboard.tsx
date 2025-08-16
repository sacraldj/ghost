"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import TraderDetailModal from './TraderDetailModal'

interface TraderStats {
  trader_id: string
  name: string
  trades: number
  winrate: number
  roi_avg: number
  roi_year: number
  pnl_usdt: number
  max_dd: number
  tp1_rate: number
  tp2_rate: number
  sl_rate: number
  avg_duration: string
  trust: number
  trend: 'up' | 'down' | 'neutral'
  status: 'active' | 'inactive' | 'stopped'
  is_trading: boolean // Торгуем или только статистика
  last_signal: string
  start_date: string // Дата старта торговли
  capital: number // Капитал для торговли
}

interface OverallStats {
  total_pnl: number
  trading_volume: number
  pnl_today: number
  pnl_7d: number
  closed_orders: number
  closed_positions: number
  success_rate: number
  pnl_long: number
  pnl_short: number
}

const TradersAnalyticsDashboard: React.FC = () => {
  const [traders, setTraders] = useState<TraderStats[]>([])
  const [overallStats, setOverallStats] = useState<OverallStats | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState('180d')
  const [selectedTrader, setSelectedTrader] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [showOnlyTrading, setShowOnlyTrading] = useState(false)
  const [chartData, setChartData] = useState<any[]>([])
  const [selectedTraderModal, setSelectedTraderModal] = useState<string | null>(null)
  const [selectedStrategy, setSelectedStrategy] = useState<'all' | 'tp2_sl_be' | 'scalping' | 'swing'>('tp2_sl_be')
  const [showStrategyDropdown, setShowStrategyDropdown] = useState(false)

  const strategies = [
    { id: 'tp2_sl_be', label: 'TP2 & SL → BE', icon: '📈', description: 'Два тейк-профита, стоп в безубыток' },
    { id: 'scalping', label: 'Scalping', icon: '⚡', description: 'Быстрые сделки, малый профит' },
    { id: 'swing', label: 'Swing Trading', icon: '🎯', description: 'Средне-срочные позиции' },
    { id: 'all', label: 'Все стратегии', icon: '🔄', description: 'Смешанная торговля' }
  ]

  const periods = [
    { id: '7d', label: '7d' },
    { id: '30d', label: '30d' },
    { id: '60d', label: '60d' },
    { id: '90d', label: '90d' },
    { id: '180d', label: '180d' },
    { id: 'all', label: 'Пользовательский срок' }
  ]

  useEffect(() => {
    loadData()
  }, [selectedPeriod, selectedTrader, showOnlyTrading, selectedStrategy])

  // Закрываем dropdown при клике вне его
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.strategy-dropdown')) {
        setShowStrategyDropdown(false)
      }
    }

    if (showStrategyDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showStrategyDropdown])

  const loadData = async () => {
    setLoading(true)
    try {
      // Загружаем общую статистику с учётом стратегии
      const statsResponse = await fetch(`/api/traders-analytics/summary?period=${selectedPeriod}&trader=${selectedTrader}&trading_only=${showOnlyTrading}&strategy=${selectedStrategy}`)
      const statsData = await statsResponse.json()
      setOverallStats(statsData)

      // Загружаем список трейдеров с пересчётом ROI для выбранной стратегии
      const tradersResponse = await fetch(`/api/traders-analytics/list?period=${selectedPeriod}&trading_only=${showOnlyTrading}&strategy=${selectedStrategy}`)
      const tradersData = await tradersResponse.json()
      setTraders(tradersData.traders || [])

      // Загружаем данные для графика P&L
      const chartResponse = await fetch(`/api/traders-analytics/chart?period=${selectedPeriod}&trader=${selectedTrader}&strategy=${selectedStrategy}`)
      const chartData = await chartResponse.json()
      setChartData(chartData.data || [])

    } catch (error) {
      console.error('Error loading traders analytics:', error)
    }
    setLoading(false)
  }

  const handleStrategyChange = (strategyId: string) => {
    setSelectedStrategy(strategyId as any)
    setShowStrategyDropdown(false)
  }

  const getCurrentStrategy = () => {
    return strategies.find(s => s.id === selectedStrategy) || strategies[0]
  }

  const toggleTraderStatus = async (traderId: string, action: 'enable' | 'disable') => {
    try {
      await fetch(`/api/traders-analytics/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trader_id: traderId, action })
      })
      loadData() // Перезагружаем данные
    } catch (error) {
      console.error('Error toggling trader status:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-500 text-white">🔥 Активен</Badge>
      case 'inactive':
        return <Badge className="bg-yellow-500 text-black">🟡 Нестабильный</Badge>
      case 'stopped':
        return <Badge className="bg-red-500 text-white">🛑 Остановлен</Badge>
      default:
        return <Badge className="bg-gray-500 text-white">⚪️ Новый</Badge>
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '📈'
      case 'down': return '📉'
      default: return '➖'
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded mb-4"></div>
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-32 bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-700 rounded mb-6"></div>
          <div className="h-96 bg-gray-700 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 bg-black text-white">
      {/* Заголовок с фильтрами как на скрине */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium">
            СТАТИСТИКА ПО ТРЕЙДЕРАМ
          </div>
          <div className="relative strategy-dropdown">
            <button
              onClick={() => setShowStrategyDropdown(!showStrategyDropdown)}
              className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg font-medium flex items-center space-x-2 transition-colors cursor-pointer"
            >
              <span>{getCurrentStrategy().icon}</span>
              <span>{getCurrentStrategy().label}</span>
              <span className="ml-2">▼</span>
            </button>
            
            {showStrategyDropdown && (
              <div className="absolute top-full left-0 mt-2 w-80 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50">
                <div className="p-2">
                  <div className="text-xs text-gray-400 mb-2 px-2">Выберите торговую стратегию:</div>
                  {strategies.map((strategy) => (
                    <button
                      key={strategy.id}
                      onClick={() => handleStrategyChange(strategy.id)}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        selectedStrategy === strategy.id
                          ? 'bg-yellow-500 text-black'
                          : 'bg-gray-700 hover:bg-gray-600 text-white'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{strategy.icon}</span>
                        <div>
                          <div className="font-medium">{strategy.label}</div>
                          <div className="text-xs opacity-75">{strategy.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-400">Бессрочные и фьючерсы</label>
            <select className="bg-gray-800 border border-gray-600 rounded px-3 py-1 text-sm">
              <option>Все контракты</option>
            </select>
          </div>
          
          <Button 
            variant={showOnlyTrading ? "default" : "outline"}
            onClick={() => setShowOnlyTrading(!showOnlyTrading)}
            className="text-sm"
          >
            {showOnlyTrading ? "Торгуем" : "Все трейдеры"}
          </Button>
        </div>
      </div>

      {/* Фильтры периодов как на скрине */}
      <div className="flex items-center space-x-2 mb-6">
        {periods.map((period) => (
          <button
            key={period.id}
            onClick={() => setSelectedPeriod(period.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedPeriod === period.id
                ? 'bg-yellow-500 text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {period.label}
          </button>
        ))}
        
        <div className="text-sm text-gray-400 ml-4">
          Данные на 2025-08-14 23:59:59 UTC
        </div>
      </div>

      {/* Верхние карточки статистики как на скрине */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400 mb-1">Общий P&L (USD)</div>
            <div className={`text-2xl font-bold ${(overallStats?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {(overallStats?.total_pnl || 0) >= 0 ? '+' : ''}{(overallStats?.total_pnl || 0).toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Данные на 2025-08-14 23:59:59 UTC
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400 mb-1">Торговый объём (USD)</div>
            <div className="text-2xl font-bold text-white">
              {(overallStats?.trading_volume || 0).toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Данные на 2025-08-14 23:59:59 UTC
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400 mb-1">P&L за сегодня (USD)</div>
            <div className={`text-lg font-bold ${(overallStats?.pnl_today || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {(overallStats?.pnl_today || 0) >= 0 ? '+' : ''}{(overallStats?.pnl_today || 0).toFixed(2)}
            </div>
            <div className="text-sm text-gray-400 mt-1">P&L за последние 7 дн. (USD)</div>
            <div className={`text-sm font-medium ${(overallStats?.pnl_7d || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {(overallStats?.pnl_7d || 0) >= 0 ? '+' : ''}{(overallStats?.pnl_7d || 0).toFixed(2)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400 mb-1">Закрытые ордера</div>
            <div className="text-2xl font-bold text-white">
              {overallStats?.closed_orders || 0}
            </div>
            <div className="text-sm text-gray-400 mt-1">Закрытые позиции</div>
            <div className="text-lg font-medium text-white">
              {overallStats?.closed_positions || 0}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Процент успешных сделок: {(overallStats?.success_rate || 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* График P&L по времени */}
      <Card className="bg-gray-900 border-gray-800 mb-6">
        <CardHeader>
          <CardTitle className="text-white">График P&L</CardTitle>
          <div className="text-sm text-gray-400">2025-07-03 (UTC)</div>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-800 rounded">
            <div className="text-gray-400">График P&L (будет реализован с реальными данными)</div>
          </div>
        </CardContent>
      </Card>

      {/* Таблица трейдеров как на скрине */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <CardTitle className="text-white">Trader Ranking</CardTitle>
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-gray-400">Стратегия:</span>
                <div className="bg-gray-700 px-2 py-1 rounded text-white text-xs">
                  {getCurrentStrategy().icon} {getCurrentStrategy().label}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-gray-400">Last Month</span>
              <select className="bg-gray-800 border border-gray-600 rounded px-2 py-1">
                <option>Last Month</option>
                <option>Last Week</option>
                <option>All Time</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400">
                  <th className="text-left p-3">Name</th>
                  <th className="text-right p-3">Кол сделок</th>
                  <th className="text-right p-3">Winrate</th>
                  <th className="text-right p-3">ROI Ср%</th>
                  <th className="text-right p-3">ROI Год%</th>
                  <th className="text-right p-3">P&L (USDT)</th>
                  <th className="text-right p-3">Сд время сделки</th>
                  <th className="text-center p-3">Последняя сделка</th>
                  <th className="text-center p-3">Тренд ROI</th>
                  <th className="text-center p-3">Trust</th>
                  <th className="text-center p-3">Старт</th>
                  <th className="text-center p-3">Капитал</th>
                  <th className="text-center p-3">Активация</th>
                </tr>
              </thead>
              <tbody>
                {traders.map((trader, index) => (
                  <tr key={trader.trader_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                    <td className="p-3">
                      <div 
                        className="flex items-center space-x-3 cursor-pointer hover:bg-gray-800/50 rounded-lg p-2 -m-2 transition-colors"
                        onClick={() => setSelectedTraderModal(trader.trader_id)}
                      >
                        <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                          {trader.name.substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div className="text-white font-medium hover:text-yellow-400 transition-colors">{trader.name}</div>
                          <div className="text-xs text-gray-400">{trader.trader_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="text-right p-3 text-white">{trader.trades}</td>
                    <td className="text-right p-3 text-white">{trader.winrate.toFixed(1)}%</td>
                    <td className="text-right p-3 text-white">{trader.roi_avg > 0 ? '+' : ''}{trader.roi_avg.toFixed(2)}%</td>
                    <td className="text-right p-3 text-white">{trader.roi_year > 0 ? '+' : ''}{trader.roi_year.toFixed(1)}%</td>
                    <td className={`text-right p-3 font-medium ${trader.pnl_usdt >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trader.pnl_usdt > 0 ? '+' : ''}{trader.pnl_usdt.toFixed(2)}
                    </td>
                    <td className="text-right p-3 text-white">{trader.avg_duration}</td>
                    <td className="text-center p-3 text-gray-400 text-xs">{trader.last_signal}</td>
                    <td className="text-center p-3">{getTrendIcon(trader.trend)}</td>
                    <td className="text-center p-3 text-white">{trader.trust}%</td>
                    <td className="text-center p-3 text-gray-400 text-xs">
                      {trader.start_date || '2025-08-15'}
                    </td>
                    <td className="text-center p-3 text-green-400 font-medium">
                      ${(trader.capital || 10000).toLocaleString()}
                    </td>
                    <td className="text-center p-3">
                      {trader.is_trading ? (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => toggleTraderStatus(trader.trader_id, 'disable')}
                          className="bg-green-600 border-green-600 text-white hover:bg-green-700"
                        >
                          Включить
                        </Button>
                      ) : (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => toggleTraderStatus(trader.trader_id, 'enable')}
                          className="bg-gray-600 border-gray-600 text-white hover:bg-gray-700"
                        >
                          Выключить
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Модальное окно детальной информации о трейдере */}
      <TraderDetailModal
        traderId={selectedTraderModal || ''}
        isOpen={!!selectedTraderModal}
        onClose={() => setSelectedTraderModal(null)}
      />
    </div>
  )
}

export default TradersAnalyticsDashboard