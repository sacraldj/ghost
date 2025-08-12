import { NextResponse } from 'next/server'

export const runtime = 'nodejs'

export async function GET() {
  try {
    // В проде подключим очередь/БД логов. Пока возвращаем пустой поток.
    return NextResponse.json({ success: true, data: [] })
  } catch (error) {
    return NextResponse.json({ success: false, error: 'failed' }, { status: 500 })
  }
}

