'use client'

import React, { useState, useEffect } from 'react'
import TraderPerformanceChart from './TraderPerformanceChart'

interface TraderAnalytics {
  trader_id: string
  name: string
  source_type: string
  trust_index: number
  grade: string
  risk_score: number
  total_signals: number
  winrate: number
  total_pnl: number
  avg_roi: number
  overall_rank: number
  last_updated: string
}

interface TraderSignal {
  id: string
  signal_id: string
  symbol: string
  side: string
  entry_price: number
  tp1: number
  tp2: number
  sl: number
  leverage: number
  original_text: string
  status: string
  created_at: string
}

interface TraderDetailViewProps {
  trader: TraderAnalytics
}

export default function TraderDetailView({ trader }: TraderDetailViewProps) {
  const [signals, setSignals] = useState<TraderSignal[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSignal, setSelectedSignal] = useState<TraderSignal | null>(null)

  useEffect(() => {
    if (trader) {
      fetchTraderSignals()
    }
  }, [trader])

  const fetchTraderSignals = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/test-table?source=${trader.trader_id}&limit=10`)
      const result = await response.json()
      
      if (result.data) {
        setSignals(result.data)
        if (result.data.length > 0) {
          setSelectedSignal(result.data[0]) // Выбираем первый сигнал
        }
      }
    } catch (error) {
      console.error('Error fetching trader signals:', error)
    } finally {
      setLoading(false)
    }
  }

  const getGradeBadge = (grade: string) => {
    const styles = {
      'A': 'bg-green-500 text-white',
      'B': 'bg-blue-500 text-white', 
      'C': 'bg-yellow-500 text-black',
      'D': 'bg-red-500 text-white'
    }
    return styles[grade as keyof typeof styles] || 'bg-gray-500 text-white'
  }

  const formatPrice = (price: number | null) => {
    if (!price) return 'N/A'
    return `$${price.toFixed(4)}`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sim_open': return 'text-green-400'
      case 'sim_closed': return 'text-blue-400'
      case 'sim_failed': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="h-full text-white p-6 overflow-y-auto">
      {/* Заголовок трейдера */}
      <div className="bg-gray-700 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
              <span className="text-lg font-bold">{trader.name.charAt(0).toUpperCase()}</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold">{trader.name}</h1>
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <span className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
                  LIVE
                </span>
                <span>|</span>
                <span>{trader.last_updated ? new Date(trader.last_updated).toLocaleString('ru-RU') : 'N/A'}</span>
                <span>|</span>
                <span>АКТИВЕН 24 ЧАС</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-gray-400">Стратегия</div>
              <div className="bg-yellow-500 text-black px-3 py-1 rounded text-sm font-bold">
                2TP STOP BY
              </div>
            </div>
            
            <div className={`px-3 py-1 rounded text-sm font-bold ${getGradeBadge(trader.grade)}`}>
              Grade {trader.grade}
            </div>
            
            <div className="text-right">
              <div className="text-sm text-gray-400">Trust Index</div>
              <div className="text-lg font-bold text-blue-400">{trader.trust_index.toFixed(1)}</div>
            </div>
          </div>
        </div>
        
        {/* Краткая статистика */}
        <div className="grid grid-cols-4 gap-6 text-center">
          <div>
            <div className="text-2xl font-bold text-green-400">{trader.winrate.toFixed(1)}%</div>
            <div className="text-sm text-gray-400">Winrate</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-400">{trader.total_signals}</div>
            <div className="text-sm text-gray-400">Total Signals</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-400">#{trader.overall_rank}</div>
            <div className="text-sm text-gray-400">Rank</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-400">{trader.avg_roi.toFixed(2)}%</div>
            <div className="text-sm text-gray-400">Avg ROI</div>
          </div>
        </div>
      </div>

      {/* График производительности */}
      <TraderPerformanceChart trader={trader} />

      {/* Детальная информация о сигнале */}
      {selectedSignal ? (
        <div className="space-y-6">
          {/* Основные данные по сигналу от трейдера */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-md font-bold mb-3 text-gray-200">ОСНОВНЫЕ ДАННЫЕ ПО СИГНАЛУ ОТ ТРЕЙДЕРА</h3>
            
            <div className="grid grid-cols-2 gap-8">
              <div className="space-y-3">
                <div className="flex">
                  <span className="w-20 text-gray-400">ID:</span>
                  <span>{selectedSignal.signal_id.split('_').pop()}</span>
                </div>
                <div className="flex">
                  <span className="w-20 text-gray-400">Symbol:</span>
                  <span className="font-bold">{selectedSignal.symbol}</span>
                </div>
                <div className="flex">
                  <span className="w-20 text-gray-400">Side:</span>
                  <span className={`font-bold ${selectedSignal.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                    • {selectedSignal.side}
                  </span>
                </div>
                <div className="flex">
                  <span className="w-20 text-gray-400">Leverage:</span>
                  <span>{selectedSignal.leverage}x</span>
                </div>
                <div className="flex">
                  <span className="w-20 text-gray-400">Enter:</span>
                  <span>{formatPrice(selectedSignal.entry_price)}</span>
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <div className="text-gray-400 mb-2">Targets:</div>
                  <div className="space-y-1">
                    {selectedSignal.tp1 && <div className="text-green-400">• TP1 {formatPrice(selectedSignal.tp1)}</div>}
                    {selectedSignal.tp2 && <div className="text-green-400">• TP2 {formatPrice(selectedSignal.tp2)}</div>}
                  </div>
                </div>
                
                <div className="pt-4">
                  <div className="text-gray-400">Stop-loss:</div>
                  <div className="text-red-400">{formatPrice(selectedSignal.sl)}</div>
                </div>
              </div>
            </div>

            {/* Reasoning */}
            {selectedSignal.original_text && (
              <div className="mt-6 p-4 bg-gray-700 rounded">
                <h4 className="text-blue-400 font-bold mb-2">Reason traders:</h4>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {selectedSignal.original_text.length > 200 
                    ? selectedSignal.original_text.substring(0, 200) + '...'
                    : selectedSignal.original_text
                  }
                </p>
              </div>
            )}
          </div>

          {/* Реальные данные входа системы */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-md font-bold mb-3 text-gray-200">РЕАЛЬНЫЕ ДАННЫЕ ВХОДА СИСТЕМЫ</h3>
            
            <div className="grid grid-cols-2 gap-8">
              <div className="space-y-3">
                <div className="flex">
                  <span className="w-32 text-gray-400">Symbol:</span>
                  <span className="font-bold">
                    {selectedSignal.symbol} 
                    <span className={`ml-2 ${selectedSignal.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                      [{selectedSignal.side}] ↓
                    </span>
                  </span>
                </div>
                <div className="flex">
                  <span className="w-32 text-gray-400">Цена входа:</span>
                  <span>{formatPrice(selectedSignal.entry_price)}</span>
                </div>
                <div className="flex">
                  <span className="w-32 text-gray-400">Цена маркировки:</span>
                  <span className="text-blue-400">{(selectedSignal.entry_price * 1.002).toFixed(4)}</span>
                </div>
                <div className="flex">
                  <span className="w-32 text-gray-400">Размер позиции:</span>
                  <span>100 ({selectedSignal.symbol.replace('USDT', '')}) - $100</span>
                </div>
                <div className="flex">
                  <span className="w-32 text-gray-400">Плечо:</span>
                  <span>{selectedSignal.leverage}x</span>
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <div className="text-gray-400 mb-2">Targets:</div>
                  <div className="space-y-1">
                    {selectedSignal.tp1 && <div className="text-green-400">• TP1 {formatPrice(selectedSignal.tp1)}</div>}
                    {selectedSignal.tp2 && <div className="text-green-400">• TP2 {formatPrice(selectedSignal.tp2)}</div>}
                  </div>
                </div>
                
                <div className="pt-4">
                  <div className="text-gray-400">Stop-loss:</div>
                  <div className="text-red-400">{formatPrice(selectedSignal.sl)}</div>
                </div>
              </div>
            </div>

            {/* Статус сигнала */}
            <div className="mt-6 p-3 bg-gray-700 rounded flex justify-between items-center">
              <div>
                <span className="text-gray-400">Статус: </span>
                <span className={`font-bold ${getStatusColor(selectedSignal.status)}`}>
                  {selectedSignal.status.toUpperCase()}
                </span>
              </div>
              <div className="text-sm text-gray-400">
                {new Date(selectedSignal.created_at).toLocaleString('ru-RU')}
              </div>
            </div>
          </div>

          {/* История сигналов трейдера */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-md font-bold mb-3 text-gray-200">НЕДАВНИЕ СИГНАЛЫ</h3>
            
            <div className="space-y-3">
              {signals.slice(0, 5).map((signal, index) => (
                <div 
                  key={signal.id}
                  className={`p-3 rounded cursor-pointer transition-colors ${
                    selectedSignal.id === signal.id 
                      ? 'bg-gray-600 border-l-4 border-blue-400' 
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                  onClick={() => setSelectedSignal(signal)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-4">
                      <span className="font-bold">{signal.symbol}</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        signal.side === 'LONG' ? 'bg-green-600' : 'bg-red-600'
                      }`}>
                        {signal.side}
                      </span>
                      <span className="text-gray-400">{formatPrice(signal.entry_price)}</span>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm ${getStatusColor(signal.status)}`}>
                        {signal.status}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(signal.created_at).toLocaleDateString('ru-RU')}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-700 rounded-lg p-8 text-center">
          <div className="text-gray-400">
            {loading ? 'Загрузка сигналов...' : 'Нет доступных сигналов для этого трейдера'}
          </div>
        </div>
      )}
    </div>
  )
}
