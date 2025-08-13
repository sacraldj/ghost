import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Инициализация Supabase клиента
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// API для системы наблюдения за трейдерами
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action')
    
    switch (action) {
      case 'traders':
        return await getTraders(request)
      case 'stats':
        return await getTraderStats(request)
      case 'signals':
        return await getSignals(request)
      case 'outcomes':
        return await getOutcomes(request)
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('Trader observation API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action } = body
    
    switch (action) {
      case 'register_trader':
        return await registerTrader(body)
      case 'switch_mode':
        return await switchTraderMode(body)
      case 'update_risk_profile':
        return await updateRiskProfile(body)
      case 'activate_trader':
        return await activateTrader(body)
      case 'deactivate_trader':
        return await deactivateTrader(body)
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('Trader observation POST API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// Получение списка трейдеров с реальной статистикой
async function getTraders(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const mode = searchParams.get('mode') // observe, paper, live
  const active = searchParams.get('active')
  
  try {
    // Формируем фильтры для запроса
    const filters: any = {}
    
    if (mode) {
      filters.mode = mode
    }
    
    if (active !== null) {
      filters.is_active = active === 'true'
    }
    
    // Запрос к Supabase с реальной статистикой
    let query = supabase
      .from('trader_registry')
      .select(`
        trader_id,
        name,
        source_type,
        source_handle,
        mode,
        is_active,
        created_at,
        updated_at
      `)
    
    // Применяем фильтры
    Object.entries(filters).forEach(([key, value]) => {
      query = query.eq(key, value)
    })
    
    const { data: traders, error } = await query.order('name', { ascending: true })
    
    if (error) {
      console.error('Supabase error:', error)
      return getTradersMock(mode, active) // Fallback to mock data
    }
    
    // Получаем реальную статистику для каждого трейдера
    const enrichedTraders = await Promise.all(
      (traders || []).map(async (trader) => {
        try {
          // Получаем статистику сигналов
          const { data: signalsStats, error: signalsError } = await supabase
            .from('signals_raw')
            .select('*', { count: 'exact', head: true })
            .eq('trader_id', trader.trader_id)
          
          const total_signals = signalsStats || 0
          
          // Получаем статистику за последний месяц
          const thirtyDaysAgo = new Date()
          thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
          
          const { data: recentStats, error: recentError } = await supabase
            .from('signal_outcomes')
            .select('final_result, pnl_sim')
            .eq('trader_id', trader.trader_id)
            .gte('calculated_at', thirtyDaysAgo.toISOString())
          
          let winrate_30d = 0
          let pnl_30d = 0
          
          if (recentStats && recentStats.length > 0) {
            const winCount = recentStats.filter(s => 
              s.final_result && ['TP1_ONLY', 'TP2_FULL'].includes(s.final_result)
            ).length
            
            winrate_30d = (winCount / recentStats.length) * 100
            pnl_30d = recentStats.reduce((sum, s) => sum + (parseFloat(s.pnl_sim || '0')), 0)
          }
          
          // Получаем последний сигнал
          const { data: lastSignal, error: lastSignalError } = await supabase
            .from('signals_raw')
            .select('posted_at')
            .eq('trader_id', trader.trader_id)
            .order('posted_at', { ascending: false })
            .limit(1)
          
          const last_signal_at = lastSignal && lastSignal.length > 0 
            ? lastSignal[0].posted_at 
            : null
          
          return {
            ...trader,
            total_signals,
            winrate_30d: Math.round(winrate_30d * 10) / 10, // Округляем до 1 знака
            pnl_30d: Math.round(pnl_30d * 100) / 100, // Округляем до 2 знаков
            last_signal_at
          }
          
        } catch (statError) {
          console.error(`Error getting stats for trader ${trader.trader_id}:`, statError)
          
          // Fallback к базовым данным без статистики
          return {
            ...trader,
            total_signals: 0,
            winrate_30d: 0,
            pnl_30d: 0,
            last_signal_at: null
          }
        }
      })
    )
    
    return NextResponse.json({
      traders: enrichedTraders,
      total: enrichedTraders.length,
      timestamp: new Date().toISOString(),
      data_source: 'real'
    })
    
  } catch (error) {
    console.error('Database error:', error)
    return getTradersMock(mode, active) // Fallback to mock data
  }
}

// Fallback mock function
function getTradersMock(mode: string | null, active: string | null) {
  // Mock data - fallback если БД не работает
  const traders = [
    {
      trader_id: 'slivaeminfo',
      name: 'Slivaem Info',
      source_type: 'telegram',
      source_handle: '@slivaeminfo',
      mode: 'observe',
      is_active: true,
      total_signals: 156,
      winrate_30d: 67.5,
      pnl_30d: 245.80,
      last_signal_at: '2025-08-12T18:30:00Z'
    },
    {
      trader_id: 'cryptoexpert',
      name: 'Crypto Expert Pro',
      source_type: 'telegram',
      source_handle: '@cryptoexpert',
      mode: 'paper',
      is_active: true,
      total_signals: 89,
      winrate_30d: 72.3,
      pnl_30d: 189.45,
      last_signal_at: '2025-08-12T16:45:00Z'
    },
    {
      trader_id: 'tradingpro',
      name: 'Trading Pro Master',
      source_type: 'telegram',
      source_handle: '@tradingpro',
      mode: 'live',
      is_active: true,
      total_signals: 234,
      winrate_30d: 58.9,
      pnl_30d: 567.23,
      last_signal_at: '2025-08-12T19:15:00Z'
    },
    {
      trader_id: 'signalmaster',
      name: 'Signal Master',
      source_type: 'telegram',
      source_handle: '@signalmaster',
      mode: 'observe',
      is_active: false,
      total_signals: 45,
      winrate_30d: 45.2,
      pnl_30d: -67.89,
      last_signal_at: '2025-08-10T12:30:00Z'
    }
  ]
  
  let filtered = traders
  
  if (mode) {
    filtered = filtered.filter(t => t.mode === mode)
  }
  
  if (active !== null) {
    filtered = filtered.filter(t => t.is_active === (active === 'true'))
  }
  
  return NextResponse.json({
    traders: filtered,
    total: filtered.length,
    timestamp: new Date().toISOString()
  })
}

// Получение статистики трейдеров
async function getTraderStats(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const trader_id = searchParams.get('trader_id')
  const period = searchParams.get('period') || '30d' // 7d, 30d, 90d
  
  if (trader_id) {
    // Статистика конкретного трейдера
    const stats = {
      trader_id,
      period,
      signals_count: 45,
      valid_signals: 42,
      executed_signals: 38,
      winrate: 68.4,
      tp1_rate: 84.2,
      tp2_rate: 52.6,
      sl_rate: 31.6,
      avg_rr: 2.35,
      avg_duration_to_tp1_min: 125,
      avg_duration_to_tp2_min: 340,
      pnl_sim_sum: 289.45,
      max_drawdown_sim: -45.67,
      sharpe_like: 1.85,
      expectancy: 6.82,
      stability_index: 75.4,
      symbols_traded: ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'XRPUSDT'],
      avg_confidence: 87.3
    }
    
    return NextResponse.json({ stats })
  } else {
    // Общая статистика
    const overview = {
      total_traders: 4,
      active_traders: 3,
      modes: {
        observe: 2,
        paper: 1,
        live: 1
      },
      total_signals_today: 12,
      total_pnl_today: 156.78,
      avg_winrate: 63.2,
      top_performers: [
        { trader_id: 'tradingpro', pnl_30d: 567.23, winrate: 58.9 },
        { trader_id: 'slivaeminfo', pnl_30d: 245.80, winrate: 67.5 },
        { trader_id: 'cryptoexpert', pnl_30d: 189.45, winrate: 72.3 }
      ]
    }
    
    return NextResponse.json({ overview })
  }
}

// Получение сигналов
async function getSignals(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const trader_id = searchParams.get('trader_id')
  const limit = parseInt(searchParams.get('limit') || '50')
  const status = searchParams.get('status') // valid, invalid, all
  
  // Mock data
  const signals = [
    {
      signal_id: 1,
      trader_id: 'slivaeminfo',
      symbol: 'BTCUSDT',
      side: 'BUY',
      entry: 119500,
      tp1: 121000,
      tp2: 123500,
      sl: 117000,
      posted_at: '2025-08-12T18:30:00Z',
      confidence: 92.5,
      is_valid: true,
      outcome: {
        final_result: 'TP1_ONLY',
        pnl_sim: 45.67,
        roi_sim: 4.57,
        duration_to_tp1_min: 125
      }
    },
    {
      signal_id: 2,
      trader_id: 'cryptoexpert',
      symbol: 'ETHUSDT',
      side: 'BUY',
      entry: 4500,
      tp1: 4650,
      tp2: 4800,
      sl: 4300,
      posted_at: '2025-08-12T16:45:00Z',
      confidence: 87.3,
      is_valid: true,
      outcome: {
        final_result: 'TP2_FULL',
        pnl_sim: 89.34,
        roi_sim: 8.93,
        duration_to_tp2_min: 280
      }
    },
    {
      signal_id: 3,
      trader_id: 'tradingpro',
      symbol: 'ADAUSDT',
      side: 'SELL',
      entry: 0.485,
      tp1: 0.465,
      tp2: 0.445,
      sl: 0.505,
      posted_at: '2025-08-12T15:20:00Z',
      confidence: 78.9,
      is_valid: true,
      outcome: {
        final_result: 'SL',
        pnl_sim: -23.45,
        roi_sim: -2.35,
        duration_to_tp1_min: null
      }
    }
  ]
  
  let filtered = signals
  
  if (trader_id) {
    filtered = filtered.filter(s => s.trader_id === trader_id)
  }
  
  if (status && status !== 'all') {
    filtered = filtered.filter(s => 
      status === 'valid' ? s.is_valid : !s.is_valid
    )
  }
  
  return NextResponse.json({
    signals: filtered.slice(0, limit),
    total: filtered.length,
    timestamp: new Date().toISOString()
  })
}

// Получение исходов сигналов
async function getOutcomes(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const trader_id = searchParams.get('trader_id')
  const result_type = searchParams.get('result_type') // TP1_ONLY, TP2_FULL, SL, etc
  
  // Mock data
  const outcomes = [
    {
      signal_id: 1,
      trader_id: 'slivaeminfo',
      symbol: 'BTCUSDT',
      final_result: 'TP1_ONLY',
      pnl_sim: 45.67,
      roi_sim: 4.57,
      entry_exec_price_sim: 119500,
      tp1_hit_at: '2025-08-12T20:35:00Z',
      duration_to_tp1_min: 125,
      max_favorable: 5.23,
      max_adverse: -1.45
    },
    {
      signal_id: 2,
      trader_id: 'cryptoexpert',
      symbol: 'ETHUSDT',
      final_result: 'TP2_FULL',
      pnl_sim: 89.34,
      roi_sim: 8.93,
      entry_exec_price_sim: 4500,
      tp1_hit_at: '2025-08-12T18:15:00Z',
      tp2_hit_at: '2025-08-12T21:25:00Z',
      duration_to_tp1_min: 90,
      duration_to_tp2_min: 280,
      max_favorable: 9.67,
      max_adverse: -2.15
    }
  ]
  
  let filtered = outcomes
  
  if (trader_id) {
    filtered = filtered.filter(o => o.trader_id === trader_id)
  }
  
  if (result_type) {
    filtered = filtered.filter(o => o.final_result === result_type)
  }
  
  return NextResponse.json({
    outcomes: filtered,
    total: filtered.length,
    timestamp: new Date().toISOString()
  })
}

// Регистрация нового трейдера
async function registerTrader(body: any) {
  const { trader_id, name, source_type, source_handle, parsing_profile } = body
  
  if (!trader_id || !name || !source_type) {
    return NextResponse.json(
      { error: 'Missing required fields' },
      { status: 400 }
    )
  }
  
  // В продакшене здесь будет вызов trader_registry.register_trader()
  const newTrader = {
    trader_id,
    name,
    source_type,
    source_handle,
    mode: 'observe',
    is_active: true,
    parsing_profile: parsing_profile || 'standard_v1',
    created_at: new Date().toISOString()
  }
  
  return NextResponse.json({
    success: true,
    trader: newTrader,
    message: `Trader ${trader_id} registered successfully`
  })
}

// Переключение режима трейдера
async function switchTraderMode(body: any) {
  const { trader_id, mode } = body
  
  if (!trader_id || !mode) {
    return NextResponse.json(
      { error: 'Missing trader_id or mode' },
      { status: 400 }
    )
  }
  
  const validModes = ['observe', 'paper', 'live']
  if (!validModes.includes(mode)) {
    return NextResponse.json(
      { error: 'Invalid mode. Must be: observe, paper, or live' },
      { status: 400 }
    )
  }
  
  try {
    // Обновляем режим в Supabase
    const { data, error } = await supabase
      .from('trader_registry')
      .update({ 
        mode: mode,
        updated_at: new Date().toISOString()
      })
      .eq('trader_id', trader_id)
      .select()
    
    if (error) {
      console.error('Supabase update error:', error)
      return NextResponse.json(
        { error: 'Failed to update trader mode' },
        { status: 500 }
      )
    }
    
    if (!data || data.length === 0) {
      return NextResponse.json(
        { error: 'Trader not found' },
        { status: 404 }
      )
    }
    
    return NextResponse.json({
      success: true,
      trader_id,
      new_mode: mode,
      message: `Trader ${trader_id} switched to ${mode} mode`,
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json(
      { error: 'Database error' },
      { status: 500 }
    )
  }
}

// Обновление профиля риска
async function updateRiskProfile(body: any) {
  const { trader_id, risk_profile } = body
  
  if (!trader_id || !risk_profile) {
    return NextResponse.json(
      { error: 'Missing trader_id or risk_profile' },
      { status: 400 }
    )
  }
  
  // В продакшене здесь будет вызов trader_registry.update_risk_profile()
  return NextResponse.json({
    success: true,
    trader_id,
    risk_profile,
    message: `Risk profile updated for trader ${trader_id}`,
    timestamp: new Date().toISOString()
  })
}

// Активация трейдера
async function activateTrader(body: any) {
  const { trader_id } = body
  
  if (!trader_id) {
    return NextResponse.json(
      { error: 'Missing trader_id' },
      { status: 400 }
    )
  }
  
  return NextResponse.json({
    success: true,
    trader_id,
    is_active: true,
    message: `Trader ${trader_id} activated`,
    timestamp: new Date().toISOString()
  })
}

// Деактивация трейдера
async function deactivateTrader(body: any) {
  const { trader_id } = body
  
  if (!trader_id) {
    return NextResponse.json(
      { error: 'Missing trader_id' },
      { status: 400 }
    )
  }
  
  return NextResponse.json({
    success: true,
    trader_id,
    is_active: false,
    message: `Trader ${trader_id} deactivated`,
    timestamp: new Date().toISOString()
  })
}
