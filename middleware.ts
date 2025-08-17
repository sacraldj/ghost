import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  // Разрешаем доступ к API маршрутам без аутентификации
  if (req.nextUrl.pathname.startsWith('/api/')) {
    return NextResponse.next()
  }

  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  const {
    data: { session },
  } = await supabase.auth.getSession()

  // Если пользователь аутентифицирован и пытается получить доступ к странице аутентификации
  if (session && req.nextUrl.pathname.startsWith('/auth')) {
    const redirectUrl = req.nextUrl.clone()
    redirectUrl.pathname = '/dashboard'
    return NextResponse.redirect(redirectUrl)
  }

  return res
}

export const config = {
  matcher: [
    // Только для страниц аутентификации, исключаем все API
    '/auth/:path*', 
    '/simple-login/:path*'
  ],
}
