'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import dynamic from 'next/dynamic'

// Импортируем новый точный дизайн как на скрине
const GhostLayoutExact = dynamic(() => import('@/components/GhostLayoutExact'), {
  ssr: false,
  loading: () => <div className="min-h-screen bg-black animate-pulse" />
})

const TradersAnalyticsDashboard = dynamic(() => import('@/components/TradersAnalyticsDashboard'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

// Все компоненты из старого дашборда
const TradingDashboard = dynamic(() => import('@/components/TradingDashboard'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

const TelegramSignalsDashboard = dynamic(() => import('@/components/TelegramSignalsDashboard'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const SystemMonitor = dynamic(() => import('@/components/SystemMonitor'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const PortfolioSnapshot = dynamic(() => import('@/components/PortfolioSnapshot'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

const NewsFeed = dynamic(() => import('@/components/NewsFeed'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const TraderObservation = dynamic(() => import('@/components/TraderObservation'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

const MarketAnalysisChart = dynamic(() => import('@/components/MarketAnalysisChart'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

const ChatInterface = dynamic(() => import('@/components/ChatInterface'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const RealtimeChart = dynamic(() => import('@/components/RealtimeChart'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

const NewsAnalysisDashboard = dynamic(() => import('@/components/NewsAnalysisDashboard'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const NewsAnalyticsTab = dynamic(() => import('@/components/NewsAnalyticsTab'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'
)

export default function GhostDashboard() {
  const [activeSection, setActiveSection] = useState('traders')
  const [loading, setLoading] = useState(true)

  const handlePageChange = (page: string) => {
    setActiveSection(page)
  }

  useEffect(() => {
    // Имитируем загрузку
    setTimeout(() => setLoading(false), 1000)
  }, [])

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'traders':
        return <TradersAnalyticsDashboard />
      
      case 'tasks':
        return (
          <div className="space-y-8">
            <div className="grid lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📈 Live Trading</h3>
                <TradingDashboard />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📈 Real-time Charts</h3>
                <RealtimeChart />
              </div>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-4">💼 Portfolio Overview</h3>
              <PortfolioSnapshot />
            </div>
          </div>
        )

      case 'messages':
        return (
          <div className="space-y-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📱 Telegram Signals</h3>
                <TelegramSignalsDashboard />
              </div>
              <div>
              <h3 className="text-xl font-bold text-white mb-4">🤖 AI Assistant</h3>
              <ChatInterface />
            </div>
          </div>
        )

      case 'goals':
        return <NewsAnalyticsTab />
      
      case 'groups':
        return (
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">📊 Live Trading Dashboard</h3>
              <TradingDashboard />
            </div>
            <div className="grid lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📈 Real-time Charts</h3>
                <RealtimeChart />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📊 Market Analysis</h3>
                <MarketAnalysisChart />
              </div>
            </div>
          </div>
        )

      case 'settings':
        return (
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">⚙️ System Monitor</h3>
              <SystemMonitor />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-4">💼 Portfolio Snapshot</h3>
              <PortfolioSnapshot />
            </div>
          </div>
        )

      default:
        return <TradersAnalyticsDashboard />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-yellow-500 border-t-transparent rounded-full"></div>
      </div>
    )
  }

  return (
    <GhostLayoutExact 
      currentPage={activeSection as any}
      onPageChange={handlePageChange}
    >
          {renderSectionContent()}
    </GhostLayoutExact>
  )
}