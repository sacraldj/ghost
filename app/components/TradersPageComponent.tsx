'use client'

import React, { useState, useEffect } from 'react'
import TradersListView from './TradersListView'
import TraderDetailView from './TraderDetailView'

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

export default function TradersPageComponent() {
  const [selectedTrader, setSelectedTrader] = useState<TraderAnalytics | null>(null)
  const [tradersData, setTradersData] = useState<TraderAnalytics[]>([])
  const [loading, setLoading] = useState(true)

  // Загружаем данные трейдеров
  useEffect(() => {
    fetchTradersData()
  }, [])

  const fetchTradersData = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/traders-analytics?limit=50')
      const result = await response.json()
      
      if (result.success && result.data) {
        setTradersData(result.data)
        // Автоматически выбираем первого трейдера
        if (result.data.length > 0 && !selectedTrader) {
          setSelectedTrader(result.data[0])
        }
      }
    } catch (error) {
      console.error('Error fetching traders data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 text-white">
          {/* Заголовок страницы в стиле Test Table */}
          <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white mb-2">👥 Traders Analytics</h1>
                <p className="text-gray-400">Comprehensive trader performance analysis and statistics</p>
              </div>
              <div className="bg-gradient-to-r from-green-600 to-green-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
                📊 Live Data
              </div>
            </div>
          </div>

          {/* Основной контент */}
          <div className="grid grid-cols-12 gap-6">
            {/* Список трейдеров (левая колонка) */}
            <div className="col-span-4">
              <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl border border-gray-700/50 shadow-lg h-full">
                <TradersListView
                  traders={tradersData}
                  selectedTrader={selectedTrader}
                  onSelectTrader={setSelectedTrader}
                  loading={loading}
                />
              </div>
            </div>

            {/* Детальная информация о трейдере (правая колонка) */}
            <div className="col-span-8">
              <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl border border-gray-700/50 shadow-lg h-full overflow-y-auto">
                {selectedTrader ? (
                  <TraderDetailView trader={selectedTrader} />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-gradient-to-br from-gray-700/50 to-gray-600/30 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                        <span className="text-2xl">👥</span>
                      </div>
                      <div className="text-gray-300 text-lg mb-2 font-medium">
                        {loading ? '⏳ Loading traders...' : '📊 Select a trader to view details'}
                      </div>
                      <div className="text-gray-400 text-sm">
                        Choose from the list to see comprehensive analytics
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
    </div>
  )
}
