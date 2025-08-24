'use client'

import React, { useState } from 'react'

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

interface TradersListViewProps {
  traders: TraderAnalytics[]
  selectedTrader: TraderAnalytics | null
  onSelectTrader: (trader: TraderAnalytics) => void
  loading: boolean
}

export default function TradersListView({ 
  traders, 
  selectedTrader, 
  onSelectTrader, 
  loading 
}: TradersListViewProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [gradeFilter, setGradeFilter] = useState<string>('all')

  const getGradeBadge = (grade: string) => {
    const styles = {
      'A': 'bg-green-500 text-white',
      'B': 'bg-blue-500 text-white', 
      'C': 'bg-yellow-500 text-black',
      'D': 'bg-red-500 text-white'
    }
    return styles[grade as keyof typeof styles] || 'bg-gray-500 text-white'
  }

  const getTrustIndexColor = (trustIndex: number) => {
    if (trustIndex >= 70) return 'text-green-400'
    if (trustIndex >= 50) return 'text-blue-400'
    if (trustIndex >= 30) return 'text-yellow-400'
    return 'text-red-400'
  }

  // Фильтрация трейдеров
  const filteredTraders = traders.filter(trader => {
    const matchesSearch = trader.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         trader.trader_id.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesGrade = gradeFilter === 'all' || trader.grade === gradeFilter
    return matchesSearch && matchesGrade
  })

  const gradeDistribution = traders.reduce((acc, trader) => {
    acc[trader.grade] = (acc[trader.grade] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="bg-gray-700 h-16 rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Заголовок и фильтры */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-bold text-white mb-4">All Traders</h2>
        
        {/* Статистика по Grade */}
        <div className="flex space-x-2 mb-4">
          {['A', 'B', 'C', 'D'].map(grade => (
            <div 
              key={grade}
              className={`px-3 py-1 rounded text-sm cursor-pointer transition-colors ${
                gradeFilter === grade 
                  ? getGradeBadge(grade)
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              onClick={() => setGradeFilter(gradeFilter === grade ? 'all' : grade)}
            >
              {grade}: {gradeDistribution[grade] || 0}
            </div>
          ))}
          <div 
            className={`px-3 py-1 rounded text-sm cursor-pointer transition-colors ${
              gradeFilter === 'all'
                ? 'bg-white text-black'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            onClick={() => setGradeFilter('all')}
          >
            All: {traders.length}
          </div>
        </div>

        {/* Поиск */}
        <input
          type="text"
          placeholder="Search traders..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Список трейдеров */}
      <div className="flex-1 overflow-y-auto">
        {filteredTraders.length === 0 ? (
          <div className="p-6 text-center text-gray-400">
            {searchQuery || gradeFilter !== 'all' 
              ? 'Нет трейдеров, соответствующих фильтрам'
              : 'Нет доступных трейдеров'
            }
          </div>
        ) : (
          <div className="space-y-2 p-4">
            {filteredTraders.map((trader) => (
              <div
                key={trader.trader_id}
                className={`p-4 rounded-lg cursor-pointer transition-all ${
                  selectedTrader?.trader_id === trader.trader_id
                    ? 'bg-blue-600 shadow-lg'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
                onClick={() => onSelectTrader(trader)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-bold">
                        {trader.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="text-white font-medium text-sm">
                        {trader.name.length > 15 
                          ? trader.name.substring(0, 15) + '...'
                          : trader.name
                        }
                      </div>
                      <div className="text-xs text-gray-400">
                        #{trader.overall_rank} • {trader.source_type}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={`px-2 py-1 rounded text-xs font-bold ${getGradeBadge(trader.grade)}`}>
                      {trader.grade}
                    </div>
                  </div>
                </div>

                {/* Метрики трейдера */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-gray-400">Trust:</span>
                    <span className={`ml-1 font-bold ${getTrustIndexColor(trader.trust_index)}`}>
                      {trader.trust_index.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Winrate:</span>
                    <span className="ml-1 text-green-400 font-bold">
                      {trader.winrate.toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Signals:</span>
                    <span className="ml-1 text-blue-400 font-bold">
                      {trader.total_signals}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">ROI:</span>
                    <span className={`ml-1 font-bold ${trader.avg_roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trader.avg_roi.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Статус активности */}
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-600">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-xs text-green-400">ACTIVE</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {trader.last_updated 
                      ? new Date(trader.last_updated).toLocaleDateString('ru-RU')
                      : 'N/A'
                    }
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
