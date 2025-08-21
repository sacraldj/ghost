'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Импортируем компоненты
import GhostLayoutExact from '@/app/components/GhostLayoutExact'
import TradersDashboard from '@/app/components/TradersDashboard'
import TradersDashboardMobile from '@/app/components/TradersDashboardMobile'

export default function GhostMainDashboard() {
  const [isClient, setIsClient] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState('180d')
  const router = useRouter()

  useEffect(() => {
    setIsClient(true)
  }, [])

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
    <GhostLayoutExact currentPage="traders">
      <div className="space-y-6">
        {/* Enhanced Header Section with Mobile-First Design */}
        <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-4 sm:p-6 border border-gray-800/50 shadow-2xl">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            {/* Left Section - Title and Filters */}
            <div className="flex-1">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
                    📊 СТАТИСТИКА ПО ТРЕЙДЕРАМ
                  </div>
                  <div className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-black px-4 py-2 rounded-xl text-sm font-bold shadow-lg">
                    🎯 ALL TRADERS
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
                <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-gray-400 text-sm">Общий P&L (USD)</div>
                    <div className="text-xs text-gray-500">Торговый объем</div>
                  </div>
                  <div className="flex justify-between items-end">
                    <div className="text-red-400 text-xl sm:text-2xl font-bold">-2,969.00</div>
                    <div className="text-white text-lg font-semibold">1.73M</div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Данные на {new Date().toLocaleDateString()} UTC
                  </div>
                </div>
                
                {/* Today's Stats */}
                <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-gray-400 text-sm">P&L сегодня</div>
                    <div className="text-gray-400 text-sm">P&L 7 дн.</div>
                  </div>
                  <div className="flex justify-between items-end">
                    <div className="text-emerald-400 text-lg font-bold">+1.79</div>
                    <div className="text-red-400 text-lg font-bold">-2.74</div>
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
            <div className="bg-gray-800/20 rounded-xl p-4 border border-gray-700/20">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-white font-semibold">Статистика ордеров</h3>
                <div className="text-xs text-gray-500">
                  {new Date().toLocaleDateString()} UTC
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white mb-1">1544</div>
                  <div className="text-xs text-gray-400">Закрытых ордеров</div>
                  <div className="text-xs text-red-400 mt-1">Long P&L: -2,152.86</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white mb-1">45%</div>
                  <div className="text-xs text-gray-400">Успешных сделок</div>
                  <div className="text-xs text-red-400 mt-1">Short P&L: -816.14</div>
                </div>
              </div>
            </div>
            
            {/* P&L Chart Placeholder */}
            <div className="bg-gray-800/20 rounded-xl p-4 border border-gray-700/20">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-white font-semibold">График P&L</h3>
                <div className="text-xs text-red-400">-2,498.75 USD</div>
              </div>
              
              <div className="h-24 sm:h-32 bg-gray-900/50 rounded-lg relative overflow-hidden">
                <div className="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-red-900/40 to-transparent"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-xs text-gray-500">Interactive Chart</div>
                </div>
                <div className="absolute bottom-2 left-2 text-xs text-gray-400">-744.39</div>
                <div className="absolute bottom-2 right-2 text-xs text-gray-400">-2,977.58</div>
                <div className="absolute top-2 right-2 text-xs text-emerald-400">+20.40 USD суточный</div>
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
    </GhostLayoutExact>
  )
}