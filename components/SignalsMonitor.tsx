'use client'

import React, { useState, useEffect } from 'react'
import { 
  SignalIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  FunnelIcon,
  UserIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

interface TradingSignal {
  id: string
  channel_name: string
  trader_name: string
  timestamp: string
  symbol: string
  direction: string
  entry_zone: number[]
  tp_levels: number[]
  sl_level?: number
  leverage?: number
  confidence?: number
  validation_status: string
  validation_errors?: string[]
}

interface ProcessedSignal {
  id?: string
  original_signal_id: string
  source_channel: string
  trader_name: string
  timestamp: string
  symbol: string
  direction: string
  entry_price: number
  tp1_price?: number
  tp2_price?: number
  sl_price?: number
  confidence_score: number
  quality_score: number
  processing_status: string
  risk_reward_ratio?: number
  trader_win_rate?: number
  trader_avg_roi?: number
  processing_errors?: string[]
}

interface SignalsData {
  signals: (TradingSignal | ProcessedSignal)[]
  count: number
  stats: {
    total: number
    valid: number
    invalid: number
    processed: number
    pending: number
  }
  traders: {
    [key: string]: {
      signal_count: number
      win_rate?: number
      avg_roi?: number
    }
  }
  timestamp: string
}

export default function SignalsMonitor() {
  const [signalsData, setSignalsData] = useState<SignalsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTab, setSelectedTab] = useState<'all' | 'new' | 'processed'>('all')
  const [selectedTrader, setSelectedTrader] = useState<string>('')
  const [selectedSymbol, setSelectedSymbol] = useState<string>('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchSignals = async () => {
    try {
      const params = new URLSearchParams({
        type: selectedTab,
        limit: '100'
      })
      
      if (selectedTrader) params.append('trader', selectedTrader)
      if (selectedSymbol) params.append('symbol', selectedSymbol)

      const response = await fetch(`/api/signals?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      setSignalsData(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch signals')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSignals()
  }, [selectedTab, selectedTrader, selectedSymbol])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(fetchSignals, 10000) // Обновление каждые 10 секунд
    return () => clearInterval(interval)
  }, [autoRefresh, selectedTab, selectedTrader, selectedSymbol])

  const getDirectionIcon = (direction: string) => {
    return direction === 'LONG' ? (
      <ArrowUpIcon className="h-4 w-4 text-green-500" />
    ) : (
      <ArrowDownIcon className="h-4 w-4 text-red-500" />
    )
  }

  const getStatusIcon = (signal: TradingSignal | ProcessedSignal) => {
    if ('validation_status' in signal) {
      switch (signal.validation_status) {
        case 'valid': return <CheckCircleIcon className="h-4 w-4 text-green-500" />
        case 'invalid': return <XCircleIcon className="h-4 w-4 text-red-500" />
        default: return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
      }
    } else {
      switch (signal.processing_status) {
        case 'processed': return <CheckCircleIcon className="h-4 w-4 text-green-500" />
        case 'rejected': return <XCircleIcon className="h-4 w-4 text-red-500" />
        case 'error': return <XCircleIcon className="h-4 w-4 text-red-600" />
        default: return <ArrowPathIcon className="h-4 w-4 text-yellow-500 animate-spin" />
      }
    }
  }

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-500'
    if (score >= 0.6) return 'text-yellow-500'
    return 'text-red-500'
  }

  const formatPrice = (price: number | undefined) => {
    if (!price) return 'N/A'
    return price.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 8 
    })
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const getUniqueSymbols = () => {
    if (!signalsData) return []
    const symbols = new Set(signalsData.signals.map(s => s.symbol))
    return Array.from(symbols).sort()
  }

  const getUniqueTraders = () => {
    if (!signalsData) return []
    return Object.keys(signalsData.traders).sort()
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center h-32">
          <ArrowPathIcon className="h-8 w-8 text-blue-500 animate-spin" />
          <span className="ml-2 text-gray-300">Загрузка сигналов...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center text-red-400">
          <XCircleIcon className="h-6 w-6 mr-2" />
          <span>Ошибка загрузки: {error}</span>
        </div>
        <button
          onClick={() => {
            setLoading(true)
            fetchSignals()
          }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Повторить
        </button>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center">
          <SignalIcon className="h-6 w-6 mr-2" />
          Trading Signals Monitor
        </h2>
        <div className="flex items-center space-x-4">
          <label className="flex items-center text-sm text-gray-300">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            Auto-refresh
          </label>
          <button
            onClick={fetchSignals}
            className="p-2 bg-gray-700 rounded hover:bg-gray-600"
          >
            <ArrowPathIcon className="h-4 w-4 text-gray-300" />
          </button>
        </div>
      </div>

      {/* Stats */}
      {signalsData && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-white">{signalsData.stats.total}</div>
            <div className="text-sm text-gray-300">Total</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-500">{signalsData.stats.valid}</div>
            <div className="text-sm text-gray-300">Valid</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-500">{signalsData.stats.processed}</div>
            <div className="text-sm text-gray-300">Processed</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-yellow-500">{signalsData.stats.pending}</div>
            <div className="text-sm text-gray-300">Pending</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-500">{signalsData.stats.invalid}</div>
            <div className="text-sm text-gray-300">Invalid</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Tabs */}
        <div className="flex space-x-2">
          {[
            { id: 'all', label: 'All' },
            { id: 'new', label: 'New' },
            { id: 'processed', label: 'Processed' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id as any)}
              className={`px-3 py-1 rounded text-sm ${
                selectedTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Trader Filter */}
        <select
          value={selectedTrader}
          onChange={(e) => setSelectedTrader(e.target.value)}
          className="bg-gray-700 text-white rounded px-3 py-1 text-sm"
        >
          <option value="">All Traders</option>
          {getUniqueTraders().map(trader => (
            <option key={trader} value={trader}>{trader}</option>
          ))}
        </select>

        {/* Symbol Filter */}
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="bg-gray-700 text-white rounded px-3 py-1 text-sm"
        >
          <option value="">All Symbols</option>
          {getUniqueSymbols().map(symbol => (
            <option key={symbol} value={symbol}>{symbol}</option>
          ))}
        </select>
      </div>

      {/* Signals List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {signalsData?.signals.map((signal, index) => (
          <div key={signal.id || index} className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                {getStatusIcon(signal)}
                <div className="flex items-center space-x-2">
                  {getDirectionIcon(signal.direction)}
                  <span className="font-semibold text-white">{signal.symbol}</span>
                  <span className={`text-sm ${signal.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                    {signal.direction}
                  </span>
                </div>
                <div className="flex items-center text-sm text-gray-400">
                  <UserIcon className="h-4 w-4 mr-1" />
                  {signal.trader_name}
                </div>
              </div>
              <div className="text-sm text-gray-400">
                {formatTime(signal.timestamp)}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {/* Entry */}
              <div>
                <span className="text-gray-400">Entry:</span>
                <div className="text-white">
                  {'entry_zone' in signal ? (
                    signal.entry_zone.length > 0 ? (
                      signal.entry_zone.length === 1 ? 
                        formatPrice(signal.entry_zone[0]) :
                        `${formatPrice(Math.min(...signal.entry_zone))} - ${formatPrice(Math.max(...signal.entry_zone))}`
                    ) : 'N/A'
                  ) : (
                    formatPrice(signal.entry_price)
                  )}
                </div>
              </div>

              {/* TP */}
              <div>
                <span className="text-gray-400">TP:</span>
                <div className="text-green-400">
                  {'tp_levels' in signal ? (
                    (signal as TradingSignal).tp_levels.length > 0 ? (signal as TradingSignal).tp_levels.map(tp => formatPrice(tp)).join(', ') : 'N/A'
                  ) : (
                    [(signal as ProcessedSignal).tp1_price, (signal as ProcessedSignal).tp2_price].filter(Boolean).map(tp => formatPrice(tp!)).join(', ') || 'N/A'
                  )}
                </div>
              </div>

              {/* SL */}
              <div>
                <span className="text-gray-400">SL:</span>
                <div className="text-red-400">
                  {'sl_level' in signal ? formatPrice((signal as TradingSignal).sl_level) : formatPrice((signal as ProcessedSignal).sl_price)}
                </div>
              </div>

              {/* Quality/Confidence */}
              <div>
                <span className="text-gray-400">
                  {'quality_score' in signal ? 'Quality:' : 'Confidence:'}
                </span>
                <div className={
                  'quality_score' in signal 
                    ? getQualityColor(signal.quality_score)
                    : getQualityColor(signal.confidence || 0)
                }>
                  {('quality_score' in signal 
                    ? signal.quality_score 
                    : signal.confidence || 0
                  ).toFixed(2)}
                </div>
              </div>
            </div>

            {/* Additional Info for Processed Signals */}
            {'risk_reward_ratio' in signal && signal.risk_reward_ratio && (
              <div className="mt-2 pt-2 border-t border-gray-600">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">R/R Ratio:</span>
                    <span className="ml-2 text-white">{signal.risk_reward_ratio.toFixed(2)}</span>
                  </div>
                  {signal.trader_win_rate && (
                    <div>
                      <span className="text-gray-400">Trader WR:</span>
                      <span className="ml-2 text-white">{(signal.trader_win_rate * 100).toFixed(1)}%</span>
                    </div>
                  )}
                  {signal.trader_avg_roi && (
                    <div>
                      <span className="text-gray-400">Avg ROI:</span>
                      <span className="ml-2 text-white">{signal.trader_avg_roi.toFixed(1)}%</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Errors */}
            {((('validation_errors' in signal && (signal as TradingSignal).validation_errors) || 
               ('processing_errors' in signal && (signal as ProcessedSignal).processing_errors)) && 
              ((signal as TradingSignal).validation_errors?.length || (signal as ProcessedSignal).processing_errors?.length)) && (
              <div className="mt-2 pt-2 border-t border-gray-600">
                <div className="text-sm text-red-400">
                  <span className="font-medium">Errors:</span>
                  <ul className="mt-1 list-disc list-inside">
                    {((signal as TradingSignal).validation_errors || (signal as ProcessedSignal).processing_errors || []).map((error, i) => (
                      <li key={i}>{error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        ))}

        {signalsData?.signals.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <SignalIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No signals found</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700 text-xs text-gray-400">
        Last updated: {signalsData ? new Date(signalsData.timestamp).toLocaleString() : 'Never'}
        {signalsData && (
          <span className="ml-4">
            Showing {signalsData.count} of {signalsData.stats.total} signals
          </span>
        )}
      </div>
    </div>
  )
}
