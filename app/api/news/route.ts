import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '20')
    const minutes = parseInt(searchParams.get('minutes') || '60')
    const sentiment = searchParams.get('sentiment')
    const influence = searchParams.get('influence')
    const urgency = searchParams.get('urgency')
    const source = searchParams.get('source')
    const important = searchParams.get('important') === 'true'

    let query = supabase
      .from('news_items')
      .select('*')
      .gte('published_at', new Date(Date.now() - minutes * 60 * 1000).toISOString())
      .order('published_at', { ascending: false })
      .limit(limit)

    // Фильтры
    if (sentiment) {
      const sentimentValue = parseFloat(sentiment)
      query = query.gte('sentiment', sentimentValue)
    }

    if (influence) {
      const influenceValue = parseFloat(influence)
      query = query.gte('influence', influenceValue)
    }

    if (urgency) {
      const urgencyValue = parseFloat(urgency)
      query = query.gte('urgency', urgencyValue)
    }

    if (source) {
      query = query.eq('source_name', source)
    }

    if (important) {
      query = query.eq('is_important', true)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching news:', error)
      return NextResponse.json({ error: 'Failed to fetch news' }, { status: 500 })
    }

    return NextResponse.json({ news: data })
  } catch (error) {
    console.error('Error in news API:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, data } = body

    switch (action) {
      case 'bookmark':
        // Добавление закладки на новость
        const { error: bookmarkError } = await supabase
          .from('news_bookmarks')
          .insert({
            user_id: data.user_id,
            news_id: data.news_id,
            created_at: new Date().toISOString()
          })

        if (bookmarkError) {
          return NextResponse.json({ error: 'Failed to bookmark news' }, { status: 500 })
        }
        break

      case 'analyze':
        // Запрос на анализ новости
        const { error: analysisError } = await supabase
          .from('analysis_history')
          .insert({
            user_id: data.user_id,
            news_id: data.news_id,
            action_type: 'analyze',
            created_at: new Date().toISOString()
          })

        if (analysisError) {
          return NextResponse.json({ error: 'Failed to log analysis' }, { status: 500 })
        }
        break

      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error in news POST API:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
