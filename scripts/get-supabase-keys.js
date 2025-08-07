#!/usr/bin/env node

/**
 * GHOST | Get Supabase Keys
 * Помощник для получения ключей Supabase
 */

console.log('🔑 ПОЛУЧЕНИЕ КЛЮЧЕЙ SUPABASE')
console.log('=' * 50)

console.log('📋 Шаги:')
console.log('')
console.log('1. Перейдите на https://supabase.com')
console.log('2. Войдите в ваш проект')
console.log('3. Перейдите в Settings → API')
console.log('4. Скопируйте следующие ключи:')
console.log('')
console.log('   Project URL: https://qjdpckwqozsbpskwplfl.supabase.co')
console.log('   anon public: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MDUyNTUsImV4cCI6MjA3MDA4MTI1NX0.kY8A88CoBNN2m7EAbJpy1TNfqu9zOY4pFKmvLZ42Lf8')
console.log('   service_role: [СКОПИРУЙТЕ ЭТОТ КЛЮЧ]')
console.log('')
console.log('5. Добавьте service_role в файл .env:')
console.log('')
console.log('   SUPABASE_SERVICE_ROLE_KEY="ваш-service-role-ключ"')
console.log('')
console.log('6. Запустите настройку:')
console.log('')
console.log('   npm run setup:supabase:simple')
console.log('')

console.log('🔗 Прямая ссылка на ваш проект:')
console.log('https://supabase.com/dashboard/project/qjdpckwqozsbpskwplfl/settings/api')
console.log('')

console.log('💡 Service Role Key нужен для создания таблиц')
console.log('   Этот ключ имеет полные права администратора')
console.log('   Храните его в безопасности!') 