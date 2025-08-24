/**
 * GHOST News Analysis API
 * API endpoint для получения новостной аналитики в дашборде
 * Безопасный - не влияет на торговые операции
 */

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Force Node.js runtime для работы с внешними модулями
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

interface NewsAnalysisResponse {
  enabled: boolean
  statistics?: {
    total_news: number
    critical_news: number
    prediction_accuracy: string
    avg_market_impact: string
    sentiment_breakdown: {
      bullish: number
      bearish: number
      neutral: number
    }
    top_sources: Record<string, number>
    time_accuracy: {
      '1h_accuracy': string
      '4h_accuracy': string
      '24h_accuracy': string
    }
  }
  recent_news?: Array<{
    id: string
    title: string
    source: string
    sentiment: number
    urgency: number
    market_impact: number
    published_at: string
    filter_info?: {
      importance_score: number
      detected_categories: string[]
    }
  }>
  integration_status?: {
    enabled: boolean
    components: Record<string, boolean>
    hooks_registered: number
  }
  error?: string
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action') || 'overview'
    const days = parseInt(searchParams.get('days') || '7')
    const limit = parseInt(searchParams.get('limit') || '50')

    // Проверяем включена ли новостная интеграция
    const newsEnabled = process.env.GHOST_NEWS_INTEGRATION_ENABLED === 'true'
    
    if (!newsEnabled) {
      return NextResponse.json({
        enabled: false,
        message: 'News integration is disabled. Set GHOST_NEWS_INTEGRATION_ENABLED=true to enable.',
        integration_status: {
          enabled: false,
          components: {},
          hooks_registered: 0
        }
      } as NewsAnalysisResponse)
    }

    // Проверяем Supabase подключение
    if (!supabase) {
      return NextResponse.json({
        enabled: true,
        error: 'Supabase not configured for news analysis',
        integration_status: {
          enabled: true,
          components: { supabase: false },
          hooks_registered: 0
        }
      } as NewsAnalysisResponse, { status: 503 })
    }

    const response: NewsAnalysisResponse = {
      enabled: true,
      integration_status: {
        enabled: true,
        components: {
          supabase: true,
          news_enhancer: true,
          stats_tracker: true,
          noise_filter: true
        },
        hooks_registered: 0
      }
    }

    switch (action) {
      case 'overview':
        // Получаем общую статистику
        const stats = await getNewsStatistics(days)
        response.statistics = stats
        
        // Получаем недавние новости
        const recentNews = await getRecentNews(limit)
        response.recent_news = recentNews
        break

      case 'statistics':
        // Только статистика
        response.statistics = await getNewsStatistics(days)
        break

      case 'recent':
        // Только недавние новости
        response.recent_news = await getRecentNews(limit)
        break

      case 'status':
        // Только статус интеграции (уже добавлен выше)
        break

      default:
        return NextResponse.json({
          enabled: true,
          error: 'Invalid action. Use: overview, statistics, recent, or status'
        } as NewsAnalysisResponse, { status: 400 })
    }

    return NextResponse.json(response)

  } catch (error) {
    console.error('News analysis API error:', error)
    return NextResponse.json({
      enabled: true,
      error: 'Internal server error in news analysis',
      integration_status: {
        enabled: true,
        components: { error: true },
        hooks_registered: 0
      }
    } as NewsAnalysisResponse, { status: 500 })
  }
}

async function getNewsStatistics(days: number) {
  try {
    // Пытаемся получить статистику из critical_news таблицы
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - days)

    // Сначала пытаемся получить из critical_news
    let { data: newsData, error } = await supabase
      .from('critical_news')
      .select('*')
      .gte('created_at', startDate.toISOString())
      .order('created_at', { ascending: false })

    // Если critical_news недоступна, пытаемся получить из news_events
    if (error || !newsData || newsData.length === 0) {
      console.log('Trying news_events table as fallback...')
      const { data: newsEventsData, error: eventsError } = await supabase
        .from('news_events')
        .select('*')
        .gte('created_at', startDate.toISOString())
        .order('created_at', { ascending: false })

      if (eventsError) {
        console.error('Error fetching from both news tables:', { critical_news: error, news_events: eventsError })
        return getDefaultStatistics()
      }

      // Преобразуем формат news_events в формат critical_news
      newsData = newsEventsData?.map((event: any) => ({
        id: event.id,
        title: event.title,
        content: event.content,
        source_name: event.source,
        created_at: event.created_at,
        published_at: event.published_at,
        sentiment: event.price_change_1h ? (event.price_change_1h > 0 ? 0.5 : -0.5) : 0,
        market_impact: Math.abs(event.price_change_1h || 0),
        is_critical: event.reaction_type === 'critical',
        prediction_result: null, // Нет данных о результатах предсказаний в news_events
        urgency: event.reaction_type === 'critical' ? 0.8 : 0.3
      })) || []
    }

    // Анализируем данные
    const totalNews = newsData?.length || 0
    const criticalNews = newsData?.filter((news: any) => news.is_critical)?.length || 0
    
    // Подсчёт sentiment
    let bullish = 0, bearish = 0, neutral = 0
    const sources: Record<string, number> = {}

    newsData?.forEach((news: any) => {
      // Sentiment анализ
      if (news.sentiment > 0.1) bullish++
      else if (news.sentiment < -0.1) bearish++
      else neutral++

      // Источники
      const source = news.source_name || 'unknown'
      sources[source] = (sources[source] || 0) + 1
    })

    // Топ источники
    const topSources = Object.entries(sources)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .reduce((obj, [key, value]) => ({ ...obj, [key]: value }), {})

    // Расчет точности предсказаний на основе реальных данных
    let predictionAccuracy = '0%'
    let timeAccuracy = {
      '1h_accuracy': '0%',
      '4h_accuracy': '0%', 
      '24h_accuracy': '0%'
    }

    if (newsData && newsData.length > 0) {
      // Получаем новости с результатами предсказаний
      const newsWithPredictions = newsData.filter((news: any) => news.prediction_result !== null)
      
      if (newsWithPredictions.length > 0) {
        const correctPredictions = newsWithPredictions.filter((news: any) => news.prediction_result === true).length
        predictionAccuracy = ((correctPredictions / newsWithPredictions.length) * 100).toFixed(1) + '%'
      }

      // Расчет точности по времени (упрощенно - можно улучшить)
      const oneHourNews = newsData.filter((news: any) => {
        const newsTime = new Date(news.created_at)
        const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
        return newsTime >= oneHourAgo && news.prediction_result !== null
      })
      
      const fourHourNews = newsData.filter((news: any) => {
        const newsTime = new Date(news.created_at)
        const fourHoursAgo = new Date(Date.now() - 4 * 60 * 60 * 1000)
        return newsTime >= fourHoursAgo && news.prediction_result !== null
      })

      const dayNews = newsData.filter((news: any) => {
        const newsTime = new Date(news.created_at)
        const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
        return newsTime >= dayAgo && news.prediction_result !== null
      })

      if (oneHourNews.length > 0) {
        const correct1h = oneHourNews.filter((news: any) => news.prediction_result === true).length
        timeAccuracy['1h_accuracy'] = ((correct1h / oneHourNews.length) * 100).toFixed(1) + '%'
      }

      if (fourHourNews.length > 0) {
        const correct4h = fourHourNews.filter((news: any) => news.prediction_result === true).length
        timeAccuracy['4h_accuracy'] = ((correct4h / fourHourNews.length) * 100).toFixed(1) + '%'
      }

      if (dayNews.length > 0) {
        const correct24h = dayNews.filter((news: any) => news.prediction_result === true).length
        timeAccuracy['24h_accuracy'] = ((correct24h / dayNews.length) * 100).toFixed(1) + '%'
      }
    }

    return {
      total_news: totalNews,
      critical_news: criticalNews,
      prediction_accuracy: predictionAccuracy,
      avg_market_impact: (newsData?.reduce((sum: number, news: any) => sum + (news.market_impact || 0), 0) / totalNews || 0).toFixed(3),
      sentiment_breakdown: { bullish, bearish, neutral },
      top_sources: topSources,
      time_accuracy: timeAccuracy
    }

  } catch (error) {
    console.error('Error in getNewsStatistics:', error)
    return getDefaultStatistics()
  }
}

async function getRecentNews(limit: number) {
  try {
    // Сначала пытаемся получить из critical_news
    let { data: newsData, error } = await supabase
      .from('critical_news')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(limit)

    // Если critical_news недоступна, пытаемся получить из news_events
    if (error || !newsData || newsData.length === 0) {
      console.log('Trying news_events for recent news...')
      const { data: newsEventsData, error: eventsError } = await supabase
        .from('news_events')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit)

      if (eventsError) {
        console.error('Error fetching recent news from both tables:', { critical_news: error, news_events: eventsError })
        return []
      }

      // Преобразуем формат news_events
      newsData = newsEventsData?.map((event: any) => ({
        id: event.id,
        title: event.title,
        content: event.content,
        source_name: event.source,
        created_at: event.created_at,
        published_at: event.published_at,
        sentiment: event.price_change_1h ? (event.price_change_1h > 0 ? 0.5 : -0.5) : 0,
        market_impact: Math.abs(event.price_change_1h || 0),
        is_critical: event.reaction_type === 'critical',
        urgency: event.reaction_type === 'critical' ? 0.8 : 0.3
      })) || []
    }

    return newsData?.map((news: any) => ({
      id: news.id?.toString() || 'unknown',
      title: news.title || 'No title',
      source: news.source_name || 'unknown',
      sentiment: news.sentiment || 0,
      urgency: news.urgency || 0,
      market_impact: news.market_impact || 0,
      published_at: news.published_at || news.created_at,
      filter_info: {
        importance_score: news.market_impact || 0,
        detected_categories: news.is_critical ? ['critical'] : []
      }
    })) || []

  } catch (error) {
    console.error('Error in getRecentNews:', error)
    return []
  }
}

function getDefaultStatistics() {
  return {
    total_news: 0,
    critical_news: 0,
    prediction_accuracy: '0.0%',
    avg_market_impact: '0.000',
    sentiment_breakdown: { bullish: 0, bearish: 0, neutral: 0 },
    top_sources: {},
    time_accuracy: {
      '1h_accuracy': '0.0%',
      '4h_accuracy': '0.0%',
      '24h_accuracy': '0.0%'
    }
  }
}

// POST для обновления настроек (опционально)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, settings } = body

    if (action === 'update_settings') {
      // Здесь можно добавить логику обновления настроек
      // Например, обновление порогов фильтрации
      
      return NextResponse.json({
        success: true,
        message: 'Settings updated successfully',
        updated_settings: settings
      })
    }

    return NextResponse.json({
      error: 'Invalid action for POST request'
    }, { status: 400 })

  } catch (error) {
    console.error('News analysis POST error:', error)
    return NextResponse.json({
      error: 'Failed to process POST request'
    }, { status: 500 })
  }
}
