#!/bin/bash

echo "🚀 Настройка переменных окружения для Vercel деплоя..."

# Получаем значения из .env.local
SUPABASE_URL=$(grep "NEXT_PUBLIC_SUPABASE_URL=" .env.local | cut -d '=' -f2 | tr -d '"')
SUPABASE_ANON_KEY=$(grep "NEXT_PUBLIC_SUPABASE_ANON_KEY=" .env.local | cut -d '=' -f2 | tr -d '"')
SUPABASE_SERVICE_KEY=$(grep "SUPABASE_SERVICE_ROLE_KEY=" .env.local | cut -d '=' -f2 | tr -d '"')

echo "📋 Значения для Vercel Dashboard:"
echo "================================"
echo ""
echo "NEXT_PUBLIC_SUPABASE_URL:"
echo "$SUPABASE_URL"
echo ""
echo "NEXT_PUBLIC_SUPABASE_ANON_KEY:"
echo "$SUPABASE_ANON_KEY" 
echo ""
echo "SUPABASE_SERVICE_ROLE_KEY:"
echo "$SUPABASE_SERVICE_KEY"
echo ""
echo "NEXTAUTH_SECRET:"
echo "$(openssl rand -base64 32)"
echo ""
echo "NEXTAUTH_URL:"
echo "https://your-vercel-app.vercel.app"
echo ""
echo "DATABASE_URL:"
echo "$(grep "DATABASE_URL=" .env.local | cut -d '=' -f2 | tr -d '"')"
echo ""
echo "================================"
echo "📝 Скопируйте эти значения в Vercel Dashboard:"
echo "   Project Settings > Environment Variables"
echo ""
echo "🌐 Vercel Dashboard: https://vercel.com/dashboard"
