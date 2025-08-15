"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Avatar, AvatarFallback } from './ui/avatar'

interface TraderStats {
  id: string
  name: string
  avatar?: string
  channel: string
  totalSignals: number
  winRate: number
  roi: number
  pnl: number
  avgHoldTime: string
  lastSignal: string
  status: 'active' | 'inactive'
  performance7d: number
  performance30d: number
  successfulTrades: number
  totalTrades: number
  maxDrawdown: number
  sharpeRatio: number
  totalVolume: number
  followers?: number
}

interface TradersData {
  traders: TraderStats[]
  summary: {
    totalTraders: number
    activeTraders: number
    totalSignals: number
    avgWinRate: number
    totalPnL: number
    bestPerformer: string
  }
  error?: string
}

const TradersDashboard: React.FC = () => {
  const [data, setData] = useState<TradersData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '60d' | '180d'>('180d')
  const [sortBy, setSortBy] = useState<'pnl' | 'winRate' | 'roi' | 'totalSignals'>('pnl')

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/traders?period=${selectedPeriod}&sortBy=${sortBy}&limit=20`)
      const result = await response.json()
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to fetch traders data')
      }
      
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      console.error('Error fetching traders:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [selectedPeriod, sortBy])

  const formatNumber = (num: number, decimals: number = 2) => {
    if (Math.abs(num) >= 1000000) {
      return `${(num / 1000000).toFixed(decimals)}M`
    } else if (Math.abs(num) >= 1000) {
      return `${(num / 1000).toFixed(decimals)}K`
    }
    return num.toFixed(decimals)
  }

  const formatCurrency = (amount: number) => {
    const sign = amount >= 0 ? '+' : ''
    return `${sign}${formatNumber(amount)} USD`
  }

  const getStatusColor = (status: string) => {
    return status === 'active' ? 'text-green-500' : 'text-gray-500'
  }

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-green-500' : 'text-red-500'
  }

  const renderSummaryCards = () => {
    if (!data?.summary) return null

    return (
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400">Общий P&L (USD)</div>
            <div className={`text-2xl font-bold ${getPnLColor(data.summary.totalPnL)}`}>
              {formatCurrency(data.summary.totalPnL)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Данные на {new Date().toLocaleDateString('ru-RU')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400">Торговый объём (USD)</div>
            <div className="text-2xl font-bold text-white">
              {formatNumber(data.traders.reduce((sum, t) => sum + t.totalVolume, 0))}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Данные на {new Date().toLocaleDateString('ru-RU')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400">P&L за сегодня (USD)</div>
            <div className="text-lg font-bold text-green-500">+1.79</div>
            <div className="text-xs text-gray-500 mt-1">
              Совпадает с предыдущим временем с 5:00 до 00:00 UTC. Последнее обновление: {new Date().toLocaleTimeString('ru-RU')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400">P&L за последние 7 дн. (USD)</div>
            <div className="text-lg font-bold text-red-500">-2.74</div>
            <div className="text-xs text-gray-500 mt-1">
              Данные на {new Date().toLocaleDateString('ru-RU')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400">Закрытые ордера</div>
            <div className="text-2xl font-bold text-white">1544</div>
            <div className="text-xs text-gray-500 mt-1">
              Данные на {new Date().toLocaleDateString('ru-RU')}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="text-sm text-gray-400">Закрытые позиции</div>
            <div className="text-2xl font-bold text-white">41%</div>
            <div className="text-xs text-gray-500 mt-1">
              Процент успешных сделок
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderPeriodTabs = () => (
    <div className="flex space-x-1 bg-gray-800 rounded-lg p-1 mb-4">
      {(['7d', '30d', '60d', '180d'] as const).map((period) => (
        <button
          key={period}
          onClick={() => setSelectedPeriod(period)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedPeriod === period
              ? 'bg-yellow-500 text-black'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          {period}
        </button>
      ))}
    </div>
  )

  const renderTraderRow = (trader: TraderStats, index: number) => (
    <tr key={trader.id} className="border-b border-gray-800 hover:bg-gray-800/50">
      <td className="px-4 py-3">
        <div className="flex items-center space-x-3">
          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-gray-700 text-white text-sm">
              {trader.avatar || trader.name.charAt(0)}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="font-medium text-white">{trader.name}</div>
            <div className="text-sm text-gray-400">{trader.channel}</div>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-center text-gray-300">{trader.totalSignals}</td>
      <td className="px-4 py-3 text-center text-gray-300">{trader.winRate.toFixed(1)}%</td>
      <td className="px-4 py-3 text-center text-gray-300">{trader.successfulTrades}</td>
      <td className="px-4 py-3 text-center">
        <span className={trader.roi >= 0 ? 'text-green-500' : 'text-red-500'}>
          {trader.roi > 0 ? '+' : ''}{trader.roi.toFixed(1)}%
        </span>
      </td>
      <td className="px-4 py-3 text-center">
        <span className={getPnLColor(trader.pnl)}>
          {formatCurrency(trader.pnl)}
        </span>
      </td>
      <td className="px-4 py-3 text-center text-gray-300">{trader.avgHoldTime}</td>
      <td className="px-4 py-3 text-center text-gray-300">{trader.lastSignal}</td>
      <td className="px-4 py-3 text-center">
        <Badge 
          variant={trader.status === 'active' ? 'default' : 'secondary'}
          className={trader.status === 'active' ? 'bg-green-600' : 'bg-gray-600'}
        >
          {trader.status === 'active' ? '🟢 растет' : '⚪ неактивен'}
        </Badge>
      </td>
      <td className="px-4 py-3 text-center text-gray-300">{(trader.sharpeRatio || 0).toFixed(1)}</td>
      <td className="px-4 py-3 text-center">
        <div className="flex space-x-2">
          <Button 
            size="sm" 
            variant="outline"
            className="bg-yellow-500 text-black border-yellow-500 hover:bg-yellow-600"
          >
            🔥 Активен
          </Button>
          <Button 
            size="sm" 
            variant="outline"
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            Включить
          </Button>
        </div>
      </td>
    </tr>
  )

  if (loading) {
    return (
      <div className="p-6 bg-gray-900 min-h-screen">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-6 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-700 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-gray-900 min-h-screen">
        <Card className="bg-red-900 border-red-700">
          <CardContent className="p-8 text-center">
            <div className="text-red-400 text-lg">❌ Error</div>
            <div className="text-sm text-red-300 mt-2">{error}</div>
            <Button 
              onClick={fetchData} 
              className="mt-4 bg-red-600 hover:bg-red-700"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <div className="flex items-center space-x-4 mb-2">
            <h1 className="text-2xl font-bold">СТАТИСТИКА ПО ТРЕЙДЕРАМ</h1>
            <Badge className="bg-yellow-500 text-black px-3 py-1">
              📊 ALL TRADERS
            </Badge>
          </div>
          <p className="text-gray-400">
            Пользовательский временной период • Все контракты
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      {renderSummaryCards()}

      {/* Period Tabs */}
      {renderPeriodTabs()}

      {/* Traders Table */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center justify-between">
            <span>Trader Ranking</span>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">Last Month</span>
              <select 
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-gray-800 border-gray-700 text-white text-sm rounded px-2 py-1"
              >
                <option value="pnl">P&L</option>
                <option value="winRate">Win Rate</option>
                <option value="roi">ROI</option>
                <option value="totalSignals">Signals</option>
              </select>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Name</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Кол-во сигналов</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Winrate</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">ROI ( сделки )</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">ROI% ( итого )</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">PNL $ (USD)</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Ср время удержания</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Последняя сделка</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Статус</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Трейд ROI</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Активация</th>
                </tr>
              </thead>
              <tbody>
                {data?.traders.map((trader, index) => renderTraderRow(trader, index))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Footer Stats */}
      {data?.summary && (
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-yellow-500">{data.summary.totalTraders}</div>
              <div className="text-sm text-gray-400">Total Traders</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-green-500">{data.summary.activeTraders}</div>
              <div className="text-sm text-gray-400">Active Now</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-blue-500">{data.summary.totalSignals}</div>
              <div className="text-sm text-gray-400">Total Signals</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-purple-500">{data.summary.avgWinRate.toFixed(1)}%</div>
              <div className="text-sm text-gray-400">Avg Win Rate</div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default TradersDashboard
