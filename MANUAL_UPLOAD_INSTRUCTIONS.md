# 📤 Ручная загрузка на GitHub

## Проблема
Аккаунт GitHub заблокирован, токен не работает. Используйте ручную загрузку.

## Решение: Ручная загрузка через веб-интерфейс

### 1. Подготовка архива
Архив уже создан: `ghost-project.zip` (226KB)

### 2. Загрузка на GitHub
1. Перейдите на https://github.com/sacraltrack18-sys/ghost-new
2. Нажмите "Add file" → "Upload files"
3. Перетащите файл `ghost-project.zip` или выберите его
4. Добавьте сообщение коммита: "Initial project upload"
5. Нажмите "Commit changes"

### 3. Альтернативно: Создайте новый репозиторий
1. Перейдите на https://github.com/new
2. Создайте репозиторий `ghost-trading`
3. Загрузите архив

## Решение: Используйте GitLab

### 1. Создайте проект на GitLab
1. Перейдите на https://gitlab.com
2. Создайте новый проект `ghost`
3. Скопируйте URL

### 2. Запушьте на GitLab
```bash
git remote set-url origin https://gitlab.com/YOUR_USERNAME/ghost.git
git push -u origin main
```

## Решение: Деплой через Vercel CLI

### 1. Установите Vercel CLI
```bash
npm i -g vercel
```

### 2. Войдите в Vercel
```bash
vercel login
```

### 3. Деплой проекта
```bash
vercel --prod
```

## Решение: Используйте GitHub CLI с новым аккаунтом

### 1. Создайте новый аккаунт GitHub
1. Перейдите на https://github.com
2. Создайте новый аккаунт с другим email
3. Создайте Personal Access Token

### 2. Используйте новый токен
```bash
git remote set-url origin https://NEW_TOKEN@github.com/NEW_USERNAME/ghost.git
git push -u origin main
```

## Решение: Используйте SSH

### 1. Создайте SSH ключ
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 2. Добавьте ключ в GitHub
1. Скопируйте публичный ключ: `cat ~/.ssh/id_ed25519.pub`
2. GitHub → Settings → SSH and GPG keys → New SSH key
3. Вставьте ключ

### 3. Используйте SSH для пуша
```bash
git remote set-url origin git@github.com:USERNAME/ghost.git
git push -u origin main
```

## Проверка после загрузки

### 1. Проверьте репозиторий
- Перейдите на https://github.com/sacraltrack18-sys/ghost-new
- Убедитесь, что код загружен

### 2. Подключите к Vercel
1. Перейдите на [Vercel](https://vercel.com)
2. Import Git Repository
3. Выберите репозиторий `ghost-new`
4. Настройте переменные окружения

### 3. Настройте переменные окружения в Vercel
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_SITE_URL=https://your-domain.vercel.app
```

## Полезные команды

```bash
# Проверка архива
ls -la ghost-project.zip

# Создание нового архива
git archive --format=zip --output=ghost-latest.zip main

# Проверка remote
git remote -v

# Изменение remote
git remote set-url origin NEW_URL
```

## Контакты для поддержки

- 📧 Email: support@ghost-trading.com
- 💬 Issues: GitHub Issues
- 📖 Документация: README.md

---

**Выберите подходящий способ и следуйте инструкциям!** 🚀
