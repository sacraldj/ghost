import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!
)

// GET /api/signal-tracking - получить статус отслеживания сигналов
export async function GET() {
  try {
    // Получаем активные подписки
    const { data: activeSubscriptions, error: activeError } = await supabase
      .from('signal_websocket_subscriptions')
      .select(`
        signal_id,
        symbol,
        status,
        start_time,
        end_time,
        candles_collected,
        last_candle_time,
        created_at
      `)
      .in('status', ['active', 'completed'])
      .order('created_at', { ascending: false })

    if (activeError) {
      console.error('Active subscriptions error:', activeError)
      return NextResponse.json({ error: activeError.message }, { status: 500 })
    }

    // Получаем общую статистику
    const { data: stats, error: statsError } = await supabase.rpc('get_tracking_statistics')
    
    if (statsError) {
      console.error('Stats error:', statsError)
      // Продолжаем без статистики
    }

    // Группируем по статусу
    const activeCount = activeSubscriptions.filter(s => s.status === 'active').length
    const completedCount = activeSubscriptions.filter(s => s.status === 'completed').length
    const totalCandlesCollected = activeSubscriptions.reduce((sum, s) => sum + (s.candles_collected || 0), 0)

    return NextResponse.json({
      subscriptions: activeSubscriptions,
      summary: {
        active_subscriptions: activeCount,
        completed_subscriptions: completedCount,
        total_subscriptions: activeSubscriptions.length,
        total_candles_collected: totalCandlesCollected,
        unique_symbols: [...new Set(activeSubscriptions.map(s => s.symbol))].length
      },
      system_stats: stats || null
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// POST /api/signal-tracking - запустить отслеживание сигнала
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { signal_id, action } = body

    if (!signal_id) {
      return NextResponse.json({ error: 'signal_id is required' }, { status: 400 })
    }

    if (action === 'start') {
      return await startSignalTracking(signal_id)
    } else if (action === 'stop') {
      return await stopSignalTracking(signal_id)
    } else {
      return NextResponse.json({ error: 'Invalid action. Use "start" or "stop"' }, { status: 400 })
    }

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// Запуск отслеживания сигнала
async function startSignalTracking(signalId: string) {
  try {
    // Получаем информацию о сигнале из v_trades
    const { data: signalData, error: signalError } = await supabase
      .from('v_trades')
      .select('id, symbol, side, entry_min, entry_max, tp1, tp2, sl, posted_ts, status')
      .eq('id', signalId)
      .single()

    if (signalError || !signalData) {
      return NextResponse.json({ error: 'Signal not found' }, { status: 404 })
    }

    // Проверяем, не отслеживается ли уже
    const { data: existingSubscription } = await supabase
      .from('signal_websocket_subscriptions')
      .select('id, status')
      .eq('signal_id', signalId)
      .single()

    if (existingSubscription) {
      if (existingSubscription.status === 'active') {
        return NextResponse.json({ 
          message: 'Signal is already being tracked',
          subscription: existingSubscription 
        })
      } else {
        // Обновляем существующую подписку
        const { data: updatedSubscription, error: updateError } = await supabase
          .from('signal_websocket_subscriptions')
          .update({
            status: 'active',
            start_time: Math.floor(Date.now() / 1000),
            end_time: null,
            error_message: null
          })
          .eq('signal_id', signalId)
          .select()
          .single()

        if (updateError) {
          return NextResponse.json({ error: updateError.message }, { status: 500 })
        }

        return NextResponse.json({
          message: 'Signal tracking restarted',
          subscription: updatedSubscription,
          signal: signalData
        })
      }
    }

    // Создаем новую подписку
    const subscriptionData = {
      signal_id: signalId,
      symbol: signalData.symbol,
      start_time: Math.floor(Date.now() / 1000),
      status: 'active',
      candles_collected: 0
    }

    const { data: newSubscription, error: insertError } = await supabase
      .from('signal_websocket_subscriptions')
      .insert([subscriptionData])
      .select()
      .single()

    if (insertError) {
      console.error('Insert error:', insertError)
      return NextResponse.json({ error: insertError.message }, { status: 500 })
    }

    // Здесь можно добавить вызов к Python сервису для запуска WebSocket
    // Пока что возвращаем успешный ответ
    
    return NextResponse.json({
      message: 'Signal tracking started successfully',
      subscription: newSubscription,
      signal: signalData
    })

  } catch (error) {
    console.error('Start tracking error:', error)
    return NextResponse.json({ error: 'Failed to start tracking' }, { status: 500 })
  }
}

// Остановка отслеживания сигнала
async function stopSignalTracking(signalId: string) {
  try {
    // Обновляем подписку
    const { data: updatedSubscription, error: updateError } = await supabase
      .from('signal_websocket_subscriptions')
      .update({
        status: 'stopped',
        end_time: Math.floor(Date.now() / 1000)
      })
      .eq('signal_id', signalId)
      .eq('status', 'active')
      .select()
      .single()

    if (updateError) {
      if (updateError.code === 'PGRST116') { // No rows updated
        return NextResponse.json({ error: 'No active tracking found for this signal' }, { status: 404 })
      }
      return NextResponse.json({ error: updateError.message }, { status: 500 })
    }

    // Здесь можно добавить вызов к Python сервису для остановки WebSocket
    
    return NextResponse.json({
      message: 'Signal tracking stopped successfully',
      subscription: updatedSubscription
    })

  } catch (error) {
    console.error('Stop tracking error:', error)
    return NextResponse.json({ error: 'Failed to stop tracking' }, { status: 500 })
  }
}

// DELETE /api/signal-tracking - очистка старых подписок
export async function DELETE() {
  try {
    const cutoffTime = Math.floor(Date.now() / 1000) - (7 * 24 * 3600) // 7 дней назад

    // Обновляем старые активные подписки на completed
    const { data: updatedSubscriptions, error: updateError } = await supabase
      .from('signal_websocket_subscriptions')
      .update({
        status: 'completed',
        end_time: Math.floor(Date.now() / 1000)
      })
      .eq('status', 'active')
      .lt('start_time', cutoffTime)
      .select()

    if (updateError) {
      console.error('Cleanup error:', updateError)
      return NextResponse.json({ error: updateError.message }, { status: 500 })
    }

    return NextResponse.json({
      message: 'Cleanup completed successfully',
      updated_subscriptions: updatedSubscriptions?.length || 0
    })

  } catch (error) {
    console.error('Cleanup error:', error)
    return NextResponse.json({ error: 'Cleanup failed' }, { status: 500 })
  }
}
