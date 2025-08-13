'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'

// Динамический импорт компонентов
const PortfolioSnapshot = dynamic(() => import('@/components/PortfolioSnapshot'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const ChatInterface = dynamic(() => import('@/components/ChatInterface'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

const NewsFeed = dynamic(() => import('@/components/NewsFeed'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

const SystemMonitor = dynamic(() => import('@/components/SystemMonitor'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

const SignalsMonitor = dynamic(() => import('@/components/SignalsMonitor'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-64" />
})

const MarketAnalysisChart = dynamic(() => import('@/components/MarketAnalysisChart'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const NewsImpactCorrelation = dynamic(() => import('@/components/NewsImpactCorrelation'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const TradingDashboard = dynamic(() => import('@/components/TradingDashboard'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const TraderObservation = dynamic(() => import('@/components/TraderObservation'), { 
  ssr: false,
  loading: () => <div className="glass rounded-xl p-6 animate-pulse bg-gray-800/20 h-96" />
})

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'
)

export default function Dashboard() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('trading')
  const [activePositions, setActivePositions] = useState([])
  const [portfolioStats, setPortfolioStats] = useState({
    totalBalance: 0,
    totalPnL: 0,
    totalROI: 0,
    winRate: 0,
    totalTrades: 0
  })
  const router = useRouter()

  // Конфигурация табов
  const tabs = [
    {
      id: 'trading',
      name: 'Live Trading',
      icon: '⚡',
      description: 'Real-time PnL & Active Trades'
    },
    {
      id: 'observation',
      name: 'Trader Signals',
      icon: '👁️',
      description: 'Signal Analysis & Performance'
    },
    {
      id: 'portfolio',
      name: 'Portfolio',
      icon: '💼',
      description: 'Balance & Trade History'
    },
    {
      id: 'analytics',
      name: 'Analytics',
      icon: '📊',
      description: 'Market Analysis & Charts'
    },
    {
      id: 'news',
      name: 'News & AI',
      icon: '🔥',
      description: 'Critical News & Impact'
    },
    {
      id: 'system',
      name: 'System',
      icon: '⚙️',
      description: 'Monitor & Settings'
    }
  ]

  useEffect(() => {
    checkUser()
    loadUserData()
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

  const loadUserData = async () => {
    try {
      const response = await fetch('/api/user')
      if (response.ok) {
        const data = await response.json()
        setActivePositions(data.trades || [])
        // Здесь можно загрузить статистику портфолио
      }
    } catch (error) {
      console.error('Error loading user data:', error)
    }
  }

  const handleSignOut = async () => {
    try {
      if (supabase) {
    await supabase.auth.signOut()
      }
      router.push('/auth')
    } catch (error) {
      console.error('Sign out error:', error)
    router.push('/auth')
    }
  }

  const handleSignIn = () => {
    router.push('/auth')
  }

  // Функция для рендеринга контента по табам
  const renderTabContent = () => {
    switch (activeTab) {
      case 'trading':
    return (
          <div className="space-y-6">
            <TradingDashboard />
      </div>
    )

      case 'observation':
  return (
          <div className="space-y-6">
            <TraderObservation />
          </div>
        )
      
      case 'portfolio':
        return (
          <div className="space-y-6">
            <PortfolioSnapshot />
            
            {/* Active Positions */}
            <div className="glass rounded-xl p-6">
              <h3 className="text-xl font-semibold text-white mb-6">Активные позиции</h3>
              
              <div className="space-y-4">
                <div className="border border-white/10 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-[#667eea] to-[#764ba2] rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold">BTC</span>
                      </div>
                      <div>
                        <h4 className="text-white font-medium">BTC/USDT</h4>
                        <p className="text-gray-400 text-sm">Long • Открыта 2 часа назад</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-green-400 font-semibold">+$450.25</div>
                      <div className="text-green-400 text-sm">+3.2%</div>
                    </div>
            </div>
            
                  <div className="grid md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Цена входа:</span>
                      <span className="text-white ml-2">$42,150</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Текущая цена:</span>
                      <span className="text-white ml-2">$43,250</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Размер:</span>
                      <span className="text-white ml-2">0.05 BTC</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Плечо:</span>
                      <span className="text-white ml-2">20x</span>
                    </div>
            </div>
            
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <div className="flex justify-between items-center">
                      <div className="flex space-x-2">
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">TP1: $44,500</span>
                        <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">SL: $41,200</span>
                      </div>
                      <button className="px-4 py-2 bg-red-500/20 text-red-400 text-sm rounded-lg hover:bg-red-500/30 transition-all duration-200">
                        Закрыть позицию
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      
      case 'analytics':
        return (
          <div className="space-y-6">
            <MarketAnalysisChart />
            <NewsImpactCorrelation />

          {/* Market Overview */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="glass rounded-xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Bitcoin (BTC)</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-400">Цена</span>
                  <span className="text-white font-semibold">$43,250.50</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Изменение 24ч</span>
                  <span className="text-green-400">+2.5%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Настроения новостей</span>
                  <span className="text-green-400">75% позитивные</span>
                </div>
                <div className="border-t border-white/10 pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Рекомендация</span>
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                      BUY
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Позитивные новости о Bitcoin ETF</p>
                </div>
              </div>
            </div>

            <div className="glass rounded-xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Ethereum (ETH)</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-400">Цена</span>
                  <span className="text-white font-semibold">$2,650.30</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Изменение 24ч</span>
                  <span className="text-green-400">+3.2%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Настроения новостей</span>
                  <span className="text-green-400">80% позитивные</span>
                </div>
                <div className="border-t border-white/10 pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Рекомендация</span>
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                      BUY
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Рост Layer 2 решений</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      
      case 'news':
        return (
          <div className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              <NewsFeed />

          {/* Trading Signals */}
          <div className="glass rounded-xl p-6">
            <h3 className="text-xl font-semibold text-white mb-6">Торговые сигналы</h3>
            
            <div className="space-y-4">
              <div className="border border-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-[#667eea] to-[#764ba2] rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold">BTC</span>
                    </div>
                    <div>
                      <h4 className="text-white font-medium">BTC/USDT</h4>
                      <p className="text-gray-400 text-sm">На основе анализа новостей</p>
                    </div>
                  </div>
                  
                  <div className="px-4 py-2 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                    BUY
                  </div>
                </div>
                
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Цена входа:</span>
                    <span className="text-white ml-2">$43,250</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Цель:</span>
                    <span className="text-white ml-2">$45,400</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Стоп:</span>
                    <span className="text-white ml-2">$41,100</span>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-white/10">
                  <p className="text-gray-400 text-sm">Позитивные новости о Bitcoin ETF с высоким влиянием</p>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-gray-500">Уверенность: 95%</span>
                    <button className="px-4 py-2 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white text-sm rounded-lg hover:from-[#5a6fd8] hover:to-[#6a4190] transition-all duration-200">
                      Исполнить сигнал
                    </button>
                  </div>
                </div>
              </div>
                </div>
              </div>
            </div>
            <ChatInterface />
          </div>
        )
      
      case 'system':
        return (
          <div className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              <SystemMonitor />
              <SignalsMonitor />
            </div>
            <ChatInterface />
          </div>
        )
      
      default:
        return <div>Выберите вкладку</div>
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0f0f23] flex items-center justify-center">
        <div className="text-white text-xl">Загрузка дашборда...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0f0f23]">
      {/* Header */}
      <header className="glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-[#667eea] to-[#764ba2] rounded-xl flex items-center justify-center neon-glow">
                <span className="text-white font-bold text-lg">G</span>
              </div>
              <span className="text-2xl font-bold gradient-text">GHOST Dashboard</span>
            </div>
            
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <span className="text-gray-300">{user.email}</span>
                  <button
                    onClick={handleSignOut}
                    className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
                  >
                    Выйти
                  </button>
                </>
              ) : (
                <button
                  onClick={handleSignIn}
                  className="px-4 py-2 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white text-sm rounded-lg hover:from-[#5a6fd8] hover:to-[#6a4190] transition-all duration-200"
                >
                  Войти
                </button>
              )}
            </div>
          </div>
                    </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-black/20 backdrop-blur-md border-b border-white/5 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto">
          {/* Desktop Navigation */}
          <div className="hidden lg:block px-6">
            <div className="flex space-x-2 py-4">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    group relative flex items-center space-x-3 px-4 py-3 rounded-xl 
                    transition-all duration-300 ease-out min-w-max
                    ${activeTab === tab.id 
                      ? 'bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white shadow-lg shadow-[#667eea]/20' 
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }
                  `}
                >
                  <span className="text-lg">{tab.icon}</span>
                  <div className="text-left">
                    <div className="text-sm font-medium">{tab.name}</div>
                    <div className="text-xs opacity-70 mt-0.5">
                      {tab.description}
                    </div>
                  </div>
                  
                  {/* Active indicator */}
                  {activeTab === tab.id && (
                    <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2">
                      <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                    </div>
                  )}
                </button>
              ))}
                  </div>
                </div>
                
          {/* Mobile Navigation */}
          <div className="lg:hidden px-2">
            <div className="flex space-x-1 py-3 overflow-x-auto scrollbar-hide">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    group relative flex flex-col items-center justify-center px-3 py-2 rounded-lg 
                    transition-all duration-300 ease-out min-w-[64px]
                    ${activeTab === tab.id 
                      ? 'bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white shadow-lg shadow-[#667eea]/20' 
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }
                  `}
                >
                  <span className="text-lg mb-1">{tab.icon}</span>
                  <div className="text-[10px] font-medium text-center leading-tight">
                    {tab.name.split(' ').map((word, i) => (
                      <div key={i}>{word}</div>
                    ))}
                  </div>
                  
                  {/* Active indicator for mobile */}
                  {activeTab === tab.id && (
                    <div className="absolute -bottom-3 left-1/2 transform -translate-x-1/2">
                      <div className="w-1 h-1 bg-white rounded-full"></div>
                  </div>
                  )}
                    </button>
              ))}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <div className="min-h-[calc(100vh-12rem)]">
          {renderTabContent()}
        </div>
      </main>
    </div>
  )
} 