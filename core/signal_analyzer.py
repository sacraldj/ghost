"""
GHOST Advanced Signal Analyzer
Система детального анализа сигналов как у Дарена с фильтрацией и предсказанием
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from supabase import create_client, Client

logger = logging.getLogger(__name__)

@dataclass
class SignalAnalysis:
    """Детальный анализ сигнала"""
    signal_id: str
    trader_id: str
    symbol: str
    
    # Базовые данные сигнала
    entry_price: float
    tp1_price: float
    tp2_price: float
    sl_price: float
    side: str
    
    # Анализ структуры сигнала
    rr_ratio_tp1: float  # Risk/Reward для TP1
    rr_ratio_tp2: float  # Risk/Reward для TP2
    risk_distance: float  # Расстояние до SL в %
    tp1_distance: float  # Расстояние до TP1 в %
    tp2_distance: float  # Расстояние до TP2 в %
    
    # Рыночные условия в момент сигнала
    market_volatility: float
    market_trend: str  # "UP", "DOWN", "SIDEWAYS"
    volume_spike: bool
    price_momentum: float
    
    # Исторический контекст
    similar_signals_count: int
    similar_signals_success_rate: float
    trader_recent_performance: float
    
    # Предсказание вероятности (как у Дарена)
    tp1_probability: float  # "89% что вероятность достигнуть TP1"
    tp2_probability: float
    sl_probability: float
    
    # Факторы влияния
    confidence_factors: List[str]
    risk_factors: List[str]
    
    # Метаданные
    analysis_time: datetime
    confidence_score: float

@dataclass
class TraderPattern:
    """Паттерн трейдера"""
    trader_id: str
    
    # Структурные паттерны
    avg_rr_ratio: float
    preferred_risk_distance: float
    typical_timeframe: str
    
    # Успешные паттерны
    successful_signal_characteristics: Dict[str, Any]
    failed_signal_characteristics: Dict[str, Any]
    
    # Временные паттерны
    best_trading_hours: List[int]
    best_weekdays: List[int]
    
    # Рыночные условия
    performs_best_in: List[str]  # Условия рынка
    avoids_markets: List[str]
    
    # Статистика
    total_analyzed: int
    success_rate: float
    last_updated: datetime

class AdvancedSignalAnalyzer:
    """Продвинутый анализатор сигналов"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase = supabase_client
        self.trader_patterns: Dict[str, TraderPattern] = {}
        
        # Весовые коэффициенты для предсказания
        self.prediction_weights = {
            "historical_success": 0.30,
            "signal_structure": 0.25,
            "market_conditions": 0.20,
            "trader_form": 0.15,
            "time_context": 0.10
        }
        
        logger.info("Advanced Signal Analyzer initialized")
    
    async def analyze_signal(self, signal_data: Dict[str, Any]) -> SignalAnalysis:
        """
        Полный анализ сигнала как у Дарена
        'А похож ли сейчас этот же сигнал по структуре на тот который достиг тп1'
        """
        try:
            # 1. Извлекаем базовые данные
            signal_id = signal_data.get("signal_id")
            trader_id = signal_data.get("trader_id")
            symbol = signal_data.get("symbol")
            
            entry = float(signal_data.get("entry", 0))
            tp1 = float(signal_data.get("tp1", 0))
            tp2 = float(signal_data.get("tp2", 0))
            sl = float(signal_data.get("sl", 0))
            side = signal_data.get("side", "BUY")
            
            # 2. Анализируем структуру сигнала
            structure_analysis = await self._analyze_signal_structure(
                entry, tp1, tp2, sl, side
            )
            
            # 3. Анализируем рыночные условия
            market_analysis = await self._analyze_market_conditions(symbol)
            
            # 4. Анализируем исторический контекст
            historical_analysis = await self._analyze_historical_context(
                trader_id, symbol, structure_analysis
            )
            
            # 5. Предсказываем вероятности (ГЛАВНАЯ ФИЧА как у Дарена)
            probabilities = await self._predict_outcome_probabilities(
                trader_id, structure_analysis, market_analysis, historical_analysis
            )
            
            # 6. Анализируем факторы уверенности и риска
            factors = await self._analyze_confidence_risk_factors(
                structure_analysis, market_analysis, historical_analysis
            )
            
            # 7. Вычисляем общий confidence score
            confidence_score = await self._calculate_confidence_score(
                structure_analysis, market_analysis, historical_analysis, probabilities
            )
            
            # Создаем результат анализа
            analysis = SignalAnalysis(
                signal_id=signal_id,
                trader_id=trader_id,
                symbol=symbol,
                
                # Базовые данные
                entry_price=entry,
                tp1_price=tp1,
                tp2_price=tp2,
                sl_price=sl,
                side=side,
                
                # Структура
                rr_ratio_tp1=structure_analysis["rr_tp1"],
                rr_ratio_tp2=structure_analysis["rr_tp2"],
                risk_distance=structure_analysis["risk_distance"],
                tp1_distance=structure_analysis["tp1_distance"],
                tp2_distance=structure_analysis["tp2_distance"],
                
                # Рынок
                market_volatility=market_analysis["volatility"],
                market_trend=market_analysis["trend"],
                volume_spike=market_analysis["volume_spike"],
                price_momentum=market_analysis["momentum"],
                
                # История
                similar_signals_count=historical_analysis["similar_count"],
                similar_signals_success_rate=historical_analysis["success_rate"],
                trader_recent_performance=historical_analysis["recent_performance"],
                
                # Предсказания (КАК У ДАРЕНА!)
                tp1_probability=probabilities["tp1"],
                tp2_probability=probabilities["tp2"],
                sl_probability=probabilities["sl"],
                
                # Факторы
                confidence_factors=factors["confidence"],
                risk_factors=factors["risk"],
                
                # Метаданные
                analysis_time=datetime.now(),
                confidence_score=confidence_score
            )
            
            # Сохраняем анализ в базу
            await self._save_analysis_to_db(analysis)
            
            logger.info(f"✅ Signal analyzed: {signal_id}, TP1 probability: {probabilities['tp1']:.1f}%")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing signal: {e}")
            raise
    
    async def _analyze_signal_structure(self, entry: float, tp1: float, tp2: float, sl: float, side: str) -> Dict[str, float]:
        """Анализ структуры сигнала"""
        try:
            is_long = side.upper() == "BUY"
            
            if is_long:
                # Для лонгов
                risk_distance = abs(entry - sl) / entry * 100
                tp1_distance = abs(tp1 - entry) / entry * 100
                tp2_distance = abs(tp2 - entry) / entry * 100
                
                rr_tp1 = tp1_distance / risk_distance if risk_distance > 0 else 0
                rr_tp2 = tp2_distance / risk_distance if risk_distance > 0 else 0
            else:
                # Для шортов
                risk_distance = abs(sl - entry) / entry * 100
                tp1_distance = abs(entry - tp1) / entry * 100
                tp2_distance = abs(entry - tp2) / entry * 100
                
                rr_tp1 = tp1_distance / risk_distance if risk_distance > 0 else 0
                rr_tp2 = tp2_distance / risk_distance if risk_distance > 0 else 0
            
            return {
                "rr_tp1": round(rr_tp1, 2),
                "rr_tp2": round(rr_tp2, 2),
                "risk_distance": round(risk_distance, 2),
                "tp1_distance": round(tp1_distance, 2),
                "tp2_distance": round(tp2_distance, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing signal structure: {e}")
            return {
                "rr_tp1": 0,
                "rr_tp2": 0,
                "risk_distance": 0,
                "tp1_distance": 0,
                "tp2_distance": 0
            }
    
    async def _analyze_market_conditions(self, symbol: str) -> Dict[str, Any]:
        """Анализ рыночных условий"""
        try:
            # Получаем последние свечи
            if self.supabase:
                result = self.supabase.table("trader_candles") \
                    .select("*") \
                    .eq("symbol", symbol) \
                    .eq("timeframe", "1m") \
                    .order("open_time", desc=True) \
                    .limit(100) \
                    .execute()
                
                candles = result.data
            else:
                candles = []
            
            if not candles:
                return {
                    "volatility": 0,
                    "trend": "UNKNOWN",
                    "volume_spike": False,
                    "momentum": 0
                }
            
            # Анализируем волатильность
            prices = [float(c["close_price"]) for c in candles[:20]]
            volatility = np.std(prices) / np.mean(prices) * 100 if len(prices) > 1 else 0
            
            # Анализируем тренд
            short_ma = np.mean(prices[:5]) if len(prices) >= 5 else prices[0]
            long_ma = np.mean(prices[:20]) if len(prices) >= 20 else prices[0]
            
            if short_ma > long_ma * 1.002:  # 0.2% выше
                trend = "UP"
            elif short_ma < long_ma * 0.998:  # 0.2% ниже
                trend = "DOWN"
            else:
                trend = "SIDEWAYS"
            
            # Анализируем объем
            volumes = [float(c["volume"]) for c in candles[:10]]
            avg_volume = np.mean(volumes) if len(volumes) > 1 else 0
            recent_volume = volumes[0] if volumes else 0
            volume_spike = recent_volume > avg_volume * 1.5
            
            # Momentum
            momentum = (prices[0] - prices[-1]) / prices[-1] * 100 if len(prices) > 1 else 0
            
            return {
                "volatility": round(volatility, 2),
                "trend": trend,
                "volume_spike": volume_spike,
                "momentum": round(momentum, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market conditions: {e}")
            return {
                "volatility": 0,
                "trend": "UNKNOWN",
                "volume_spike": False,
                "momentum": 0
            }
    
    async def _analyze_historical_context(self, trader_id: str, symbol: str, structure: Dict[str, float]) -> Dict[str, Any]:
        """Анализ исторического контекста"""
        try:
            if not self.supabase:
                return {
                    "similar_count": 0,
                    "success_rate": 0,
                    "recent_performance": 0
                }
            
            # Ищем похожие сигналы по структуре
            rr_tolerance = 0.3  # 30% допуск на R/R
            risk_tolerance = 1.0  # 1% допуск на риск
            
            # Получаем исторические сигналы с исходами
            result = self.supabase.table("signals_parsed") \
                .select("""
                    *,
                    signal_outcomes!inner(final_result, pnl_sim)
                """) \
                .eq("trader_id", trader_id) \
                .eq("symbol", symbol) \
                .execute()
            
            historical_signals = result.data or []
            
            # Фильтруем похожие по структуре
            similar_signals = []
            for signal in historical_signals:
                if (
                    abs(float(signal.get("rr_ratio", 0)) - structure["rr_tp1"]) <= rr_tolerance and
                    abs(float(signal.get("risk_distance", 0)) - structure["risk_distance"]) <= risk_tolerance
                ):
                    similar_signals.append(signal)
            
            # Вычисляем успешность похожих сигналов
            successful_similar = [
                s for s in similar_signals 
                if s.get("signal_outcomes", {}).get("final_result") in ["TP1_ONLY", "TP2_FULL"]
            ]
            
            success_rate = (len(successful_similar) / len(similar_signals)) * 100 if similar_signals else 0
            
            # Анализируем недавнюю форму трейдера (последние 10 сигналов)
            recent_result = self.supabase.table("signal_outcomes") \
                .select("final_result") \
                .eq("trader_id", trader_id) \
                .order("calculated_at", desc=True) \
                .limit(10) \
                .execute()
            
            recent_outcomes = recent_result.data or []
            recent_wins = [
                o for o in recent_outcomes 
                if o.get("final_result") in ["TP1_ONLY", "TP2_FULL"]
            ]
            
            recent_performance = (len(recent_wins) / len(recent_outcomes)) * 100 if recent_outcomes else 0
            
            return {
                "similar_count": len(similar_signals),
                "success_rate": round(success_rate, 1),
                "recent_performance": round(recent_performance, 1)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing historical context: {e}")
            return {
                "similar_count": 0,
                "success_rate": 0,
                "recent_performance": 0
            }
    
    async def _predict_outcome_probabilities(
        self, 
        trader_id: str, 
        structure: Dict[str, float], 
        market: Dict[str, Any], 
        historical: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        ГЛАВНАЯ ФИЧА: Предсказание вероятностей как у Дарена
        'Система говорит 89% что вероятность достигнуть тп 1'
        """
        try:
            # Базовая вероятность из исторических данных
            base_tp1_prob = historical["success_rate"] if historical["success_rate"] > 0 else 50.0
            
            # Корректировки на основе факторов
            adjustments = 0.0
            
            # 1. R/R соотношение (хорошее R/R = больше вероятность)
            if structure["rr_tp1"] >= 2.0:
                adjustments += 10  # +10% за хорошее R/R
            elif structure["rr_tp1"] >= 1.5:
                adjustments += 5   # +5% за среднее R/R
            elif structure["rr_tp1"] < 1.0:
                adjustments -= 15  # -15% за плохое R/R
            
            # 2. Риск (меньше риск = больше вероятность)
            if structure["risk_distance"] <= 2.0:
                adjustments += 8   # +8% за низкий риск
            elif structure["risk_distance"] >= 5.0:
                adjustments -= 10  # -10% за высокий риск
            
            # 3. Рыночные условия
            if market["trend"] == "UP" and structure["rr_tp1"] > 0:  # Лонг в аптренде
                adjustments += 5
            elif market["trend"] == "DOWN" and structure["rr_tp1"] > 0:  # Шорт в даунтренде
                adjustments += 5
            
            if market["volatility"] > 3.0:  # Высокая волатильность = больше риск
                adjustments -= 8
            
            if market["volume_spike"]:  # Всплеск объема = хороший сигнал
                adjustments += 6
            
            # 4. Форма трейдера
            if historical["recent_performance"] >= 70:
                adjustments += 8   # Трейдер в форме
            elif historical["recent_performance"] <= 40:
                adjustments -= 12  # Трейдер не в форме
            
            # 5. Количество похожих сигналов (больше данных = больше уверенность)
            if historical["similar_count"] >= 10:
                adjustments += 5   # Достаточно данных
            elif historical["similar_count"] < 3:
                adjustments -= 10  # Мало данных
            
            # Применяем корректировки
            tp1_probability = max(5.0, min(95.0, base_tp1_prob + adjustments))
            
            # TP2 обычно в 2 раза сложнее достичь
            tp2_probability = max(5.0, tp1_probability * 0.6)
            
            # SL - остаток вероятности с учетом BE
            sl_probability = max(5.0, 100 - tp1_probability - 5)  # 5% на BE
            
            return {
                "tp1": round(tp1_probability, 1),
                "tp2": round(tp2_probability, 1),
                "sl": round(sl_probability, 1)
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting probabilities: {e}")
            return {"tp1": 50.0, "tp2": 30.0, "sl": 20.0}
    
    async def _analyze_confidence_risk_factors(
        self, 
        structure: Dict[str, float], 
        market: Dict[str, Any], 
        historical: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Анализ факторов уверенности и риска"""
        confidence_factors = []
        risk_factors = []
        
        # Структурные факторы
        if structure["rr_tp1"] >= 2.0:
            confidence_factors.append(f"Отличное R/R: {structure['rr_tp1']:.1f}")
        elif structure["rr_tp1"] < 1.0:
            risk_factors.append(f"Плохое R/R: {structure['rr_tp1']:.1f}")
        
        if structure["risk_distance"] <= 2.0:
            confidence_factors.append(f"Низкий риск: {structure['risk_distance']:.1f}%")
        elif structure["risk_distance"] >= 5.0:
            risk_factors.append(f"Высокий риск: {structure['risk_distance']:.1f}%")
        
        # Рыночные факторы
        if market["volume_spike"]:
            confidence_factors.append("Всплеск объема")
        
        if market["volatility"] > 3.0:
            risk_factors.append(f"Высокая волатильность: {market['volatility']:.1f}%")
        
        # Исторические факторы
        if historical["success_rate"] >= 70:
            confidence_factors.append(f"Высокий успех похожих: {historical['success_rate']:.1f}%")
        elif historical["success_rate"] <= 40:
            risk_factors.append(f"Низкий успех похожих: {historical['success_rate']:.1f}%")
        
        if historical["recent_performance"] >= 70:
            confidence_factors.append(f"Трейдер в форме: {historical['recent_performance']:.1f}%")
        elif historical["recent_performance"] <= 40:
            risk_factors.append(f"Трейдер не в форме: {historical['recent_performance']:.1f}%")
        
        if historical["similar_count"] < 3:
            risk_factors.append(f"Мало данных: {historical['similar_count']} сигналов")
        
        return {
            "confidence": confidence_factors,
            "risk": risk_factors
        }
    
    async def _calculate_confidence_score(
        self, 
        structure: Dict[str, float], 
        market: Dict[str, Any], 
        historical: Dict[str, Any], 
        probabilities: Dict[str, float]
    ) -> float:
        """Вычисление общего индекса уверенности"""
        try:
            scores = []
            
            # Структурный скор (0-100)
            if structure["rr_tp1"] >= 2.0:
                scores.append(90)
            elif structure["rr_tp1"] >= 1.5:
                scores.append(70)
            elif structure["rr_tp1"] >= 1.0:
                scores.append(50)
            else:
                scores.append(20)
            
            # Исторический скор (0-100)
            if historical["similar_count"] >= 10:
                hist_score = min(100, historical["success_rate"] + 10)
            elif historical["similar_count"] >= 5:
                hist_score = historical["success_rate"]
            else:
                hist_score = max(30, historical["success_rate"] - 20)
            scores.append(hist_score)
            
            # Рыночный скор (0-100)
            market_score = 50  # Базовый
            if market["volume_spike"]:
                market_score += 20
            if market["volatility"] < 2.0:
                market_score += 15
            elif market["volatility"] > 4.0:
                market_score -= 25
            scores.append(max(0, min(100, market_score)))
            
            # Скор вероятности
            prob_score = probabilities["tp1"]
            scores.append(prob_score)
            
            # Взвешенное среднее
            weights = [0.3, 0.3, 0.2, 0.2]  # Структура, история, рынок, вероятность
            confidence = sum(score * weight for score, weight in zip(scores, weights))
            
            return round(confidence, 1)
            
        except Exception as e:
            logger.error(f"❌ Error calculating confidence score: {e}")
            return 50.0
    
    async def _save_analysis_to_db(self, analysis: SignalAnalysis):
        """Сохранение анализа в базу"""
        try:
            if not self.supabase:
                return
            
            analysis_data = {
                "signal_id": analysis.signal_id,
                "trader_id": analysis.trader_id,
                "symbol": analysis.symbol,
                "tp1_probability": analysis.tp1_probability,
                "tp2_probability": analysis.tp2_probability,
                "sl_probability": analysis.sl_probability,
                "confidence_score": analysis.confidence_score,
                "rr_ratio_tp1": analysis.rr_ratio_tp1,
                "rr_ratio_tp2": analysis.rr_ratio_tp2,
                "risk_distance": analysis.risk_distance,
                "market_conditions": {
                    "volatility": analysis.market_volatility,
                    "trend": analysis.market_trend,
                    "volume_spike": analysis.volume_spike,
                    "momentum": analysis.price_momentum
                },
                "confidence_factors": analysis.confidence_factors,
                "risk_factors": analysis.risk_factors,
                "similar_signals_count": analysis.similar_signals_count,
                "similar_signals_success_rate": analysis.similar_signals_success_rate,
                "analysis_time": analysis.analysis_time.isoformat()
            }
            
            # Создаем таблицу если её нет
            result = self.supabase.table("signal_analysis").upsert(
                analysis_data,
                on_conflict="signal_id"
            ).execute()
            
            if result.data:
                logger.debug(f"💾 Analysis saved for signal {analysis.signal_id}")
            
        except Exception as e:
            logger.error(f"❌ Error saving analysis: {e}")
    
    async def get_trader_insights(self, trader_id: str) -> Dict[str, Any]:
        """Получение инсайтов по трейдеру"""
        try:
            if not self.supabase:
                return {}
            
            # Получаем все анализы трейдера
            result = self.supabase.table("signal_analysis") \
                .select("*") \
                .eq("trader_id", trader_id) \
                .order("analysis_time", desc=True) \
                .execute()
            
            analyses = result.data or []
            
            if not analyses:
                return {"message": "No analysis data available"}
            
            # Агрегируем инсайты
            avg_tp1_prob = np.mean([a["tp1_probability"] for a in analyses])
            avg_confidence = np.mean([a["confidence_score"] for a in analyses])
            avg_rr = np.mean([a["rr_ratio_tp1"] for a in analyses])
            
            # Наиболее частые факторы
            all_confidence_factors = []
            all_risk_factors = []
            
            for a in analyses:
                all_confidence_factors.extend(a.get("confidence_factors", []))
                all_risk_factors.extend(a.get("risk_factors", []))
            
            from collections import Counter
            top_confidence = Counter(all_confidence_factors).most_common(3)
            top_risks = Counter(all_risk_factors).most_common(3)
            
            return {
                "trader_id": trader_id,
                "total_analyses": len(analyses),
                "avg_tp1_probability": round(avg_tp1_prob, 1),
                "avg_confidence_score": round(avg_confidence, 1),
                "avg_rr_ratio": round(avg_rr, 2),
                "top_confidence_factors": [{"factor": f, "count": c} for f, c in top_confidence],
                "top_risk_factors": [{"factor": f, "count": c} for f, c in top_risks],
                "last_analysis": analyses[0]["analysis_time"] if analyses else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting trader insights: {e}")
            return {"error": str(e)}


# Глобальный экземпляр
signal_analyzer = None

def get_signal_analyzer(supabase_client: Optional[Client] = None) -> AdvancedSignalAnalyzer:
    """Получение глобального экземпляра анализатора"""
    global signal_analyzer
    if signal_analyzer is None:
        signal_analyzer = AdvancedSignalAnalyzer(supabase_client)
    return signal_analyzer


# Тестирование
async def test_signal_analyzer():
    """Тестирование анализатора сигналов"""
    print("🧪 ТЕСТИРОВАНИЕ ADVANCED SIGNAL ANALYZER")
    print("=" * 60)
    
    analyzer = get_signal_analyzer()
    
    # Тестовый сигнал
    test_signal = {
        "signal_id": "test_001",
        "trader_id": "slivaeminfo",
        "symbol": "BTCUSDT",
        "entry": 65000,
        "tp1": 67000,
        "tp2": 69000,
        "sl": 63000,
        "side": "BUY"
    }
    
    print(f"📊 Analyzing signal: {test_signal}")
    
    # Анализируем
    analysis = await analyzer.analyze_signal(test_signal)
    
    print(f"\n🎯 РЕЗУЛЬТАТЫ АНАЛИЗА:")
    print(f"   TP1 Probability: {analysis.tp1_probability}%")
    print(f"   TP2 Probability: {analysis.tp2_probability}%")
    print(f"   SL Probability: {analysis.sl_probability}%")
    print(f"   Confidence Score: {analysis.confidence_score}")
    print(f"   R/R Ratio: {analysis.rr_ratio_tp1}")
    print(f"   Risk Distance: {analysis.risk_distance}%")
    
    print(f"\n✅ Confidence Factors:")
    for factor in analysis.confidence_factors:
        print(f"   + {factor}")
    
    print(f"\n⚠️ Risk Factors:")
    for factor in analysis.risk_factors:
        print(f"   - {factor}")
    
    print(f"\n📈 Market Conditions:")
    print(f"   Trend: {analysis.market_trend}")
    print(f"   Volatility: {analysis.market_volatility}%")
    print(f"   Volume Spike: {analysis.volume_spike}")
    
    print("\n✅ Analysis completed!")


if __name__ == "__main__":
    asyncio.run(test_signal_analyzer())
