import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!
)

export async function GET(request: NextRequest) {
  try {
    console.log('🏥 [HEALTH CHECK] Starting health check...')
    
    const healthStatus = {
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'unknown',
      status: 'healthy',
      checks: {
        api: { status: 'ok', message: 'API endpoint is responding' },
        environment: {
          status: 'ok',
          details: {
            NODE_ENV: process.env.NODE_ENV || 'not set',
            SUPABASE_URL_SET: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
            SUPABASE_SECRET_SET: !!process.env.SUPABASE_SECRET_KEY,
          }
        },
        supabase: { status: 'checking', message: 'Testing Supabase connection...' },
        external: { status: 'checking', message: 'Testing external API access...' }
      }
    }

    // Проверяем подключение к Supabase
    try {
      const { data, error } = await supabase
        .from('v_trades')
        .select('id')
        .limit(1)
      
      if (error) {
        healthStatus.checks.supabase = {
          status: 'error',
          message: `Supabase error: ${error.message}`
        }
        healthStatus.status = 'degraded'
      } else {
        healthStatus.checks.supabase = {
          status: 'ok',
          message: `Supabase connected, found ${data?.length || 0} records`,
        }
      }
    } catch (supabaseError) {
      healthStatus.checks.supabase = {
        status: 'error',
        message: `Supabase connection failed: ${supabaseError}`,
      }
      healthStatus.status = 'degraded'
    }

    // Проверяем доступ к внешним API (Bybit)
    try {
      const bybitUrl = 'https://api.bybit.com/v5/market/kline?category=linear&symbol=BTCUSDT&interval=1&limit=1'
      const response = await fetch(bybitUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        signal: AbortSignal.timeout(10000) // 10 секунд timeout
      })
      
      if (response.ok) {
        const data = await response.json()
        healthStatus.checks.external = {
          status: 'ok',
          message: `External API accessible, Bybit response code: ${data.retCode || 'unknown'}`
        }
      } else {
        healthStatus.checks.external = {
          status: 'error',
          message: `External API error: ${response.status} ${response.statusText}`
        }
        healthStatus.status = 'degraded'
      }
    } catch (externalError) {
      healthStatus.checks.external = {
        status: 'error',
        message: `External API failed: ${externalError}`
      }
      healthStatus.status = 'degraded'
    }

    console.log('✅ [HEALTH CHECK] Completed:', JSON.stringify(healthStatus, null, 2))

    return NextResponse.json(healthStatus, { 
      status: healthStatus.status === 'healthy' ? 200 : 503 
    })
    
  } catch (error) {
    console.error('❌ [HEALTH CHECK] Critical error:', error)
    
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      status: 'critical',
      error: error instanceof Error ? error.message : 'Unknown health check error',
      environment: process.env.NODE_ENV || 'unknown'
    }, { status: 500 })
  }
}
