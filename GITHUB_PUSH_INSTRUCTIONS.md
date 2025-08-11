# 🔧 Инструкции для пуша на GitHub

## Проблема
Аккаунт GitHub заблокирован. Используйте альтернативные способы.

## Решение 1: Создайте новый аккаунт GitHub

### 1. Создайте новый аккаунт
1. Перейдите на [GitHub](https://github.com)
2. Создайте новый аккаунт с другим email
3. Создайте репозиторий `ghost`

### 2. Обновите remote URL
```bash
git remote set-url origin https://github.com/NEW_USERNAME/ghost.git
git push -u origin main
```

## Решение 2: Используйте Personal Access Token

### 1. Создайте токен
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Выберите scopes: `repo`, `workflow`
4. Скопируйте токен

### 2. Используйте токен для пуша
```bash
git remote set-url origin https://TOKEN@github.com/sacraltrack18-sys/ghost.git
git push -u origin main
```

## Решение 3: Используйте SSH

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
git remote set-url origin git@github.com:sacraltrack18-sys/ghost.git
git push -u origin main
```

## Решение 4: Используйте GitLab

### 1. Создайте проект на GitLab
1. Перейдите на [GitLab](https://gitlab.com)
2. Создайте новый проект `ghost`
3. Скопируйте URL

### 2. Запушьте на GitLab
```bash
git remote set-url origin https://gitlab.com/YOUR_USERNAME/ghost.git
git push -u origin main
```

## Решение 5: Деплой через Vercel CLI

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

## Решение 6: Создайте архив и загрузите вручную

### 1. Создайте архив
```bash
git archive --format=zip --output=ghost.zip main
```

### 2. Загрузите на GitHub
1. Перейдите в репозиторий на GitHub
2. Upload files
3. Загрузите архив

### 3. Или используйте GitHub CLI
```bash
# Установите GitHub CLI
brew install gh

# Войдите
gh auth login

# Создайте репозиторий
gh repo create ghost --public

# Запушьте код
git push -u origin main
```

## Проверка после пуша

### 1. Проверьте репозиторий
- Перейдите на https://github.com/sacraltrack18-sys/ghost
- Убедитесь, что код загружен

### 2. Подключите к Vercel
1. Перейдите на [Vercel](https://vercel.com)
2. Import Git Repository
3. Выберите репозиторий `ghost`
4. Настройте переменные окружения

### 3. Настройте переменные окружения в Vercel
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_SITE_URL=https://your-domain.vercel.app
```

## Альтернативные платформы

### GitLab
- Бесплатный хостинг
- CI/CD встроен
- Можно подключить к Vercel

### Bitbucket
- Бесплатный хостинг
- Интеграция с Jira
- Можно подключить к Vercel

### Gitea
- Self-hosted Git
- Полный контроль
- Можно подключить к Vercel

## Полезные команды

```bash
# Проверка remote
git remote -v

# Изменение remote
git remote set-url origin NEW_URL

# Принудительный пуш (осторожно!)
git push -f origin main

# Создание архива
git archive --format=zip --output=ghost.zip main

# Проверка статуса
git status
git log --oneline
```

## Контакты для поддержки

- 📧 Email: support@ghost-trading.com
- 💬 Issues: GitHub Issues
- 📖 Документация: README.md

---

**Выберите подходящий способ и следуйте инструкциям!** 🚀
