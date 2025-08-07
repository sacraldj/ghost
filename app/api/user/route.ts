import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET() {
  try {
    const supabase = createRouteHandlerClient({ cookies })
    
    // Получаем текущего пользователя
    const { data: { user }, error } = await supabase.auth.getUser()
    
    if (error || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Ищем или создаем пользователя в нашей БД
    let dbUser = await prisma.user.findUnique({
      where: { email: user.email! },
      include: {
        trades: {
          take: 10,
          orderBy: { openedAt: 'desc' }
        },
        portfolios: true
      }
    })

    if (!dbUser) {
      // Создаем нового пользователя
      dbUser = await prisma.user.create({
        data: {
          email: user.email!,
          name: user.user_metadata?.full_name || user.email,
          avatar: user.user_metadata?.avatar_url
        },
        include: {
          trades: {
            take: 10,
            orderBy: { openedAt: 'desc' }
          },
          portfolios: true
        }
      })
    }

    return NextResponse.json({
      user: {
        id: dbUser.id,
        email: dbUser.email,
        name: dbUser.name,
        avatar: dbUser.avatar,
        role: dbUser.role,
        createdAt: dbUser.createdAt
      },
      trades: dbUser.trades,
      portfolios: dbUser.portfolios
    })

  } catch (error) {
    console.error('Error fetching user data:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
} 