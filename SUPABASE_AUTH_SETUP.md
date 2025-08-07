# Настройка аутентификации в Supabase

## Проблема
Ошибка `"Unsupported provider: provider is not enabled"` означает, что провайдер аутентификации не включен в настройках Supabase.

## Решение

### 1. Включение Email/Password аутентификации

1. **Войдите в Supabase Dashboard**
   - Перейдите на https://supabase.com/dashboard
   - Выберите ваш проект

2. **Настройка Authentication**
   - В левом меню выберите **Authentication**
   - Перейдите в **Settings**

3. **Включите Email аутентификацию**
   - Найдите раздел **Email Auth**
   - Убедитесь, что **Enable Email Signup** включен
   - Убедитесь, что **Enable Email Confirmations** включен

### 2. Настройка Google OAuth (опционально)

1. **В разделе Authentication > Providers**
   - Найдите **Google**
   - Нажмите **Enable**

2. **Настройка Google OAuth**
   - Создайте проект в Google Cloud Console
   - Получите Client ID и Client Secret
   - Добавьте их в настройки Google в Supabase

### 3. Настройка URL перенаправлений

1. **В Authentication > Settings**
   - Найдите **Site URL**
   - Установите: `http://localhost:3000` (для разработки)
   - Для продакшена: `https://yourdomain.com`

2. **Redirect URLs**
   - Добавьте: `http://localhost:3000/auth/callback`
   - Добавьте: `http://localhost:3000/dashboard`

### 4. Настройка Email Templates

1. **В Authentication > Templates**
   - Настройте **Confirm signup** template
   - Настройте **Reset password** template

### 5. Проверка переменных окружения

Убедитесь, что в `.env.local` есть:

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### 6. Тестирование

1. **Запустите приложение**
   ```bash
   npm run dev
   ```

2. **Проверьте регистрацию**
   - Перейдите на http://localhost:3000/auth
   - Попробуйте зарегистрироваться

3. **Проверьте вход**
   - Попробуйте войти с существующим аккаунтом

## Альтернативное решение

Если проблема с провайдерами продолжается, можно использовать только Email/Password аутентификацию:

### Обновление компонента Auth

```typescript
// Удалите Google OAuth кнопку из components/Auth.tsx
// Оставьте только Email/Password аутентификацию
```

### Обновление конфигурации

```typescript
// В Supabase Dashboard
// Authentication > Settings > Auth Providers
// Отключите все провайдеры кроме Email
```

## Проверка статуса

После настройки проверьте:

1. **В Supabase Dashboard > Authentication > Users**
   - Должны появляться новые пользователи

2. **В логах приложения**
   - Проверьте консоль браузера на ошибки

3. **В Network tab**
   - Проверьте запросы к `/api/auth/*`

## Частые проблемы

### 1. "Email not confirmed"
- Проверьте настройки Email в Supabase
- Убедитесь, что SMTP настроен правильно

### 2. "Invalid login credentials"
- Проверьте правильность email/password
- Убедитесь, что пользователь подтвердил email

### 3. "Provider not enabled"
- Проверьте настройки провайдеров в Supabase Dashboard
- Убедитесь, что Email аутентификация включена

## Дополнительные настройки

### 1. Настройка SMTP (для email подтверждений)

1. **В Supabase Dashboard > Settings > Auth**
2. **Найдите SMTP Settings**
3. **Настройте SMTP сервер** (Gmail, SendGrid, etc.)

### 2. Настройка RLS (Row Level Security)

```sql
-- Включите RLS для таблиц
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Создайте политики
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);
```

### 3. Настройка профилей пользователей

```sql
-- Создайте функцию для автоматического создания профиля
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, created_at)
  VALUES (new.id, new.email, new.created_at);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Создайте триггер
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
```

## Заключение

После выполнения всех настроек аутентификация должна работать корректно. Если проблемы продолжаются, проверьте:

1. **Логи Supabase** в Dashboard
2. **Консоль браузера** на ошибки
3. **Network tab** для анализа запросов
4. **Переменные окружения** на правильность

Система готова к использованию после правильной настройки!
