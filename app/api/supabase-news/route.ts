import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Инициализация Supabase клиента с новыми или старыми ключами
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY!

const supabase = createClient(supabaseUrl, supabaseKey)

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '10')
    const minutes = parseInt(searchParams.get('minutes') || '5')
    const type = searchParams.get('type') || 'critical' // 'critical' или 'regular'
    const source = searchParams.get('source')

    let query = supabase

    if (type === 'critical') {
      // Получаем критические новости из Supabase
      query = query
        .from('critical_news')
        .select('*')
        .gte('published_at', new Date(Date.now() - minutes * 60 * 1000).toISOString())
        .order('published_at', { ascending: false })
        .limit(limit)
    } else {
      // Получаем обычные новости из Supabase
      query = query
        .from('news_items')
        .select('*')
        .gte('published_at', new Date(Date.now() - minutes * 60 * 1000).toISOString())
        .order('published_at', { ascending: false })
        .limit(limit)
    }

    // Фильтр по источнику если указан
    if (source) {
      query = query.eq('source_name', source)
    }

    const { data, error } = await query

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: 'Database error' }, { status: 500 })
    }

    // Преобразование данных
    const news = data?.map(item => ({
      id: item.id,
      source: item.source_name,
      title: item.title,
      content: item.content,
      url: item.url,
      publishedAt: item.published_at,
      sentiment: item.sentiment,
      urgency: item.urgency,
      isCritical: type === 'critical' ? item.is_critical : item.is_important,
      priority: type === 'critical' ? item.priority : item.priority_level,
      marketImpact: type === 'critical' ? item.market_impact : null,
      syncedAt: item.synced_at
    })) || []

    return NextResponse.json({
      news,
      count: news.length,
      timestamp: new Date().toISOString(),
      source: 'supabase',
      type,
      message: news.length > 0 
        ? `${type === 'critical' ? 'Критические' : 'Обычные'} новости из Supabase` 
        : 'Новостей нет'
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
