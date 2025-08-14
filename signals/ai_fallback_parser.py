"""
GHOST AI Fallback Parser
AI-парсер как fallback для нераспознанных сигналов
Реализует идею Дарена: если парсер не сработал → ChatGPT/Gemini разбирает сигнал
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class AIFallbackParser:
    """AI-парсер для fallback обработки сигналов"""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        
        # Инициализируем доступные AI клиенты
        self._initialize_ai_clients()
        
        # Промпты для разных типов AI
        self.prompts = {
            "openai": self._get_openai_prompt(),
            "gemini": self._get_gemini_prompt()
        }
        
        # Статистика AI парсинга
        self.ai_stats = {
            "total_requests": 0,
            "openai_success": 0,
            "gemini_success": 0,
            "failures": 0,
            "avg_confidence": 0.0
        }
        
        logger.info("AI Fallback Parser initialized")
    
    def _initialize_ai_clients(self):
        """Инициализация AI клиентов"""
        
        # OpenAI GPT
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
                self.openai_client = openai
                logger.info("✅ OpenAI client initialized")
            else:
                logger.warning("⚠️ OPENAI_API_KEY not found")
        except ImportError:
            logger.warning("⚠️ OpenAI library not installed")
        
        # Google Gemini
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_client = genai
                logger.info("✅ Gemini client initialized")
            else:
                logger.warning("⚠️ GEMINI_API_KEY not found")
        except ImportError:
            logger.warning("⚠️ Google AI library not installed")
    
    def _get_openai_prompt(self) -> str:
        """Промпт для OpenAI GPT"""
        return """
You are a professional crypto trading signal parser. Analyze the given text and extract trading signal data.

RULES:
1. If the text is NOT a trading signal, return: {"is_signal": false}
2. If it IS a trading signal, extract all available data
3. Always return valid JSON only, no explanations
4. Use null for missing data

REQUIRED FIELDS:
- symbol: trading pair (normalize to format like "BTCUSDT")
- side: "LONG" or "SHORT" 
- entry: price or [min_price, max_price] for range
- targets: array of target prices [tp1, tp2, tp3, ...]
- stop_loss: stop loss price
- leverage: leverage value if mentioned
- reason: trading reason/analysis if provided

EXAMPLE OUTPUT:
{
    "is_signal": true,
    "symbol": "BTCUSDT",
    "side": "LONG", 
    "entry": [45000, 46000],
    "targets": [47000, 48000, 49000],
    "stop_loss": 44000,
    "leverage": "10x",
    "reason": "bullish breakout pattern",
    "confidence": 0.9
}

TEXT TO ANALYZE:
"""
    
    def _get_gemini_prompt(self) -> str:
        """Промпт для Google Gemini"""
        return """
Parse this crypto trading signal. Return JSON only.

Format:
{
  "is_signal": true/false,
  "symbol": "BTCUSDT", 
  "side": "LONG/SHORT",
  "entry": price or [min, max],
  "targets": [tp1, tp2, ...],
  "stop_loss": price,
  "leverage": "Nx",
  "reason": "explanation",
  "confidence": 0.0-1.0
}

If not a trading signal, return: {"is_signal": false}

Text:
"""
    
    async def parse_with_ai(self, text: str, 
                           preferred_ai: str = "openai") -> Optional[Dict[str, Any]]:
        """Основная функция AI парсинга"""
        
        self.ai_stats["total_requests"] += 1
        
        # Попробуем предпочтительный AI
        if preferred_ai == "openai" and self.openai_client:
            result = await self._parse_with_openai(text)
            if result:
                self.ai_stats["openai_success"] += 1
                return result
        
        elif preferred_ai == "gemini" and self.gemini_client:
            result = await self._parse_with_gemini(text)
            if result:
                self.ai_stats["gemini_success"] += 1
                return result
        
        # Fallback на другой AI
        if preferred_ai == "openai" and self.gemini_client:
            result = await self._parse_with_gemini(text)
            if result:
                self.ai_stats["gemini_success"] += 1
                return result
        
        elif preferred_ai == "gemini" and self.openai_client:
            result = await self._parse_with_openai(text)
            if result:
                self.ai_stats["openai_success"] += 1
                return result
        
        self.ai_stats["failures"] += 1
        return None
    
    async def _parse_with_openai(self, text: str) -> Optional[Dict[str, Any]]:
        """Парсинг через OpenAI GPT"""
        try:
            if not self.openai_client:
                return None
            
            prompt = self.prompts["openai"] + text
            
            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-4o",  # Используем новую модель
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise crypto trading signal parser. Return only valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"}  # Принудительный JSON
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Парсим JSON
            try:
                result = json.loads(result_text)
                
                # Валидация результата
                if self._validate_ai_result(result):
                    result["ai_model"] = "gpt-4o"
                    result["ai_provider"] = "openai"
                    logger.info(f"✅ OpenAI parsed: {result.get('symbol', 'N/A')} {result.get('side', 'N/A')}")
                    return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ OpenAI JSON decode error: {e}")
                logger.debug(f"Raw response: {result_text}")
        
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
        
        return None
    
    async def _parse_with_gemini(self, text: str) -> Optional[Dict[str, Any]]:
        """Парсинг через Google Gemini"""
        try:
            if not self.gemini_client:
                return None
            
            prompt = self.prompts["gemini"] + text
            
            model = self.gemini_client.GenerativeModel('gemini-1.5-pro')
            response = await model.generate_content_async(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 500,
                }
            )
            
            result_text = response.text.strip()
            
            # Парсим JSON
            try:
                result = json.loads(result_text)
                
                # Валидация результата
                if self._validate_ai_result(result):
                    result["ai_model"] = "gemini-1.5-pro"
                    result["ai_provider"] = "gemini"
                    logger.info(f"✅ Gemini parsed: {result.get('symbol', 'N/A')} {result.get('side', 'N/A')}")
                    return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Gemini JSON decode error: {e}")
                logger.debug(f"Raw response: {result_text}")
        
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
        
        return None
    
    def _validate_ai_result(self, result: Dict[str, Any]) -> bool:
        """Валидация результата AI парсинга"""
        
        # Проверяем, что это сигнал
        if not result.get("is_signal", False):
            return False
        
        # Обязательные поля для торгового сигнала
        required_fields = ["symbol", "side"]
        
        for field in required_fields:
            if field not in result or not result[field]:
                logger.debug(f"Missing required field: {field}")
                return False
        
        # Проверяем валидность стороны
        if result["side"] not in ["LONG", "SHORT", "BUY", "SELL"]:
            logger.debug(f"Invalid side: {result['side']}")
            return False
        
        # Должен быть хотя бы entry или targets
        has_entry = "entry" in result and result["entry"]
        has_targets = "targets" in result and result["targets"]
        
        if not (has_entry or has_targets):
            logger.debug("No entry or targets found")
            return False
        
        return True
    
    def normalize_ai_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализация результата AI парсинга"""
        
        normalized = result.copy()
        
        # Нормализация символа
        if "symbol" in normalized:
            symbol = normalized["symbol"].upper()
            if not symbol.endswith("USDT") and "/" not in symbol:
                symbol += "USDT"
            elif "/" in symbol:
                base, quote = symbol.split("/")
                symbol = f"{base}{quote}"
            normalized["symbol"] = symbol
        
        # Нормализация стороны
        if "side" in normalized:
            side = normalized["side"].upper()
            if side in ["BUY", "LONG"]:
                normalized["side"] = "LONG"
            elif side in ["SELL", "SHORT"]:
                normalized["side"] = "SHORT"
        
        # Нормализация entry
        if "entry" in normalized and normalized["entry"]:
            entry = normalized["entry"]
            if isinstance(entry, (int, float)):
                normalized["entry"] = [float(entry)]
            elif isinstance(entry, list):
                normalized["entry"] = [float(x) for x in entry if x]
        
        # Нормализация targets
        if "targets" in normalized and normalized["targets"]:
            targets = normalized["targets"]
            if isinstance(targets, list):
                normalized["targets"] = [float(x) for x in targets if x]
        
        # Нормализация stop_loss
        if "stop_loss" in normalized and normalized["stop_loss"]:
            normalized["stop_loss"] = float(normalized["stop_loss"])
        
        return normalized
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Получение статистики AI парсинга"""
        stats = self.ai_stats.copy()
        
        if stats["total_requests"] > 0:
            success_rate = (stats["openai_success"] + stats["gemini_success"]) / stats["total_requests"]
            stats["success_rate"] = success_rate
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def is_available(self) -> Dict[str, bool]:
        """Проверка доступности AI сервисов"""
        return {
            "openai": self.openai_client is not None,
            "gemini": self.gemini_client is not None,
            "any_available": self.openai_client is not None or self.gemini_client is not None
        }


# Глобальный экземпляр AI парсера
ai_fallback_parser = AIFallbackParser()

def get_ai_parser() -> AIFallbackParser:
    """Получение глобального экземпляра AI парсера"""
    return ai_fallback_parser


# Функция для тестирования AI парсера
async def test_ai_parser():
    """Тестирование AI парсера"""
    print("🤖 ТЕСТИРОВАНИЕ AI FALLBACK PARSER")
    print("=" * 60)
    
    parser = get_ai_parser()
    
    # Проверяем доступность
    availability = parser.is_available()
    print(f"📡 AI AVAILABILITY:")
    for service, available in availability.items():
        status = "✅" if available else "❌"
        print(f"   {service}: {status}")
    
    if not availability["any_available"]:
        print("\n⚠️ No AI services available. Set OPENAI_API_KEY or GEMINI_API_KEY")
        return
    
    # Тестовые сигналы для AI
    test_signals = [
        {
            "name": "Нестандартный формат",
            "text": """🚀 Покупаем биток!
            
            BTC сейчас хорошая цена 45к
            Цели: 47к, 49к, 52к
            Если упадет до 43к - выходим
            Плечо можно 5х взять"""
        },
        {
            "name": "Неполный сигнал",
            "text": """ETH выглядит хорошо
            
            Покупать можно от 2800
            Цель 3000
            
            Риск до 2700"""
        },
        {
            "name": "Не сигнал",
            "text": """Доброе утро, трейдеры!
            
            Сегодня ожидается волатильность.
            Будьте осторожны с рисками."""
        }
    ]
    
    for i, test in enumerate(test_signals, 1):
        print(f"\n{i}️⃣ ТЕСТ: {test['name']}")
        print("-" * 50)
        print(f"📝 Текст: {test['text'][:100]}...")
        
        result = await parser.parse_with_ai(test['text'])
        
        if result and result.get("is_signal"):
            normalized = parser.normalize_ai_result(result)
            print(f"✅ AI РАСПОЗНАЛ СИГНАЛ:")
            print(f"   Symbol: {normalized.get('symbol')}")
            print(f"   Side: {normalized.get('side')}")
            print(f"   Entry: {normalized.get('entry')}")
            print(f"   Targets: {normalized.get('targets')}")
            print(f"   SL: {normalized.get('stop_loss')}")
            print(f"   Model: {result.get('ai_model')}")
            print(f"   Confidence: {result.get('confidence', 0):.1%}")
        elif result and not result.get("is_signal"):
            print(f"❌ AI определил: НЕ СИГНАЛ")
        else:
            print(f"⚠️ AI не смог обработать")
    
    # Статистика
    print(f"\n📊 AI СТАТИСТИКА:")
    stats = parser.get_ai_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n🎉 AI FALLBACK PARSER READY!")


if __name__ == "__main__":
    asyncio.run(test_ai_parser())
