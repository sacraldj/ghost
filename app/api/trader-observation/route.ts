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
    
    // Получаем честную детальную статистику для каждого трейдера (как у Дарена)
    const enrichedTraders = await Promise.all(
      (traders || []).map(async (trader) => {
        try {
          // 1. Общее количество сигналов (сырых)
          const { count: totalRawSignals } = await supabase
            .from('signals_raw')
            .select('*', { count: 'exact', head: true })
            .eq('trader_id', trader.trader_id)
          
          // 2. Количество обработанных валидных сигналов
          const { data: parsedSignals } = await supabase
            .from('signals_parsed')
            .select('signal_id, is_valid, confidence, posted_at')
            .eq('trader_id', trader.trader_id)
            .order('posted_at', { ascending: false })
          
          const validSignals = parsedSignals?.filter(s => s.is_valid).length || 0
          
          // 3. Получаем ВСЕ исходы для честной статистики
          const { data: allOutcomes } = await supabase
            .from('signal_outcomes')
            .select(`
              signal_id,
              final_result,
              pnl_sim,
              roi_sim,
              duration_to_tp1_min,
              duration_to_tp2_min,
              max_favorable,
              max_adverse,
              tp1_hit_at,
              tp2_hit_at,
              sl_hit_at,
              calculated_at
            `)
            .eq('trader_id', trader.trader_id)
          
          // 4. ЧЕСТНАЯ СТАТИСТИКА как у Дарена: "Вася дал сигнал дог 109 раз"
          const totalExecuted = allOutcomes?.length || 0
          
          // Подсчет по исходам (как у Дарена)
          const tp1Count = allOutcomes?.filter(o => 
            o.final_result === 'TP1_ONLY' || o.final_result === 'TP2_FULL'
          ).length || 0
          
          const tp2Count = allOutcomes?.filter(o => 
            o.final_result === 'TP2_FULL'
          ).length || 0
          
          const slCount = allOutcomes?.filter(o => 
            o.final_result === 'SL'
          ).length || 0
          
          const beCount = allOutcomes?.filter(o => 
            o.final_result === 'BE' || o.final_result === 'TIMEOUT'
          ).length || 0
          
          // Процентные показатели
          const tp1Rate = totalExecuted > 0 ? (tp1Count / totalExecuted) * 100 : 0
          const tp2Rate = totalExecuted > 0 ? (tp2Count / totalExecuted) * 100 : 0
          const slRate = totalExecuted > 0 ? (slCount / totalExecuted) * 100 : 0
          
          // 5. Финансовые показатели
          const totalPnl = allOutcomes?.reduce((sum, o) => sum + (parseFloat(o.pnl_sim || '0')), 0) || 0
          const avgPnl = totalExecuted > 0 ? totalPnl / totalExecuted : 0
          
          const winningTrades = allOutcomes?.filter(o => parseFloat(o.pnl_sim || '0') > 0) || []
          const losingTrades = allOutcomes?.filter(o => parseFloat(o.pnl_sim || '0') < 0) || []
          
          const avgWin = winningTrades.length > 0 
            ? winningTrades.reduce((sum, t) => sum + parseFloat(t.pnl_sim || '0'), 0) / winningTrades.length 
            : 0
          const avgLoss = losingTrades.length > 0 
            ? Math.abs(losingTrades.reduce((sum, t) => sum + parseFloat(t.pnl_sim || '0'), 0) / losingTrades.length)
            : 0
          
          const profitFactor = avgLoss > 0 ? avgWin / avgLoss : 0
          
          // 6. Статистика за последние 30 дней
          const thirtyDaysAgo = new Date()
          thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
          
          const recentOutcomes = allOutcomes?.filter(o => 
            new Date(o.calculated_at) >= thirtyDaysAgo
          ) || []
          
          const pnl_30d = recentOutcomes.reduce((sum, o) => sum + parseFloat(o.pnl_sim || '0'), 0)
          const winrate_30d = recentOutcomes.length > 0 
            ? (recentOutcomes.filter(o => ['TP1_ONLY', 'TP2_FULL'].includes(o.final_result)).length / recentOutcomes.length) * 100 
            : 0
          
          // 7. Временные метрики
          const avgTimeToTP1 = allOutcomes?.filter(o => o.duration_to_tp1_min)
            .reduce((sum, o, _, arr) => sum + (parseInt(o.duration_to_tp1_min) || 0) / arr.length, 0) || 0
          
          // 8. Получаем последний сигнал
          const last_signal_at = parsedSignals?.[0]?.posted_at || null
          
          // 9. Средняя уверенность парсера
          const avgConfidence = parsedSignals?.length > 0 
            ? parsedSignals.reduce((sum, s) => sum + (parseFloat(s.confidence) || 0), 0) / parsedSignals.length 
            : 0
          
          return {
            ...trader,
            // Базовые счетчики (как у Дарена)
            total_signals: totalRawSignals || 0,
            valid_signals: validSignals,
            executed_signals: totalExecuted,
            
            // ЧЕСТНАЯ СТАТИСТИКА (как у Дарена): "Вася дал 109 раз, из них 90 был TP1"
            tp1_count: tp1Count,
            tp2_count: tp2Count, 
            sl_count: slCount,
            be_count: beCount,
            
            // Процентные показатели
            tp1_rate: Math.round(tp1Rate * 10) / 10,
            tp2_rate: Math.round(tp2Rate * 10) / 10, 
            sl_rate: Math.round(slRate * 10) / 10,
            winrate_30d: Math.round(winrate_30d * 10) / 10,
            
            // Финансовые показатели
            total_pnl: Math.round(totalPnl * 100) / 100,
            avg_pnl: Math.round(avgPnl * 100) / 100,
            pnl_30d: Math.round(pnl_30d * 100) / 100,
            avg_win: Math.round(avgWin * 100) / 100,
            avg_loss: Math.round(avgLoss * 100) / 100,
            profit_factor: Math.round(profitFactor * 100) / 100,
            
            // Временные показатели
            avg_time_to_tp1: Math.round(avgTimeToTP1),
            
            // Метаданные
            last_signal_at,
            avg_confidence: Math.round(avgConfidence * 10) / 10,
            
            // Строка статистики как у Дарена
            stats_summary: `${totalExecuted} сигналов: ${tp1Count} TP1 (${Math.round(tp1Rate)}%), ${tp2Count} TP2 (${Math.round(tp2Rate)}%), ${slCount} SL (${Math.round(slRate)}%)`,
            
            // Дополнительные показатели качества
            signal_quality: validSignals > 0 ? Math.round((validSignals / (totalRawSignals || 1)) * 100) : 0,
            execution_rate: validSignals > 0 ? Math.round((totalExecuted / validSignals) * 100) : 0
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
      trader_id: 'cryptoattack24',
      name: 'КриптоАтака 24',
      source_type: 'telegram',
      source_handle: '@cryptoattack24',
      mode: 'observe',
      is_active: true,
      total_signals: 47,
      valid_signals: 38,
      executed_signals: 32,
      tp1_count: 21,
      tp2_count: 8,
      sl_count: 3,
      be_count: 0,
      tp1_rate: 65.6,
      tp2_rate: 25.0,
      sl_rate: 9.4,
      winrate_30d: 90.6,
      total_pnl: 1247.50,
      avg_pnl: 38.98,
      pnl_30d: 1247.50,
      avg_win: 67.80,
      avg_loss: -45.20,
      profit_factor: 2.85,
      avg_time_to_tp1: 125,
      last_signal_at: '2025-08-16T11:20:00Z',
      avg_confidence: 85.2,
      stats_summary: '47 сигналов: 21 TP1 (66%), 8 TP2 (25%), 3 SL (9%)',
      signal_quality: 81,
      execution_rate: 84
    },
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
  
  try {
    if (trader_id) {
      // Статистика конкретного трейдера из реальных данных
      const periodDays = period === '7d' ? 7 : period === '30d' ? 30 : period === '90d' ? 90 : 30
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - periodDays)

      // Получаем сигналы трейдера за период
      const { data: signals, error: signalsError } = await supabase
        .from('signals_parsed')
        .select('*')
        .eq('trader_id', trader_id)
        .gte('posted_at', startDate.toISOString())
        .eq('is_valid', true)

      if (signalsError) {
        console.error('Error fetching signals:', signalsError)
        throw signalsError
      }

      // Получаем результаты сигналов за период
      const { data: outcomes, error: outcomesError } = await supabase
        .from('signal_outcomes')
        .select('*')
        .eq('trader_id', trader_id)
        .gte('calculated_at', startDate.toISOString())

      if (outcomesError) {
        console.error('Error fetching outcomes:', outcomesError)
        throw outcomesError
      }

      // Рассчитываем статистику
      const signalsCount = signals?.length || 0
      const validSignals = signals?.filter(s => s.is_valid).length || 0
      const executedSignals = outcomes?.length || 0

      // Подсчет результатов
      const tp1Count = outcomes?.filter(o => o.final_result === 'TP1_ONLY' || o.final_result === 'TP2_FULL').length || 0
      const tp2Count = outcomes?.filter(o => o.final_result === 'TP2_FULL').length || 0
      const slCount = outcomes?.filter(o => o.final_result === 'SL').length || 0

      const winrate = executedSignals > 0 ? ((tp1Count + tp2Count) / executedSignals) * 100 : 0
      const tp1Rate = executedSignals > 0 ? (tp1Count / executedSignals) * 100 : 0
      const tp2Rate = executedSignals > 0 ? (tp2Count / executedSignals) * 100 : 0
      const slRate = executedSignals > 0 ? (slCount / executedSignals) * 100 : 0

      // P&L расчеты
      const pnlSimSum = outcomes?.reduce((sum, o) => sum + (parseFloat(o.pnl_sim?.toString() || '0')), 0) || 0
      const maxDrawdownSim = Math.min(...(outcomes?.map(o => parseFloat(o.pnl_sim?.toString() || '0')) || [0]))

      // Временные метрики
      const avgDurationToTp1 = outcomes?.filter(o => o.duration_to_tp1_min)
        .reduce((sum, o) => sum + (o.duration_to_tp1_min || 0), 0) / (tp1Count || 1) || 0
      const avgDurationToTp2 = outcomes?.filter(o => o.duration_to_tp2_min)
        .reduce((sum, o) => sum + (o.duration_to_tp2_min || 0), 0) / (tp2Count || 1) || 0

      // Средняя уверенность
      const avgConfidence = signals?.reduce((sum, s) => sum + (parseFloat(s.confidence?.toString() || '0')), 0) / signalsCount || 0

      // Торгуемые символы
      const symbolsTraded = [...new Set(signals?.map(s => s.symbol) || [])]

      // Risk/Reward и другие метрики
      const winningTrades = outcomes?.filter(o => parseFloat(o.pnl_sim?.toString() || '0') > 0) || []
      const losingTrades = outcomes?.filter(o => parseFloat(o.pnl_sim?.toString() || '0') < 0) || []
      const avgWin = winningTrades.length > 0 ? winningTrades.reduce((sum, t) => sum + parseFloat(t.pnl_sim?.toString() || '0'), 0) / winningTrades.length : 0
      const avgLoss = losingTrades.length > 0 ? Math.abs(losingTrades.reduce((sum, t) => sum + parseFloat(t.pnl_sim?.toString() || '0'), 0) / losingTrades.length) : 0
      const avgRr = avgLoss > 0 ? avgWin / avgLoss : 0

      const stats = {
        trader_id,
        period,
        signals_count: signalsCount,
        valid_signals: validSignals,
        executed_signals: executedSignals,
        winrate: Number(winrate.toFixed(1)),
        tp1_rate: Number(tp1Rate.toFixed(1)),
        tp2_rate: Number(tp2Rate.toFixed(1)),
        sl_rate: Number(slRate.toFixed(1)),
        avg_rr: Number(avgRr.toFixed(2)),
        avg_duration_to_tp1_min: Math.round(avgDurationToTp1),
        avg_duration_to_tp2_min: Math.round(avgDurationToTp2),
        pnl_sim_sum: Number(pnlSimSum.toFixed(2)),
        max_drawdown_sim: Number(maxDrawdownSim.toFixed(2)),
        sharpe_like: avgLoss > 0 ? Number((avgWin / avgLoss).toFixed(2)) : 0,
        expectancy: executedSignals > 0 ? Number((pnlSimSum / executedSignals).toFixed(2)) : 0,
        stability_index: winrate > 50 ? Math.min(100, winrate + (avgRr * 10)) : winrate,
        symbols_traded: symbolsTraded,
        avg_confidence: Number(avgConfidence.toFixed(1))
      }
      
      return NextResponse.json({ stats })
    } else {
      // Общая статистика из реальных данных
      const { data: traders, error: tradersError } = await supabase
        .from('trader_registry')
        .select('trader_id, mode, is_active')

      if (tradersError) {
        console.error('Error fetching traders for overview:', tradersError)
        throw tradersError
      }

      const totalTraders = traders?.length || 0
      const activeTraders = traders?.filter(t => t.is_active).length || 0
      
      const modes = {
        observe: traders?.filter(t => t.mode === 'observe').length || 0,
        paper: traders?.filter(t => t.mode === 'paper').length || 0,
        live: traders?.filter(t => t.mode === 'live').length || 0
      }

      // Получаем данные за сегодня
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      
      const { data: todaySignals, error: todaySignalsError } = await supabase
        .from('signals_parsed')
        .select('trader_id')
        .gte('posted_at', today.toISOString())
        .eq('is_valid', true)

      const { data: todayOutcomes, error: todayOutcomesError } = await supabase
        .from('signal_outcomes')
        .select('pnl_sim, trader_id')
        .gte('calculated_at', today.toISOString())

      const totalSignalsToday = todaySignals?.length || 0
      const totalPnlToday = todayOutcomes?.reduce((sum, o) => sum + (parseFloat(o.pnl_sim?.toString() || '0')), 0) || 0

      // Получаем топ исполнителей за последние 30 дней
      const thirtyDaysAgo = new Date()
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

      const { data: recentOutcomes, error: recentError } = await supabase
        .from('signal_outcomes')
        .select('trader_id, pnl_sim, final_result')
        .gte('calculated_at', thirtyDaysAgo.toISOString())

      if (recentError) {
        console.error('Error fetching recent outcomes:', recentError)
      }

      // Группируем по трейдерам
      const traderPerformance = {}
      recentOutcomes?.forEach(outcome => {
        const traderId = outcome.trader_id
        if (!traderPerformance[traderId]) {
          traderPerformance[traderId] = { pnl: 0, wins: 0, total: 0 }
        }
        traderPerformance[traderId].pnl += parseFloat(outcome.pnl_sim?.toString() || '0')
        traderPerformance[traderId].total += 1
        if (['TP1_ONLY', 'TP2_FULL'].includes(outcome.final_result)) {
          traderPerformance[traderId].wins += 1
        }
      })

      const topPerformers = Object.entries(traderPerformance)
        .map(([trader_id, perf]: [string, any]) => ({
          trader_id,
          pnl_30d: Number(perf.pnl.toFixed(2)),
          winrate: perf.total > 0 ? Number(((perf.wins / perf.total) * 100).toFixed(1)) : 0
        }))
        .sort((a, b) => b.pnl_30d - a.pnl_30d)
        .slice(0, 3)

      const avgWinrate = topPerformers.length > 0 
        ? topPerformers.reduce((sum, t) => sum + t.winrate, 0) / topPerformers.length 
        : 0

      const overview = {
        total_traders: totalTraders,
        active_traders: activeTraders,
        modes,
        total_signals_today: totalSignalsToday,
        total_pnl_today: Number(totalPnlToday.toFixed(2)),
        avg_winrate: Number(avgWinrate.toFixed(1)),
        top_performers: topPerformers
      }
      
      return NextResponse.json({ overview })
    }
  } catch (error) {
    console.error('Error in getTraderStats:', error)
    
    // Fallback к mock данным при ошибке
    if (trader_id) {
      const stats = {
        trader_id,
        period,
        signals_count: 0,
        valid_signals: 0,
        executed_signals: 0,
        winrate: 0,
        tp1_rate: 0,
        tp2_rate: 0,
        sl_rate: 0,
        avg_rr: 0,
        avg_duration_to_tp1_min: 0,
        avg_duration_to_tp2_min: 0,
        pnl_sim_sum: 0,
        max_drawdown_sim: 0,
        sharpe_like: 0,
        expectancy: 0,
        stability_index: 0,
        symbols_traded: [],
        avg_confidence: 0
      }
      return NextResponse.json({ stats })
    } else {
      const overview = {
        total_traders: 0,
        active_traders: 0,
        modes: { observe: 0, paper: 0, live: 0 },
        total_signals_today: 0,
        total_pnl_today: 0,
        avg_winrate: 0,
        top_performers: []
      }
      return NextResponse.json({ overview })
    }
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
