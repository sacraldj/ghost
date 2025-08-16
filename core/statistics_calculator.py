#!/usr/bin/env python3
"""
Автоматический расчет статистики трейдеров
Анализирует результаты сигналов и строит статистику
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TraderStats:
    """Статистика трейдера"""
    trader_id: str
    period: str
    total_signals: int
    valid_signals: int
    tp1_hits: int
    tp2_hits: int
    sl_hits: int
    winrate_pct: float
    avg_profit_pct: float
    avg_loss_pct: float
    total_pnl_pct: float
    max_drawdown_pct: float
    avg_duration_hours: float
    best_signal_pct: float
    worst_signal_pct: float
    updated_at: datetime

class StatisticsCalculator:
    """Калькулятор статистики трейдеров"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        
    async def calculate_trader_stats(self, trader_id: str, period_days: int = 30) -> TraderStats:
        """Рассчитать статистику трейдера за период"""
        try:
            # Определяем период
            start_date = (datetime.now() - timedelta(days=period_days)).isoformat()
            
            # Получаем сигналы трейдера
            signals = self.supabase.table('signals_parsed').select('*').eq('trader_id', trader_id).gte('posted_at', start_date).execute()
            
            if not signals.data:
                return TraderStats(
                    trader_id=trader_id,
                    period=f"{period_days}d",
                    total_signals=0,
                    valid_signals=0,
                    tp1_hits=0,
                    tp2_hits=0,
                    sl_hits=0,
                    winrate_pct=0,
                    avg_profit_pct=0,
                    avg_loss_pct=0,
                    total_pnl_pct=0,
                    max_drawdown_pct=0,
                    avg_duration_hours=0,
                    best_signal_pct=0,
                    worst_signal_pct=0,
                    updated_at=datetime.now()
                )
            
            # Получаем события и валидации для этих сигналов
            signal_ids = [s['signal_id'] for s in signals.data]
            
            events = []
            validations = []
            
            if signal_ids:
                # Получаем события
                events_result = self.supabase.table('signal_events').select('*').in_('signal_id', signal_ids).execute()
                events = events_result.data if events_result.data else []
                
                # Получаем валидации
                validations_result = self.supabase.table('signal_validations').select('*').in_('signal_id', signal_ids).execute()
                validations = validations_result.data if validations_result.data else []
            
            # Анализируем данные
            total_signals = len(signals.data)
            valid_signals = len([s for s in signals.data if s.get('is_valid', False)])
            
            tp1_hits = 0
            tp2_hits = 0
            sl_hits = 0
            profits = []
            losses = []
            durations = []
            pnl_series = []
            
            # Группируем события по сигналам
            events_by_signal = {}
            for event in events:
                signal_id = event['signal_id']
                if signal_id not in events_by_signal:
                    events_by_signal[signal_id] = []
                events_by_signal[signal_id].append(event)
            
            # Группируем валидации по сигналам
            validations_by_signal = {v['signal_id']: v for v in validations}
            
            # Анализируем каждый сигнал
            for signal in signals.data:
                signal_id = signal['signal_id']
                signal_events = events_by_signal.get(signal_id, [])
                validation = validations_by_signal.get(signal_id)
                
                # Определяем результат сигнала
                signal_tp1 = False
                signal_tp2 = False
                signal_sl = False
                signal_profit = 0
                signal_duration = 0
                
                # Из событий
                for event in signal_events:
                    if event['event_type'] == 'tp1':
                        signal_tp1 = True
                        signal_profit = max(signal_profit, event.get('profit_pct', 0))
                    elif event['event_type'] == 'tp2':
                        signal_tp2 = True
                        signal_profit = max(signal_profit, event.get('profit_pct', 0))
                    elif event['event_type'] == 'sl':
                        signal_sl = True
                        signal_profit = min(signal_profit, -event.get('loss_pct', 0))
                
                # Из валидации (если нет событий)
                if validation and not signal_events:
                    signal_tp1 = validation.get('tp1_reached', False)
                    signal_tp2 = validation.get('tp2_reached', False)
                    signal_sl = validation.get('sl_hit', False)
                    signal_profit = validation.get('max_profit_pct', 0) if not signal_sl else -validation.get('max_loss_pct', 0)
                    signal_duration = validation.get('duration_hours', 0)
                
                # Подсчитываем статистику
                if signal_tp1:
                    tp1_hits += 1
                if signal_tp2:
                    tp2_hits += 1
                if signal_sl:
                    sl_hits += 1
                
                if signal_profit > 0:
                    profits.append(signal_profit)
                elif signal_profit < 0:
                    losses.append(abs(signal_profit))
                
                if signal_duration > 0:
                    durations.append(signal_duration)
                
                pnl_series.append(signal_profit)
            
            # Рассчитываем метрики
            winrate = ((tp1_hits + tp2_hits) / valid_signals * 100) if valid_signals > 0 else 0
            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            total_pnl = sum(pnl_series)
            
            # Рассчитываем максимальную просадку
            max_drawdown = 0
            running_pnl = 0
            peak = 0
            
            for pnl in pnl_series:
                running_pnl += pnl
                if running_pnl > peak:
                    peak = running_pnl
                drawdown = peak - running_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            best_signal = max(pnl_series) if pnl_series else 0
            worst_signal = min(pnl_series) if pnl_series else 0
            
            return TraderStats(
                trader_id=trader_id,
                period=f"{period_days}d",
                total_signals=total_signals,
                valid_signals=valid_signals,
                tp1_hits=tp1_hits,
                tp2_hits=tp2_hits,
                sl_hits=sl_hits,
                winrate_pct=round(winrate, 2),
                avg_profit_pct=round(avg_profit, 2),
                avg_loss_pct=round(avg_loss, 2),
                total_pnl_pct=round(total_pnl, 2),
                max_drawdown_pct=round(max_drawdown, 2),
                avg_duration_hours=round(avg_duration, 2),
                best_signal_pct=round(best_signal, 2),
                worst_signal_pct=round(worst_signal, 2),
                updated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка расчета статистики для {trader_id}: {e}")
            return TraderStats(
                trader_id=trader_id,
                period=f"{period_days}d",
                total_signals=0,
                valid_signals=0,
                tp1_hits=0,
                tp2_hits=0,
                sl_hits=0,
                winrate_pct=0,
                avg_profit_pct=0,
                avg_loss_pct=0,
                total_pnl_pct=0,
                max_drawdown_pct=0,
                avg_duration_hours=0,
                best_signal_pct=0,
                worst_signal_pct=0,
                updated_at=datetime.now()
            )
    
    async def save_trader_stats(self, stats: TraderStats):
        """Сохранить статистику трейдера"""
        try:
            stats_data = {
                'trader_id': stats.trader_id,
                'period': stats.period,
                'total_signals': stats.total_signals,
                'valid_signals': stats.valid_signals,
                'tp1_hits': stats.tp1_hits,
                'tp2_hits': stats.tp2_hits,
                'sl_hits': stats.sl_hits,
                'winrate_pct': stats.winrate_pct,
                'avg_profit_pct': stats.avg_profit_pct,
                'avg_loss_pct': stats.avg_loss_pct,
                'total_pnl_pct': stats.total_pnl_pct,
                'max_drawdown_pct': stats.max_drawdown_pct,
                'avg_duration_hours': stats.avg_duration_hours,
                'best_signal_pct': stats.best_signal_pct,
                'worst_signal_pct': stats.worst_signal_pct,
                'updated_at': stats.updated_at.isoformat()
            }
            
            # Используем upsert для обновления или создания
            self.supabase.table('trader_statistics').upsert(stats_data).execute()
            
            print(f"📊 Статистика сохранена: {stats.trader_id} ({stats.period}) - WR: {stats.winrate_pct}%, PnL: {stats.total_pnl_pct}%")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения статистики: {e}")
    
    async def calculate_all_traders_stats(self, periods: List[int] = [7, 30, 90]):
        """Рассчитать статистику для всех трейдеров"""
        try:
            # Получаем всех активных трейдеров
            traders = self.supabase.table('trader_registry').select('trader_id').eq('is_active', True).execute()
            
            if not traders.data:
                print("❌ Нет активных трейдеров")
                return
            
            total_calculations = 0
            
            for trader in traders.data:
                trader_id = trader['trader_id']
                
                for period in periods:
                    stats = await self.calculate_trader_stats(trader_id, period)
                    await self.save_trader_stats(stats)
                    total_calculations += 1
                    
                    # Небольшая пауза между расчетами
                    await asyncio.sleep(0.1)
            
            print(f"✅ Рассчитано статистик: {total_calculations}")
            
        except Exception as e:
            logger.error(f"Ошибка расчета статистики всех трейдеров: {e}")
    
    async def get_top_traders(self, period: str = "30d", limit: int = 10) -> List[Dict]:
        """Получить топ трейдеров по статистике"""
        try:
            stats = self.supabase.table('trader_statistics').select('*').eq('period', period).order('total_pnl_pct', desc=True).limit(limit).execute()
            
            return stats.data if stats.data else []
            
        except Exception as e:
            logger.error(f"Ошибка получения топ трейдеров: {e}")
            return []
    
    async def run_periodic_calculation(self, interval_hours: int = 1):
        """Запуск периодического расчета статистики"""
        print(f"🔄 ЗАПУСК ПЕРИОДИЧЕСКОГО РАСЧЕТА СТАТИСТИКИ (каждые {interval_hours}ч)")
        
        while True:
            try:
                print(f"📊 Начинаем расчет статистики: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                await self.calculate_all_traders_stats()
                
                print(f"✅ Расчет завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Ждем до следующего расчета
                await asyncio.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                print("⏹️ Остановка периодического расчета...")
                break
            except Exception as e:
                logger.error(f"Ошибка периодического расчета: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    
    load_dotenv()
    
    supabase = create_client(
        os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    calculator = StatisticsCalculator(supabase)
    
    async def test():
        # Тестируем расчет для одного трейдера
        stats = await calculator.calculate_trader_stats('cryptoattack24', 30)
        print(f"Статистика cryptoattack24: {stats}")
        
        # Рассчитываем для всех
        await calculator.calculate_all_traders_stats()
    
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("⏹️ Остановлено пользователем")
