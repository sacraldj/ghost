import { NextRequest, NextResponse } from 'next/server';

/**
 * API для получения кода авторизации Telegram
 * Используется системой полной автоматизации
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const phone = searchParams.get('phone');
    const since = searchParams.get('since');
    
    if (!phone) {
      return NextResponse.json({ 
        success: false, 
        error: 'Phone required' 
      }, { status: 400 });
    }
    
    // TODO: Реализовать чтение кода из Telegram через Python backend
    // Пока возвращаем mock для тестирования
    
    const mockCode = await getMockAuthCode();
    
    if (mockCode) {
      return NextResponse.json({
        success: true,
        code: mockCode,
        method: 'mock',
        timestamp: new Date().toISOString()
      });
    }
    
    return NextResponse.json({
      success: false,
      error: 'Code not found',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error in get-auth-code:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Internal server error'
    }, { status: 500 });
  }
}

async function getMockAuthCode(): Promise<string | null> {
  // Mock для тестирования - в реальности будет обращение к Python backend
  const mockCodes = ['12345', '67890', '11111', '22222'];
  const randomCode = mockCodes[Math.floor(Math.random() * mockCodes.length)];
  
  // Симулируем случайность получения кода
  if (Math.random() > 0.7) {
    return randomCode;
  }
  
  return null;
}
