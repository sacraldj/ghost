'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'

// Импортируем точный дизайн с левой панелью
const GhostLayoutExact = dynamic(() => import('@/components/GhostLayoutExact'), {
  ssr: false,
  loading: () => <div className="min-h-screen bg-black animate-pulse" />
})

// Импортируем исправленный TradersDashboard
const TradersDashboard = dynamic(() => import('@/components/TradersDashboard'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

// Другие компоненты для разных секций
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

const NewsAnalysisDashboard = dynamic(() => import('@/components/NewsAnalysisDashboard'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const NewsFeed = dynamic(() => import('@/components/NewsFeed'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

const NewsImpactCorrelation = dynamic(() => import('@/components/NewsImpactCorrelation'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-96" />
})

const ChatInterface = dynamic(() => import('@/components/ChatInterface'), { 
  ssr: false,
  loading: () => <div className="p-6 animate-pulse bg-gray-900 h-64" />
})

export default function GhostDashboard() {
  const [activeSection, setActiveSection] = useState('traders')
  const [loading, setLoading] = useState(true)

  const handlePageChange = (page: string) => {
    setActiveSection(page)
  }

  useEffect(() => {
    // Короткая загрузка
    setTimeout(() => setLoading(false), 500)
  }, [])

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'traders':
        return <TradersDashboard />
      
      case 'tasks':
        return (
          <div className="space-y-8 p-6">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">📈 Live Trading</h3>
              <TradingDashboard />
            </div>
          </div>
        )

      case 'messages':
        return (
          <div className="space-y-8 p-6">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">📱 Telegram Signals</h3>
              <TelegramSignalsDashboard />
            </div>
          </div>
        )

      case 'goals':
        return (
          <div className="space-y-6 p-6">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-3xl font-bold text-white">📰 News & AI Analysis</h1>
              <div className="text-sm text-gray-400">
                Real-time market intelligence
              </div>
            </div>
            
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Лента новостей */}
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📰 Critical News Feed</h3>
                <NewsFeed />
              </div>
              
              {/* AI Chat */}
              <div>
                <h3 className="text-xl font-bold text-white mb-4">🤖 AI Assistant</h3>
                <ChatInterface />
              </div>
            </div>
            
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Анализ новостей */}
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📊 News Analysis</h3>
                <NewsAnalysisDashboard />
              </div>
              
              {/* Корреляция новостей с ценами */}
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📈 Price Impact Correlation</h3>
                <NewsImpactCorrelation />
              </div>
            </div>
          </div>
        )
      
      case 'groups':
        return (
          <div className="space-y-8 p-6">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">👥 Trading Groups</h3>
              <TradingDashboard />
            </div>
          </div>
        )

      case 'settings':
        return (
          <div className="space-y-8 p-6">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">⚙️ System Monitor</h3>
              <SystemMonitor />
            </div>
          </div>
        )

      default:
        return <TradersDashboard />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin w-8 h-8 border-4 border-yellow-500 border-t-transparent rounded-full"></div>
          <div className="text-yellow-500 font-bold">Loading GHOST Dashboard...</div>
        </div>
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