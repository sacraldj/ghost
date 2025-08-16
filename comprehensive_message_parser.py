#!/usr/bin/env python3
"""
УНИВЕРСАЛЬНЫЙ ПАРСЕР СООБЩЕНИЙ ИЗ TELEGRAM КАНАЛОВ
Собирает ВСЕ типы сообщений, использует AI для анализа
"""

import asyncio
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

try:
    from telethon import TelegramClient
    from supabase import create_client, Client
    import openai
    import google.generativeai as genai
except ImportError as e:
    print(f"❌ Отсутствуют модули: {e}")
    print("Установите: pip install telethon supabase openai google-generativeai")
    exit(1)

@dataclass
class ParsedMessage:
    """Структура распарсенного сообщения"""
    message_id: str
    trader_id: str
    raw_text: str
    timestamp: datetime
    message_type: str  # 'trading_signal', 'news', 'whale_alert', 'analysis', 'other'
    
    # Торговые данные
    symbol: Optional[str] = None
    side: Optional[str] = None  # BUY/SELL/HOLD
    entry_price: Optional[float] = None
    targets: List[float] = None
    stop_loss: Optional[float] = None
    leverage: Optional[int] = None
    
    # Новостные данные
    news_category: Optional[str] = None  # 'regulation', 'whale_movement', 'partnership', etc.
    mentioned_tokens: List[str] = None
    sentiment: Optional[str] = None  # 'positive', 'negative', 'neutral'
    
    # Whale данные
    whale_action: Optional[str] = None  # 'buy', 'sell', 'transfer'
    whale_amount: Optional[float] = None
    whale_token: Optional[str] = None
    
    # AI анализ
    ai_confidence: Optional[float] = None
    ai_summary: Optional[str] = None
    
    # Метаданные
    confidence: float = 0.5
    is_valid: bool = False
    parsing_method: str = "rule_based"
    
    def __post_init__(self):
        if self.targets is None:
            self.targets = []
        if self.mentioned_tokens is None:
            self.mentioned_tokens = []

class ComprehensiveMessageParser:
    """Комплексный парсер сообщений"""
    
    def __init__(self):
        # API ключи
        self.telegram_api_id = os.getenv('TELEGRAM_API_ID')
        self.telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
        self.telegram_phone = os.getenv('TELEGRAM_PHONE')
        
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        
        # Клиенты
        self.telegram_client = None
        self.supabase_client = None
        
        # AI настройки
        if self.openai_key:
            openai.api_key = self.openai_key
            print("✅ OpenAI подключен")
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Gemini подключен")
        
        # Каналы для парсинга
        self.channels = {
            '-1001263635145': {
                'name': 'КриптоАтака 24',
                'trader_id': 'cryptoattack24',
                'type': 'news_analytics'
            },
            '-1001288385100': {
                'name': 'Whales Crypto Guide', 
                'trader_id': 'whales_guide_main',
                'type': 'trading_signals'
            }
        }
        
        # Статистика
        self.stats = {
            'total_messages': 0,
            'by_type': {
                'trading_signal': 0,
                'news': 0,
                'whale_alert': 0,
                'analysis': 0,
                'other': 0
            },
            'saved_to_db': 0,
            'errors': 0
        }
        
        # Регулярные выражения для парсинга
        self.patterns = {
            'crypto_symbols': r'\b([A-Z]{2,10}(?:USDT?|BTC|ETH)?)\b',
            'prices': r'\$?(\d+(?:,\d{3})*(?:\.\d{1,8})?)',
            'percentages': r'([+-]?\d+(?:\.\d+)?%)',
            'whale_amounts': r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(млн|тыс|K|M|B)',
            'trading_terms': r'\b(long|short|buy|sell|entry|target|tp\d*|sl|stop|leverage)\b',
            'news_keywords': r'\b(SEC|обвиняет|подала в суд|купили|продали|транзакции|китов)\b'
        }
    
    async def initialize(self):
        """Инициализация всех компонентов"""
        print("🔧 Инициализация парсера...")
        
        # Telegram
        self.telegram_client = TelegramClient('ghost_session', self.telegram_api_id, self.telegram_api_hash)
        await self.telegram_client.start(phone=self.telegram_phone)
        
        if not await self.telegram_client.is_user_authorized():
            print("❌ Не авторизован в Telegram")
            return False
        
        # Supabase
        self.supabase_client = create_client(self.supabase_url, self.supabase_key)
        
        print("✅ Все компоненты инициализированы")
        return True
    
    async def parse_channel_history(self, channel_id: str, limit: int = 200):
        """Парсинг истории канала"""
        channel_info = self.channels.get(channel_id)
        if not channel_info:
            print(f"❌ Канал {channel_id} не найден")
            return
        
        print(f"\n📡 Парсинг канала: {channel_info['name']}")
        print(f"   Тип: {channel_info['type']}")
        print(f"   Лимит сообщений: {limit}")
        
        try:
            entity = await self.telegram_client.get_entity(int(channel_id))
            print(f"   ✅ Подключен к: {entity.title}")
            
            messages_processed = 0
            messages_parsed = 0
            
            # Получаем сообщения
            async for message in self.telegram_client.iter_messages(entity, limit=limit):
                if not message.text:
                    continue
                
                messages_processed += 1
                self.stats['total_messages'] += 1
                
                # Парсим сообщение
                parsed = await self.parse_message(message, channel_info)
                
                if parsed:
                    messages_parsed += 1
                    
                    # Сохраняем в базу
                    await self.save_to_database(parsed)
                    
                    # Обновляем статистику
                    self.stats['by_type'][parsed.message_type] += 1
                    self.stats['saved_to_db'] += 1
                
                # Прогресс
                if messages_processed % 50 == 0:
                    print(f"   📊 Обработано: {messages_processed}, распарсено: {messages_parsed}")
            
            print(f"   ✅ Завершено: {messages_processed} обработано, {messages_parsed} распарсено")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            self.stats['errors'] += 1
    
    async def parse_message(self, message, channel_info) -> Optional[ParsedMessage]:
        """Парсинг одного сообщения"""
        try:
            text = message.text
            
            # Определяем тип сообщения сначала
            message_type = self.classify_message_type(text)
            
            # Базовая структура
            parsed = ParsedMessage(
                message_id=f"{channel_info['trader_id']}_{message.id}",
                trader_id=channel_info['trader_id'],
                raw_text=text,
                timestamp=message.date,
                message_type=message_type,
                confidence=0.5,
                is_valid=False,
                parsing_method="rule_based"
            )
            
            # Парсим в зависимости от типа
            if parsed.message_type == 'trading_signal':
                await self.parse_trading_signal(parsed, text)
            elif parsed.message_type == 'news':
                await self.parse_news_message(parsed, text)
            elif parsed.message_type == 'whale_alert':
                await self.parse_whale_alert(parsed, text)
            elif parsed.message_type == 'analysis':
                await self.parse_analysis_message(parsed, text)
            
            # AI анализ
            await self.ai_enhance_parsing(parsed)
            
            return parsed
            
        except Exception as e:
            print(f"   ❌ Ошибка парсинга сообщения: {e}")
            return None
    
    def classify_message_type(self, text: str) -> str:
        """Классификация типа сообщения"""
        text_lower = text.lower()
        
        # Торговые сигналы
        trading_keywords = ['long', 'short', 'buy', 'sell', 'entry', 'target', 'tp1', 'tp2', 'sl', 'leverage']
        if any(keyword in text_lower for keyword in trading_keywords):
            return 'trading_signal'
        
        # Whale alerts
        whale_keywords = ['потратили', 'купили', 'продали', 'транзакции', 'китов', 'млн', 'активы']
        if any(keyword in text_lower for keyword in whale_keywords):
            return 'whale_alert'
        
        # Новости
        news_keywords = ['sec', 'обвиняет', 'подала в суд', 'компании', 'регулятор']
        if any(keyword in text_lower for keyword in news_keywords):
            return 'news'
        
        # Анализ
        analysis_keywords = ['анализ', 'прогноз', 'тренд', 'поддержка', 'сопротивление']
        if any(keyword in text_lower for keyword in analysis_keywords):
            return 'analysis'
        
        return 'other'
    
    async def parse_trading_signal(self, parsed: ParsedMessage, text: str):
        """Парсинг торгового сигнала"""
        # Символ
        symbols = re.findall(self.patterns['crypto_symbols'], text.upper())
        if symbols:
            parsed.symbol = symbols[0]
        
        # Направление
        if any(word in text.lower() for word in ['long', 'buy', 'покупка']):
            parsed.side = 'BUY'
        elif any(word in text.lower() for word in ['short', 'sell', 'продажа']):
            parsed.side = 'SELL'
        
        # Цены
        prices = re.findall(self.patterns['prices'], text)
        if prices:
            try:
                parsed.entry_price = float(prices[0].replace(',', ''))
                if len(prices) > 1:
                    parsed.targets = [float(p.replace(',', '')) for p in prices[1:]]
            except:
                pass
    
    async def parse_news_message(self, parsed: ParsedMessage, text: str):
        """Парсинг новостного сообщения"""
        # Упомянутые токены
        tokens = re.findall(self.patterns['crypto_symbols'], text.upper())
        parsed.mentioned_tokens = list(set(tokens))
        
        # Категория новости
        if 'sec' in text.lower() or 'регулятор' in text.lower():
            parsed.news_category = 'regulation'
        elif 'суд' in text.lower():
            parsed.news_category = 'legal'
        elif 'партнерство' in text.lower():
            parsed.news_category = 'partnership'
        else:
            parsed.news_category = 'general'
    
    async def parse_whale_alert(self, parsed: ParsedMessage, text: str):
        """Парсинг whale alert"""
        # Действие
        if any(word in text.lower() for word in ['купили', 'покупку']):
            parsed.whale_action = 'buy'
        elif any(word in text.lower() for word in ['продали', 'вывели']):
            parsed.whale_action = 'sell'
        else:
            parsed.whale_action = 'transfer'
        
        # Сумма
        amounts = re.findall(self.patterns['whale_amounts'], text)
        if amounts:
            try:
                amount, unit = amounts[0]
                multiplier = {'тыс': 1000, 'млн': 1000000, 'K': 1000, 'M': 1000000, 'B': 1000000000}
                parsed.whale_amount = float(amount.replace(',', '')) * multiplier.get(unit, 1)
            except:
                pass
        
        # Токен
        tokens = re.findall(r'#([A-Z]+)', text)
        if tokens:
            parsed.whale_token = tokens[0]
    
    async def parse_analysis_message(self, parsed: ParsedMessage, text: str):
        """Парсинг аналитического сообщения"""
        # Упомянутые токены
        tokens = re.findall(self.patterns['crypto_symbols'], text.upper())
        parsed.mentioned_tokens = list(set(tokens))
        
        # Настроение
        positive_words = ['рост', 'поднимается', 'бычий', 'покупка']
        negative_words = ['падение', 'снижение', 'медвежий', 'продажа']
        
        if any(word in text.lower() for word in positive_words):
            parsed.sentiment = 'positive'
        elif any(word in text.lower() for word in negative_words):
            parsed.sentiment = 'negative'
        else:
            parsed.sentiment = 'neutral'
    
    async def ai_enhance_parsing(self, parsed: ParsedMessage):
        """AI улучшение парсинга через OpenAI"""
        try:
            if self.openai_key:
                prompt = f"""
                Проанализируй это сообщение из криптовалютного канала:
                
                "{parsed.raw_text}"
                
                Определи:
                1. Тип сообщения (торговый сигнал, новости, whale alert, анализ)
                2. Упомянутые криптовалюты
                3. Настроение (позитивное/негативное/нейтральное)
                4. Краткое резюме (1-2 предложения)
                5. Уверенность в анализе (0-100%)
                
                Ответь в JSON формате:
                {{"type": "...", "cryptocurrencies": [...], "sentiment": "...", "summary": "...", "confidence": 85}}
                """
                
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты эксперт по анализу криптовалютных сообщений. Отвечай только в JSON формате."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                
                try:
                    ai_result = json.loads(response.choices[0].message.content)
                    parsed.ai_confidence = ai_result.get('confidence', 50) / 100
                    parsed.ai_summary = ai_result.get('summary', '')
                    
                    # Обновляем данные на основе AI
                    if ai_result.get('cryptocurrencies'):
                        parsed.mentioned_tokens = ai_result['cryptocurrencies']
                    if ai_result.get('sentiment'):
                        parsed.sentiment = ai_result['sentiment']
                        
                except Exception as parse_error:
                    print(f"   ⚠️ Ошибка парсинга AI ответа: {parse_error}")
                    parsed.ai_confidence = 0.5
                    parsed.ai_summary = 'AI анализ частично недоступен'
                    
        except Exception as e:
            print(f"   ⚠️ AI анализ недоступен: {e}")
            parsed.ai_confidence = 0.5
    
    async def save_to_database(self, parsed: ParsedMessage):
        """Сохранение в базу данных с фильтрацией актуальных сигналов"""
        try:
            # Фильтр актуальности - только торговые сигналы с символом
            is_actual_signal = (
                parsed.message_type == 'trading_signal' and 
                parsed.symbol and 
                parsed.is_valid and
                (parsed.entry_price or parsed.targets)
            )
            
            # Сырое сообщение - сохраняем всё для истории
            raw_data = {
                'trader_id': parsed.trader_id,
                'source_msg_id': parsed.message_id,
                'text': parsed.raw_text,
                'posted_at': parsed.timestamp.isoformat(),
                'meta': {
                    'source_type': 'telegram',
                    'message_type': parsed.message_type,
                    'is_actual_signal': is_actual_signal,
                    'parsing_method': parsed.parsing_method
                },
                'processed': is_actual_signal
            }
            
            raw_result = self.supabase_client.table('signals_raw').upsert(raw_data).execute()
            print(f"   ✅ Сырой сигнал сохранен: {parsed.trader_id}")
            
            # Обработанное сообщение - только актуальные торговые сигналы
            if is_actual_signal:
                # Получаем raw_id из результата
                raw_id = raw_result.data[0]['raw_id'] if raw_result.data else None
                
                processed_data = {
                    'signal_id': f"{parsed.trader_id}_{parsed.message_id}",
                    'trader_id': parsed.trader_id,
                    'raw_id': raw_id,
                    'posted_at': parsed.timestamp.isoformat(),
                    'symbol': parsed.symbol,
                    'side': parsed.side,
                    'entry_type': 'market',
                    'entry': parsed.entry_price,
                    'range_low': None,
                    'range_high': None,
                    'tp1': parsed.targets[0] if len(parsed.targets) > 0 else None,
                    'tp2': parsed.targets[1] if len(parsed.targets) > 1 else None,
                    'tp3': parsed.targets[2] if len(parsed.targets) > 2 else None,
                    'tp4': parsed.targets[3] if len(parsed.targets) > 3 else None,
                    'sl': parsed.stop_loss,
                    'leverage_hint': parsed.leverage,
                    'confidence': parsed.confidence or 0.7,
                    'parsed_at': parsed.timestamp.isoformat(),
                    'parse_version': 'v1.0',
                    'is_valid': True
                }
                
                self.supabase_client.table('signals_parsed').upsert(processed_data).execute()
                print(f"   🎯 Торговый сигнал сохранен: {parsed.symbol} {parsed.side}")
                
        except Exception as e:
            print(f"   ❌ Ошибка сохранения: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_comprehensive_parsing(self, messages_per_channel: int = 200):
        """Запуск полного парсинга"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ПАРСИНГА")
        print("=" * 60)
        
        if not await self.initialize():
            return False
        
        # Парсим каждый канал
        for channel_id in self.channels:
            await self.parse_channel_history(channel_id, messages_per_channel)
        
        # Итоговая статистика
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Всего сообщений: {self.stats['total_messages']}")
        print(f"   Сохранено в БД: {self.stats['saved_to_db']}")
        print(f"   Ошибок: {self.stats['errors']}")
        
        print("\n📋 ПО ТИПАМ СООБЩЕНИЙ:")
        for msg_type, count in self.stats['by_type'].items():
            print(f"   {msg_type}: {count}")
        
        await self.telegram_client.disconnect()
        print("\n✅ ПАРСИНГ ЗАВЕРШЕН!")
        return True

async def main():
    """Главная функция"""
    parser = ComprehensiveMessageParser()
    await parser.run_comprehensive_parsing(messages_per_channel=200)

if __name__ == "__main__":
    asyncio.run(main())
