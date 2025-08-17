import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'nodejs'

export async function GET(request: NextRequest) {
  try {
    // В проде подключим очередь/БД логов. Пока возвращаем пустой поток.
    return NextResponse.json({ 
      success: true, 
      data: [],
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    console.error('Alerts feed error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to fetch alerts feed' 
    }, { status: 500 })
  }
}
