# 🔧 Настройка реальных Telegram каналов

## ⚠️ КРИТИЧЕСКИ ВАЖНО

В текущей конфигурации `config/sources.json` используются **ТЕСТОВЫЕ channel_id**:

```json
"channel_id": "-1001234567890"  // ❌ ТЕСТОВЫЙ ID
```

Эти ID **НЕ СУЩЕСТВУЮТ** и поэтому система не получает сигналы!

## 🔍 Как получить реальные channel_id

### Способ 1: Через @userinfobot

1. Добавьте бота **@userinfobot** в нужный канал
2. Отправьте любое сообщение в канал  
3. Бот ответит с информацией, включая **Chat ID**
4. Используйте этот ID в конфигурации

### Способ 2: Через Telegram API

```python
from telethon import TelegramClient

# Ваши API ключи
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'

client = TelegramClient('session', api_id, api_hash)

async def get_channel_ids():
    await client.start()
    
    # Получить все диалоги
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            print(f"Channel: {dialog.name}")
            print(f"ID: {dialog.id}")
            print(f"Username: @{dialog.entity.username}")
            print("---")

# Запустить
import asyncio
asyncio.run(get_channel_ids())
```

### Способ 3: Через веб-версию Telegram

1. Откройте **web.telegram.org**
2. Перейдите в нужный канал
3. В URL будете видеть ID: `https://web.telegram.org/z/#-1001234567890`
4. Число после `#` - это channel_id

## 📝 Обновление конфигурации

После получения реальных ID, обновите `config/sources.json`:

```json
{
  "source_id": "whales_guide_main",
  "connection_params": {
    "channel_id": "-1001234567890",  // ← Замените на реальный ID
    "username": "@whalesguide"
  }
}
```

## 🔑 Настройка Telegram API ключей

Убедитесь что в переменных окружения есть:

```env
TELEGRAM_API_ID=your_real_api_id
TELEGRAM_API_HASH=your_real_api_hash
TELEGRAM_PHONE=your_phone_number
```

### Получение API ключей:

1. Перейдите на **https://my.telegram.org**
2. Войдите с номером телефона
3. Создайте приложение в "API development tools"
4. Скопируйте `api_id` и `api_hash`

## ✅ Проверка работы

После настройки реальных каналов:

1. Система будет получать реальные сообщения
2. В Supabase появятся записи в таблицах:
   - `signals_raw` - сырые сообщения
   - `signals_parsed` - обработанные сигналы
3. В логах будут сообщения типа:
   ```
   📨 Signal detected from Whales Crypto Guide
   ✅ Signal processed: BTCUSDT long
   ```

## 🚨 Важные моменты

1. **Приватные каналы**: Ваш аккаунт должен быть подписан на канал
2. **Публичные каналы**: Можно использовать без подписки
3. **Права доступа**: API ключи должны иметь права на чтение сообщений
4. **Лимиты**: Telegram API имеет лимиты на количество запросов

## 🛠️ Отладка

Если сигналы не поступают:

1. Проверьте логи на наличие ошибок авторизации
2. Убедитесь что channel_id правильные (начинаются с `-100`)
3. Проверьте что аккаунт подписан на приватные каналы
4. Убедитесь что фильтры ключевых слов не слишком строгие

---

**После настройки реальных каналов система будет работать на 100%!**
