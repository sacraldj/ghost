import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Vercel Cron Job для сбора данных каждую минуту
export async function GET(request: NextRequest) {
  try {
    // Проверяем что это запрос от Vercel Cron
    const authHeader = request.headers.get('authorization')
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    console.log('🚀 Starting GHOST data collection cron job...')

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!
    const supabase = createClient(supabaseUrl, supabaseKey)

    const results = {
      news_created: 0,
      market_data_created: 0,
      alerts_created: 0,
      errors: []
    }

    // 1. Собираем рыночные данные
    const symbols = ['BTCUSDT', 'ETHUSDT', 'ORDIUSDT', 'SOLUSDT', 'ADAUSDT']
    
    for (const symbol of symbols) {
      try {
        // Получаем данные с Binance
        const response = await fetch(`https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=${symbol}`)
        
        if (response.ok) {
          const data = await response.json()
          
          const marketSnapshot = {
            symbol,
            snapshot_timestamp: new Date().toISOString(),
            current_price: parseFloat(data.lastPrice),
            volume_24h: parseFloat(data.volume),
            price_change_24h: parseFloat(data.priceChangePercent),
            high_price: parseFloat(data.highPrice),
            low_price: parseFloat(data.lowPrice),
            open_price: parseFloat(data.openPrice)
          }

          // Сохраняем в Supabase
          const result = await supabase.from('market_snapshots').insert([marketSnapshot])
          
          if (result.error) {
            results.errors.push(`Market data error for ${symbol}: ${result.error.message}`)
          } else {
            results.market_data_created++
            console.log(`📊 Market data saved for ${symbol}: $${marketSnapshot.current_price}`)
          }
        }
      } catch (error) {
        results.errors.push(`Failed to fetch ${symbol}: ${error}`)
      }
    }

    // 2. Генерируем новости на основе рыночных данных
    try {
      const newsItems = []
      
      // Получаем последние рыночные данные для анализа
      const recentMarketData = await supabase
        .from('market_snapshots')
        .select('*')
        .gte('snapshot_timestamp', new Date(Date.now() - 5 * 60 * 1000).toISOString())
        .order('snapshot_timestamp', { ascending: false })

      if (recentMarketData.data) {
        for (const data of recentMarketData.data.slice(0, 5)) {
          const priceChange = data.price_change_24h || 0
          
          if (Math.abs(priceChange) > 3) { // Значительное изменение цены
            const emoji = priceChange > 0 ? "📈" : "📉"
            const direction = priceChange > 0 ? "растет" : "падает"
            
            const newsItem = {
              title: `${emoji} ${data.symbol.replace('USDT', '')} ${direction} на ${Math.abs(priceChange).toFixed(2)}%`,
              content: `Криптовалюта ${data.symbol} показывает значительное движение: ${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}% за 24 часа. Текущая цена: $${data.current_price}`,
              source_name: 'GHOST Market Monitor',
              url: `https://binance.com/en/futures/${data.symbol}`,
              published_at: new Date().toISOString(),
              category: 'price_alert',
              impact_score: Math.min(Math.abs(priceChange) / 10, 1.0),
              is_critical: Math.abs(priceChange) > 8
            }
            
            newsItems.push(newsItem)
          }
        }
      }

      // Добавляем общие рыночные новости
      const marketNews = [
        {
          title: `📊 Рыночный обзор: ${symbols.length} активов отслеживается`,
          content: `GHOST система мониторит ${symbols.length} основных криптовалют в режиме реального времени. Данные обновляются каждую минуту.`,
          source_name: 'GHOST System',
          published_at: new Date().toISOString(),
          category: 'market_update',
          impact_score: 0.3,
          is_critical: false
        }
      ]

      newsItems.push(...marketNews)

      if (newsItems.length > 0) {
        const newsResult = await supabase.from('critical_news').insert(newsItems)
        
        if (newsResult.error) {
          results.errors.push(`News creation error: ${newsResult.error.message}`)
        } else {
          results.news_created = newsItems.length
          console.log(`📰 Created ${newsItems.length} news items`)
        }
      }
    } catch (error) {
      results.errors.push(`News generation error: ${error}`)
    }

    // 3. Создаем системные алерты при необходимости
    try {
      const alertsToCreate = []

      // Проверяем на экстремальные движения цен
      const extremeMovements = await supabase
        .from('market_snapshots')
        .select('*')
        .gte('snapshot_timestamp', new Date(Date.now() - 2 * 60 * 1000).toISOString())
        .or('price_change_24h.gt.10,price_change_24h.lt.-10')

      if (extremeMovements.data && extremeMovements.data.length > 0) {
        for (const movement of extremeMovements.data) {
          alertsToCreate.push({
            alert_type: 'EXTREME_PRICE_MOVEMENT',
            priority: 'HIGH',
            title: `🚨 Экстремальное движение ${movement.symbol}`,
            message: `${movement.symbol} изменился на ${movement.price_change_24h}% за 24 часа`,
            status: 'PENDING',
            delivery_channels: ['dashboard']
          })
        }
      }

      if (alertsToCreate.length > 0) {
        const alertResult = await supabase.from('alerts').insert(alertsToCreate)
        
        if (alertResult.error) {
          results.errors.push(`Alert creation error: ${alertResult.error.message}`)
        } else {
          results.alerts_created = alertsToCreate.length
          console.log(`🔔 Created ${alertsToCreate.length} alerts`)
        }
      }
    } catch (error) {
      results.errors.push(`Alert generation error: ${error}`)
    }

    console.log('✅ GHOST cron job completed:', results)

    return NextResponse.json({
      success: true,
      timestamp: new Date().toISOString(),
      results,
      message: `Processed ${results.market_data_created} market updates, ${results.news_created} news items, ${results.alerts_created} alerts`
    })

  } catch (error) {
    console.error('❌ GHOST cron job failed:', error)
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}

// Также поддерживаем POST для ручного запуска
export async function POST(request: NextRequest) {
  return GET(request)
}
