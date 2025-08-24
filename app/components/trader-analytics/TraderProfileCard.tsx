// ДЕМО: Детальная карточка трейдера уровня фонда
"use client"

import React from 'react'
import { useState, useEffect } from 'react'

interface TraderProfileData {
  trader_id: string
  name: string
  trust_index: number      // 0-100
  grade: 'A' | 'B' | 'C' | 'D'
  risk_score: number       // 0-100
  
  // Основные метрики
  total_signals: number
  valid_signals: number
  executed_signals: number
  
  // Результативность  
  winrate: number
  tp1_rate: number
  tp2_rate: number
  sl_rate: number
  
  // Финансы
  total_pnl: number
  avg_roi: number
  sharpe_ratio: number
  max_drawdown: number
  
  // Риск-менеджмент
  avg_rrr: number
  consistency_score: number
  
  // Рейтинги
  overall_rank: number
  total_traders: number
  rank_change: number      // +/- from previous period
  
  // Временные паттерны
  best_day: string
  best_hour: number
  avg_frequency: number    // signals per day
  
  // Статус
  status: 'active' | 'inactive' | 'suspended'
  last_signal: string
  
  // Специализация
  best_symbols: string[]
  worst_symbols: string[]
  
  // Поведенческие флаги
  has_duplicates: boolean
  has_contradictions: boolean
  copy_paste_score: number // 0-100 (higher = more likely copying)
}

interface TraderProfileCardProps {
  trader_id: string
}

export default function TraderProfileCard({ trader_id }: TraderProfileCardProps) {
  const [data, setData] = useState<TraderProfileData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTraderProfile()
  }, [trader_id])

  const fetchTraderProfile = async () => {
    try {
      const response = await fetch(`/api/traders/${trader_id}/profile`)
      const result = await response.json()
      setData(result.data)
    } catch (error) {
      console.error('Error fetching trader profile:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (!data) return null

  // Определяем цвета для Grade
  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'bg-green-500 text-white'
      case 'B': return 'bg-blue-500 text-white'  
      case 'C': return 'bg-yellow-500 text-black'
      case 'D': return 'bg-red-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const getGradeDescription = (grade: string) => {
    switch (grade) {
      case 'A': return 'Excellent (Top Performer)'
      case 'B': return 'Good (Above Average)'
      case 'C': return 'Average (Standard Performance)'
      case 'D': return 'Poor (Below Average)'
      default: return 'Not Rated'
    }
  }

  const getTrustIndexColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-blue-400'
    if (score >= 40) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getRiskScoreColor = (score: number) => {
    if (score <= 30) return 'text-green-400'  // Low risk = good
    if (score <= 50) return 'text-yellow-400'
    if (score <= 70) return 'text-orange-400'
    return 'text-red-400'                     // High risk = bad
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
      {/* Header with Grade and Status */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${getGradeColor(data.grade)}`}>
              {data.grade}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{data.name}</h2>
              <p className="text-sm text-gray-400">{getGradeDescription(data.grade)}</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Status indicator */}
          <div className={`w-3 h-3 rounded-full ${
            data.status === 'active' ? 'bg-green-500' : 
            data.status === 'inactive' ? 'bg-yellow-500' : 'bg-red-500'
          }`}></div>
          <span className="text-sm text-gray-400 capitalize">{data.status}</span>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Trust Index */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Trust Index</div>
          <div className={`text-2xl font-bold ${getTrustIndexColor(data.trust_index)}`}>
            {data.trust_index}
          </div>
          <div className="text-xs text-gray-500">of 100</div>
        </div>

        {/* Risk Score */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Risk Score</div>
          <div className={`text-2xl font-bold ${getRiskScoreColor(data.risk_score)}`}>
            {data.risk_score}
          </div>
          <div className="text-xs text-gray-500">
            {data.risk_score <= 30 ? 'Low Risk' : 
             data.risk_score <= 50 ? 'Medium Risk' : 
             data.risk_score <= 70 ? 'High Risk' : 'Very High Risk'}
          </div>
        </div>

        {/* Winrate */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Winrate</div>
          <div className="text-2xl font-bold text-blue-400">
            {data.winrate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">
            {data.executed_signals} trades
          </div>
        </div>

        {/* Average ROI */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Avg ROI</div>
          <div className={`text-2xl font-bold ${data.avg_roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {data.avg_roi > 0 ? '+' : ''}{data.avg_roi.toFixed(2)}%
          </div>
          <div className="text-xs text-gray-500">per signal</div>
        </div>
      </div>

      {/* Ranking and Performance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Ranking */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-3">🏆 Ranking</h3>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-blue-400">
                #{data.overall_rank}
              </div>
              <div className="text-sm text-gray-400">
                of {data.total_traders} traders
              </div>
            </div>
            <div className={`flex items-center gap-1 px-2 py-1 rounded ${
              data.rank_change > 0 ? 'bg-green-900 text-green-400' :
              data.rank_change < 0 ? 'bg-red-900 text-red-400' : 
              'bg-gray-700 text-gray-400'
            }`}>
              {data.rank_change > 0 ? '↗' : data.rank_change < 0 ? '↘' : '→'}
              {Math.abs(data.rank_change)}
            </div>
          </div>
        </div>

        {/* Advanced Metrics */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-3">📊 Advanced</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Sharpe Ratio</span>
              <span className="text-white font-mono">{data.sharpe_ratio.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Max Drawdown</span>
              <span className="text-red-400 font-mono">-{data.max_drawdown.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Avg RRR</span>
              <span className="text-white font-mono">{data.avg_rrr.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Time Patterns */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold text-white mb-3">⏰ Time Patterns</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-400">Best Day</div>
            <div className="text-white font-semibold">{data.best_day}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Best Hour</div>
            <div className="text-white font-semibold">{data.best_hour}:00</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Frequency</div>
            <div className="text-white font-semibold">{data.avg_frequency.toFixed(1)}/day</div>
          </div>
        </div>
      </div>

      {/* Behavioral Warnings */}
      {(data.has_duplicates || data.has_contradictions || data.copy_paste_score > 70) && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 mb-6">
          <h3 className="text-red-400 font-semibold mb-2">⚠️ Behavioral Alerts</h3>
          <div className="space-y-1 text-sm">
            {data.has_duplicates && (
              <div className="text-red-300">• Duplicate signals detected</div>
            )}
            {data.has_contradictions && (
              <div className="text-red-300">• Contradictory signals found</div>
            )}
            {data.copy_paste_score > 70 && (
              <div className="text-red-300">• High copy-paste similarity ({data.copy_paste_score}%)</div>
            )}
          </div>
        </div>
      )}

      {/* Specialization */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Best Symbols */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-green-400 mb-2">✅ Best Symbols</h3>
          <div className="flex flex-wrap gap-1">
            {data.best_symbols.map((symbol, idx) => (
              <span key={idx} className="px-2 py-1 bg-green-900/30 text-green-300 rounded text-xs">
                {symbol}
              </span>
            ))}
          </div>
        </div>

        {/* Worst Symbols */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-red-400 mb-2">❌ Avoid Symbols</h3>
          <div className="flex flex-wrap gap-1">
            {data.worst_symbols.map((symbol, idx) => (
              <span key={idx} className="px-2 py-1 bg-red-900/30 text-red-300 rounded text-xs">
                {symbol}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700 text-xs text-gray-500 text-center">
        Last signal: {new Date(data.last_signal).toLocaleDateString()} • 
        Updated: {new Date().toLocaleDateString()}
      </div>
    </div>
  )
}
