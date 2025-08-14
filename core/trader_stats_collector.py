"""
GHOST Trader Stats Collector
Система сбора и анализа статистики по трейдерам
Создает отчеты типа:
🏆 TRADER STATS:
├── Whales Standard: 73% Win Rate, +15.2% ROI
├── Spot Trader: 68% Win Rate, +12.8% ROI  
└── Whales Precision: 61% Win Rate, +8.4% ROI
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import statistics

logger = logging.getLogger(__name__)

@dataclass
class TraderPerformance:
    """Производительность трейдера"""
    trader_id: str
    trader_name: str
    
    # Основные метрики
    total_signals: int = 0
    successful_signals: int = 0
    failed_signals: int = 0
    
    # Win Rate
    win_rate: float = 0.0
    
    # Прибыльность
    total_roi: float = 0.0
    avg_roi: float = 0.0
    best_roi: float = 0.0
    worst_roi: float = 0.0
    
    # Risk/Reward
    avg_risk_reward: float = 0.0
    max_drawdown: float = 0.0
    
    # Временные метрики
    avg_duration_hours: float = 0.0
    fastest_profit_hours: float = 0.0
    
    # Качество сигналов
    avg_confidence: float = 0.0
    total_targets_hit: int = 0
    avg_targets_per_signal: float = 0.0
    
    # Частота
    signals_per_day: float = 0.0
    most_active_hour: int = 0
    
    # Популярные символы
    favorite_symbols: List[str] = None
    
    # Временные рамки
    period_start: datetime = None
    period_end: datetime = None
    
    def __post_init__(self):
        if self.favorite_symbols is None:
            self.favorite_symbols = []

@dataclass 
class SignalOutcome:
    """Результат выполнения сигнала"""
    signal_id: str
    trader_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float]
    
    # Результат
    outcome: str  # "TP1", "TP2", "SL", "BE", "TIMEOUT", "MANUAL"
    roi_percent: float
    pnl_usd: Optional[float]
    
    # Временные метрики
    entry_time: datetime
    exit_time: Optional[datetime]
    duration_hours: Optional[float]
    
    # Цели
    targets_hit: int
    total_targets: int
    
    # Качество
    confidence: float
    slippage: Optional[float]

class TraderStatsCollector:
    """Сборщик статистики по трейдерам"""
    
    def __init__(self):
        self.outcomes: List[SignalOutcome] = []
        self.performances: Dict[str, TraderPerformance] = {}
        
        logger.info("Trader Stats Collector initialized")
    
    def add_signal_outcome(self, outcome: SignalOutcome):
        """Добавление результата сигнала"""
        self.outcomes.append(outcome)
        logger.debug(f"Added outcome for {outcome.trader_id}: {outcome.outcome} ({outcome.roi_percent:.1f}%)")
    
    def calculate_trader_performance(self, trader_id: str, 
                                   period_days: int = 30) -> TraderPerformance:
        """Расчет производительности трейдера за период"""
        
        # Фильтруем сигналы трейдера за период
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        trader_outcomes = [
            outcome for outcome in self.outcomes
            if outcome.trader_id == trader_id and 
               outcome.entry_time >= start_date
        ]
        
        if not trader_outcomes:
            return TraderPerformance(
                trader_id=trader_id,
                trader_name=self._get_trader_name(trader_id),
                period_start=start_date,
                period_end=end_date
            )
        
        # Базовые подсчеты
        total_signals = len(trader_outcomes)
        successful = [o for o in trader_outcomes if o.roi_percent > 0]
        failed = [o for o in trader_outcomes if o.roi_percent <= 0]
        
        # Win Rate
        win_rate = (len(successful) / total_signals * 100) if total_signals > 0 else 0
        
        # ROI метрики
        roi_values = [o.roi_percent for o in trader_outcomes]
        total_roi = sum(roi_values)
        avg_roi = statistics.mean(roi_values) if roi_values else 0
        best_roi = max(roi_values) if roi_values else 0
        worst_roi = min(roi_values) if roi_values else 0
        
        # Risk/Reward
        positive_roi = [r for r in roi_values if r > 0]
        negative_roi = [abs(r) for r in roi_values if r < 0]
        
        avg_risk_reward = 0
        if negative_roi:
            avg_profit = statistics.mean(positive_roi) if positive_roi else 0
            avg_loss = statistics.mean(negative_roi) if negative_roi else 1
            avg_risk_reward = avg_profit / avg_loss if avg_loss > 0 else 0
        
        # Максимальная просадка
        max_drawdown = abs(worst_roi)
        
        # Временные метрики
        durations = [o.duration_hours for o in trader_outcomes if o.duration_hours]
        avg_duration = statistics.mean(durations) if durations else 0
        fastest_profit = min([d for d, r in zip(durations, roi_values) if r > 0]) if durations else 0
        
        # Качество сигналов
        confidences = [o.confidence for o in trader_outcomes if o.confidence]
        avg_confidence = statistics.mean(confidences) if confidences else 0
        
        total_targets_hit = sum(o.targets_hit for o in trader_outcomes)
        total_possible_targets = sum(o.total_targets for o in trader_outcomes)
        avg_targets_per_signal = total_possible_targets / total_signals if total_signals > 0 else 0
        
        # Частота сигналов
        signals_per_day = total_signals / period_days
        
        # Самый активный час
        hours = [o.entry_time.hour for o in trader_outcomes]
        most_active_hour = statistics.mode(hours) if hours else 0
        
        # Популярные символы
        symbols = [o.symbol for o in trader_outcomes]
        symbol_counts = {}
        for symbol in symbols:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        favorite_symbols = sorted(symbol_counts.keys(), 
                                key=lambda x: symbol_counts[x], reverse=True)[:5]
        
        return TraderPerformance(
            trader_id=trader_id,
            trader_name=self._get_trader_name(trader_id),
            total_signals=total_signals,
            successful_signals=len(successful),
            failed_signals=len(failed),
            win_rate=win_rate,
            total_roi=total_roi,
            avg_roi=avg_roi,
            best_roi=best_roi,
            worst_roi=worst_roi,
            avg_risk_reward=avg_risk_reward,
            max_drawdown=max_drawdown,
            avg_duration_hours=avg_duration,
            fastest_profit_hours=fastest_profit,
            avg_confidence=avg_confidence,
            total_targets_hit=total_targets_hit,
            avg_targets_per_signal=avg_targets_per_signal,
            signals_per_day=signals_per_day,
            most_active_hour=most_active_hour,
            favorite_symbols=favorite_symbols,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_top_traders(self, limit: int = 10, 
                       sort_by: str = "win_rate") -> List[TraderPerformance]:
        """Получение топ трейдеров по заданному критерию"""
        
        # Собираем всех уникальных трейдеров
        trader_ids = list(set(outcome.trader_id for outcome in self.outcomes))
        
        # Рассчитываем производительность для каждого
        performances = []
        for trader_id in trader_ids:
            perf = self.calculate_trader_performance(trader_id)
            if perf.total_signals >= 5:  # Минимум 5 сигналов для рейтинга
                performances.append(perf)
        
        # Сортируем по выбранному критерию
        sort_key_map = {
            "win_rate": lambda p: p.win_rate,
            "total_roi": lambda p: p.total_roi,
            "avg_roi": lambda p: p.avg_roi,
            "risk_reward": lambda p: p.avg_risk_reward,
            "signals_count": lambda p: p.total_signals
        }
        
        sort_key = sort_key_map.get(sort_by, sort_key_map["win_rate"])
        performances.sort(key=sort_key, reverse=True)
        
        return performances[:limit]
    
    def generate_trader_report(self, trader_id: str) -> str:
        """Генерация детального отчета по трейдеру"""
        perf = self.calculate_trader_performance(trader_id)
        
        report = f"""
🏆 TRADER REPORT: {perf.trader_name}
{'='*50}

📊 ОСНОВНЫЕ МЕТРИКИ:
   • Total Signals: {perf.total_signals}
   • Win Rate: {perf.win_rate:.1f}%
   • Average ROI: {perf.avg_roi:+.1f}%
   • Total ROI: {perf.total_roi:+.1f}%

💰 ПРИБЫЛЬНОСТЬ:
   • Best Trade: +{perf.best_roi:.1f}%
   • Worst Trade: {perf.worst_roi:.1f}%
   • Risk/Reward: {perf.avg_risk_reward:.2f}
   • Max Drawdown: {perf.max_drawdown:.1f}%

⏱️ ВРЕМЕННЫЕ МЕТРИКИ:
   • Avg Duration: {perf.avg_duration_hours:.1f} hours
   • Fastest Profit: {perf.fastest_profit_hours:.1f} hours
   • Signals per Day: {perf.signals_per_day:.1f}
   • Most Active Hour: {perf.most_active_hour:02d}:00

🎯 КАЧЕСТВО СИГНАЛОВ:
   • Avg Confidence: {perf.avg_confidence:.1f}%
   • Targets Hit: {perf.total_targets_hit}
   • Avg Targets/Signal: {perf.avg_targets_per_signal:.1f}

📈 ПОПУЛЯРНЫЕ СИМВОЛЫ:
   • {', '.join(perf.favorite_symbols[:3])}

📅 ПЕРИОД: {perf.period_start.strftime('%Y-%m-%d')} - {perf.period_end.strftime('%Y-%m-%d')}
"""
        return report
    
    def generate_leaderboard(self) -> str:
        """Генерация таблицы лидеров"""
        top_traders = self.get_top_traders(limit=10)
        
        if not top_traders:
            return "📊 No trader data available yet"
        
        leaderboard = """
🏆 TRADER LEADERBOARD (Top 10)
{'='*60}

"""
        
        for i, trader in enumerate(top_traders, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
            
            leaderboard += f"{medal} {trader.trader_name:<20} │ "
            leaderboard += f"{trader.win_rate:5.1f}% WR │ "
            leaderboard += f"{trader.avg_roi:+6.1f}% ROI │ "
            leaderboard += f"{trader.total_signals:3d} signals\n"
        
        return leaderboard
    
    def _get_trader_name(self, trader_id: str) -> str:
        """Получение человеко-читаемого имени трейдера"""
        name_mapping = {
            "whalesguide_whales_standard": "Whales Standard",
            "whalesguide_spot_trader": "Spot Trader", 
            "whalesguide_whales_precision": "Whales Precision",
            "2trade_main": "2Trade Main",
            "vip_private_group": "VIP Signals"
        }
        
        return name_mapping.get(trader_id, trader_id.replace('_', ' ').title())
    
    def export_performance_data(self, filepath: str):
        """Экспорт данных о производительности в JSON"""
        try:
            # Собираем данные всех трейдеров
            trader_ids = list(set(outcome.trader_id for outcome in self.outcomes))
            export_data = {
                "generated_at": datetime.now().isoformat(),
                "total_outcomes": len(self.outcomes),
                "traders": {}
            }
            
            for trader_id in trader_ids:
                perf = self.calculate_trader_performance(trader_id)
                export_data["traders"][trader_id] = asdict(perf)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Performance data exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")


# Функция для создания тестовых данных
def create_test_data() -> List[SignalOutcome]:
    """Создание тестовых данных для демонстрации"""
    
    test_outcomes = []
    
    # Whales Standard - хороший трейдер
    for i in range(20):
        outcome = SignalOutcome(
            signal_id=f"whales_std_{i}",
            trader_id="whalesguide_whales_standard",
            symbol=["BTCUSDT", "ETHUSDT", "SOLUSDT"][i % 3],
            side="LONG",
            entry_price=45000.0,
            exit_price=46500.0 if i < 15 else 44000.0,  # 75% успешных
            outcome="TP1" if i < 15 else "SL",
            roi_percent=15.2 if i < 15 else -8.5,
            pnl_usd=152.0 if i < 15 else -85.0,
            entry_time=datetime.now() - timedelta(days=30-i),
            exit_time=datetime.now() - timedelta(days=30-i, hours=-6),
            duration_hours=6.0,
            targets_hit=1 if i < 15 else 0,
            total_targets=3,
            confidence=85.0,
            slippage=0.1
        )
        test_outcomes.append(outcome)
    
    # Spot Trader - средний трейдер
    for i in range(15):
        outcome = SignalOutcome(
            signal_id=f"spot_trader_{i}",
            trader_id="whalesguide_spot_trader",
            symbol=["TACUSDT", "DOGENUSDT", "ADAUSDT"][i % 3],
            side="LONG",
            entry_price=0.015,
            exit_price=0.0165 if i < 10 else 0.014,  # 67% успешных
            outcome="TP1" if i < 10 else "SL",
            roi_percent=12.8 if i < 10 else -6.2,
            pnl_usd=64.0 if i < 10 else -31.0,
            entry_time=datetime.now() - timedelta(days=25-i),
            exit_time=datetime.now() - timedelta(days=25-i, hours=-4),
            duration_hours=4.0,
            targets_hit=1 if i < 10 else 0,
            total_targets=2,
            confidence=72.0,
            slippage=0.2
        )
        test_outcomes.append(outcome)
    
    # Whales Precision - более слабый трейдер
    for i in range(12):
        outcome = SignalOutcome(
            signal_id=f"whales_prec_{i}",
            trader_id="whalesguide_whales_precision",
            symbol=["SUIUSDT", "AVAXUSDT", "LINKUSDT"][i % 3],
            side="LONG",
            entry_price=3.85,
            exit_price=4.15 if i < 7 else 3.65,  # 58% успешных
            outcome="TP2" if i < 7 else "SL",
            roi_percent=8.4 if i < 7 else -5.8,
            pnl_usd=42.0 if i < 7 else -29.0,
            entry_time=datetime.now() - timedelta(days=20-i),
            exit_time=datetime.now() - timedelta(days=20-i, hours=-8),
            duration_hours=8.0,
            targets_hit=2 if i < 7 else 0,
            total_targets=4,
            confidence=68.0,
            slippage=0.15
        )
        test_outcomes.append(outcome)
    
    return test_outcomes


# Тестирование системы
def test_trader_stats():
    """Тестирование сборщика статистики"""
    print("🧪 ТЕСТИРОВАНИЕ TRADER STATS COLLECTOR")
    print("=" * 60)
    
    # Создаем сборщик
    collector = TraderStatsCollector()
    
    # Добавляем тестовые данные
    test_data = create_test_data()
    for outcome in test_data:
        collector.add_signal_outcome(outcome)
    
    print(f"✅ Загружено {len(test_data)} результатов сигналов")
    
    # Генерируем таблицу лидеров
    print("\n" + collector.generate_leaderboard())
    
    # Детальный отчет по лучшему трейдеру
    top_traders = collector.get_top_traders(limit=1)
    if top_traders:
        print(collector.generate_trader_report(top_traders[0].trader_id))
    
    # Экспортируем данные
    collector.export_performance_data("trader_performance.json")
    print("📁 Данные экспортированы в trader_performance.json")


if __name__ == "__main__":
    test_trader_stats()
