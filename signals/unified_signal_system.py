"""
GHOST Unified Signal System
Гибридная система парсинга сигналов на основе лучших решений:
- Собственные разработки (TraderDetector, ParserFactory)
- Боевой опыт Дарена (специализированные парсеры)
- Modern best practices (AI fallback, adaptive parsing)
"""

import asyncio
import logging
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Импорты наших компонентов
from signals.trader_detector import TraderDetector, TraderStyle
from signals.parsers.parser_factory import ParserFactory

logger = logging.getLogger(__name__)

class SignalStatus(Enum):
    """Статусы обработки сигнала"""
    RAW = "raw"
    PARSED = "parsed"
    AI_PARSED = "ai_parsed"
    FAILED = "failed"
    VALIDATED = "validated"

class SignalSource(Enum):
    """Источники сигналов"""
    TELEGRAM_WHALESGUIDE = "telegram_whalesguide"
    TELEGRAM_2TRADE = "telegram_2trade"
    TELEGRAM_CRYPTO_HUB = "telegram_crypto_hub"
    TELEGRAM_COINPULSE = "telegram_coinpulse"
    DISCORD_VIP = "discord_vip"
    UNKNOWN = "unknown"

@dataclass
class UnifiedSignal:
    """Универсальная структура сигнала"""
    # Идентификация
    signal_id: str
    raw_id: str
    trader_id: str
    source: SignalSource
    raw_text: str
    
    # Временные метки
    received_at: datetime
    parsed_at: Optional[datetime] = None
    
    # Исходные данные
    original_message_id: Optional[str] = None
    
    # Торговые данные
    symbol: str = ""
    raw_symbol: Optional[str] = None
    side: str = ""  # LONG/SHORT
    
    # Вход
    entry_type: str = "range"  # range, market, limit
    entry_single: Optional[float] = None
    entry_min: Optional[float] = None
    entry_max: Optional[float] = None
    entry_zone: Optional[List[float]] = None
    avg_entry_price: Optional[float] = None
    
    # Цели (гибкая структура под любое количество)
    targets: List[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    tp4: Optional[float] = None
    tp5: Optional[float] = None
    tp6: Optional[float] = None
    tp7: Optional[float] = None
    
    # Риск-менеджмент
    sl: Optional[float] = None
    sl_type: str = "fixed"  # fixed, trailing, be
    
    # Плечо и объем
    leverage: Optional[str] = None
    source_leverage: Optional[str] = None
    volume_split: Optional[str] = None  # как трейдер делит объем
    
    # Метаданные парсинга
    parser_type: str = "unknown"
    parsing_method: str = "rule_based"  # rule_based, ai_assisted, hybrid
    confidence: float = 0.0
    
    # AI-ассистированный парсинг
    ai_used: bool = False
    ai_model: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_explanation: Optional[str] = None
    
    # Детекция трейдера
    detected_trader_style: Optional[str] = None
    detection_confidence: Optional[float] = None
    
    # Статус и валидация
    status: SignalStatus = SignalStatus.RAW
    is_valid: bool = False
    validation_errors: List[str] = None
    
    # Дополнительная информация
    reason: Optional[str] = None
    note: Optional[str] = None
    
    def __post_init__(self):
        if self.targets is None:
            self.targets = []
        if self.entry_zone is None:
            self.entry_zone = []
        if self.validation_errors is None:
            self.validation_errors = []
        
        # Автоматическое заполнение некоторых полей
        if not self.signal_id:
            self.signal_id = self.generate_signal_id()
        
        # Заполняем отдельные TP поля из targets
        self._populate_tp_fields()
        
        # Вычисляем среднюю цену входа
        self._calculate_avg_entry()
    
    def generate_signal_id(self) -> str:
        """Генерирует уникальный ID сигнала"""
        timestamp = self.received_at.strftime("%Y%m%d_%H%M%S")
        text_hash = hashlib.md5(self.raw_text.encode()).hexdigest()[:8]
        return f"{self.trader_id}_{timestamp}_{text_hash}"
    
    def _populate_tp_fields(self):
        """Заполняет отдельные TP поля из списка targets"""
        tp_fields = ['tp1', 'tp2', 'tp3', 'tp4', 'tp5', 'tp6', 'tp7']
        for i, target in enumerate(self.targets[:7]):
            setattr(self, tp_fields[i], target)
    
    def _calculate_avg_entry(self):
        """Вычисляет среднюю цену входа"""
        if self.entry_zone and len(self.entry_zone) >= 2:
            self.entry_min = min(self.entry_zone)
            self.entry_max = max(self.entry_zone)
            self.avg_entry_price = (self.entry_min + self.entry_max) / 2
        elif self.entry_single:
            self.avg_entry_price = self.entry_single
            self.entry_min = self.entry_single
            self.entry_max = self.entry_single

class UnifiedSignalParser:
    """Объединенный парсер сигналов"""
    
    def __init__(self):
        # Компоненты системы
        self.trader_detector = TraderDetector()
        self.parser_factory = ParserFactory()
        
        # Специализированные парсеры (только лучшие и рабочие)
        self.specialized_parsers = {
            "whales_guide": self._parse_whales_guide_signal,
            "cryptoattack24": self._parse_cryptoattack24_signal,
            "2trade": self._parse_2trade_signal,
            "crypto_hub": self._parse_crypto_hub_signal
        }
        
        # Импортируем внешний парсер CryptoAttack24
        self.cryptoattack24_parser = None
        try:
            import sys
            import os
            from signals.parsers.cryptoattack24_parser import CryptoAttack24Parser
            self.cryptoattack24_parser = CryptoAttack24Parser()
            logger.info("✅ CryptoAttack24Parser loaded successfully")
        except ImportError as e:
            logger.warning(f"⚠️ CryptoAttack24Parser not available: {e}")
        
        # AI клиенты для fallback
        self.ai_clients = {}
        self._initialize_ai_clients()
        
        # Статистика
        self.stats = {
            "total_signals": 0,
            "parsed_by_rules": 0,
            "parsed_by_ai": 0,
            "failed_parsing": 0,
            "avg_confidence": 0.0
        }
        
        logger.info("Unified Signal Parser initialized")
    
    def _initialize_ai_clients(self):
        """Инициализация AI клиентов для fallback парсинга"""
        try:
            # OpenAI GPT
            import openai
            self.ai_clients['openai'] = openai
            
            # Google Gemini (если доступен)
            try:
                import google.generativeai as genai
                self.ai_clients['gemini'] = genai
            except ImportError:
                pass
                
        except ImportError:
            logger.warning("AI clients not available - install openai and google-generativeai")
    
    async def parse_signal(self, raw_text: str, source: SignalSource, 
                          trader_id: Optional[str] = None,
                          message_id: Optional[str] = None) -> Optional[UnifiedSignal]:
        """Главная функция парсинга сигнала"""
        
        # Создаем базовый объект сигнала
        signal = UnifiedSignal(
            signal_id="",  # будет сгенерирован автоматически
            raw_id=f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            trader_id=trader_id or "unknown",
            source=source,
            received_at=datetime.now(),
            raw_text=raw_text,
            original_message_id=message_id,
            symbol="",  # будет заполнен парсером
            side=""     # будет заполнен парсером
        )
        
        self.stats["total_signals"] += 1
        
        try:
            # Этап 1: Автоматическое определение трейдера (если не указан)
            if not trader_id or trader_id == "unknown":
                detected_style, detection_conf, details = self.trader_detector.detect_trader(raw_text)
                signal.trader_id = self.trader_detector.get_trader_id(detected_style, source.value)
                signal.detected_trader_style = detected_style.value
                signal.detection_confidence = detection_conf
                
                logger.debug(f"Detected trader: {signal.trader_id} (confidence: {detection_conf:.2f})")
            
            # Этап 2: Парсинг специализированными парсерами
            parsing_success = await self._try_specialized_parsing(signal)
            
            if parsing_success:
                signal.parsing_method = "rule_based"
                signal.status = SignalStatus.PARSED
                self.stats["parsed_by_rules"] += 1
                logger.info(f"✅ Rule-based parsing successful: {signal.symbol} {signal.side}")
            else:
                # Этап 3: AI Fallback парсинг
                ai_success = await self._try_ai_parsing(signal)
                
                if ai_success:
                    signal.parsing_method = "ai_assisted"
                    signal.status = SignalStatus.AI_PARSED
                    signal.ai_used = True
                    self.stats["parsed_by_ai"] += 1
                    logger.info(f"🤖 AI parsing successful: {signal.symbol} {signal.side}")
                else:
                    signal.status = SignalStatus.FAILED
                    self.stats["failed_parsing"] += 1
                    logger.warning(f"❌ All parsing methods failed")
                    return None
            
            # Этап 4: Постобработка и валидация
            self._post_process_signal(signal)
            
            # Этап 5: Валидация
            signal.is_valid = self._validate_signal(signal)
            if signal.is_valid:
                signal.status = SignalStatus.VALIDATED
            
            # Обновляем статистику
            self._update_stats(signal)
            
            signal.parsed_at = datetime.now()
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            signal.status = SignalStatus.FAILED
            signal.validation_errors.append(str(e))
            return signal
    
    async def _try_specialized_parsing(self, signal: UnifiedSignal) -> bool:
        """Попытка парсинга специализированными парсерами"""
        
        # Определяем тип парсера по источнику и трейдеру
        parser_candidates = []
        
        if "2trade" in signal.trader_id.lower():
            parser_candidates.append("2trade")
        elif "crypto_hub" in signal.trader_id.lower():
            parser_candidates.append("crypto_hub")
        elif "coinpulse" in signal.trader_id.lower():
            parser_candidates.append("coinpulse")
        elif "whales" in signal.trader_id.lower():
            parser_candidates.append("whales_guide")
        elif "cryptoattack24" in signal.trader_id.lower():
            parser_candidates.append("cryptoattack24")
        
        # Добавляем fallback парсеры
        parser_candidates.extend(["whales_guide", "2trade", "crypto_hub"])
        
        # Пробуем каждый парсер
        for parser_type in parser_candidates:
            try:
                parser_func = self.specialized_parsers.get(parser_type)
                if parser_func:
                    result = parser_func(signal.raw_text)
                    
                    if result and self._is_valid_parse_result(result):
                        # Переносим данные в unified signal
                        self._transfer_parse_data(result, signal, parser_type)
                        return True
                        
            except Exception as e:
                logger.debug(f"Parser {parser_type} failed: {e}")
                continue
        
        return False
    
    async def _try_ai_parsing(self, signal: UnifiedSignal) -> bool:
        """AI-ассистированный парсинг как fallback"""
        
        if not self.ai_clients:
            return False
        
        # Пробуем сначала OpenAI
        if 'openai' in self.ai_clients:
            try:
                result = await self._parse_with_openai(signal.raw_text)
                if result:
                    self._transfer_parse_data(result, signal, "openai")
                    signal.ai_model = "gpt-4"
                    return True
            except Exception as e:
                logger.debug(f"OpenAI parsing failed: {e}")
        
        # Fallback на Gemini
        if 'gemini' in self.ai_clients:
            try:
                result = await self._parse_with_gemini(signal.raw_text)
                if result:
                    self._transfer_parse_data(result, signal, "gemini")
                    signal.ai_model = "gemini-pro"
                    return True
            except Exception as e:
                logger.debug(f"Gemini parsing failed: {e}")
        
        return False
    
    async def _parse_with_openai(self, text: str) -> Optional[Dict]:
        """Парсинг через OpenAI GPT"""
        try:
            openai = self.ai_clients['openai']
            
            prompt = f"""
Analyze this trading signal and extract structured data. If this is not a trading signal, return null.

Signal text:
{text}

Extract:
- symbol (trading pair)
- side (LONG/SHORT/BUY/SELL)
- entry (price or range)
- targets (TP levels)
- stop_loss (SL level)
- leverage (if mentioned)
- reason (if provided)

Return as JSON only, no explanation:
{{
    "symbol": "BTCUSDT",
    "side": "LONG",
    "entry": [45000, 46000],
    "targets": [47000, 48000, 49000],
    "stop_loss": 44000,
    "leverage": "10x",
    "reason": "bullish pattern"
}}
"""
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Парсим JSON ответ
            if result_text.startswith('{') and result_text.endswith('}'):
                result = json.loads(result_text)
                return result
                
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
        
        return None
    
    async def _parse_with_gemini(self, text: str) -> Optional[Dict]:
        """Парсинг через Google Gemini"""
        try:
            genai = self.ai_clients['gemini']
            
            # Аналогичный промпт для Gemini
            prompt = f"""
Extract trading signal data from this text. Return JSON only:

{text}

Format: {{"symbol": "BTCUSDT", "side": "LONG", "entry": [45000], "targets": [47000], "stop_loss": 44000}}
"""
            
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async(prompt)
            
            result_text = response.text.strip()
            
            if result_text.startswith('{') and result_text.endswith('}'):
                result = json.loads(result_text)
                return result
                
        except Exception as e:
            logger.error(f"Gemini parsing error: {e}")
        
        return None
    
    def _parse_2trade_signal(self, text: str) -> Optional[Dict]:
        """Парсер 2Trade (по опыту Дарена)"""
        try:
            text = text.upper()
            text = text.replace("—", "-").replace("–", "-").replace("−", "-")
            lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
            text = "\n".join(lines)

            # Symbol и Side
            coin_line = next((l for l in lines if "USDT" in l and ("LONG" in l or "SHORT" in l)), None)
            if not coin_line:
                return None

            symbol_match = re.search(r"([A-Z0-9\-]{2,20})USDT", coin_line)
            if not symbol_match:
                return None

            symbol_raw = symbol_match.group(1).replace("-", "")
            symbol = f"{symbol_raw}USDT"
            side = "LONG" if "LONG" in coin_line else "SHORT"

            # Entry
            entry_match = re.search(r"(ВХОД|ENTRY)(?:\s*ZONE)?[:=]?\s*([\d\.]+)", text)
            if not entry_match:
                return None

            entry_val = float(entry_match.group(2))
            entry_padding = entry_val * 0.003  # ±0.3%
            entry = [entry_val - entry_padding, entry_val + entry_padding]

            # Targets
            targets = []
            entry_idx = next(i for i, l in enumerate(lines) if "ВХОД" in l or "ENTRY" in l)
            for line in lines[entry_idx + 1:]:
                if any(x in line for x in ["СТОП", "STOP", "SL"]):
                    break
                try:
                    val = float(line.strip())
                    targets.append(val)
                except:
                    continue

            # Stop Loss
            sl_match = re.search(r"(СТОП|STOP LOSS|SL|STOP)[:=]?\s*([\d\.]+)", text)
            sl = float(sl_match.group(2)) if sl_match else None

            return {
                "symbol": symbol,
                "side": side,
                "entry": entry,
                "targets": targets,
                "stop_loss": sl,
                "source_type": "2trade"
            }

        except Exception as e:
            logger.debug(f"2Trade parser error: {e}")
            return None
    
    def _parse_crypto_hub_signal(self, text: str) -> Optional[Dict]:
        """Парсер Crypto Hub (по опыту Дарена)"""
        try:
            text = text.upper()
            text = text.replace("—", "-").replace("–", "-").replace("−", "-")

            # Symbol
            coin_match = re.search(r"([A-Z]{2,15})[\/\s\-]?USDT", text)
            if not coin_match:
                coin_match = re.search(r"\$([A-Z]{2,15})", text)
            if not coin_match:
                return None

            symbol = f"{coin_match.group(1)}USDT"

            # Entry
            entry_match = re.search(r"ENTRY(?:\s*ZONE)?\s*[:=]?\s*([\d\.]+)\s*[-/]\s*([\d\.]+)", text)
            if not entry_match:
                return None

            entry = [float(entry_match.group(1)), float(entry_match.group(2))]

            # Targets
            targets = []
            tp1_match = re.search(r"TP1[:=]?\s*([\d\.]+)", text)
            tp2_match = re.search(r"TP2[:=]?\s*([\d\.]+)", text)
            tp3_match = re.search(r"TP3[:=]?\s*([\d\.]+)", text)
            
            if tp1_match:
                targets.append(float(tp1_match.group(1)))
            if tp2_match:
                targets.append(float(tp2_match.group(1)))
            if tp3_match:
                targets.append(float(tp3_match.group(1)))

            # Stop Loss
            sl_match = re.search(r"(STOP LOSS|SL)[:=]?\s*([\d\.]+)", text)
            sl = float(sl_match.group(2)) if sl_match else None

            # Side
            side = "SHORT" if "SHORT" in text else "LONG"

            # Leverage
            lev_match = re.search(r"(\d{1,3})X", text)
            leverage = f"{lev_match.group(1)}x" if lev_match else None

            return {
                "symbol": symbol,
                "side": side,
                "entry": entry,
                "targets": targets,
                "stop_loss": sl,
                "leverage": leverage,
                "source_type": "crypto_hub"
            }

        except Exception as e:
            logger.debug(f"Crypto Hub parser error: {e}")
            return None
    
    def _parse_coinpulse_signal(self, text: str) -> Optional[Dict]:
        """Парсер CoinPulse (по опыту Дарена)"""
        try:
            text = text.upper()
            text = text.replace("：", ":").replace("–", "-").replace("—", "-")

            # Symbol
            match = re.search(r"PAIR[:\s]+([A-Z]+)\/([A-Z]+)", text)
            if not match:
                return None
            
            symbol = f"{match.group(1)}{match.group(2)}"

            # Side
            if "#LONG" in text:
                side = "LONG"
            elif "#SHORT" in text:
                side = "SHORT"
            else:
                return None

            # Entry
            entry_match = re.search(r"ENTRY[:\s]+([\d\.]+)\s*[-]\s*([\d\.]+)", text)
            if not entry_match:
                return None
            
            entry_low = float(entry_match.group(1))
            entry_high = float(entry_match.group(2))
            entry = [min(entry_low, entry_high), max(entry_low, entry_high)]

            # Stop Loss
            sl_match = re.search(r"STOPLOSS[:\s]+([\d\.]+)", text)
            sl = float(sl_match.group(1)) if sl_match else None

            return {
                "symbol": symbol,
                "side": side,
                "entry": entry,
                "targets": [],  # CoinPulse обычно без targets
                "stop_loss": sl,
                "source_type": "coinpulse"
            }

        except Exception as e:
            logger.debug(f"CoinPulse parser error: {e}")
            return None
    
    def _parse_whales_guide_signal(self, text: str) -> Optional[Dict]:
        """Улучшенный парсер Whales Guide - извлекает данные из ВСЕХ типов сообщений"""
        try:
            import re
            
            text_upper = text.upper()
            text_clean = re.sub(r'[^\w\s\.\$\-\#\:\(\)\/]', ' ', text_upper)
            
            # Извлекаем символ криптовалюты (множественные паттерны)
            symbol = self._extract_symbol_comprehensive(text_clean)
            if not symbol:
                return None
            
            # Определяем направление (LONG/SHORT или анализируем контекст)
            side = self._extract_direction_comprehensive(text_clean)
            
            # Извлекаем цены и уровни
            prices = self._extract_all_prices(text)
            
            # Извлекаем entry зоны
            entry = self._extract_entry_comprehensive(text_clean, prices)
            
            # Извлекаем targets
            targets = self._extract_targets_comprehensive(text_clean, prices)
            
            # Извлекаем stop loss
            stop_loss = self._extract_stop_loss_comprehensive(text_clean, prices)
            
            # Извлекаем leverage
            leverage = self._extract_leverage_comprehensive(text_clean)
            
            # Извлекаем дополнительную информацию
            analysis = self._extract_market_analysis(text)
            
            # Если не удалось извлечь основные торговые данные, сохраняем как анализ
            if not entry and not targets and not stop_loss:
                if symbol and (side or analysis):
                    return {
                        "symbol": symbol,
                        "side": side or "ANALYSIS",
                        "entry": [],
                        "targets": [],
                        "stop_loss": None,
                        "leverage": leverage,
                        "analysis": analysis,
                        "message_type": "market_analysis",
                        "source_type": "whales_guide"
                    }
            
            # Стандартный торговый сигнал
            if symbol and side and (entry or targets):
                return {
                    "symbol": symbol,
                    "side": side,
                    "entry": entry or [],
                    "targets": targets or [],
                    "stop_loss": stop_loss,
                    "leverage": leverage,
                    "analysis": analysis,
                    "message_type": "trading_signal",
                        "source_type": "whales_guide"
                    }
            
            return None

        except Exception as e:
            logger.debug(f"Whales Guide enhanced parser error: {e}")
            return None
    
    def _parse_cryptoattack24_signal(self, text: str) -> Optional[Dict]:
        """Парсер для КриптоАтака 24 - использует специализированный парсер"""
        if self.cryptoattack24_parser:
            try:
                result = self.cryptoattack24_parser.parse_message(text)
                if result:
                    return {
                        "symbol": result.symbol,
                        "side": "LONG" if result.action in ["pump", "growth"] else "NEWS",
                        "entry": [],
                        "targets": [],
                        "stop_loss": None,
                        "leverage": None,
                        "analysis": result.context,
                        "price_movement": result.price_movement,
                        "exchange": result.exchange,
                        "sector": result.sector,
                        "message_type": "news_signal",
                        "source_type": "cryptoattack24"
                    }
            except Exception as e:
                logger.debug(f"CryptoAttack24 specialized parser error: {e}")
        
        # Fallback к простому парсингу
        return self._parse_cryptoattack24_fallback(text)
    
    def _parse_cryptoattack24_fallback(self, text: str) -> Optional[Dict]:
        """Парсер для CryptoAttack24 - новостные сигналы и движения цен"""
        try:
            import re
            
            # Импортируем наш специализированный парсер
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'telegram_parsers'))
            
            try:
                from signals.parsers.cryptoattack24_parser import CryptoAttack24Parser
                parser = CryptoAttack24Parser()
                result = parser.parse_message(text)
                
                if result:
                    # Преобразуем в формат UnifiedSignal
                    return {
                        "symbol": result.symbol,
                        "side": "Buy" if result.action in ["pump", "growth"] else "Analysis",
                        "entry": [],
                        "targets": [],
                        "stop_loss": None,
                        "leverage": None,
                        "analysis": result.context,
                        "message_type": "news_signal" if result.action == "pump" else "market_analysis",
                        "source_type": "cryptoattack24",
                        "confidence": result.confidence,
                        "price_movement": result.price_movement,
                        "exchange": result.exchange,
                        "sector": result.sector
                    }
                    
            except ImportError:
                logger.debug("CryptoAttack24Parser not available, using fallback")
                
                # Fallback парсинг
                text_lower = text.lower()
                
                # Поиск символа
                symbol_match = re.search(r'#?([A-Z]{2,10})\b', text.upper())
                if symbol_match:
                    symbol = symbol_match.group(1)
                    
                    # Определяем тип события
                    if any(word in text_lower for word in ['запампили', 'рост', 'выросли']):
                        action_type = "pump"
                    elif any(word in text_lower for word in ['закрепился', 'топе', 'первое место']):
                        action_type = "consolidation"
                    else:
                        action_type = "news"
                    
                    # Поиск процентного движения
                    price_match = re.search(r'\+(\d+)%', text)
                    price_movement = price_match.group(0) if price_match else None
                    
                    return {
                        "symbol": symbol,
                        "side": "Buy" if action_type == "pump" else "Analysis",
                        "entry": [],
                        "targets": [],
                        "stop_loss": None,
                        "leverage": None,
                        "analysis": text[:100],
                        "message_type": "news_signal",
                        "source_type": "cryptoattack24",
                        "confidence": 0.7,
                        "price_movement": price_movement
                    }
            
            return None

        except Exception as e:
            logger.debug(f"CryptoAttack24 parser error: {e}")
            return None
    
    def _extract_symbol_comprehensive(self, text: str) -> Optional[str]:
        """Извлечение символа криптовалюты из любого типа сообщения"""
        # Паттерны для поиска символов
        patterns = [
            r'([A-Z]{2,15})USDT',           # BTCUSDT
            r'([A-Z]{2,15})/USDT',          # BTC/USDT  
            r'([A-Z]{2,15})\s*USDT',        # BTC USDT
            r'\$([A-Z]{2,15})',             # $BTC
            r'#([A-Z]{2,15})',              # #BTC
            r'\b([A-Z]{2,15})\b',           # BTC (отдельное слово)
        ]
        
        # Известные криптовалютные символы (расширенный список)
        crypto_symbols = [
            # Топ криптовалюты
            'BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'DOGE', 'MATIC', 'AVAX',
            'SHIB', 'LTC', 'LINK', 'UNI', 'ATOM', 'XLM', 'VET', 'ICP', 'FIL', 'TRX',
            'ETC', 'FTT', 'NEAR', 'ALGO', 'MANA', 'SAND', 'GALA', 'APE', 'LRC', 'CRV',
            'AAVE', 'MKR', 'COMP', 'SNX', 'YFI', 'SUSHI', 'BAL', 'ZRX', 'KNC', 'REN',
            # Дополнительные токены часто встречающиеNear в Whales Guide
            'BEL', 'BELLA', 'CHZ', 'ENJ', 'FLOW', 'GRT', 'HBAR', 'HOT', 'IOST', 'IOTA',
            'JST', 'KSM', 'KAVA', 'MINA', 'NEO', 'OMG', 'QTUM', 'RUNE', 'STORJ', 'SUSHI',
            'SXP', 'THETA', 'TOMO', 'WAVES', 'WIN', 'ZEC', 'ZIL', 'ONT', 'ICX', 'NANO',
            'DASH', 'DCR', 'DGB', 'RVN', 'BTT', 'CELR', 'COTI', 'DENT', 'FET', 'FTM',
            'HIVE', 'IOTX', 'KEY', 'LOOM', 'NKN', 'NMR', 'NULS', 'OGN', 'ONE', 'OXT',
            'PERP', 'PUNDIX', 'REEF', 'RSR', 'SKL', 'SLP', 'STMX', 'SUN', 'TLM', 'TROY',
            'UNFI', 'UTK', 'WAN', 'WRX', 'ALPHA', 'ANKR', 'ARDR', 'ARPA', 'AUDIO', 'BAND',
            'BAT', 'BEAM', 'BICO', 'BLKZ', 'BNT', 'BOND', 'BTS', 'BURGER', 'BZRX', 'C98',
            'CAKE', 'CHR', 'CKB', 'CLV', 'COCOS', 'COS', 'CTK', 'CTXC', 'CVP', 'DATA',
            'DF', 'DIA', 'DOCK', 'DODO', 'DUSK', 'DYDX', 'EGGG', 'ELF', 'ERN', 'FIRO'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match in crypto_symbols:
                    return f"{match}USDT"
        
        return None
    
    def _extract_direction_comprehensive(self, text: str) -> Optional[str]:
        """Определение направления торговли"""
        # Явные указания (английский + русский)
        long_keywords = ['LONG', 'LONGING', 'BUY', 'BUYING', 'ПОКУПАЕМ', 'ПОКУПАТЬ', 'ЛОНГ', 'ПОКУПКА']
        short_keywords = ['SHORT', 'SHORTING', 'SELL', 'SELLING', 'ПРОДАЕМ', 'ПРОДАТЬ', 'ШОРТ', 'ПРОДАЖА']
        
        if any(word in text for word in long_keywords):
            return "LONG"
        if any(word in text for word in short_keywords):
            return "SHORT"
        
        # Анализ контекста
        bullish_words = ['PUMP', 'MOON', 'BULLISH', 'UP', 'RISE', 'INCREASE', 'BREAKOUT']
        bearish_words = ['DUMP', 'CRASH', 'BEARISH', 'DOWN', 'FALL', 'DECREASE', 'BREAKDOWN']
        
        bullish_count = sum(1 for word in bullish_words if word in text)
        bearish_count = sum(1 for word in bearish_words if word in text)
        
        if bullish_count > bearish_count and bullish_count > 0:
            return "LONG"
        elif bearish_count > bullish_count and bearish_count > 0:
            return "SHORT"
        
        return None
    
    def _extract_all_prices(self, text: str) -> List[float]:
        """Извлечение всех цен из текста"""
        import re
        
        prices = []
        
        # Паттерны для цен
        price_patterns = [
            r'\$\s*(\d+\.?\d*)',           # $45000.50
            r'\$\s*(\d*\.\d{4,8})',        # $0.2793
            r'(\d+\.\d{4,8})',             # 0.2793
            r'(\d+\.\d{2,3})',             # 45000.12
            r'(\d{4,})',                   # 45000
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if 0.000001 <= price <= 1000000:  # Разумные пределы
                        prices.append(price)
                except:
                    continue
        
        return sorted(list(set(prices)))  # Убираем дубликаты и сортируем
    
    def _extract_entry_comprehensive(self, text: str, prices: List[float]) -> List[float]:
        """Извлечение зон входа"""
        import re
        
        # Поиск явных указаний entry (английский + русский)
        entry_patterns = [
            r'ENTRY[:\s]+(\d+\.?\d*)\s*[-/]\s*(\d+\.?\d*)',  # ENTRY: 45000-46000
            r'ENTRY[:\s]+(\d+\.?\d*)',                       # ENTRY: 45000
            r'BUY[:\s]+(\d+\.?\d*)\s*[-/]\s*(\d+\.?\d*)',   # BUY: 45000-46000
            r'BUY[:\s]+(\d+\.?\d*)',                         # BUY: 45000
            r'ВХОД[:\s]+(\d+\.?\d*)\s*[-/]\s*(\d+\.?\d*)',  # ВХОД: 45000-46000
            r'ВХОД[:\s]+(\d+\.?\d*)',                        # ВХОД: 45000
            r'ENTRY ZONE[:\s]+\$?(\d+\.?\d*)\s*[-/]\s*\$?(\d+\.?\d*)',  # Entry Zone: $95.50 - $96.20
        ]
        
        for pattern in entry_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:
                    return [float(match.group(1)), float(match.group(2))]
                else:
                    return [float(match.group(1))]
        
        # Если нет явных указаний, используем первые цены
        if prices and len(prices) >= 2:
            return prices[:2]
        elif prices:
            return [prices[0]]
        
        return []
    
    def _extract_targets_comprehensive(self, text: str, prices: List[float]) -> List[float]:
        """Извлечение целевых уровней"""
        import re
        
        targets = []
        
        # Поиск TP уровней (английский + русский)
        tp_patterns = [
            r'TP\s*(\d+)[:\s]+\$?(\d+\.?\d*)',  # TP1: 47000, TP1: $47000
            r'TARGET[:\s]+\$?(\d+\.?\d*)',       # TARGET: 47000
            r'TARGETS[:\s]+\$?(\d+\.?\d*)',      # TARGETS: 46000, 47000, 48000
            r'PROFIT[:\s]+\$?(\d+\.?\d*)',       # PROFIT: 47000
            r'ЦЕЛИ[:\s]+(\d+\.?\d*)',            # ЦЕЛИ: 46000, 47000
            r'ЦЕЛЬ[:\s]+(\d+\.?\d*)',            # ЦЕЛЬ: 46000
            r'🎯\s*TP\s*(\d+)[:\s]+\$?(\d+\.?\d*)',  # 🎯 TP1: $98.00
        ]
        
        for pattern in tp_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    if len(match.groups()) == 2:
                        targets.append(float(match.group(2)))
                    else:
                        targets.append(float(match.group(1)))
                except:
                    continue
        
        # Если нет явных TP, используем высокие цены
        if not targets and prices:
            # Берем цены выше среднего как потенциальные targets
            if len(prices) > 2:
                avg_price = sum(prices) / len(prices)
                targets = [p for p in prices if p > avg_price]
        
        return sorted(targets)
    
    def _extract_stop_loss_comprehensive(self, text: str, prices: List[float]) -> Optional[float]:
        """Извлечение уровня стоп-лосса"""
        import re
        
        # Поиск явных указаний SL
        sl_patterns = [
            r'(STOP LOSS|STOPLOSS|SL)[:\s]+(\d+\.?\d*)',  # SL: 43000
            r'STOP[:\s]+(\d+\.?\d*)',                      # STOP: 43000
        ]
        
        for pattern in sl_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(-1))  # Последняя группа
                except:
                    continue
        
        # Если нет явного SL, используем самую низкую цену
        if prices:
            return min(prices)
        
        return None
    
    def _extract_leverage_comprehensive(self, text: str) -> Optional[str]:
        """Извлечение плеча"""
        import re
        
        patterns = [
            r'(\d{1,3})X',           # 10X
            r'LEVERAGE[:\s]+(\d+)',  # LEVERAGE: 10
            r'LEV[:\s]+(\d+)',       # LEV: 10
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"{match.group(1)}x"
        
        return None
    
    def _extract_market_analysis(self, text: str) -> Optional[str]:
        """Извлечение рыночного анализа из сообщения"""
        # Ключевые фразы анализа
        analysis_indicators = [
            'analysis', 'outlook', 'prediction', 'forecast', 'trend', 'pattern',
            'support', 'resistance', 'breakout', 'breakdown', 'consolidation',
            'bullish', 'bearish', 'neutral', 'overbought', 'oversold'
        ]
        
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in analysis_indicators):
            # Возвращаем первые 200 символов как краткий анализ
            return text[:200].strip()
        
            return None
    
    def _is_valid_parse_result(self, result: Dict) -> bool:
        """Проверка валидности результата парсинга"""
        required_fields = ["symbol", "side"]
        
        for field in required_fields:
            if field not in result or not result[field]:
                return False
        
        # Должен быть хотя бы entry или targets
        has_entry = "entry" in result and result["entry"]
        has_targets = "targets" in result and result["targets"]
        
        return has_entry or has_targets
    
    def _transfer_parse_data(self, result: Dict, signal: UnifiedSignal, parser_type: str):
        """Перенос данных из результата парсинга в UnifiedSignal"""
        
        signal.parser_type = parser_type
        
        # Основные поля
        signal.symbol = result.get("symbol", "")
        signal.side = result.get("side", "")
        
        # Entry данные
        entry = result.get("entry", [])
        if isinstance(entry, list) and len(entry) >= 2:
            signal.entry_zone = entry
            signal.entry_type = "range"
        elif isinstance(entry, (int, float)):
            signal.entry_single = float(entry)
            signal.entry_type = "market"
        elif isinstance(entry, list) and len(entry) == 1:
            signal.entry_single = float(entry[0])
            signal.entry_type = "market"
        
        # Targets
        targets = result.get("targets", [])
        if targets:
            signal.targets = [float(t) for t in targets if t]
        
        # Stop Loss
        if "stop_loss" in result and result["stop_loss"]:
            signal.sl = float(result["stop_loss"])
        
        # Дополнительные поля
        signal.leverage = result.get("leverage")
        signal.reason = result.get("reason")
        
        # AI-специфичные поля
        if parser_type in ["openai", "gemini"]:
            signal.ai_confidence = result.get("confidence", 0.8)
            signal.ai_explanation = result.get("explanation", "AI parsed")
    
    def _post_process_signal(self, signal: UnifiedSignal):
        """Постобработка сигнала"""
        
        # Нормализация символа
        if signal.symbol and not signal.symbol.endswith("USDT"):
            if "/" in signal.symbol:
                base, quote = signal.symbol.split("/")
                signal.symbol = f"{base}{quote}"
            else:
                signal.symbol = f"{signal.symbol}USDT"
        
        # Нормализация стороны
        if signal.side.upper() in ["BUY", "LONG"]:
            signal.side = "LONG"
        elif signal.side.upper() in ["SELL", "SHORT"]:
            signal.side = "SHORT"
        
        # Расчет confidence
        confidence_factors = []
        
        if signal.symbol:
            confidence_factors.append(0.3)
        if signal.side:
            confidence_factors.append(0.2)
        if signal.entry_zone or signal.entry_single:
            confidence_factors.append(0.2)
        if signal.targets:
            confidence_factors.append(0.2)
        if signal.sl:
            confidence_factors.append(0.1)
        
        signal.confidence = sum(confidence_factors) * 100
        
        # AI confidence override
        if signal.ai_used and signal.ai_confidence:
            signal.confidence = signal.ai_confidence * 100
    
    def _validate_signal(self, signal: UnifiedSignal) -> bool:
        """Валидация сигнала"""
        errors = []
        
        # Обязательные поля
        if not signal.symbol:
            errors.append("Symbol is required")
        
        if not signal.side:
            errors.append("Side is required")
        
        # Логическая валидация
        if signal.side == "LONG":
            # Для LONG: TP должны быть выше entry, SL ниже
            entry_price = signal.avg_entry_price or 0
            
            if entry_price > 0:  # Только если entry определен
                if signal.targets:
                    for i, tp in enumerate(signal.targets):
                        if tp <= entry_price:
                            errors.append(f"TP{i+1} should be higher than entry for LONG")
                
                if signal.sl and signal.sl >= entry_price:
                    errors.append("SL should be lower than entry for LONG")
        
        elif signal.side == "SHORT":
            # Для SHORT: TP должны быть ниже entry, SL выше
            entry_price = signal.avg_entry_price or 0
            
            if entry_price > 0:  # Только если entry определен
                if signal.targets:
                    for i, tp in enumerate(signal.targets):
                        if tp >= entry_price:
                            errors.append(f"TP{i+1} should be lower than entry for SHORT")
                
                if signal.sl and signal.sl <= entry_price:
                    errors.append("SL should be higher than entry for SHORT")
        
        signal.validation_errors = errors
        return len(errors) == 0
    
    def _update_stats(self, signal: UnifiedSignal):
        """Обновление статистики"""
        confidences = []
        
        if hasattr(self, '_confidence_history'):
            self._confidence_history.append(signal.confidence)
        else:
            self._confidence_history = [signal.confidence]
        
        # Скользящее среднее по последним 100 сигналам
        recent_confidences = self._confidence_history[-100:]
        self.stats["avg_confidence"] = sum(recent_confidences) / len(recent_confidences)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики парсера"""
        return self.stats.copy()


# Глобальный экземпляр unified парсера
unified_parser = UnifiedSignalParser()

def get_unified_parser() -> UnifiedSignalParser:
    """Получение глобального экземпляра парсера"""
    return unified_parser


# Функция для тестирования
async def test_unified_parser():
    """Тестирование unified парсера"""
    print("🧪 ТЕСТИРОВАНИЕ UNIFIED SIGNAL PARSER")
    print("=" * 60)
    
    parser = get_unified_parser()
    
    # Тестовые сигналы разных форматов
    test_signals = [
        {
            "name": "Whales Guide Format",
            "text": """Longing #BTCUSDT Here

Long (5x - 10x)

Entry: $45000 - $44500

Targets: $46000, $47000, $48000

Stoploss: $43000""",
            "source": SignalSource.TELEGRAM_WHALESGUIDE
        },
        {
            "name": "2Trade Format", 
            "text": """BTCUSDT LONG

ВХОД: 45000

47000
48000
49000

СТОП: 43000""",
            "source": SignalSource.TELEGRAM_2TRADE
        },
        {
            "name": "Crypto Hub Format",
            "text": """🔥 ETHUSDT LONG

Entry: 2800 - 2850

TP1: 2900
TP2: 2950

SL: 2750""",
            "source": SignalSource.TELEGRAM_CRYPTO_HUB
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_signals, 1):
        print(f"\n{i}️⃣ ТЕСТ: {test['name']}")
        print("-" * 50)
        
        signal = await parser.parse_signal(
            raw_text=test['text'],
            source=test['source']
        )
        
        if signal and signal.is_valid:
            print(f"✅ SUCCESS:")
            print(f"   Symbol: {signal.symbol}")
            print(f"   Side: {signal.side}")
            print(f"   Entry: {signal.entry_zone or [signal.entry_single]}")
            print(f"   Targets: {signal.targets}")
            print(f"   SL: {signal.sl}")
            print(f"   Parser: {signal.parser_type}")
            print(f"   Method: {signal.parsing_method}")
            print(f"   Confidence: {signal.confidence:.1f}%")
            print(f"   AI Used: {signal.ai_used}")
            results.append(True)
        else:
            print(f"❌ FAILED:")
            if signal:
                print(f"   Errors: {signal.validation_errors}")
            results.append(False)
    
    # Статистика
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"   Успешно: {sum(results)}/{len(results)}")
    print(f"   Статистика парсера: {parser.get_stats()}")
    
    print(f"\n🎉 UNIFIED PARSER READY!")


if __name__ == "__main__":
    asyncio.run(test_unified_parser())
