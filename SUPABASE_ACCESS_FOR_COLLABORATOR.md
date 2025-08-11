# 🔐 Доступ к Supabase для второго человека

## 📋 Инструкция для предоставления доступа

### **Вариант 1: Полный доступ через Dashboard (Рекомендуется)**

#### **Шаги для владельца аккаунта:**

1. **Войдите в Supabase Dashboard**
   ```
   https://supabase.com/dashboard
   ```

2. **Выберите проект Ghost**
   - Найдите проект с URL: `qjdpckwqozsbpskwplfl.supabase.co`

3. **Добавьте нового члена команды**
   - Перейдите в **Settings** → **General**
   - Найдите раздел **Team Members**
   - Нажмите **Invite member**
   - Введите email второго человека
   - Выберите роль: **Developer** или **Admin**

4. **Отправьте приглашение**
   - Второй человек получит email
   - Он должен перейти по ссылке и создать аккаунт

#### **Шаги для второго человека:**

1. **Проверьте email**
   - Найдите письмо от Supabase с приглашением
   - Перейдите по ссылке в письме

2. **Создайте аккаунт Supabase**
   - Если у вас нет аккаунта, создайте его
   - Если есть, войдите в существующий

3. **Примите приглашение**
   - Подтвердите участие в проекте
   - Теперь у вас есть доступ к Dashboard

### **Вариант 2: Доступ только к API**

#### **Для разработки и работы с данными:**

1. **Получите ключи доступа**
   ```bash
   # Project URL
   NEXT_PUBLIC_SUPABASE_URL="https://qjdpckwqozsbpskwplfl.supabase.co"
   
   # Anon Key (публичный)
   NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MDUyNTUsImV4cCI6MjA3MDA4MTI1NX0.kY8A88CoBNN2m7EAbJpy1TNfqu9zOY4pFKmvLZ42Lf8"
   
   # Service Role Key (приватный - только для серверной части)
   SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
   ```

2. **Создайте файл .env.local**
   ```bash
   # Скопируйте эти переменные в .env.local
   NEXT_PUBLIC_SUPABASE_URL=https://qjdpckwqozsbpskwplfl.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MDUyNTUsImV4cCI6MjA3MDA4MTI1NX0.kY8A88CoBNN2m7EAbJpy1TNfqu9zOY4pFKmvLZ42Lf8
   ```

3. **Установите Supabase клиент**
   ```bash
   npm install @supabase/supabase-js
   ```

4. **Используйте в коде**
   ```typescript
   import { createClient } from '@supabase/supabase-js'
   
   const supabase = createClient(
     process.env.NEXT_PUBLIC_SUPABASE_URL!,
     process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
   )
   ```

### **Вариант 3: Доступ через SQL Editor**

#### **Для работы с базой данных:**

1. **Получите Database Password**
   - В Supabase Dashboard → Settings → Database
   - Найдите **Database Password**

2. **Подключитесь через любой SQL клиент**
   ```bash
   # Host: db.qjdpckwqozsbpskwplfl.supabase.co
   # Port: 5432
   # Database: postgres
   # Username: postgres
   # Password: [получите из Dashboard]
   ```

### **🔒 Безопасность**

#### **Рекомендации:**

1. **Не делитесь Service Role Key**
   - Этот ключ дает полный доступ к базе данных
   - Используйте только для серверной части

2. **Anon Key безопасен для клиента**
   - Можно использовать в браузере
   - Ограничен правами RLS (Row Level Security)

3. **Используйте RLS политики**
   ```sql
   -- Пример политики безопасности
   CREATE POLICY "Users can only see their own data" ON users
   FOR ALL USING (auth.uid() = user_id);
   ```

### **📊 Что можно делать с доступом:**

#### **С полным доступом (Dashboard):**
- ✅ Просматривать данные в таблицах
- ✅ Выполнять SQL запросы
- ✅ Настраивать аутентификацию
- ✅ Управлять API ключами
- ✅ Настраивать Edge Functions
- ✅ Просматривать логи

#### **С API доступом:**
- ✅ Читать данные через API
- ✅ Записывать данные (с ограничениями RLS)
- ✅ Использовать аутентификацию
- ✅ Вызывать Edge Functions

#### **С Database доступом:**
- ✅ Выполнять SQL запросы
- ✅ Управлять схемой базы данных
- ✅ Создавать/удалять таблицы
- ✅ Настраивать триггеры и функции

### **🚀 Быстрый старт для второго человека:**

1. **Клонируйте проект**
   ```bash
   git clone [URL вашего репозитория]
   cd Ghost
   ```

2. **Установите зависимости**
   ```bash
   npm install
   ```

3. **Создайте .env.local**
   ```bash
   cp env.example .env.local
   # Отредактируйте файл с вашими ключами
   ```

4. **Запустите проект**
   ```bash
   npm run dev
   ```

5. **Проверьте доступ**
   - Откройте http://localhost:3000
   - Попробуйте зарегистрироваться/войти
   - Проверьте работу с данными

### **📞 Поддержка**

Если возникнут проблемы:

1. **Проверьте логи Supabase**
   - Dashboard → Logs

2. **Проверьте консоль браузера**
   - F12 → Console

3. **Проверьте Network tab**
   - F12 → Network → Supabase запросы

4. **Обратитесь к владельцу проекта**
   - Для получения дополнительных прав доступа
   - Для настройки новых функций

### **✅ Чек-лист готовности:**

- [ ] Второй человек получил приглашение в команду
- [ ] Создан аккаунт Supabase
- [ ] Принято приглашение в проект
- [ ] Настроен .env.local с ключами
- [ ] Установлены зависимости проекта
- [ ] Проект запускается локально
- [ ] Аутентификация работает
- [ ] API запросы выполняются

**🎯 Готово! Второй человек теперь имеет доступ к вашему Supabase проекту!**
