import { NextRequest, NextResponse } from 'next/server';

/**
 * API для автоматической авторизации через Render
 * Render читает коды из своей авторизованной сессии и отправляет их сюда
 */
export async function POST(request: NextRequest) {
  try {
    const { phone, session_name } = await request.json();
    
    if (!phone || !session_name) {
      return NextResponse.json({ 
        success: false, 
        error: 'Phone and session_name required' 
      }, { status: 400 });
    }
    
    // TODO: Вызвать Python скрипт на Render для автоматической авторизации
    // Пока возвращаем заглушку
    
    return NextResponse.json({
      success: true,
      message: `Auto-auth request for ${phone} -> ${session_name}`,
      status: 'processing',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error in auto-auth:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Auto-auth failed'
    }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const session_name = searchParams.get('session');
    
    // Проверяем статус авторизации
    return NextResponse.json({
      success: true,
      session_name,
      status: 'authorized', // TODO: реальная проверка
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Status check failed'
    }, { status: 500 });
  }
}
