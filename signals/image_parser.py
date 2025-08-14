"""
GHOST Image Signal Parser
Парсер для анализа торговых сигналов из изображений в Telegram
"""

import os
import io
import base64
import logging
from typing import Optional, Dict, Any, List
from PIL import Image
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageSignalParser:
    """Парсер сигналов из изображений"""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        
        # Инициализируем AI клиенты
        self._initialize_ai_clients()
        
        logger.info("Image Signal Parser initialized")
    
    def _initialize_ai_clients(self):
        """Инициализация AI клиентов для анализа изображений"""
        try:
            # OpenAI для анализа изображений
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    logger.info("✅ OpenAI client initialized for image analysis")
                else:
                    logger.warning("⚠️ OPENAI_API_KEY not found")
            except ImportError:
                logger.warning("⚠️ OpenAI library not installed")
            
            # Google Gemini для анализа изображений
            try:
                import google.generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                    self.gemini_client = genai.GenerativeModel('gemini-pro-vision')
                    logger.info("✅ Gemini Vision client initialized")
                else:
                    logger.warning("⚠️ GEMINI_API_KEY not found")
            except ImportError:
                logger.warning("⚠️ Google AI library not installed")
                
        except Exception as e:
            logger.error(f"❌ Error initializing AI clients: {e}")
    
    async def parse_image_signal(self, image_data: bytes, 
                               image_format: str = "PNG",
                               telegram_caption: str = "") -> Optional[Dict[str, Any]]:
        """Парсинг торгового сигнала из изображения"""
        try:
            logger.info(f"🖼️ Analyzing image signal, format: {image_format}, caption: {telegram_caption[:50]}...")
            
            # Пробуем разные AI модели
            results = []
            
            # OpenAI GPT-4 Vision
            if self.openai_client:
                openai_result = await self._analyze_with_openai(image_data, telegram_caption)
                if openai_result:
                    results.append(("openai", openai_result))
            
            # Google Gemini Vision
            if self.gemini_client:
                gemini_result = await self._analyze_with_gemini(image_data, telegram_caption)
                if gemini_result:
                    results.append(("gemini", gemini_result))
            
            # Выбираем лучший результат
            if results:
                best_result = self._select_best_result(results)
                logger.info(f"✅ Image signal parsed successfully with {best_result['ai_model']}")
                return best_result
            else:
                logger.warning("⚠️ No AI models available for image analysis")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error parsing image signal: {e}")
            return None
    
    async def _analyze_with_openai(self, image_data: bytes, caption: str = "") -> Optional[Dict[str, Any]]:
        """Анализ изображения с помощью OpenAI GPT-4 Vision"""
        try:
            # Конвертируем изображение в base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Создаем промпт
            prompt = self._get_image_analysis_prompt(caption)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            # Парсим JSON ответ
            import json
            result = json.loads(result_text)
            result["ai_model"] = "gpt-4-vision"
            result["ai_confidence"] = 0.85
            
            return result
            
        except Exception as e:
            logger.error(f"❌ OpenAI image analysis error: {e}")
            return None
    
    async def _analyze_with_gemini(self, image_data: bytes, caption: str = "") -> Optional[Dict[str, Any]]:
        """Анализ изображения с помощью Google Gemini Vision"""
        try:
            # Конвертируем в PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Создаем промпт
            prompt = self._get_image_analysis_prompt(caption)
            
            response = self.gemini_client.generate_content([prompt, image])
            result_text = response.text
            
            # Парсим JSON ответ
            import json
            result = json.loads(result_text)
            result["ai_model"] = "gemini-vision"
            result["ai_confidence"] = 0.80
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini image analysis error: {e}")
            return None
    
    def _get_image_analysis_prompt(self, caption: str = "") -> str:
        """Промпт для анализа изображений с торговыми сигналами"""
        base_prompt = """
You are a professional crypto trading signal analyzer specializing in chart analysis and trading screenshots.

Analyze this image and extract trading signal information. The image might contain:
1. Trading charts with technical analysis
2. Screenshots of trading signals
3. Price action setups
4. Support/resistance levels
5. Trading recommendations

CAPTION CONTEXT: {caption}

EXTRACT THE FOLLOWING IF PRESENT:
- symbol: trading pair (normalize to "BTCUSDT" format)
- side: "LONG" or "SHORT"
- entry: entry price or range
- targets: array of target prices
- stop_loss: stop loss price
- leverage: leverage if mentioned
- chart_pattern: technical pattern (breakout, triangle, etc.)
- timeframe: chart timeframe (1h, 4h, 1d, etc.)
- key_levels: important support/resistance levels
- indicators: technical indicators mentioned
- confidence: your confidence in the analysis (0.0-1.0)

RETURN VALID JSON ONLY:
{
    "is_signal": true/false,
    "symbol": "BTCUSDT",
    "side": "LONG",
    "entry": [45000, 46000],
    "targets": [47000, 48000, 49000],
    "stop_loss": 44000,
    "leverage": "10x",
    "chart_pattern": "ascending triangle breakout",
    "timeframe": "4h",
    "key_levels": [45000, 47000, 49000],
    "indicators": ["RSI oversold", "MACD bullish cross"],
    "confidence": 0.85,
    "reason": "Strong breakout above resistance with volume"
}

If no trading signal is found, return: {"is_signal": false}
        """.format(caption=caption if caption else "No caption provided")
        
        return base_prompt
    
    def _select_best_result(self, results: List[tuple]) -> Dict[str, Any]:
        """Выбор лучшего результата из нескольких AI моделей"""
        try:
            # Сортируем по confidence
            sorted_results = sorted(results, 
                                  key=lambda x: x[1].get("confidence", 0.0), 
                                  reverse=True)
            
            best_model, best_result = sorted_results[0]
            
            # Добавляем информацию о том, что использовались множественные модели
            best_result["analysis_method"] = "multi_ai_vision"
            best_result["models_used"] = [model for model, _ in results]
            
            return best_result
            
        except Exception as e:
            logger.error(f"❌ Error selecting best result: {e}")
            # Возвращаем первый доступный результат
            return results[0][1] if results else {}
    
    def is_image_message(self, message_data: Dict[str, Any]) -> bool:
        """Проверка, содержит ли сообщение изображение"""
        try:
            # Проверяем наличие photo в Telegram сообщении
            if "photo" in message_data:
                return True
            
            # Проверяем наличие document с типом изображения
            if "document" in message_data:
                document = message_data["document"]
                mime_type = document.get("mime_type", "")
                if mime_type.startswith("image/"):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking image message: {e}")
            return False
    
    async def download_telegram_image(self, message_data: Dict[str, Any], 
                                    bot_token: str) -> Optional[bytes]:
        """Скачивание изображения из Telegram"""
        try:
            file_id = None
            
            # Получаем file_id из photo или document
            if "photo" in message_data:
                # Берем изображение наибольшего размера
                photos = message_data["photo"]
                largest_photo = max(photos, key=lambda x: x.get("file_size", 0))
                file_id = largest_photo["file_id"]
            elif "document" in message_data:
                file_id = message_data["document"]["file_id"]
            
            if not file_id:
                logger.warning("⚠️ No file_id found in message")
                return None
            
            # Получаем file_path через Telegram Bot API
            file_info_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
            file_info_response = requests.get(file_info_url)
            file_info = file_info_response.json()
            
            if not file_info.get("ok"):
                logger.error(f"❌ Error getting file info: {file_info}")
                return None
            
            file_path = file_info["result"]["file_path"]
            
            # Скачиваем файл
            download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            download_response = requests.get(download_url)
            
            if download_response.status_code == 200:
                logger.info(f"✅ Image downloaded successfully, size: {len(download_response.content)} bytes")
                return download_response.content
            else:
                logger.error(f"❌ Error downloading image: {download_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error downloading Telegram image: {e}")
            return None


# Глобальный экземпляр
image_parser = None

def get_image_parser() -> ImageSignalParser:
    """Получение глобального экземпляра парсера изображений"""
    global image_parser
    if image_parser is None:
        image_parser = ImageSignalParser()
    return image_parser


# Тестирование
async def test_image_parser():
    """Тестирование парсера изображений"""
    print("🧪 ТЕСТИРОВАНИЕ IMAGE SIGNAL PARSER")
    print("=" * 60)
    
    parser = get_image_parser()
    
    # Здесь можно добавить тестирование с реальными изображениями
    print("📊 Image parser initialized")
    print(f"OpenAI available: {parser.openai_client is not None}")
    print(f"Gemini available: {parser.gemini_client is not None}")
    
    print("✅ Test completed!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_image_parser())
