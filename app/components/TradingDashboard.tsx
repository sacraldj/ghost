'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'
import { Badge } from '@/app/components/ui/badge'
import { TrendingUp, TrendingDown, DollarSign, Clock, Target, AlertTriangle } from 'lucide-react'

interface ActiveTrade {
  id: string
  trade_id: string
  symbol: string
  side: 'Buy' | 'Sell'
  real_entry_price: number
  position_qty: number
  margin_used: number
  leverage: number
  tp1_price?: number
  tp2_price?: number
  sl_price?: number
  opened_at: string
  current_price?: number
  unrealized_pnl?: number
  unrealized_roi?: number
  time_in_trade?: string
  distance_to_tp1?: number
  distance_to_tp2?: number
  distance_to_sl?: number
}

interface LivePnLData {
  total_unrealized_pnl: number
  total_realized_pnl_today: number
  total_portfolio_value: number
  active_trades_count: number
  win_rate_today: number
  avg_trade_duration: string
}

export default function TradingDashboard() {
  const [livePnL, setLivePnL] = useState<LivePnLData>({
    total_unrealized_pnl: 0,
    total_realized_pnl_today: 0,
    total_portfolio_value: 1000, // Default balance
    active_trades_count: 0,
    win_rate_today: 0,
    avg_trade_duration: '0h 0m'
  })
  
  const [activeTrades, setActiveTrades] = useState<ActiveTrade[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  // Fetch active trades and calculate live PnL
  const fetchLiveData = async () => {
    try {
      // Fetch active trades from database
      const tradesResponse = await fetch('/api/trades/active')
      const trades: ActiveTrade[] = await tradesResponse.json()

      // Fetch live prices for each symbol
      const symbols = [...new Set(trades.map(t => t.symbol))]
      
      let priceMap: Record<string, number> = {}
      
      if (symbols.length > 0) {
        try {
          const response = await fetch('/api/prices/live', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbols })
          })
          const data = await response.json()
          
          if (data.prices) {
            priceMap = data.prices.reduce((acc: Record<string, number>, item: any) => {
              acc[item.symbol] = item.price
              return acc
            }, {})
          }
        } catch (error) {
          console.error('Error fetching live prices:', error)
          // Fallback: use entry prices
          priceMap = trades.reduce((acc, trade) => {
            acc[trade.symbol] = trade.real_entry_price
            return acc
          }, {} as Record<string, number>)
        }
      }

      // Calculate unrealized PnL for each trade
      const tradesWithPnL = trades.map(trade => {
        const currentPrice = priceMap[trade.symbol] || trade.real_entry_price
        const priceChange = currentPrice - trade.real_entry_price
        const direction = trade.side === 'Buy' ? 1 : -1
        const unrealizedPnL = priceChange * trade.position_qty * direction
        const unrealizedROI = trade.margin_used > 0 ? (unrealizedPnL / trade.margin_used) * 100 : 0
        
        // Calculate time in trade
        const openTime = new Date(trade.opened_at)
        const now = new Date()
        const diffMs = now.getTime() - openTime.getTime()
        const hours = Math.floor(diffMs / (1000 * 60 * 60))
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
        const timeInTrade = `${hours}h ${minutes}m`

        // Calculate distance to levels
        const distanceToTP1 = trade.tp1_price ? ((trade.tp1_price - currentPrice) / currentPrice * 100) * direction : null
        const distanceToTP2 = trade.tp2_price ? ((trade.tp2_price - currentPrice) / currentPrice * 100) * direction : null
        const distanceToSL = trade.sl_price ? ((trade.sl_price - currentPrice) / currentPrice * 100) * direction : null

        return {
          ...trade,
          current_price: currentPrice,
          unrealized_pnl: unrealizedPnL,
          unrealized_roi: unrealizedROI,
          time_in_trade: timeInTrade,
          distance_to_tp1: distanceToTP1,
          distance_to_tp2: distanceToTP2,
          distance_to_sl: distanceToSL
        }
      })

      // Calculate aggregate metrics
      const totalUnrealizedPnL = tradesWithPnL.reduce((sum, trade) => sum + (trade.unrealized_pnl || 0), 0)
      
      // Fetch today's realized PnL
      const todayResponse = await fetch('/api/trades/today-stats')
      const todayStats = await todayResponse.json()

      setActiveTrades(tradesWithPnL)
      setLivePnL({
        total_unrealized_pnl: totalUnrealizedPnL,
        total_realized_pnl_today: todayStats.realized_pnl || 0,
        total_portfolio_value: livePnL.total_portfolio_value + totalUnrealizedPnL,
        active_trades_count: tradesWithPnL.length,
        win_rate_today: todayStats.win_rate || 0,
        avg_trade_duration: todayStats.avg_duration || '0h 0m'
      })
      
      setLastUpdate(new Date())
      setIsLoading(false)
    } catch (error) {
      console.error('Error fetching live data:', error)
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchLiveData()
    
    // Update every 10 seconds
    const interval = setInterval(fetchLiveData, 10000)
    
    return () => clearInterval(interval)
  }, [])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`
  }

  const getPnLColor = (value: number) => {
    if (value > 0) return 'text-green-600'
    if (value < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getROIBadgeColor = (roi: number) => {
    if (roi > 5) return 'bg-green-500'
    if (roi > 0) return 'bg-green-400'
    if (roi > -5) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700/50 rounded-xl w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gradient-to-br from-gray-800/50 to-gray-700/30 rounded-2xl"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header in Test Table style */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-4 border border-gray-800/50">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-white">💹 Live Trading Overview</h2>
            <p className="text-gray-400 text-sm mt-1">
              Real-time portfolio performance and active positions
            </p>
          </div>
          <div className="text-xs text-gray-400">
            🕒 Last update: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Live PnL Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Live PnL */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/50 shadow-lg relative overflow-hidden">
          <div className="pb-2">
            <div className="text-sm font-medium text-gray-300 flex items-center gap-2">
              🔴 LIVE P&L
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            </div>
          </div>
          <div>
            <div className={`text-2xl font-bold ${getPnLColor(livePnL.total_unrealized_pnl)}`}>
              {formatCurrency(livePnL.total_unrealized_pnl)}
            </div>
            <div className={`text-sm ${getPnLColor(livePnL.total_unrealized_pnl)}`}>
              {formatPercentage((livePnL.total_unrealized_pnl / livePnL.total_portfolio_value) * 100)}
            </div>
          </div>
        </div>

        {/* Today's Realized */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/50 shadow-lg">
          <div className="pb-2">
            <div className="text-sm font-medium text-gray-300 flex items-center gap-2">
              💰 Today Realized
            </div>
          </div>
          <div>
            <div className={`text-2xl font-bold ${getPnLColor(livePnL.total_realized_pnl_today)}`}>
              {formatCurrency(livePnL.total_realized_pnl_today)}
            </div>
            <div className="text-sm text-gray-400">
              📊 Win Rate: {livePnL.win_rate_today.toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Active Trades */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/50 shadow-lg">
          <div className="pb-2">
            <div className="text-sm font-medium text-gray-300 flex items-center gap-2">
              🎯 Active Trades
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {livePnL.active_trades_count}
            </div>
            <div className="text-sm text-gray-400">
              ⏱️ Avg: {livePnL.avg_trade_duration}
            </div>
          </div>
        </div>

        {/* Portfolio Value */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/50 shadow-lg">
          <div className="pb-2">
            <div className="text-sm font-medium text-gray-300 flex items-center gap-2">
              📈 Portfolio
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {formatCurrency(livePnL.total_portfolio_value)}
            </div>
            <div className="text-sm text-gray-400">
              💎 Total Value
            </div>
          </div>
        </div>
      </div>

      {/* Active Trades Table */}
      <div className="bg-gradient-to-br from-gray-900/30 to-gray-800/20 backdrop-blur-sm rounded-2xl border border-gray-700/30 shadow-lg">
        <div className="p-4 border-b border-gray-700/30">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-white">🎯 Active Trades ({activeTrades.length})</h3>
          </div>
        </div>
        <div className="p-4">
          {activeTrades.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              📭 No active trades
            </div>
          ) : (
            <div className="space-y-4">
              {activeTrades.map((trade) => (
                <div key={trade.id} className="bg-gradient-to-br from-gray-800/50 to-gray-700/30 rounded-xl p-4 border border-gray-700/50 hover:border-gray-600/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant={trade.side === 'Buy' ? 'default' : 'secondary'}>
                        {trade.symbol}
                      </Badge>
                      <Badge variant="outline">
                        {trade.side} {trade.leverage}x
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={`text-lg font-bold ${getPnLColor(trade.unrealized_pnl || 0)}`}>
                        {formatCurrency(trade.unrealized_pnl || 0)}
                      </div>
                      <Badge className={`${getROIBadgeColor(trade.unrealized_roi || 0)} text-white`}>
                        {formatPercentage(trade.unrealized_roi || 0)}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-500">Entry / Current</div>
                      <div className="font-medium">
                        {trade.real_entry_price.toFixed(4)} / {trade.current_price?.toFixed(4)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-500">Size / Margin</div>
                      <div className="font-medium">
                        {trade.position_qty} / {formatCurrency(trade.margin_used)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-500">Time in Trade</div>
                      <div className="font-medium flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {trade.time_in_trade}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-500">Distance to Levels</div>
                      <div className="font-medium text-xs space-x-2">
                        {trade.distance_to_tp1 !== null && (
                          <span className="text-green-600">
                            TP1: {trade.distance_to_tp1.toFixed(1)}%
                          </span>
                        )}
                        {trade.distance_to_sl !== null && (
                          <span className="text-red-600">
                            SL: {Math.abs(trade.distance_to_sl).toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
