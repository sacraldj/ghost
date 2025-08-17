import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Middleware для API маршрутов - отключаем аутентификацию
export function middleware(request: NextRequest) {
  // Разрешаем все API запросы без аутентификации
  const response = NextResponse.next()
  
  // Добавляем CORS заголовки
  response.headers.set('Access-Control-Allow-Origin', '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  return response
}

export const config = {
  matcher: '/api/:path*',
}
