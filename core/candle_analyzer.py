#!/usr/bin/env python3
"""
Анализ свечами для подтверждения торговых сигналов
Проверяет сигналы по реальным рыночным данным
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CandleData:
    """Данные свечи"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class SignalValidation:
    """Результат валидации сигнала"""
    signal_id: str
    is_valid: bool
    entry_confirmed: bool
    tp1_reached: bool
    tp2_reached: bool
    sl_hit: bool
    max_profit_pct: float
    max_loss_pct: float
    duration_hours: float
    validation_time: datetime
    notes: str

class CandleAnalyzer:
    """Анализатор свечей для валидации сигналов"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.binance_base = "https://api.binance.com/api/v3"
        
    async def get_candles(self, symbol: str, interval: str = "1m", 
                         start_time: int = None, end_time: int = None, 
                         limit: int = 1000) -> List[CandleData]:
        """Получить свечи с Binance"""
        try:
            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
                
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.binance_base}/klines", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candles = []
                        for candle in data:
                            candles.append(CandleData(
                                timestamp=int(candle[0]),
                                open=float(candle[1]),
                                high=float(candle[2]),
                                low=float(candle[3]),
                                close=float(candle[4]),
                                volume=float(candle[5])
                            ))
                        return candles
                    else:
                        logger.error(f"Ошибка получения свечей: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Ошибка получения свечей для {symbol}: {e}")
            return []
    
    async def validate_signal(self, signal_data: Dict) -> SignalValidation:
        """Валидация сигнала по свечам"""
        try:
            symbol = signal_data['symbol']
            side = signal_data['side']
            entry = signal_data.get('entry')
            tp1 = signal_data.get('tp1')
            tp2 = signal_data.get('tp2')
            sl = signal_data.get('sl')
            signal_time = datetime.fromisoformat(signal_data['posted_at'].replace('Z', '+00:00'))
            
            # Получаем свечи с момента сигнала + 24 часа
            start_time = int(signal_time.timestamp() * 1000)
            end_time = int((signal_time + timedelta(hours=24)).timestamp() * 1000)
            
            candles = await self.get_candles(symbol, "1m", start_time, end_time)
            
            if not candles:
                return SignalValidation(
                    signal_id=signal_data['signal_id'],
                    is_valid=False,
                    entry_confirmed=False,
                    tp1_reached=False,
                    tp2_reached=False,
                    sl_hit=False,
                    max_profit_pct=0,
                    max_loss_pct=0,
                    duration_hours=0,
                    validation_time=datetime.now(),
                    notes="Не удалось получить данные свечей"
                )
            
            # Анализируем движение цены
            entry_confirmed = False
            tp1_reached = False
            tp2_reached = False
            sl_hit = False
            max_profit = 0
            max_loss = 0
            
            for candle in candles:
                if entry and not entry_confirmed:
                    # Проверяем касание зоны входа
                    if side == "Buy" and candle.low <= entry <= candle.high:
                        entry_confirmed = True
                        entry_price = entry
                    elif side == "Sell" and candle.low <= entry <= candle.high:
                        entry_confirmed = True
                        entry_price = entry
                
                if entry_confirmed:
                    # Рассчитываем прибыль/убыток
                    if side == "Buy":
                        profit_pct = ((candle.high - entry_price) / entry_price) * 100
                        loss_pct = ((entry_price - candle.low) / entry_price) * 100
                        
                        # Проверяем достижение целей
                        if tp1 and candle.high >= tp1 and not tp1_reached:
                            tp1_reached = True
                        if tp2 and candle.high >= tp2 and not tp2_reached:
                            tp2_reached = True
                        if sl and candle.low <= sl and not sl_hit:
                            sl_hit = True
                            
                    else:  # Sell
                        profit_pct = ((entry_price - candle.low) / entry_price) * 100
                        loss_pct = ((candle.high - entry_price) / entry_price) * 100
                        
                        # Проверяем достижение целей
                        if tp1 and candle.low <= tp1 and not tp1_reached:
                            tp1_reached = True
                        if tp2 and candle.low <= tp2 and not tp2_reached:
                            tp2_reached = True
                        if sl and candle.high >= sl and not sl_hit:
                            sl_hit = True
                    
                    max_profit = max(max_profit, profit_pct)
                    max_loss = max(max_loss, loss_pct)
            
            duration_hours = len(candles) / 60  # минуты в часы
            
            # Определяем валидность
            is_valid = entry_confirmed and (tp1_reached or tp2_reached) and not sl_hit
            
            notes = []
            if not entry_confirmed:
                notes.append("Зона входа не была достигнута")
            if tp1_reached:
                notes.append("TP1 достигнут")
            if tp2_reached:
                notes.append("TP2 достигнут")
            if sl_hit:
                notes.append("SL сработал")
            
            return SignalValidation(
                signal_id=signal_data['signal_id'],
                is_valid=is_valid,
                entry_confirmed=entry_confirmed,
                tp1_reached=tp1_reached,
                tp2_reached=tp2_reached,
                sl_hit=sl_hit,
                max_profit_pct=max_profit,
                max_loss_pct=max_loss,
                duration_hours=duration_hours,
                validation_time=datetime.now(),
                notes="; ".join(notes)
            )
            
        except Exception as e:
            logger.error(f"Ошибка валидации сигнала: {e}")
            return SignalValidation(
                signal_id=signal_data.get('signal_id', 'unknown'),
                is_valid=False,
                entry_confirmed=False,
                tp1_reached=False,
                tp2_reached=False,
                sl_hit=False,
                max_profit_pct=0,
                max_loss_pct=0,
                duration_hours=0,
                validation_time=datetime.now(),
                notes=f"Ошибка анализа: {str(e)}"
            )
    
    async def save_validation_result(self, validation: SignalValidation):
        """Сохранить результат валидации"""
        try:
            # Создаем таблицу signal_validations если её нет
            validation_data = {
                'signal_id': validation.signal_id,
                'is_valid': validation.is_valid,
                'entry_confirmed': validation.entry_confirmed,
                'tp1_reached': validation.tp1_reached,
                'tp2_reached': validation.tp2_reached,
                'sl_hit': validation.sl_hit,
                'max_profit_pct': validation.max_profit_pct,
                'max_loss_pct': validation.max_loss_pct,
                'duration_hours': validation.duration_hours,
                'validation_time': validation.validation_time.isoformat(),
                'notes': validation.notes
            }
            
            self.supabase.table('signal_validations').upsert(validation_data).execute()
            logger.info(f"Валидация сохранена для сигнала {validation.signal_id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения валидации: {e}")
    
    async def validate_pending_signals(self):
        """Валидировать все необработанные сигналы"""
        try:
            # Получаем сигналы без валидации
            signals = self.supabase.table('signals_parsed').select('*').eq('is_valid', True).execute()
            
            validated_count = 0
            for signal in signals.data:
                # Проверяем, есть ли уже валидация
                existing = self.supabase.table('signal_validations').select('signal_id').eq('signal_id', signal['signal_id']).execute()
                
                if not existing.data:
                    validation = await self.validate_signal(signal)
                    await self.save_validation_result(validation)
                    validated_count += 1
                    
                    print(f"✅ Валидирован: {signal['symbol']} - {'✅' if validation.is_valid else '❌'}")
                    
                    # Пауза между запросами к API
                    await asyncio.sleep(0.1)
            
            print(f"🎯 Валидировано сигналов: {validated_count}")
            
        except Exception as e:
            logger.error(f"Ошибка валидации сигналов: {e}")

if __name__ == "__main__":
    # Тест модуля
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    
    load_dotenv()
    
    supabase = create_client(
        os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    analyzer = CandleAnalyzer(supabase)
    
    async def test():
        await analyzer.validate_pending_signals()
    
    asyncio.run(test())
