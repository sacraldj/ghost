// НОВЫЙ API: Расширенная аналитика трейдеров  
// ⚠️ НЕ трогает существующие API endpoints
// ✅ Добавляет Trust Index, Grade, детальную статистику

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// GET /api/traders-analytics - Получение расширенной аналитики всех трейдеров
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const trader_id = searchParams.get('trader_id')
    const include_behavior = searchParams.get('include_behavior') === 'true'
    const include_time_patterns = searchParams.get('include_time_patterns') === 'true'
    const sort_by = searchParams.get('sort_by') || 'trust_index' // trust_index, grade, winrate, total_pnl
    const order = searchParams.get('order') || 'desc'
    const limit = parseInt(searchParams.get('limit') || '50')

    if (trader_id) {
      // Получение детальной аналитики конкретного трейдера
      return getTraderDetailedAnalytics(trader_id, include_behavior, include_time_patterns)
    } else {
      // Получение аналитики всех трейдеров для таблицы
      return getAllTradersAnalytics(sort_by, order, limit)
    }

  } catch (error) {
    console.error('Traders analytics API error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

// Получение аналитики всех трейдеров (для таблицы)
async function getAllTradersAnalytics(sort_by: string, order: string, limit: number) {
  try {
    // Базовый запрос аналитики БЕЗ JOIN (избегаем проблем схемы)
    let query = supabase
      .from('trader_analytics')
      .select('*')
      .limit(limit)

    // Сортировка
    const ascending = order.toLowerCase() === 'asc'
    switch (sort_by) {
      case 'trust_index':
        query = query.order('trust_index', { ascending })
        break
      case 'grade':
        query = query.order('grade', { ascending })
        break  
      case 'winrate':
        query = query.order('winrate', { ascending })
        break
      case 'total_pnl':
        query = query.order('total_pnl', { ascending })
        break
      case 'overall_rank':
        query = query.order('overall_rank', { ascending: true }) // rank всегда по возрастанию
        break
      default:
        query = query.order('trust_index', { ascending: false })
    }

    const { data: analyticsData, error: analyticsError } = await query

    if (analyticsError) {
      throw new Error(`Analytics query error: ${analyticsError.message}`)
    }

    // Форматируем данные для фронтенда (упрощенно, без trader_registry)
    const formattedData = analyticsData?.map(item => ({
      trader_id: item.trader_id,
      name: item.trader_id, // Используем trader_id как имя
      source_type: 'telegram', // По умолчанию telegram
      source_handle: item.trader_id,
      is_active: true, // По умолчанию активен

      // Ключевые метрики
      trust_index: Number(item.trust_index),
      grade: item.grade,
      risk_score: Number(item.risk_score),
      overall_rank: item.overall_rank,
      rank_change: item.rank_change,

      // Статистика
      total_signals: item.total_signals,
      valid_signals: item.valid_signals,
      executed_signals: item.executed_signals,
      
      // Результативность  
      winrate: Number(item.winrate),
      tp1_rate: Number(item.tp1_rate),
      tp2_rate: Number(item.tp2_rate),
      sl_rate: Number(item.sl_rate),

      // Финансы
      total_pnl: Number(item.total_pnl),
      avg_roi: Number(item.avg_roi),
      best_roi: Number(item.best_roi),
      worst_roi: Number(item.worst_roi),

      // Риск-менеджмент
      avg_rrr: Number(item.avg_rrr),
      max_drawdown: Number(item.max_drawdown),
      consistency_score: Number(item.consistency_score),

      // Мета
      last_updated: item.updated_at,
      period: `${item.period_start} - ${item.period_end}`
    })) || []

    // Получаем общую статистику
    const summary = {
      total_traders: formattedData.length,
      grade_distribution: {
        A: formattedData.filter(t => t.grade === 'A').length,
        B: formattedData.filter(t => t.grade === 'B').length,
        C: formattedData.filter(t => t.grade === 'C').length,
        D: formattedData.filter(t => t.grade === 'D').length,
      },
      avg_trust_index: formattedData.reduce((sum, t) => sum + t.trust_index, 0) / formattedData.length,
      avg_winrate: formattedData.reduce((sum, t) => sum + t.winrate, 0) / formattedData.length,
      total_signals: formattedData.reduce((sum, t) => sum + t.total_signals, 0)
    }

    return NextResponse.json({
      success: true,
      data: formattedData,
      summary,
      timestamp: new Date().toISOString(),
      query_params: { sort_by, order, limit }
    })

  } catch (error) {
    console.error('Error in getAllTradersAnalytics:', error)
    throw error
  }
}

// Получение детальной аналитики конкретного трейдера
async function getTraderDetailedAnalytics(trader_id: string, include_behavior: boolean, include_time_patterns: boolean) {
  try {
    // Основная аналитика (упрощенно, без JOIN)
    const { data: analytics, error: analyticsError } = await supabase
      .from('trader_analytics')
      .select('*')
      .eq('trader_id', trader_id)
      .single()

    if (analyticsError || !analytics) {
      return NextResponse.json(
        { error: 'Trader not found', trader_id },
        { status: 404 }
      )
    }

    let detailedData: any = {
      trader_id: analytics.trader_id,
      name: analytics.trader_id, // Используем trader_id как имя
      source_type: 'telegram', // По умолчанию telegram
      source_handle: analytics.trader_id,
      is_active: true, // По умолчанию активен
      member_since: analytics.created_at, // Используем created_at из trader_analytics

      // Основные метрики
      trust_index: Number(analytics.trust_index),
      grade: analytics.grade,
      risk_score: Number(analytics.risk_score),
      overall_rank: analytics.overall_rank,
      rank_change: analytics.rank_change,

      // Детальная статистика
      total_signals: analytics.total_signals,
      valid_signals: analytics.valid_signals,
      executed_signals: analytics.executed_signals,
      
      winrate: Number(analytics.winrate),
      tp1_rate: Number(analytics.tp1_rate),
      tp2_rate: Number(analytics.tp2_rate),
      sl_rate: Number(analytics.sl_rate),

      total_pnl: Number(analytics.total_pnl),
      avg_roi: Number(analytics.avg_roi),
      best_roi: Number(analytics.best_roi),
      worst_roi: Number(analytics.worst_roi),

      avg_rrr: Number(analytics.avg_rrr),
      max_drawdown: Number(analytics.max_drawdown),
      consistency_score: Number(analytics.consistency_score),

      analysis_period: `${analytics.period_start} - ${analytics.period_end}`,
      last_updated: analytics.updated_at
    }

    // Поведенческие флаги (если запрошены)
    if (include_behavior) {
      const { data: behaviorData } = await supabase
        .from('trader_behavior_flags')
        .select('*')
        .eq('trader_id', trader_id)
        .single()

      detailedData.behavior = {
        has_duplicates: behaviorData?.has_duplicates || false,
        has_contradictions: behaviorData?.has_contradictions || false,
        suspected_copy_paste: behaviorData?.suspected_copy_paste || false,
        duplicate_score: behaviorData?.duplicate_score || 0,
        contradiction_score: behaviorData?.contradiction_score || 0,
        copy_paste_score: behaviorData?.copy_paste_score || 0,
        last_analyzed: behaviorData?.last_analyzed
      }
    }

    // Временные паттерны (если запрошены)
    if (include_time_patterns) {
      const { data: timeData } = await supabase
        .from('trader_time_stats')
        .select('*')
        .eq('trader_id', trader_id)
        .order('signals_count', { ascending: false })

      detailedData.time_patterns = timeData?.map(item => ({
        hour_of_day: item.hour_of_day,
        day_of_week: item.day_of_week,
        signals_count: item.signals_count,
        avg_roi: Number(item.avg_roi),
        success_rate: Number(item.success_rate)
      })) || []
    }

    // Последние ошибки (всегда включаем топ-5)
    const { data: errorsData } = await supabase
      .from('signal_errors')
      .select('*')
      .eq('trader_id', trader_id)
      .order('detected_at', { ascending: false })
      .limit(5)

    detailedData.recent_errors = errorsData?.map(error => ({
      category: error.error_category,
      type: error.error_type,
      message: error.error_message,
      severity: error.severity,
      detected_at: error.detected_at
    })) || []

    return NextResponse.json({
      success: true,
      data: detailedData,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Error in getTraderDetailedAnalytics:', error)
    throw error
  }
}

// POST /api/traders-analytics - Пересчет аналитики (manual trigger)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { trader_id, action } = body

    if (action === 'recalculate') {
      // Вызываем SQL функцию для пересчета
      const { error } = await supabase.rpc('update_trader_basic_analytics', {
        target_trader_id: trader_id || null
      })

      if (error) {
        throw new Error(`Recalculation error: ${error.message}`)
      }

      return NextResponse.json({
        success: true,
        message: trader_id 
          ? `Analytics recalculated for trader: ${trader_id}` 
          : 'Analytics recalculated for all traders',
        timestamp: new Date().toISOString()
      })
    }

    return NextResponse.json(
      { error: 'Invalid action. Use action: "recalculate"' },
      { status: 400 }
    )

  } catch (error) {
    console.error('Error in traders analytics POST:', error)
    return NextResponse.json(
      { error: 'Recalculation failed', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
