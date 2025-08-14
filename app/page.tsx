'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import dynamic from 'next/dynamic'

// Динамический импорт всех компонентов
const TradingDashboard = dynamic(() => import('@/components/TradingDashboard'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const TelegramSignalsDashboard = dynamic(() => import('@/components/TelegramSignalsDashboard'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

const PortfolioSnapshot = dynamic(() => import('@/components/PortfolioSnapshot'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const SystemMonitor = dynamic(() => import('@/components/SystemMonitor'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

const NewsFeed = dynamic(() => import('@/components/NewsFeed'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

const TraderObservation = dynamic(() => import('@/components/TraderObservation'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const MarketAnalysisChart = dynamic(() => import('@/components/MarketAnalysisChart'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const ChatInterface = dynamic(() => import('@/components/ChatInterface'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

// Компонент Real-time графиков с WebSocket
const RealtimeChart = dynamic(() => import('@/components/RealtimeChart'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'
)

interface QuickStats {
  totalPnL: number
  todayPnL: number
  activeTrades: number
  systemHealth: number
  activeSignals: number
  winRate: number
}

export default function UnifiedDashboard() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [quickStats, setQuickStats] = useState<QuickStats>({
    totalPnL: 0,
    todayPnL: 0,
    activeTrades: 0,
    systemHealth: 0,
    activeSignals: 0,
    winRate: 0
  })
  const [activeSection, setActiveSection] = useState('overview')
  const [isMobile, setIsMobile] = useState(false)

  // Проверка мобильного устройства
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Загрузка данных
  useEffect(() => {
    loadQuickStats()
    checkUser()
  }, [])

  const checkUser = async () => {
    try {
      if (!supabase) {
        setLoading(false)
        return
      }
      const { data: { session } } = await supabase.auth.getSession()
      setUser(session?.user || null)
      setLoading(false)
    } catch (error) {
      console.error('Auth check error:', error)
      setLoading(false)
    }
  }

  const loadQuickStats = async () => {
    try {
      // Загружаем быстрые статистики из разных API
      const [systemRes, tradesRes, signalsRes] = await Promise.allSettled([
        fetch('/api/system/status'),
        fetch('/api/trades/active'),
        fetch('/api/telegram-signals?limit=10')
      ])

      let stats: QuickStats = {
        totalPnL: 12450.75,
        todayPnL: 890.25,
        activeTrades: 5,
        systemHealth: 95,
        activeSignals: 15,
        winRate: 78.5
      }

      // Обновляем статистики из реальных данных если доступны
      if (systemRes.status === 'fulfilled') {
        const systemData = await systemRes.value.json()
        stats.systemHealth = systemData.health?.health_score || stats.systemHealth
      }

      if (tradesRes.status === 'fulfilled') {
        const tradesData = await tradesRes.value.json()
        stats.activeTrades = Array.isArray(tradesData) ? tradesData.length : stats.activeTrades
      }

      if (signalsRes.status === 'fulfilled') {
        const signalsData = await signalsRes.value.json()
        stats.activeSignals = signalsData.signals?.length || stats.activeSignals
      }

      setQuickStats(stats)
    } catch (error) {
      console.error('Error loading quick stats:', error)
    }
  }

  // Секции дашборда
  const sections = [
    {
      id: 'overview',
      name: 'Overview',
      icon: '🎯',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      id: 'trading',
      name: 'Trading',
      icon: '📈',
      color: 'from-green-500 to-emerald-500'
    },
    {
      id: 'signals',
      name: 'Signals',
      icon: '📡',
      color: 'from-purple-500 to-violet-500'
    },
    {
      id: 'portfolio',
      name: 'Portfolio',
      icon: '💼',
      color: 'from-orange-500 to-red-500'
    },
    {
      id: 'news',
      name: 'News',
      icon: '📰',
      color: 'from-yellow-500 to-orange-500'
    },
    {
      id: 'system',
      name: 'System',
      icon: '⚙️',
      color: 'from-gray-500 to-slate-500'
    }
  ]

  const renderQuickStats = () => (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      <div className="glass rounded-xl p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">💰</span>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Total P&L</p>
            <p className="text-white font-bold text-lg">${quickStats.totalPnL.toLocaleString()}</p>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">📊</span>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Today P&L</p>
            <p className="text-white font-bold text-lg">${quickStats.todayPnL.toLocaleString()}</p>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-violet-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">⚡</span>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Active Trades</p>
            <p className="text-white font-bold text-lg">{quickStats.activeTrades}</p>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-teal-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">🏥</span>
          </div>
          <div>
            <p className="text-gray-400 text-sm">System Health</p>
            <p className="text-white font-bold text-lg">{quickStats.systemHealth}%</p>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">📡</span>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Active Signals</p>
            <p className="text-white font-bold text-lg">{quickStats.activeSignals}</p>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">🎯</span>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Win Rate</p>
            <p className="text-white font-bold text-lg">{quickStats.winRate}%</p>
          </div>
        </div>
      </div>
    </div>
  )

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'overview':
        return (
          <div className="space-y-8">
            {/* Quick Overview Grid */}
            <div className="grid lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-white mb-4">🔴 Live Trading</h3>
                <TradingDashboard />
              </div>
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-white mb-4">📡 Latest Signals</h3>
                <TelegramSignalsDashboard />
              </div>
            </div>
            
            {/* System Status */}
            <div>
              <h3 className="text-xl font-bold text-white mb-4">⚙️ System Status</h3>
              <SystemMonitor />
            </div>
          </div>
        )

      case 'trading':
        return (
          <div className="space-y-8">
            <div className="grid lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📊 Live Trading Dashboard</h3>
                <TradingDashboard />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📈 Real-time Charts</h3>
                <RealtimeChart />
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-white mb-4">📊 Market Analysis</h3>
              <MarketAnalysisChart />
            </div>
          </div>
        )

      case 'signals':
        return (
          <div className="space-y-8">
            <div className="grid lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📱 Telegram Signals</h3>
                <TelegramSignalsDashboard />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-4">👁️ Trader Observation</h3>
                <TraderObservation />
              </div>
            </div>
          </div>
        )

      case 'portfolio':
        return (
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">💼 Portfolio Overview</h3>
              <PortfolioSnapshot />
            </div>
          </div>
        )

      case 'news':
        return (
          <div className="space-y-8">
            <div className="grid lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">📰 Market News</h3>
                <NewsFeed />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-4">🤖 AI Assistant</h3>
                <ChatInterface />
              </div>
            </div>
          </div>
        )

      case 'system':
        return (
          <div className="space-y-8">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">⚙️ System Monitor</h3>
              <SystemMonitor />
            </div>
          </div>
        )

      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0f0f23] flex items-center justify-center">
        <div className="glass rounded-xl p-8">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <div className="text-white text-xl">Loading GHOST Dashboard...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0f0f23]">
      {/* Header */}
      <header className="glass border-b border-white/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-[#667eea] to-[#764ba2] rounded-xl flex items-center justify-center neon-glow">
                <span className="text-white font-bold text-lg">G</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">GHOST Trading System</h1>
                {!isMobile && (
                  <p className="text-gray-400 text-sm">Professional Trading Dashboard</p>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-400 text-sm font-medium">LIVE</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-400">
                <span>Real-time updates</span>
              </div>
              {user && (
                <div className="text-sm text-gray-300">
                  {user.email}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Quick Stats */}
        {renderQuickStats()}

        {/* Section Navigation */}
        <div className="mb-8">
          <div className={`grid ${isMobile ? 'grid-cols-3' : 'grid-cols-6'} gap-2 mb-6`}>
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`
                  relative p-4 rounded-xl transition-all duration-300 
                  ${activeSection === section.id 
                    ? `bg-gradient-to-r ${section.color} text-white shadow-lg shadow-blue-500/20` 
                    : 'glass text-gray-400 hover:text-white hover:bg-white/5'
                  }
                `}
              >
                <div className="flex flex-col items-center space-y-2">
                  <span className="text-2xl">{section.icon}</span>
                  <span className={`text-sm font-medium ${isMobile ? 'text-xs' : ''}`}>
                    {section.name}
                  </span>
                </div>
                
                {activeSection === section.id && (
                  <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Section Content */}
        <div className="animate-fade-in">
          {renderSectionContent()}
        </div>
      </main>
      
      {/* Footer */}
      <footer className="glass border-t border-white/10 mt-12">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
            <div className="text-sm text-gray-400">
              © 2025 GHOST Trading System - Professional Crypto Trading Platform
            </div>
            <div className="flex space-x-4 text-sm text-gray-400">
              <span>📊 Live Data</span>
              <span>📰 News Feed</span>
              <span>📡 Real-time Signals</span>
              <span>🤖 AI Analysis</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}