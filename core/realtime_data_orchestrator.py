#!/usr/bin/env python3
"""
🚀 GHOST Real-Time Data Orchestrator
Система реального времени для обновления ВСЕХ данных каждую минуту
"""

import asyncio
import logging
import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

try:
    from supabase import create_client, Client
    import aiohttp
    import requests
except ImportError as e:
    print(f"❌ Отсутствуют зависимости: {e}")
    print("Установите: pip install supabase aiohttp requests")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/realtime_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RealtimeOrchestrator')

class RealtimeDataOrchestrator:
    """Оркестратор данных реального времени"""
    
    def __init__(self):
        # Supabase
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # API ключи
        self.binance_api = "https://fapi.binance.com/fapi/v1"
        self.coinapi_key = os.getenv('COINAPI_KEY', '')
        self.news_api_key = os.getenv('NEWS_API_KEY', '')
        
        # Список популярных символов для мониторинга
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'ORDIUSDT', 'SOLUSDT', 'ADAUSDT',
            'DOGEUSDT', 'BNBUSDT', 'XRPUSDT', 'AVAXUSDT', 'LINKUSDT'
        ]
        
        # Статистика
        self.stats = {
            'updates_total': 0,
            'market_updates': 0,
            'news_updates': 0,
            'signals_processed': 0,
            'errors': 0,
            'last_update': None
        }
        
        # Кэш данных
        self.cache = {
            'market_data': {},
            'news_data': [],
            'signals_data': []
        }
    
    async def start_realtime_updates(self):
        """Запуск системы обновлений в реальном времени"""
        logger.info("🚀 Запуск системы обновлений реального времени")
        
        # Создаем папку для логов
        os.makedirs('../logs', exist_ok=True)
        
        # Запускаем параллельные задачи
        tasks = [
            asyncio.create_task(self._market_data_loop()),
            asyncio.create_task(self._news_data_loop()),
            asyncio.create_task(self._signals_processing_loop()),
            asyncio.create_task(self._analytics_loop()),
            asyncio.create_task(self._stats_logger_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 Остановка системы по запросу пользователя")
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
    
    async def _market_data_loop(self):
        """Цикл обновления рыночных данных каждые 30 секунд"""
        logger.info("📊 Запуск цикла рыночных данных")
        
        while True:
            try:
                start_time = time.time()
                
                # Получаем данные для всех символов параллельно
                tasks = [self._update_market_data(symbol) for symbol in self.symbols]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Подсчитываем успешные обновления
                successful = sum(1 for r in results if not isinstance(r, Exception))
                self.stats['market_updates'] += successful
                
                execution_time = time.time() - start_time
                logger.info(f"📈 Обновлено {successful}/{len(self.symbols)} символов за {execution_time:.2f}с")
                
                # Ждем 30 секунд до следующего обновления
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле рыночных данных: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(30)
    
    async def _update_market_data(self, symbol: str) -> bool:
        """Обновление рыночных данных для одного символа"""
        try:
            async with aiohttp.ClientSession() as session:
                # Получаем данные с Binance
                ticker_url = f"{self.binance_api}/ticker/24hr?symbol={symbol}"
                klines_url = f"{self.binance_api}/klines?symbol={symbol}&interval=1m&limit=100"
                
                # Параллельные запросы
                ticker_task = session.get(ticker_url)
                klines_task = session.get(klines_url)
                
                ticker_resp, klines_resp = await asyncio.gather(ticker_task, klines_task)
                
                if ticker_resp.status == 200 and klines_resp.status == 200:
                    ticker_data = await ticker_resp.json()
                    klines_data = await klines_resp.json()
                    
                    # Рассчитываем технические индикаторы
                    market_snapshot = await self._calculate_technical_indicators(symbol, ticker_data, klines_data)
                    
                    # Сохраняем в Supabase
                    result = self.supabase.table('market_snapshots').insert([market_snapshot]).execute()
                    
                    if result.data:
                        self.cache['market_data'][symbol] = market_snapshot
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления {symbol}: {e}")
            return False
    
    async def _calculate_technical_indicators(self, symbol: str, ticker_data: dict, klines_data: list) -> dict:
        """Расчет технических индикаторов"""
        try:
            # Извлекаем цены закрытия
            closes = [float(kline[4]) for kline in klines_data]
            volumes = [float(kline[5]) for kline in klines_data]
            
            current_price = float(ticker_data['lastPrice'])
            volume_24h = float(ticker_data['volume'])
            price_change_24h = float(ticker_data['priceChangePercent'])
            
            # Простые технические индикаторы
            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else current_price
            
            # RSI упрощенный
            rsi_14 = await self._calculate_rsi(closes, 14)
            
            # Волатильность
            volatility_24h = abs(price_change_24h) / 100
            
            return {
                'symbol': symbol,
                'snapshot_timestamp': datetime.now(timezone.utc).isoformat(),
                'current_price': current_price,
                'open_price': float(ticker_data['openPrice']),
                'high_price': float(ticker_data['highPrice']),
                'low_price': float(ticker_data['lowPrice']),
                'close_price': current_price,
                'volume_24h': volume_24h,
                'volatility_24h': volatility_24h,
                'rsi_14': rsi_14,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'price_change_24h': price_change_24h
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета индикаторов для {symbol}: {e}")
            return {
                'symbol': symbol,
                'snapshot_timestamp': datetime.now(timezone.utc).isoformat(),
                'current_price': float(ticker_data.get('lastPrice', 0))
            }
    
    async def _calculate_rsi(self, prices: list, period: int = 14) -> float:
        """Расчет RSI"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except:
            return 50.0
    
    async def _news_data_loop(self):
        """Цикл обновления новостей каждые 2 минуты"""
        logger.info("📰 Запуск цикла новостей")
        
        while True:
            try:
                start_time = time.time()
                
                # Собираем новости из разных источников
                news_sources = [
                    self._fetch_crypto_news(),
                    self._fetch_market_alerts(),
                    self._generate_price_alerts()
                ]
                
                results = await asyncio.gather(*news_sources, return_exceptions=True)
                
                total_news = 0
                for result in results:
                    if isinstance(result, list):
                        total_news += len(result)
                
                self.stats['news_updates'] += total_news
                
                execution_time = time.time() - start_time
                logger.info(f"📰 Обработано {total_news} новостей за {execution_time:.2f}с")
                
                # Ждем 2 минуты
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле новостей: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(120)
    
    async def _fetch_crypto_news(self) -> list:
        """Получение криптовалютных новостей"""
        try:
            # Используем бесплатные источники новостей
            news_items = []
            
            # Генерируем новости на основе рыночных данных
            for symbol in self.symbols[:5]:  # Топ 5 символов
                if symbol in self.cache['market_data']:
                    market_data = self.cache['market_data'][symbol]
                    price_change = market_data.get('price_change_24h', 0)
                    
                    if abs(price_change) > 5:  # Значительное изменение цены
                        emoji = "📈" if price_change > 0 else "📉"
                        direction = "растет" if price_change > 0 else "падает"
                        
                        news_item = {
                            'title': f'{emoji} {symbol.replace("USDT", "")} {direction} на {abs(price_change):.2f}%',
                            'content': f'Цена {symbol} показывает значительное движение: {price_change:+.2f}% за 24 часа. Текущая цена: ${market_data.get("current_price", 0)}',
                            'source_name': 'GHOST Price Monitor',
                            'url': f'https://binance.com/en/futures/{symbol}',
                            'published_at': datetime.now(timezone.utc).isoformat(),
                            'category': 'price_alert',
                            'impact_score': min(abs(price_change) / 10, 1.0),
                            'is_critical': abs(price_change) > 10
                        }
                        
                        news_items.append(news_item)
            
            # Сохраняем в Supabase
            if news_items:
                result = self.supabase.table('critical_news').insert(news_items).execute()
                if result.data:
                    logger.info(f"📰 Сохранено {len(news_items)} новостей")
            
            return news_items
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения новостей: {e}")
            return []
    
    async def _fetch_market_alerts(self) -> list:
        """Создание рыночных алертов"""
        try:
            alerts = []
            
            # Проверяем экстремальные RSI
            for symbol, data in self.cache['market_data'].items():
                rsi = data.get('rsi_14', 50)
                
                if rsi > 80:
                    alerts.append({
                        'title': f'⚠️ {symbol}: Зона перекупленности (RSI: {rsi})',
                        'content': f'{symbol} находится в зоне перекупленности. RSI: {rsi}. Возможна коррекция.',
                        'source_name': 'GHOST Technical Analysis',
                        'category': 'technical_alert',
                        'published_at': datetime.now(timezone.utc).isoformat(),
                        'impact_score': 0.7,
                        'is_critical': False
                    })
                elif rsi < 20:
                    alerts.append({
                        'title': f'⚠️ {symbol}: Зона перепроданности (RSI: {rsi})',
                        'content': f'{symbol} находится в зоне перепроданности. RSI: {rsi}. Возможен отскок.',
                        'source_name': 'GHOST Technical Analysis',
                        'category': 'technical_alert',
                        'published_at': datetime.now(timezone.utc).isoformat(),
                        'impact_score': 0.7,
                        'is_critical': False
                    })
            
            if alerts:
                result = self.supabase.table('critical_news').insert(alerts).execute()
                if result.data:
                    logger.info(f"⚠️ Создано {len(alerts)} технических алертов")
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания алертов: {e}")
            return []
    
    async def _generate_price_alerts(self) -> list:
        """Генерация алертов о критических движениях цен"""
        try:
            alerts = []
            
            # Проверяем волатильность
            for symbol, data in self.cache['market_data'].items():
                volatility = data.get('volatility_24h', 0)
                
                if volatility > 0.15:  # Волатильность > 15%
                    alerts.append({
                        'title': f'🌪️ Высокая волатильность {symbol}: {volatility*100:.1f}%',
                        'content': f'{symbol} показывает высокую волатильность {volatility*100:.1f}% за 24 часа. Будьте осторожны с позициями.',
                        'source_name': 'GHOST Volatility Monitor',
                        'category': 'volatility_alert',
                        'published_at': datetime.now(timezone.utc).isoformat(),
                        'impact_score': min(volatility * 2, 1.0),
                        'is_critical': volatility > 0.25
                    })
            
            if alerts:
                result = self.supabase.table('critical_news').insert(alerts).execute()
                if result.data:
                    logger.info(f"🌪️ Создано {len(alerts)} алертов волатильности")
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации алертов: {e}")
            return []
    
    async def _signals_processing_loop(self):
        """Цикл обработки сигналов каждую минуту"""
        logger.info("📡 Запуск цикла обработки сигналов")
        
        while True:
            try:
                # Проверяем новые сигналы
                recent_signals = self.supabase.table('signals_parsed').select('*').gte('posted_at', 
                    datetime.now(timezone.utc).replace(minute=datetime.now().minute-5).isoformat()
                ).execute()
                
                if recent_signals.data:
                    logger.info(f"📡 Найдено {len(recent_signals.data)} новых сигналов")
                    self.stats['signals_processed'] += len(recent_signals.data)
                    
                    # Создаем снимки рынка для каждого сигнала
                    for signal in recent_signals.data:
                        symbol = signal.get('symbol')
                        if symbol and symbol in self.cache['market_data']:
                            market_data = self.cache['market_data'][symbol].copy()
                            market_data['signal_id'] = signal.get('signal_id')
                            
                            # Сохраняем снимок
                            self.supabase.table('market_snapshots').insert([market_data]).execute()
                
                await asyncio.sleep(60)  # Каждую минуту
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле сигналов: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(60)
    
    async def _analytics_loop(self):
        """Цикл обновления аналитики каждые 5 минут"""
        logger.info("📊 Запуск цикла аналитики")
        
        while True:
            try:
                # Обновляем аналитику производительности источников
                sources = self.supabase.table('signal_sources').select('*').execute()
                
                for source in sources.data:
                    source_id = source.get('source_id')
                    if source_id:
                        await self._update_source_performance(source_id)
                
                logger.info("📊 Аналитика производительности обновлена")
                
                await asyncio.sleep(300)  # Каждые 5 минут
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле аналитики: {e}")
                await asyncio.sleep(300)
    
    async def _update_source_performance(self, source_id: str):
        """Обновление производительности источника"""
        try:
            # Получаем сделки за последние 24 часа
            trades = self.supabase.table('trades').select('*').eq('trader_id', source_id).gte(
                'created_at', datetime.now(timezone.utc).replace(hour=datetime.now().hour-24).isoformat()
            ).execute()
            
            if trades.data:
                total_trades = len(trades.data)
                winning_trades = len([t for t in trades.data if t.get('pnl', 0) > 0])
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Сохраняем аналитику
                performance_data = {
                    'entity_type': 'SIGNAL_SOURCE',
                    'entity_id': source_id,
                    'analysis_period_start': datetime.now(timezone.utc).replace(hour=datetime.now().hour-24).isoformat(),
                    'analysis_period_end': datetime.now(timezone.utc).isoformat(),
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'win_rate': win_rate
                }
                
                self.supabase.table('performance_analytics').insert([performance_data]).execute()
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления производительности {source_id}: {e}")
    
    async def _stats_logger_loop(self):
        """Цикл логирования статистики каждые 30 секунд"""
        while True:
            try:
                self.stats['last_update'] = datetime.now(timezone.utc).isoformat()
                self.stats['updates_total'] = self.stats['market_updates'] + self.stats['news_updates']
                
                logger.info(f"📊 СТАТИСТИКА: Обновлений: {self.stats['updates_total']}, "
                           f"Рынок: {self.stats['market_updates']}, "
                           f"Новости: {self.stats['news_updates']}, "
                           f"Сигналы: {self.stats['signals_processed']}, "
                           f"Ошибки: {self.stats['errors']}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Ошибка логирования статистики: {e}")
                await asyncio.sleep(30)

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск GHOST Real-Time Data Orchestrator")
    
    orchestrator = RealtimeDataOrchestrator()
    await orchestrator.start_realtime_updates()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
