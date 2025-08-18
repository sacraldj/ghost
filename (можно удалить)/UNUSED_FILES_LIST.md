# 🗑️ НЕИСПОЛЬЗУЕМЫЕ ФАЙЛЫ ПОСЛЕ УПРОЩЕНИЯ АРХИТЕКТУРЫ

## ❌ МОЖНО УДАЛИТЬ:

### Старые оркестраторы:
- `scripts/start_live_system.py` - заменён встроенным в SignalOrchestratorWithSupabase
- `core/live_signal_processor.py` - функционал перенесён в основной оркестратор
- `core/ghost_orchestrator.py` - старый orchestrator через subprocess

### Дублирующие компоненты:
- `core/candle_websocket.py` - не нужен для базовой работы
- `core/signal_analyzer.py` - избыточный анализ
- `engine/signal_outcome_resolver.py` - дополнительная логика

### Старые конфиги:
- `config/system_config.yaml` - использовался GhostOrchestrator
- `config/signal_processor_config.yaml` - старые настройки

### Неиспользуемые парсеры:
- `signals/unified_signal_system.py` - дублирует функционал
- `signals/signal_orchestrator.py` - старая версия без Supabase

### News Engine (если не нужен):
- `news_engine/enhanced_news_engine.py`
- `news_engine/price_feed_engine.py` 
- `news_engine/supabase_sync.py`
- `news_engine/telegram_listener.py`

### Скрипты setup:
- `start_orchestrator.sh`
- `setup_env_telegram.py`
- `setup_telegram_auto.py`

### Docker файлы (если не используем):
- `Dockerfile.news`
- `Dockerfile.signals` 
- `Dockerfile.telegram`

### Тестовые файлы:
- `test_*.py` - различные тестовые скрипты
- `scripts/test_*.py`

## ✅ ОСТАВЛЯЕМ:

### Основная система:
- `start_all.py` ✅
- `signals/signal_orchestrator_with_supabase.py` ✅
- `core/telegram_listener.py` ✅

### Парсеры:
- `signals/parsers/whales_crypto_parser.py` ✅
- `signals/parsers/parser_2trade.py` ✅
- `signals/parsers/crypto_hub_parser.py` ✅
- `signals/parsers/cryptoattack24_parser.py` ✅
- `signals/parsers/signal_parser_base.py` ✅

### Frontend:
- `app/` - вся Next.js система ✅
- `package.json`, `next.config.js` ✅

### Конфигурация:
- `requirements.txt` ✅
- `render.yaml` ✅
- `vercel.json` ✅
