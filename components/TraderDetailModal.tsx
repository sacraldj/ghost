"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

interface TraderSignal {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  entry_price: number
  targets: number[]
  stop_loss: number
  pnl: number
  roi: number
  status: 'active' | 'tp1' | 'tp2' | 'sl' | 'closed'
  created_at: string
  closed_at?: string
  duration?: string
}

interface TraderDetailData {
  trader_id: string
  name: string
  is_trading: boolean
  total_signals: number
  total_pnl: number
  winrate: number
  avg_roi: number
  signals: TraderSignal[]
  pnl_by_symbol: Record<string, {
    symbol: string
    trades: number
    pnl: number
    winrate: number
  }>
}

interface TraderDetailModalProps {
  traderId: string
  isOpen: boolean
  onClose: () => void
}

const TraderDetailModal: React.FC<TraderDetailModalProps> = ({ traderId, isOpen, onClose }) => {
  const [data, setData] = useState<TraderDetailData | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'signals' | 'symbols' | 'stats'>('signals')

  useEffect(() => {
    if (isOpen && traderId) {
      loadTraderDetails()
    }
  }, [isOpen, traderId])

  const loadTraderDetails = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/traders-analytics/details/${traderId}`)
      const traderData = await response.json()
      setData(traderData)
    } catch (error) {
      console.error('Error loading trader details:', error)
    }
    setLoading(false)
  }

  const toggleTrading = async () => {
    if (!data) return
    
    try {
      await fetch('/api/traders-analytics/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          trader_id: traderId, 
          action: data.is_trading ? 'disable' : 'enable' 
        })
      })
      loadTraderDetails()
    } catch (error) {
      console.error('Error toggling trading:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-blue-500 text-white">Активен</Badge>
      case 'tp1':
        return <Badge className="bg-green-500 text-white">TP1</Badge>
      case 'tp2':
        return <Badge className="bg-green-600 text-white">TP2</Badge>
      case 'sl':
        return <Badge className="bg-red-500 text-white">SL</Badge>
      case 'closed':
        return <Badge className="bg-gray-500 text-white">Закрыт</Badge>
      default:
        return <Badge className="bg-gray-400 text-white">{status}</Badge>
    }
  }

  const getSideBadge = (side: string) => {
    return (
      <Badge className={side === 'BUY' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}>
        {side === 'BUY' ? 'LONG' : 'SHORT'}
      </Badge>
    )
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Заголовок */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold">
              {data?.name?.substring(0, 2).toUpperCase() || 'TR'}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">{data?.name || traderId}</h2>
              <div className="flex items-center space-x-2 mt-1">
                <span className="text-gray-400">ID: {traderId}</span>
                {data?.is_trading ? (
                  <Badge className="bg-green-500 text-white">🔄 Торгуем</Badge>
                ) : (
                  <Badge className="bg-yellow-500 text-black">📊 Только статистика</Badge>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button
              onClick={toggleTrading}
              variant={data?.is_trading ? "outline" : "default"}
              className={data?.is_trading ? "border-red-500 text-red-500 hover:bg-red-500 hover:text-white" : "bg-green-600 hover:bg-green-700"}
            >
              {data?.is_trading ? '🛑 Отключить торговлю' : '🚀 Включить торговлю'}
            </Button>
            
            <Button variant="ghost" onClick={onClose} className="text-gray-400 hover:text-white">
              ✕
            </Button>
          </div>
        </div>

        {/* Быстрая статистика */}
        <div className="p-6 border-b border-gray-800">
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{data?.total_signals || 0}</div>
              <div className="text-sm text-gray-400">Всего сигналов</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${(data?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(data?.total_pnl || 0) >= 0 ? '+' : ''}{(data?.total_pnl || 0).toFixed(2)} USDT
              </div>
              <div className="text-sm text-gray-400">Общий P&L</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{(data?.winrate || 0).toFixed(1)}%</div>
              <div className="text-sm text-gray-400">Winrate</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{(data?.avg_roi || 0).toFixed(1)}%</div>
              <div className="text-sm text-gray-400">Средний ROI</div>
            </div>
          </div>
        </div>

        {/* Табы */}
        <div className="flex border-b border-gray-800">
          {[
            { id: 'signals', label: '📊 Все сигналы', count: data?.signals?.length || 0 },
            { id: 'symbols', label: '💰 По монетам', count: Object.keys(data?.pnl_by_symbol || {}).length },
            { id: 'stats', label: '📈 Подробная статистика', count: null }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-yellow-500 border-b-2 border-yellow-500'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
              {tab.count !== null && (
                <span className="ml-2 px-2 py-1 bg-gray-800 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Контент табов */}
        <div className="p-6 overflow-y-auto max-h-[50vh]">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin w-8 h-8 border-4 border-yellow-500 border-t-transparent rounded-full"></div>
            </div>
          ) : (
            <>
              {/* Таб: Все сигналы */}
              {activeTab === 'signals' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-white">Все сигналы трейдера</h3>
                    <div className="text-sm text-gray-400">
                      Показано: {data?.signals?.length || 0} сигналов
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    {(data?.signals || []).map((signal) => (
                      <Card key={signal.id} className="bg-gray-800 border-gray-700">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="font-bold text-white">{signal.symbol}</div>
                              {getSideBadge(signal.side)}
                              {getStatusBadge(signal.status)}
                            </div>
                            
                            <div className="flex items-center space-x-4 text-sm">
                              <div className="text-gray-400">
                                Вход: <span className="text-white">${signal.entry_price}</span>
                              </div>
                              <div className="text-gray-400">
                                P&L: <span className={`font-medium ${signal.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  {signal.pnl >= 0 ? '+' : ''}{signal.pnl.toFixed(2)} USDT
                                </span>
                              </div>
                              <div className="text-gray-400">
                                ROI: <span className={`font-medium ${signal.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  {signal.roi >= 0 ? '+' : ''}{signal.roi.toFixed(1)}%
                                </span>
                              </div>
                              <div className="text-gray-400">
                                {new Date(signal.created_at).toLocaleDateString('ru-RU')}
                              </div>
                            </div>
                          </div>
                          
                          <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                            <span>Targets: {signal.targets.join(', ')}</span>
                            <span>SL: {signal.stop_loss}</span>
                            {signal.duration && <span>Длительность: {signal.duration}</span>}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Таб: По монетам */}
              {activeTab === 'symbols' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-bold text-white">Статистика по монетам</h3>
                  
                  <div className="grid gap-4">
                    {Object.values(data?.pnl_by_symbol || {}).map((symbolData) => (
                      <Card key={symbolData.symbol} className="bg-gray-800 border-gray-700">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="font-bold text-white text-lg">{symbolData.symbol}</div>
                              <Badge variant="outline" className="text-gray-400">
                                {symbolData.trades} сделок
                              </Badge>
                            </div>
                            
                            <div className="flex items-center space-x-6">
                              <div className="text-center">
                                <div className={`font-bold ${symbolData.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  {symbolData.pnl >= 0 ? '+' : ''}{symbolData.pnl.toFixed(2)} USDT
                                </div>
                                <div className="text-xs text-gray-400">P&L</div>
                              </div>
                              
                              <div className="text-center">
                                <div className="font-bold text-white">{symbolData.winrate.toFixed(1)}%</div>
                                <div className="text-xs text-gray-400">Winrate</div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Таб: Подробная статистика */}
              {activeTab === 'stats' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-bold text-white">Подробная статистика</h3>
                  
                  <div className="grid grid-cols-2 gap-6">
                    <Card className="bg-gray-800 border-gray-700">
                      <CardHeader>
                        <CardTitle className="text-white">Общие показатели</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Всего сигналов:</span>
                          <span className="text-white">{data?.total_signals || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Успешных:</span>
                          <span className="text-green-400">{Math.round((data?.winrate || 0) * (data?.total_signals || 0) / 100)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Убыточных:</span>
                          <span className="text-red-400">{(data?.total_signals || 0) - Math.round((data?.winrate || 0) * (data?.total_signals || 0) / 100)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Общий P&L:</span>
                          <span className={`font-bold ${(data?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {(data?.total_pnl || 0) >= 0 ? '+' : ''}{(data?.total_pnl || 0).toFixed(2)} USDT
                          </span>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-800 border-gray-700">
                      <CardHeader>
                        <CardTitle className="text-white">Торговая активность</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Статус торговли:</span>
                          <span className={data?.is_trading ? 'text-green-400' : 'text-yellow-400'}>
                            {data?.is_trading ? '🔄 Активна' : '📊 Отключена'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Средний ROI:</span>
                          <span className="text-white">{(data?.avg_roi || 0).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Winrate:</span>
                          <span className="text-white">{(data?.winrate || 0).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Уникальных монет:</span>
                          <span className="text-white">{Object.keys(data?.pnl_by_symbol || {}).length}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default TraderDetailModal
