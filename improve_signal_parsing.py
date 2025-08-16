#!/usr/bin/env python3
"""
Улучшение парсинга сигналов - обрабатываем больше сырых сообщений
"""

import re
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

class ImprovedSignalParser:
    def __init__(self):
        self.supabase = create_client(
            os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
    
    def parse_trading_signal(self, text: str):
        """Улучшенный парсинг торговых сигналов"""
        
        # Ищем символы криптовалют
        symbol_patterns = [
            r'#(\w+USDT?)\b',
            r'#(\w+)\b',
            r'\$(\w+USDT?)\b',
            r'\$(\w+)\b',
            r'\b(\w+USDT?)\b',
            r'\b([A-Z]{3,5})\s*(?:USDT?|/USDT?)',
            r'(?:купить|buy|long|short|sell)\s+([A-Z]{3,8})',
            r'([A-Z]{3,8})\s*(?:лонг|long|шорт|short)'
        ]
        
        symbol = None
        for pattern in symbol_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                symbol = matches[0].upper()
                # Добавляем USDT если его нет
                if not symbol.endswith('USDT') and not symbol.endswith('USD'):
                    symbol += 'USDT'
                break
        
        # Ищем направление торговли
        side = 'BUY'
        long_words = ['long', 'лонг', 'buy', 'купить', 'покупка', '🟢', '⬆️', 'bull']
        short_words = ['short', 'шорт', 'sell', 'продать', 'продажа', '🔴', '⬇️', 'bear']
        
        text_lower = text.lower()
        if any(word in text_lower for word in short_words):
            side = 'SELL'
        elif any(word in text_lower for word in long_words):
            side = 'BUY'
        
        # Ищем цены входа
        entry_patterns = [
            r'entry[:\s]*(\d+(?:\.\d+)?)',
            r'вход[:\s]*(\d+(?:\.\d+)?)',
            r'входная[:\s]*(\d+(?:\.\d+)?)',
            r'цена входа[:\s]*(\d+(?:\.\d+)?)',
            r'от\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:usdt?|долл|$)',
            r'по\s*(\d+(?:\.\d+)?)',
            r'около\s*(\d+(?:\.\d+)?)'
        ]
        
        entry_price = None
        for pattern in entry_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    entry_price = float(matches[0])
                    if entry_price > 0:
                        break
                except:
                    continue
        
        # Ищем цели (TP)
        target_patterns = [
            r'tp\s*[1-4]?[:\s]*(\d+(?:\.\d+)?)',
            r'target[:\s]*(\d+(?:\.\d+)?)',
            r'цель[:\s]*(\d+(?:\.\d+)?)',
            r'тейк[:\s]*(\d+(?:\.\d+)?)',
            r'до\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:цель|target|tp)'
        ]
        
        targets = []
        for pattern in target_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match)
                    if price > 0 and price not in targets:
                        targets.append(price)
                except:
                    continue
        
        # Сортируем цели
        targets = sorted(set(targets))[:4]  # Максимум 4 цели
        
        # Ищем стоп-лосс
        sl_patterns = [
            r'sl[:\s]*(\d+(?:\.\d+)?)',
            r'stop[:\s]*(\d+(?:\.\d+)?)',
            r'стоп[:\s]*(\d+(?:\.\d+)?)',
            r'лосс[:\s]*(\d+(?:\.\d+)?)',
            r'убыток[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        stop_loss = None
        for pattern in sl_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    stop_loss = float(matches[0])
                    if stop_loss > 0:
                        break
                except:
                    continue
        
        # Ищем плечо
        leverage_patterns = [
            r'leverage[:\s]*(\d+)[x]?',
            r'плечо[:\s]*(\d+)[x]?',
            r'x(\d+)',
            r'(\d+)x'
        ]
        
        leverage = None
        for pattern in leverage_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    leverage = int(matches[0])
                    if 1 <= leverage <= 125:
                        break
                except:
                    continue
        
        # Определяем является ли это торговым сигналом
        is_trading_signal = bool(
            symbol and 
            (entry_price or targets) and
            any(word in text_lower for word in [
                'signal', 'сигнал', 'trade', 'торговля', 'buy', 'sell', 
                'long', 'short', 'лонг', 'шорт', 'tp', 'sl', 'entry', 'вход'
            ])
        )
        
        confidence = 0.3
        if symbol and entry_price and targets:
            confidence = 0.9
        elif symbol and (entry_price or targets):
            confidence = 0.7
        elif symbol:
            confidence = 0.5
        
        return {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'targets': targets,
            'stop_loss': stop_loss,
            'leverage': leverage,
            'is_trading_signal': is_trading_signal,
            'confidence': confidence
        }
    
    def process_raw_signals(self, limit=100):
        """Обработка сырых сигналов"""
        print(f'🔄 Обработка {limit} сырых сигналов...')
        
        # Получаем необработанные сырые сигналы
        raw_signals = self.supabase.table('signals_raw').select('*').eq('processed', False).limit(limit).execute()
        
        processed_count = 0
        trading_signals_count = 0
        
        for raw_signal in raw_signals.data:
            try:
                # Парсим сигнал
                parsed = self.parse_trading_signal(raw_signal['text'])
                
                if parsed['is_trading_signal']:
                    # Создаем торговый сигнал
                    signal_data = {
                        # signal_id пропускаем - он auto-increment
                        'trader_id': raw_signal['trader_id'][:10],  # Обрезаем до 10 символов
                        'raw_id': raw_signal['raw_id'],
                        'posted_at': raw_signal['posted_at'],
                        'symbol': parsed['symbol'][:10] if parsed['symbol'] else None,  # Ограничиваем длину
                        'side': parsed['side'][:10] if parsed['side'] else None,
                        'entry_type': 'market'[:10],
                        'entry': parsed['entry_price'],
                        'tp1': parsed['targets'][0] if len(parsed['targets']) > 0 else None,
                        'tp2': parsed['targets'][1] if len(parsed['targets']) > 1 else None,
                        'tp3': parsed['targets'][2] if len(parsed['targets']) > 2 else None,
                        'tp4': parsed['targets'][3] if len(parsed['targets']) > 3 else None,
                        'sl': parsed['stop_loss'],
                        'leverage_hint': parsed['leverage'],
                        'confidence': parsed['confidence'],
                        'parsed_at': datetime.now().isoformat(),
                        'parse_version': 'v1.1'[:10],  # Обрезаем
                        'is_valid': True
                    }
                    
                    # Сохраняем торговый сигнал
                    self.supabase.table('signals_parsed').upsert(signal_data).execute()
                    trading_signals_count += 1
                    
                    print(f'🎯 Торговый сигнал: {parsed["symbol"]} {parsed["side"]} ({parsed["confidence"]:.1f})')
                
                # Отмечаем как обработанный
                self.supabase.table('signals_raw').update({'processed': True}).eq('raw_id', raw_signal['raw_id']).execute()
                processed_count += 1
                
            except Exception as e:
                print(f'❌ Ошибка обработки сигнала {raw_signal["raw_id"]}: {e}')
        
        print(f'✅ Обработано: {processed_count} сообщений')
        print(f'🎯 Найдено торговых сигналов: {trading_signals_count}')
        
        return processed_count, trading_signals_count

if __name__ == "__main__":
    parser = ImprovedSignalParser()
    parser.process_raw_signals(200)  # Обрабатываем 200 сырых сигналов
