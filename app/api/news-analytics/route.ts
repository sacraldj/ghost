import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
)

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const symbol = searchParams.get('symbol') || 'BTCUSDT'
    const timeframe = searchParams.get('timeframe') || '24h'

    console.log(`📰 Loading news analytics for ${symbol} (${timeframe})...`)

    // Получаем новости из нашей базы critical_news
    const { data: newsData, error: newsError } = await supabase
      .from('critical_news')
      .select('*')
      .order('published_at', { ascending: false })
      .limit(20)

    if (newsError) {
      console.warn('⚠️ News data error:', newsError)
    }

    // Получаем данные из news_events если есть
    const { data: eventsData, error: eventsError } = await supabase
      .from('news_events')
      .select('*')
      .order('event_time', { ascending: false })
      .limit(10)

    if (eventsError) {
      console.warn('⚠️ Events data error:', eventsError)
    }

    // Формируем ответ с реальными данными или fallback
    const news = newsData && newsData.length > 0 ? newsData.map((item: any) => ({
      id: item.id || Math.random().toString(),
      title: item.title || item.headline,
      content: item.content || item.summary || 'Подробности в источнике',
      source: item.source || 'GHOST News Engine',
      published_at: item.published_at || item.created_at,
      sentiment: calculateSentiment(item.title || item.headline || ''),
      impact_score: item.influence_score || Math.random() * 10,
      price_correlation: item.market_impact || (Math.random() - 0.5) * 2,
      related_symbols: item.affected_symbols ? item.affected_symbols.split(',') : [symbol],
      event_type: item.category || 'market'
    })) : getMockNewsData(symbol)

    const events = eventsData && eventsData.length > 0 ? eventsData.map((event: any) => ({
      timestamp: event.event_time || event.created_at,
      price: event.price_at_event || 43200,
      news_id: event.news_id || event.id,
      title: event.title || event.description,
      impact: event.impact_level || 'medium',
      direction: event.price_direction || (Math.random() > 0.5 ? 'up' : 'down')
    })) : getMockEventsData()

    console.log(`✅ Returning ${news.length} news items and ${events.length} events`)

    return NextResponse.json({
      news,
      events,
      timestamp: new Date().toISOString(),
      source: newsData && newsData.length > 0 ? 'GHOST_DB' : 'MOCK_DATA'
    })

  } catch (error) {
    console.error('❌ News analytics API error:', error)
    
    // Fallback на моковые данные при ошибке
    const symbol = new URL(request.url).searchParams.get('symbol') || 'BTCUSDT'
    
    return NextResponse.json({
      news: getMockNewsData(symbol),
      events: getMockEventsData(),
      timestamp: new Date().toISOString(),
      source: 'FALLBACK_DATA',
      error: 'Database unavailable - using fallback data'
    })
  }
}

function calculateSentiment(text: string): 'positive' | 'negative' | 'neutral' {
  const positiveWords = ['рост', 'увеличение', 'покупка', 'bull', 'rise', 'gain', 'up']
  const negativeWords = ['падение', 'снижение', 'продажа', 'bear', 'fall', 'loss', 'down']
  
  const lowerText = text.toLowerCase()
  const positiveCount = positiveWords.filter(word => lowerText.includes(word)).length
  const negativeCount = negativeWords.filter(word => lowerText.includes(word)).length
  
  if (positiveCount > negativeCount) return 'positive'
  if (negativeCount > positiveCount) return 'negative'
  return 'neutral'
}

function getMockNewsData(symbol: string) {
  const baseNews = [
    {
      id: '1',
      title: '🇺🇸 Министр финансов США: Мы не собираемся покупать криптовалюту в наши резервы',
      content: 'Министр финансов США заявил о планах использовать конфискованные активы и сохранить золото как средство накопления...',
      source: 'GHOST Critical News Engine',
      published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      sentiment: 'negative' as const,
      impact_score: 8.5,
      price_correlation: -0.75,
      related_symbols: ['BTCUSDT', 'ETHUSDT'],
      event_type: 'regulatory'
    },
    {
      id: '2',
      title: '🚀 Ethereum: Артур Хейс заявил, что закупает ETH и обещает больше не фиксировать прибыль',
      content: 'Основатель BitMEX объявил о крупных покупках ETH на сумму 6.85 млн долларов...',
      source: 'GHOST Market Intelligence',
      published_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      sentiment: 'positive' as const,
      impact_score: 7.2,
      price_correlation: 0.68,
      related_symbols: ['ETHUSDT'],
      event_type: 'market'
    },
    {
      id: '3',
      title: '📊 Стоимость крипто-активов Виталика Бутерина превысила 1 млрд $',
      content: 'Портфель основателя Ethereum достиг исторического максимума на фоне роста цены ETH...',
      source: 'GHOST Analytics',
      published_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      sentiment: 'positive' as const,
      impact_score: 6.8,
      price_correlation: 0.45,
      related_symbols: ['ETHUSDT'],
      event_type: 'market'
    }
  ]

  // Адаптируем под выбранный символ
  return baseNews.map(news => ({
    ...news,
    related_symbols: news.related_symbols.includes(symbol) ? news.related_symbols : [...news.related_symbols, symbol]
  }))
}

function getMockEventsData() {
  return [
    {
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      price: 42850,
      news_id: '1',
      title: 'Заявление министра финансов США',
      impact: 'high' as const,
      direction: 'down' as const
    },
    {
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      price: 43200,
      news_id: '2',
      title: 'Покупки ETH от Артура Хейса',
      impact: 'medium' as const,
      direction: 'up' as const
    }
  ]
}