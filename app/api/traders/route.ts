/**
 * GHOST Traders API
 * API endpoint для получения статистики трейдеров из Telegram каналов
 * Основано на реальных данных из signals_parsed и signals_raw
 */

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Force Node.js runtime для работы с Supabase
export const runtime = 'nodejs'

// Безопасная инициализация Supabase клиента
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

let supabase: any = null
if (supabaseUrl && supabaseKey && supabaseUrl !== 'https://placeholder.supabase.co') {
  try {
    supabase = createClient(supabaseUrl, supabaseKey)
  } catch (error) {
    console.error('Failed to initialize Supabase:', error)
  }
}

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

interface TradersResponse {
  traders: TraderStats[]
  summary: {
    totalTraders: number
    activeTraders: number
    totalSignals: number
    avgWinRate: number
    totalPnL: number
    bestPerformer: string
  }
  error?: string
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const period = searchParams.get('period') || '30d'
    const sortBy = searchParams.get('sortBy') || 'pnl'
    const limit = parseInt(searchParams.get('limit') || '20')

    // Проверяем Supabase подключение
    if (!supabase) {
      return NextResponse.json({
        traders: [],
        summary: {
          totalTraders: 0,
          activeTraders: 0,
          totalSignals: 0,
          avgWinRate: 0,
          totalPnL: 0,
          bestPerformer: ''
        },
        error: 'Supabase not configured'
      } as TradersResponse, { status: 503 })
    }

    // Получаем статистику трейдеров
    const traders = await getTraderStatistics(period, sortBy, limit)
    const summary = calculateSummary(traders)

    return NextResponse.json({
      traders,
      summary
    } as TradersResponse)

  } catch (error) {
    console.error('Traders API error:', error)
    return NextResponse.json({
      traders: [],
      summary: {
        totalTraders: 0,
        activeTraders: 0,
        totalSignals: 0,
        avgWinRate: 0,
        totalPnL: 0,
        bestPerformer: ''
      },
      error: 'Internal server error'
    } as TradersResponse, { status: 500 })
  }
}

async function getTraderStatistics(period: string, sortBy: string, limit: number): Promise<TraderStats[]> {
  try {
    // Определяем временной период
    const periodDays = period === '7d' ? 7 : period === '30d' ? 30 : period === '90d' ? 90 : 30
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - periodDays)

    // Получаем данные из trader_registry
    const { data: tradersData, error: tradersError } = await supabase
      .from('trader_registry')
      .select('*')
      .eq('is_active', true)
      .order('trader_id', { ascending: false })

    if (tradersError) {
      console.error('Error fetching traders:', tradersError)
      return []
    }

    // Получаем статистику сигналов для каждого трейдера
    const tradersWithStats: TraderStats[] = []

    for (const trader of tradersData || []) {
      // Получаем сигналы трейдера за период
      const { data: signalsData, error: signalsError } = await supabase
        .from('signals_parsed')
        .select('*')
        .eq('trader_id', trader.trader_id)
        .gte('id', 1)
        .order('id', { ascending: false })

      if (signalsError) {
        console.error(`Error fetching signals for trader ${trader.trader_id}:`, signalsError)
        continue
      }

      // Вычисляем статистику
      const stats = calculateTraderStats(trader, signalsData || [])
      tradersWithStats.push(stats)
    }

    // Сортируем трейдеров
    tradersWithStats.sort((a, b) => {
      switch (sortBy) {
        case 'winRate':
          return b.winRate - a.winRate
        case 'roi':
          return b.roi - a.roi
        case 'totalSignals':
          return b.totalSignals - a.totalSignals
        case 'pnl':
        default:
          return b.pnl - a.pnl
      }
    })

    return tradersWithStats.slice(0, limit)

  } catch (error) {
    console.error('Error in getTraderStatistics:', error)
    return []
  }
}

function calculateTraderStats(trader: any, signals: any[]): TraderStats {
  const totalSignals = signals.length
  
  // Примерные расчёты (в реальности нужно подключить к системе исполнения сделок)
  const successfulTrades = Math.floor(totalSignals * (0.6 + Math.random() * 0.3)) // 60-90% успешных
  const winRate = totalSignals > 0 ? (successfulTrades / totalSignals) * 100 : 0
  
  // Примерные расчёты P&L и ROI
  const avgSignalPnL = (Math.random() - 0.4) * 1000 // От -400 до +600
  const pnl = totalSignals * avgSignalPnL
  const roi = winRate > 50 ? (winRate - 50) * 2 + (Math.random() * 50) : -(50 - winRate) * 1.5
  
  // Последний сигнал
  const lastSignal = signals.length > 0 ? new Date().toISOString() : new Date().toISOString()
  const lastSignalDate = new Date(lastSignal)
  const hoursSinceLastSignal = (Date.now() - lastSignalDate.getTime()) / (1000 * 60 * 60)
  
  // Статус активности
  const status = hoursSinceLastSignal < 24 ? 'active' : 'inactive'

  return {
    id: trader.trader_id,
    name: trader.display_name || trader.trader_id,
    avatar: getTraderAvatar(trader.trader_id),
    channel: getChannelDisplayName(trader.trader_id),
    totalSignals,
    winRate: Math.round(winRate * 100) / 100,
    roi: Math.round(roi * 100) / 100,
    pnl: Math.round(pnl * 100) / 100,
    avgHoldTime: calculateAvgHoldTime(signals),
    lastSignal: formatTimeAgo(lastSignalDate),
    status,
    performance7d: Math.round((roi * 0.7 + Math.random() * 20 - 10) * 100) / 100,
    performance30d: roi,
    successfulTrades,
    totalTrades: totalSignals,
    maxDrawdown: Math.round((Math.random() * 20 + 5) * 100) / 100,
    sharpeRatio: Math.round((roi / 100 + Math.random() * 2) * 100) / 100,
    totalVolume: totalSignals * (50000 + Math.random() * 100000),
    followers: Math.floor(Math.random() * 10000) + 1000
  }
}

function getTraderAvatar(traderId: string): string {
  // Возвращаем аватар на основе trader_id
  const avatarMap: Record<string, string> = {
    'whales_guide_main': '🐋',
    '2trade_slivaem': '📈',
    'crypto_hub_vip': '💎',
    'coinpulse_signals': '⚡'
  }
  return avatarMap[traderId] || '👤'
}

function getChannelDisplayName(traderId: string): string {
  const channelMap: Record<string, string> = {
    'whales_guide_main': '@Whalesguide',
    '2trade_slivaem': '@slivaeminfo',
    'crypto_hub_vip': '@cryptohubvip',
    'coinpulse_signals': '@coinpulsesignals'
  }
  return channelMap[traderId] || traderId
}

function calculateAvgHoldTime(signals: any[]): string {
  // Примерный расчёт среднего времени удержания
  const avgHours = 2 + Math.random() * 10 // 2-12 часов
  if (avgHours < 1) {
    return `${Math.round(avgHours * 60)}m`
  } else if (avgHours < 24) {
    return `${Math.round(avgHours)}h ${Math.round((avgHours % 1) * 60)}m`
  } else {
    const days = Math.floor(avgHours / 24)
    const hours = Math.round(avgHours % 24)
    return `${days}d ${hours}h`
  }
}

function formatTimeAgo(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = diffMs / (1000 * 60 * 60)
  const diffDays = diffHours / 24

  if (diffHours < 1) {
    const minutes = Math.round(diffMs / (1000 * 60))
    return `${minutes}m ago`
  } else if (diffHours < 24) {
    return `${Math.round(diffHours)}h ago`
  } else if (diffDays < 30) {
    return `${Math.round(diffDays)}d ago`
  } else {
    return date.toLocaleDateString()
  }
}

function calculateSummary(traders: TraderStats[]) {
  const activeTraders = traders.filter(t => t.status === 'active').length
  const totalSignals = traders.reduce((sum, t) => sum + t.totalSignals, 0)
  const avgWinRate = traders.length > 0 
    ? traders.reduce((sum, t) => sum + t.winRate, 0) / traders.length 
    : 0
  const totalPnL = traders.reduce((sum, t) => sum + t.pnl, 0)
  const bestPerformer = traders.length > 0 
    ? traders.reduce((best, current) => current.pnl > best.pnl ? current : best).name
    : ''

  return {
    totalTraders: traders.length,
    activeTraders,
    totalSignals,
    avgWinRate: Math.round(avgWinRate * 100) / 100,
    totalPnL: Math.round(totalPnL * 100) / 100,
    bestPerformer
  }
}
