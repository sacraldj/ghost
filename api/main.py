"""
GHOST API для Render.com
FastAPI сервер для обработки webhook'ов и API запросов
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import json
import os
import sys
from datetime import datetime
import asyncio

# Добавляем путь к core модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импорты
try:
    from core.safe_news_integrator import get_safe_news_integrator
    from core.news_statistics_tracker import get_news_stats_tracker
except ImportError:
    print("⚠️ Core modules not available, using mock implementations")
    get_safe_news_integrator = None
    get_news_stats_tracker = None

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем FastAPI app
app = FastAPI(
    title="GHOST API",
    description="API for Telegram → Render → Supabase → Vercel pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class TelegramSignal(BaseModel):
    type: str
    timestamp: str
    data: Dict[str, Any]

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

# Глобальные переменные
app_stats = {
    'start_time': datetime.now(),
    'requests_count': 0,
    'signals_processed': 0,
    'errors_count': 0
}

# Middleware для подсчета запросов
@app.middleware("http")
async def count_requests(request: Request, call_next):
    app_stats['requests_count'] += 1
    response = await call_next(request)
    return response

# Главная страница
@app.get("/")
async def root():
    return {
        "message": "GHOST API is running!",
        "docs": "/docs",
        "health": "/health",
        "stats": "/stats"
    }

# Health check для Render
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint для Render.com"""
    
    # Проверяем доступность сервисов
    services = {
        "api": "healthy",
        "supabase": "unknown",
        "news_integration": "unknown"
    }
    
    # Проверяем Supabase
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url:
            services["supabase"] = "configured"
        else:
            services["supabase"] = "not_configured"
    except Exception:
        services["supabase"] = "error"
    
    # Проверяем новостную интеграцию
    try:
        if get_safe_news_integrator:
            integrator = get_safe_news_integrator()
            services["news_integration"] = "available"
        else:
            services["news_integration"] = "not_available"
    except Exception:
        services["news_integration"] = "error"
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        services=services
    )

# Статистика API
@app.get("/stats")
async def get_stats():
    """Получение статистики работы API"""
    uptime = datetime.now() - app_stats['start_time']
    
    return {
        "uptime_seconds": int(uptime.total_seconds()),
        "requests_total": app_stats['requests_count'],
        "signals_processed": app_stats['signals_processed'],
        "errors_count": app_stats['errors_count'],
        "start_time": app_stats['start_time'].isoformat(),
        "current_time": datetime.now().isoformat()
    }

# Webhook для получения сигналов от Telegram Bridge
@app.post("/webhooks/telegram")
async def telegram_webhook(signal: TelegramSignal, background_tasks: BackgroundTasks):
    """
    Webhook для получения сигналов от Telegram Bridge
    """
    try:
        logger.info(f"📨 Received telegram signal: {signal.type}")
        
        # Обрабатываем в фоне
        background_tasks.add_task(process_telegram_signal, signal)
        
        app_stats['signals_processed'] += 1
        
        return {"status": "received", "message": "Signal queued for processing"}
        
    except Exception as e:
        app_stats['errors_count'] += 1
        logger.error(f"Error processing telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_telegram_signal(signal: TelegramSignal):
    """Фоновая обработка telegram сигнала"""
    try:
        logger.info(f"🔄 Processing signal from {signal.data.get('trader_id', 'unknown')}")
        
        # Здесь можно добавить дополнительную обработку:
        # - Обогащение новостями
        # - Анализ настроений
        # - Сохранение в дополнительные системы
        # - Отправка уведомлений
        
        # Пример обогащения новостями
        if get_safe_news_integrator and signal.data.get('symbol'):
            try:
                integrator = get_safe_news_integrator()
                # Можно добавить логику обогащения
                logger.debug(f"News integration available for {signal.data['symbol']}")
            except Exception as e:
                logger.warning(f"News integration error: {e}")
        
        logger.info(f"✅ Signal processed successfully")
        
    except Exception as e:
        logger.error(f"Error in background signal processing: {e}")

# API для получения новостной аналитики
@app.get("/api/news-analysis")
async def news_analysis(action: str = "overview"):
    """
    API для получения новостной аналитики
    Совместимо с существующим фронтендом
    """
    try:
        if not get_safe_news_integrator:
            return {
                "status": "news_integration_disabled",
                "message": "News integration is not available",
                "data": {}
            }
        
        integrator = get_safe_news_integrator()
        stats_tracker = get_news_stats_tracker() if get_news_stats_tracker else None
        
        if action == "overview":
            return {
                "status": "success",
                "data": {
                    "total_signals_analyzed": 0,
                    "news_enhanced_signals": 0,
                    "accuracy_improvement": 0,
                    "last_update": datetime.now().isoformat()
                }
            }
        
        elif action == "statistics":
            if stats_tracker:
                stats = stats_tracker.get_current_stats()
                return {"status": "success", "data": stats}
            else:
                return {"status": "error", "message": "Statistics tracker not available"}
        
        elif action == "recent":
            return {
                "status": "success", 
                "data": {
                    "recent_news": [],
                    "count": 0
                }
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action parameter")
            
    except Exception as e:
        logger.error(f"Error in news analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API для тестирования парсеров
@app.post("/api/test-parser")
async def test_parser(data: Dict[str, Any]):
    """
    API для тестирования парсеров
    """
    try:
        parser_type = data.get('parser_type', 'cryptoattack24')
        test_message = data.get('message', '')
        
        if not test_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Динамический импорт парсера
        if parser_type == 'cryptoattack24':
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'telegram_parsers'))
                from cryptoattack24_parser import CryptoAttack24Parser
                
                parser = CryptoAttack24Parser()
                result = parser.parse_message(test_message)
                
                if result:
                    return {
                        "status": "success",
                        "parsed": True,
                        "result": {
                            "symbol": result.symbol,
                            "action": result.action,
                            "confidence": result.confidence,
                            "price_movement": result.price_movement,
                            "exchange": result.exchange,
                            "sector": result.sector
                        }
                    }
                else:
                    return {
                        "status": "success",
                        "parsed": False,
                        "message": "Message not recognized or filtered as noise"
                    }
                    
            except ImportError as e:
                return {
                    "status": "error",
                    "message": f"Parser not available: {e}"
                }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported parser type")
            
    except Exception as e:
        logger.error(f"Error testing parser: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint для конфигурации
@app.get("/api/config")
async def get_config():
    """Получение текущей конфигурации"""
    return {
        "telegram_integration": bool(os.getenv('TELEGRAM_API_ID')),
        "supabase_integration": bool(os.getenv('SUPABASE_URL')),
        "news_integration": bool(get_safe_news_integrator),
        "render_deployment": True,
        "version": "1.0.0"
    }

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    app_stats['errors_count'] += 1
    logger.error(f"Global error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
