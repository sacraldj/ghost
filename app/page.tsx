'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Импортируем компоненты
import UnifiedLayout from '@/app/components/UnifiedLayout'
import TradersDashboard from '@/app/components/TradersDashboard'
import TradersDashboardMobile from '@/app/components/TradersDashboardMobile'

interface SummaryData {
  total_pnl: number
  trading_volume: number
  pnl_today: number
  pnl_7d: number
  closed_orders: number
  closed_positions: number
  success_rate: number
  pnl_long: number
  pnl_short: number
  total_trades: number
  total_signals: number
}

export default function GhostMainDashboard() {
  const [isClient, setIsClient] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState('180d')
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  
  // Build timestamp: 2025-08-22T10:57:00Z

  useEffect(() => {
    setIsClient(true)
    fetchSummaryData()
  }, [selectedPeriod])

  const fetchSummaryData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/traders-analytics/summary?period=${selectedPeriod}`)
      const data = await response.json()
      setSummaryData(data)
    } catch (error) {
      console.error('Error fetching summary data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isClient) {
    return <div className="min-h-screen bg-black" />
  }

  // Функция для обработки клика по трейдеру
  const handleTraderClick = (traderId: string) => {
    router.push(`/trader/${traderId}`)
  }

  const periods = [
    { id: '7d', label: '7d' },
    { id: '30d', label: '30d' },
    { id: '60d', label: '60d' },
    { id: '90d', label: '90d' },
    { id: '180d', label: '180d' },
  ]

  return (
    <UnifiedLayout>
      <div className="space-y-6">
        {/* Enhanced Header Section with Mobile-First Design */}
        <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-4 sm:p-6 border border-gray-800/50 shadow-2xl">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            {/* Left Section - Title and Filters */}
            <div className="flex-1">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
                    📊 GHOST Trading Dashboard
                  </div>
                  <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg">
                    🎯 Pro Analytics
                  </div>
                </div>
              </div>
              
              {/* Period Filter Buttons - Mobile Optimized */}
              <div className="flex flex-wrap gap-2 mb-4">
                {periods.map((period) => (
                  <button 
                    key={period.id}
                    onClick={() => setSelectedPeriod(period.id)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                      selectedPeriod === period.id
                        ? 'bg-gradient-to-r from-orange-600 to-orange-700 text-white shadow-lg shadow-orange-500/25'
                        : 'bg-gray-800/50 text-gray-300 hover:bg-gray-700/50 hover:text-white'
                    }`}
                  >
                    {period.label}
                  </button>
                ))}
                <span className="hidden sm:inline-flex items-center px-4 py-2 text-gray-400 text-sm">
                  Пользовательский ранг
                </span>
              </div>
            </div>
            
            {/* Right Section - Statistics Cards - Mobile Responsive */}
            <div className="lg:w-96">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
                {/* Main P&L Stats */}
                <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/50 shadow-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-gray-300 text-sm font-medium">💰 Общий P&L (USD)</div>
                    <div className="text-xs text-gray-400">📊 Торговый объем</div>
                  </div>
                  <div className="flex justify-between items-end">
                    {loading ? (
                      <div className="text-gray-400 text-xl sm:text-2xl font-bold">Loading...</div>
                    ) : (
                      <div className={`text-xl sm:text-2xl font-bold ${
                        summaryData && summaryData.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {summaryData ? (summaryData.total_pnl >= 0 ? '+' : '') + summaryData.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '0.00'}
                      </div>
                    )}
                    {loading ? (
                      <div className="text-white text-lg font-semibold">Loading...</div>
                    ) : (
                      <div className="text-white text-lg font-semibold">
                        {summaryData ? 
                          summaryData.trading_volume >= 1000000 ? 
                            (summaryData.trading_volume / 1000000).toFixed(2) + 'M' : 
                            summaryData.trading_volume >= 1000 ?
                              (summaryData.trading_volume / 1000).toFixed(1) + 'K' :
                              summaryData.trading_volume.toFixed(0)
                          : '0'
                        }
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Данные на {new Date().toLocaleDateString()} UTC
                  </div>
                </div>
                
                {/* Today's Stats */}
                <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/50 shadow-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-gray-300 text-sm font-medium">📈 P&L сегодня</div>
                    <div className="text-gray-300 text-sm font-medium">📅 P&L 7 дн.</div>
                  </div>
                  <div className="flex justify-between items-end">
                    {loading ? (
                      <>
                        <div className="text-gray-400 text-lg font-bold">Loading...</div>
                        <div className="text-gray-400 text-lg font-bold">Loading...</div>
                      </>
                    ) : (
                      <>
                        <div className={`text-lg font-bold ${
                          summaryData && summaryData.pnl_today >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {summaryData ? (summaryData.pnl_today >= 0 ? '+' : '') + summaryData.pnl_today.toFixed(2) : '0.00'}
                        </div>
                        <div className={`text-lg font-bold ${
                          summaryData && summaryData.pnl_7d >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {summaryData ? (summaryData.pnl_7d >= 0 ? '+' : '') + summaryData.pnl_7d.toFixed(2) : '0.00'}
                        </div>
                      </>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Обновлено в реальном времени
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Additional Metrics - Mobile Responsive Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
            {/* Orders Statistics */}
            <div className="bg-gradient-to-br from-gray-900/30 to-gray-800/20 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/30 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  📋 Статистика ордеров
                </h3>
                <div className="text-xs text-gray-400">
                  🕒 {new Date().toLocaleDateString()} UTC
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  {loading ? (
                    <div className="text-2xl font-bold text-gray-400 mb-1">Loading...</div>
                  ) : (
                    <div className="text-2xl font-bold text-white mb-1">
                      {summaryData?.closed_orders || 0}
                    </div>
                  )}
                  <div className="text-xs text-gray-400">Закрытых ордеров</div>
                  {loading ? (
                    <div className="text-xs text-gray-400 mt-1">Loading...</div>
                  ) : (
                    <div className={`text-xs mt-1 ${
                      summaryData && summaryData.pnl_long >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      Long P&L: {summaryData ? (summaryData.pnl_long >= 0 ? '+' : '') + summaryData.pnl_long.toFixed(2) : '0.00'}
                    </div>
                  )}
                </div>
                <div className="text-center">
                  {loading ? (
                    <div className="text-2xl font-bold text-gray-400 mb-1">Loading...</div>
                  ) : (
                    <div className="text-2xl font-bold text-white mb-1">
                      {summaryData ? summaryData.success_rate.toFixed(0) + '%' : '0%'}
                    </div>
                  )}
                  <div className="text-xs text-gray-400">Успешных сделок</div>
                  {loading ? (
                    <div className="text-xs text-gray-400 mt-1">Loading...</div>
                  ) : (
                    <div className={`text-xs mt-1 ${
                      summaryData && summaryData.pnl_short >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      Short P&L: {summaryData ? (summaryData.pnl_short >= 0 ? '+' : '') + summaryData.pnl_short.toFixed(2) : '0.00'}
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* P&L Chart Placeholder */}
            <div className="bg-gradient-to-br from-gray-900/30 to-gray-800/20 backdrop-blur-sm rounded-2xl p-4 border border-gray-700/30 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  📊 График P&L
                </h3>
                {loading ? (
                  <div className="text-xs text-gray-400">Loading...</div>
                ) : (
                  <div className={`text-xs ${
                    summaryData && summaryData.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {summaryData ? (summaryData.total_pnl >= 0 ? '+' : '') + summaryData.total_pnl.toFixed(2) + ' USD' : '0.00 USD'}
                  </div>
                )}
              </div>
              
              <div className="h-24 sm:h-32 bg-gray-900/50 rounded-lg relative overflow-hidden">
                <div className={`absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t ${
                  summaryData && summaryData.total_pnl >= 0 ? 'from-emerald-900/40' : 'from-red-900/40'
                } to-transparent`}></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-xs text-gray-500">Interactive Chart</div>
                </div>
                {loading ? (
                  <div className="absolute bottom-2 left-2 text-xs text-gray-400">Loading...</div>
                ) : (
                  <>
                    <div className="absolute bottom-2 left-2 text-xs text-gray-400">
                      {summaryData ? summaryData.pnl_7d.toFixed(2) : '0.00'}
                    </div>
                    <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                      {summaryData ? summaryData.total_pnl.toFixed(2) : '0.00'}
                    </div>
                    <div className={`absolute top-2 right-2 text-xs ${
                      summaryData && summaryData.pnl_today >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {summaryData ? (summaryData.pnl_today >= 0 ? '+' : '') + summaryData.pnl_today.toFixed(2) + ' USD суточный' : '0.00 USD суточный'}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Responsive Traders Dashboard */}
        <div className="hidden lg:block">
          <TradersDashboard onTraderClick={handleTraderClick} />
        </div>
        
        <div className="lg:hidden">
          <TradersDashboardMobile onTraderClick={handleTraderClick} />
        </div>
      </div>
    </UnifiedLayout>
  )
}