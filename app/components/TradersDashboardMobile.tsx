"use client"

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Avatar, AvatarFallback } from './ui/avatar'
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Users, 
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  ChevronRight,
  Filter,
  Search
} from 'lucide-react'

interface TraderStats {
  id: string
  name: string
  avatar?: string
  channel: string
  totalSignals: number
  winRate: number
  roi: number
  pnl: number
  avgHoldTime: string
  lastSignal: string
  status: 'active' | 'inactive'
  performance7d: number
  performance30d: number
  successfulTrades: number
  totalTrades: number
  maxDrawdown: number
  sharpeRatio: number
  totalVolume: number
  followers?: number
}

interface TradersDashboardMobileProps {
  onTraderClick?: (traderId: string) => void
}

export default function TradersDashboardMobile({ onTraderClick }: TradersDashboardMobileProps) {
  const [traders, setTraders] = useState<TraderStats[]>([])
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState('pnl')
  const [period, setPeriod] = useState('30d')
  const [searchTerm, setSearchTerm] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const router = useRouter()

  useEffect(() => {
    fetchTraders()
  }, [sortBy, period])

  const fetchTraders = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/traders?sortBy=${sortBy}&period=${period}&limit=20`)
      const data = await response.json()
      
      if (data.traders) {
        setTraders(data.traders)
      }
    } catch (error) {
      console.error('Error fetching traders:', error)
      // Fallback demo data for mobile
      setTraders([
        {
          id: 'whales_guide_main',
          name: 'Whales Guide',
          avatar: '🐋',
          channel: '@Whalesguide',
          totalSignals: 156,
          winRate: 68.5,
          roi: 24.8,
          pnl: 12450.00,
          avgHoldTime: '4h 32m',
          lastSignal: '2h ago',
          status: 'active',
          performance7d: 8.3,
          performance30d: 24.8,
          successfulTrades: 107,
          totalTrades: 156,
          maxDrawdown: -8.2,
          sharpeRatio: 1.85,
          totalVolume: 245000,
          followers: 8500
        },
        {
          id: 'crypto_hub_vip',
          name: 'Crypto Hub VIP',
          avatar: '💎',
          channel: '@cryptohubvip',
          totalSignals: 134,
          winRate: 72.1,
          roi: 31.2,
          pnl: 18750.00,
          avgHoldTime: '3h 15m',
          lastSignal: '45m ago',
          status: 'active',
          performance7d: 12.1,
          performance30d: 31.2,
          successfulTrades: 97,
          totalTrades: 134,
          maxDrawdown: -6.8,
          sharpeRatio: 2.15,
          totalVolume: 312000,
          followers: 12500
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleTraderClick = (traderId: string) => {
    if (onTraderClick) {
      onTraderClick(traderId)
    } else {
      router.push(`/trader/${traderId}`)
    }
  }

  const filteredTraders = traders.filter(trader => 
    trader.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    trader.channel.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-gray-900/50 rounded-2xl p-4 animate-pulse">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gray-800 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-800 rounded w-32" />
                <div className="h-3 bg-gray-800 rounded w-24" />
              </div>
              <div className="w-16 h-8 bg-gray-800 rounded" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Mobile Header with Search and Filters */}
      <div className="bg-gradient-to-r from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-4 border border-gray-800/50">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Top Traders
              </h2>
              <p className="text-sm text-gray-400">Real-time performance</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="bg-gray-800/50 border-gray-700/50 text-white hover:bg-gray-700/50"
            >
              <Filter className="w-4 h-4" />
            </Button>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search traders..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all duration-200"
            />
          </div>

          {/* Filters (collapsible) */}
          {showFilters && (
            <div className="flex flex-col sm:flex-row gap-3 pt-2 border-t border-gray-800/50">
              <select 
                className="flex-1 bg-gray-800/50 text-white px-3 py-2 rounded-xl text-sm border border-gray-700/50 focus:border-blue-500/50 transition-all duration-200"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="pnl">Sort by P&L</option>
                <option value="winRate">Sort by Win Rate</option>
                <option value="roi">Sort by ROI</option>
                <option value="totalSignals">Sort by Signals</option>
              </select>
              <select 
                className="flex-1 bg-gray-800/50 text-white px-3 py-2 rounded-xl text-sm border border-gray-700/50 focus:border-blue-500/50 transition-all duration-200"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option value="7d">7 Days</option>
                <option value="30d">30 Days</option>
                <option value="90d">90 Days</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Traders List */}
      <div className="space-y-3">
        {filteredTraders.map((trader, index) => (
          <div
            key={trader.id}
            onClick={() => handleTraderClick(trader.id)}
            className="bg-gradient-to-r from-gray-900/80 to-gray-950/80 backdrop-blur-sm rounded-2xl p-4 border border-gray-800/50 hover:border-blue-500/30 transition-all duration-300 active:scale-98 cursor-pointer shadow-lg hover:shadow-xl"
            style={{
              animationDelay: `${index * 100}ms`,
              animation: 'fadeInUp 0.5s ease-out forwards'
            }}
          >
            <div className="flex items-center gap-4">
              {/* Avatar and Basic Info */}
              <div className="flex-shrink-0">
                <div className="relative">
                  <Avatar className="w-14 h-14 border-2 border-gray-700/50">
                    <AvatarFallback className="bg-gradient-to-r from-blue-600 to-purple-600 text-white text-lg font-bold">
                      {trader.avatar || trader.name.charAt(0)}
                    </AvatarFallback>
                  </Avatar>
                  <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-gray-900 ${
                    trader.status === 'active' ? 'bg-emerald-500' : 'bg-gray-500'
                  }`} />
                </div>
              </div>

              {/* Main Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-white text-sm truncate">
                      {trader.name}
                    </h3>
                    <p className="text-xs text-gray-400 truncate">
                      {trader.channel}
                    </p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="bg-gray-800/30 rounded-lg p-2">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <DollarSign className="w-3 h-3 text-emerald-400" />
                      <span className="text-xs font-medium text-emerald-400">P&L</span>
                    </div>
                    <div className={`text-sm font-bold ${
                      trader.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      ${trader.pnl >= 0 ? '+' : ''}${trader.pnl.toFixed(0)}
                    </div>
                  </div>

                  <div className="bg-gray-800/30 rounded-lg p-2">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <Activity className="w-3 h-3 text-blue-400" />
                      <span className="text-xs font-medium text-blue-400">Win</span>
                    </div>
                    <div className="text-sm font-bold text-white">
                      {trader.winRate.toFixed(1)}%
                    </div>
                  </div>

                  <div className="bg-gray-800/30 rounded-lg p-2">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <TrendingUp className="w-3 h-3 text-purple-400" />
                      <span className="text-xs font-medium text-purple-400">ROI</span>
                    </div>
                    <div className={`text-sm font-bold ${
                      trader.roi >= 0 ? 'text-purple-400' : 'text-red-400'
                    }`}>
                      {trader.roi >= 0 ? '+' : ''}{trader.roi.toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Capital Simulation Row */}
                <div className="mt-3 p-3 bg-blue-600/10 border border-blue-500/20 rounded-xl">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-blue-400" />
                      <span className="text-sm font-medium text-blue-400">Капитал ($10,000)</span>
                    </div>
                    <div className="text-lg font-bold text-blue-400">
                      ${(10000 + (10000 * trader.roi / 100)).toFixed(0)}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Симуляция прибыли с капиталом $10,000
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 mt-3">
                  <Button
                    size="sm"
                    className="flex-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs py-1 h-8"
                    onClick={(e) => {
                      e.stopPropagation()
                      console.log(`TP1 clicked for trader ${trader.id}`)
                    }}
                  >
                    TP
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs py-1 h-8"
                    onClick={(e) => {
                      e.stopPropagation()
                      console.log(`TP2 clicked for trader ${trader.id}`)
                    }}
                  >
                    TP2
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 bg-gray-800/30 hover:bg-gray-700/50 text-gray-300 border-gray-600/50 text-xs py-1 h-8"
                    onClick={(e) => {
                      e.stopPropagation()
                      console.log(`Follow clicked for trader ${trader.id}`)
                    }}
                  >
                    Follow
                  </Button>
                </div>

                {/* Last Activity */}
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-800/30">
                  <span className="text-xs text-gray-500">
                    Last signal: {trader.lastSignal}
                  </span>
                  <Badge 
                    variant={trader.status === 'active' ? 'default' : 'secondary'}
                    className={`text-xs ${
                      trader.status === 'active' 
                        ? 'bg-emerald-600/20 text-emerald-400 border-emerald-500/30' 
                        : 'bg-gray-600/20 text-gray-400 border-gray-500/30'
                    }`}
                  >
                    {trader.status}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredTraders.length === 0 && (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-400 mb-2">No traders found</h3>
          <p className="text-sm text-gray-500">Try adjusting your search or filters</p>
        </div>
      )}
    </div>
  )
}

// CSS for animations
const styles = `
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
`

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style')
  styleSheet.type = 'text/css'
  styleSheet.innerText = styles
  document.head.appendChild(styleSheet)
}
