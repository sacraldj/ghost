'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Shield,
  Activity,
  AlertTriangle,
  Clock,
  BarChart3,
  PieChart,
  Zap,
  Users,
  Brain
} from 'lucide-react'

interface PortfolioSnapshotData {
  // Top KPIs
  aum: number
  equity: number
  pnl_mtd: number
  pnl_ytd: number
  win_rate: number
  exposure_net: number
  leverage: number
  long_exposure: number
  short_exposure: number
  
  // Active Positions
  active_positions: {
    count: number
    total_risk: number
    positions: Array<{
      id: string
      symbol: string
      side: string
      qty: number
      entry_price: number
      tp1_price?: number
      tp2_price?: number
      sl_price?: number
      roi_current: number
      risk_usd: number
      timer_seconds: number
      margin_used: number
      leverage: number
    }>
  }
  
  // Risk Snapshot
  risk_snapshot: {
    var_1d: number
    expected_shortfall_1d: number
    max_drawdown_mtd: number
    portfolio_volatility: number
  }
  
  // Performance Attribution
  performance_attribution: {
    by_strategy: Array<{
      strategy_id: string
      pnl_30d: number
      win_rate: number
      trades_count: number
    }>
    by_symbol: Array<{
      symbol: string
      pnl_30d: number
      trades_count: number
    }>
    by_exit_type: {
      tp1_pnl: number
      tp2_pnl: number
      sl_pnl: number
      manual_pnl: number
    }
  }
  
  // Execution Metrics
  execution_metrics: {
    signal_to_open_p50: number
    signal_to_open_p95: number
    entry_slippage_avg: number
    exit_slippage_avg: number
    fill_rate: number
  }
  
  // Recent Trades
  recent_trades: Array<{
    id: string
    symbol: string
    side: string
    exit_reason: string
    roi_final: number
    roi_tp1?: number
    roi_tp2?: number
    fees: number
    pnl_net: number
    opened_at: string
    closed_at: string
  }>
  
  // Cross Analysis with News
  news_correlation: {
    news_driven_trades_30d: number
    avg_news_impact_score: number
    news_accuracy: number
    recent_news_trades: Array<{
      symbol: string
      news_title: string
      predicted_impact: number
      actual_roi: number
      accuracy_score: number
      timestamp: string
    }>
  }
  
  timestamp: string
}

export default function PortfolioSnapshot() {
  const [data, setData] = useState<PortfolioSnapshotData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      const response = await fetch('/api/portfolio-snapshot')
      const result = await response.json()
      
      if (result.success) {
        setData(result.data)
      } else {
        setError(result.error || 'Failed to fetch portfolio data')
      }
    } catch (err) {
      setError('Network error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const formatNumber = (num: number, decimals = 2) => {
    if (Math.abs(num) >= 1000000) {
      return `$${(num / 1000000).toFixed(1)}M`
    } else if (Math.abs(num) >= 1000) {
      return `$${(num / 1000).toFixed(1)}K`
    }
    return `$${num.toFixed(decimals)}`
  }

  const formatPercent = (num: number) => `${num.toFixed(2)}%`

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-24" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass rounded-xl p-6 border border-red-500/20">
        <div className="flex items-center space-x-2 text-red-400">
          <AlertTriangle className="w-5 h-5" />
          <span>Ошибка загрузки портфеля: {error}</span>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      {/* Top KPIs Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* AUM / Equity */}
        <motion.div 
          className="glass rounded-xl p-6 border border-emerald-500/20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">AUM / Equity</p>
              <p className="text-2xl font-bold text-white">{formatNumber(data.equity)}</p>
              <p className="text-emerald-400 text-sm">Base: {formatNumber(data.aum)}</p>
            </div>
            <DollarSign className="w-8 h-8 text-emerald-500" />
          </div>
        </motion.div>

        {/* P&L MTD/YTD */}
        <motion.div 
          className="glass rounded-xl p-6 border border-blue-500/20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">P&L (MTD/YTD)</p>
              <p className={`text-2xl font-bold ${data.pnl_mtd >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {data.pnl_mtd >= 0 ? '+' : ''}{formatNumber(data.pnl_mtd)}
              </p>
              <p className={`text-sm ${data.pnl_ytd >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                YTD: {data.pnl_ytd >= 0 ? '+' : ''}{formatNumber(data.pnl_ytd)}
              </p>
            </div>
            {data.pnl_mtd >= 0 ? 
              <TrendingUp className="w-8 h-8 text-emerald-500" /> : 
              <TrendingDown className="w-8 h-8 text-red-500" />
            }
          </div>
        </motion.div>

        {/* Win Rate */}
        <motion.div 
          className="glass rounded-xl p-6 border border-purple-500/20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Win Rate</p>
              <p className="text-2xl font-bold text-white">{formatPercent(data.win_rate)}</p>
              <p className="text-purple-400 text-sm">Overall Performance</p>
            </div>
            <Target className="w-8 h-8 text-purple-500" />
          </div>
        </motion.div>

        {/* Exposure / Leverage */}
        <motion.div 
          className="glass rounded-xl p-6 border border-orange-500/20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Exposure / Leverage</p>
              <p className="text-2xl font-bold text-white">
                Net: {formatPercent(data.exposure_net)}
              </p>
              <p className="text-orange-400 text-sm">Lev: {data.leverage.toFixed(1)}x</p>
            </div>
            <Activity className="w-8 h-8 text-orange-500" />
          </div>
        </motion.div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Positions */}
        <motion.div 
          className="glass rounded-xl p-6"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <Users className="w-5 h-5 mr-2 text-blue-500" />
              Active Positions
            </h3>
            <div className="text-right">
              <p className="text-white font-semibold">Count: {data.active_positions.count}</p>
              <p className="text-gray-400 text-sm">Risk: {formatNumber(data.active_positions.total_risk)}</p>
            </div>
          </div>
          
          {data.active_positions.positions.length > 0 ? (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {data.active_positions.positions.map((position) => (
                <div key={position.id} className="bg-white/5 rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-semibold text-white">{position.symbol}</span>
                      <span className={`ml-2 px-2 py-1 rounded text-xs ${
                        position.side === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {position.side}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${position.roi_current >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {position.roi_current >= 0 ? '+' : ''}{formatPercent(position.roi_current)}
                      </p>
                      <p className="text-gray-400 text-xs">{formatNumber(position.risk_usd)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-400 text-center py-8">Нет активных позиций</div>
          )}
        </motion.div>

        {/* Risk Snapshot */}
        <motion.div 
          className="glass rounded-xl p-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Shield className="w-5 h-5 mr-2 text-orange-500" />
            Risk Snapshot
          </h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">VaR(1d)</span>
              <span className="text-white font-semibold">{formatNumber(data.risk_snapshot.var_1d)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">ES(1d)</span>
              <span className="text-white font-semibold">{formatNumber(data.risk_snapshot.expected_shortfall_1d)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Max DD (MTD)</span>
              <span className="text-red-400 font-semibold">{formatNumber(data.risk_snapshot.max_drawdown_mtd)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Volatility</span>
              <span className="text-white font-semibold">{formatNumber(data.risk_snapshot.portfolio_volatility)}</span>
            </div>
          </div>
        </motion.div>

        {/* Performance Attribution */}
        <motion.div 
          className="glass rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-purple-500" />
            Performance Attribution (30d)
          </h3>
          
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-2">By Symbol</h4>
              <div className="space-y-1">
                {data.performance_attribution.by_symbol.slice(0, 5).map((item) => (
                  <div key={item.symbol} className="flex justify-between items-center">
                    <span className="text-gray-400">{item.symbol}</span>
                    <span className={`font-semibold ${item.pnl_30d >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {item.pnl_30d >= 0 ? '+' : ''}{formatNumber(item.pnl_30d)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-2">By Exit Type</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-emerald-500/10 p-2 rounded">
                  <p className="text-emerald-400 text-xs">TP1</p>
                  <p className="text-white font-semibold">{formatNumber(data.performance_attribution.by_exit_type.tp1_pnl)}</p>
                </div>
                <div className="bg-blue-500/10 p-2 rounded">
                  <p className="text-blue-400 text-xs">TP2</p>
                  <p className="text-white font-semibold">{formatNumber(data.performance_attribution.by_exit_type.tp2_pnl)}</p>
                </div>
                <div className="bg-red-500/10 p-2 rounded">
                  <p className="text-red-400 text-xs">SL</p>
                  <p className="text-white font-semibold">{formatNumber(data.performance_attribution.by_exit_type.sl_pnl)}</p>
                </div>
                <div className="bg-gray-500/10 p-2 rounded">
                  <p className="text-gray-400 text-xs">Manual</p>
                  <p className="text-white font-semibold">{formatNumber(data.performance_attribution.by_exit_type.manual_pnl)}</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Execution & Latency + News Correlation */}
        <motion.div 
          className="glass rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2 text-yellow-500" />
            Execution & News Analysis
          </h3>
          
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-2">Execution Metrics</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-gray-400 text-xs">Signal→Open</p>
                  <p className="text-white font-semibold">
                    {data.execution_metrics.signal_to_open_p50}s / {data.execution_metrics.signal_to_open_p95}s
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-xs">Fill Rate</p>
                  <p className="text-emerald-400 font-semibold">{formatPercent(data.execution_metrics.fill_rate)}</p>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center">
                <Brain className="w-4 h-4 mr-1" />
                News Correlation
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">News-driven trades (30d)</span>
                  <span className="text-white font-semibold">{data.news_correlation.news_driven_trades_30d}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Avg impact score</span>
                  <span className="text-blue-400 font-semibold">{data.news_correlation.avg_news_impact_score.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Prediction accuracy</span>
                  <span className="text-emerald-400 font-semibold">{formatPercent(data.news_correlation.news_accuracy)}</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Recent Trades Table */}
      <motion.div 
        className="glass rounded-xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2 text-blue-500" />
          Recent Trades (Closed)
        </h3>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left text-gray-400 py-2">Symbol</th>
                <th className="text-left text-gray-400 py-2">Side</th>
                <th className="text-left text-gray-400 py-2">Exit Reason</th>
                <th className="text-right text-gray-400 py-2">ROI</th>
                <th className="text-right text-gray-400 py-2">PnL</th>
                <th className="text-right text-gray-400 py-2">Closed</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_trades.map((trade) => (
                <tr key={trade.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="py-2 text-white font-semibold">{trade.symbol}</td>
                  <td className="py-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      trade.side === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {trade.side}
                    </span>
                  </td>
                  <td className="py-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      trade.exit_reason === 'TP1' || trade.exit_reason === 'TP2' 
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : trade.exit_reason === 'SL'
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {trade.exit_reason}
                    </span>
                  </td>
                  <td className={`py-2 text-right font-semibold ${
                    trade.roi_final >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {trade.roi_final >= 0 ? '+' : ''}{formatPercent(trade.roi_final)}
                  </td>
                  <td className={`py-2 text-right font-semibold ${
                    trade.pnl_net >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {trade.pnl_net >= 0 ? '+' : ''}{formatNumber(trade.pnl_net)}
                  </td>
                  <td className="py-2 text-right text-gray-400">
                    {new Date(trade.closed_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}
