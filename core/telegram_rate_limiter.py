"""
GHOST Telegram Rate Limiter
Защита от многократных попыток подключения к Telegram
Предотвращает FloodWaitError и блокировки аккаунта
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AuthAttempt:
    """Попытка авторизации"""
    timestamp: float
    phone: str
    success: bool
    error_type: Optional[str] = None
    wait_time: Optional[int] = None  # секунды блокировки, если есть

class TelegramRateLimiter:
    """Ограничитель частоты попыток авторизации Telegram"""
    
    def __init__(self, config_file: str = "logs/telegram_auth_attempts.json"):
        self.config_file = config_file
        self.max_attempts_per_day = 3  # МАКСИМУМ 3 попытки в день
        self.max_attempts_per_hour = 2  # МАКСИМУМ 2 попытки в час
        self.cooldown_period = 3600  # 1 час перерыв после неудачных попыток
        
        # Загружаем историю попыток
        self.attempts = self._load_attempts()
        
        logger.info(f"TelegramRateLimiter инициализирован. Лимит: {self.max_attempts_per_day} попыток/день")

    def _load_attempts(self) -> List[AuthAttempt]:
        """Загрузка истории попыток из файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    attempts = []
                    for item in data:
                        attempts.append(AuthAttempt(**item))
                    
                    # Очищаем старые попытки (старше 24 часов)
                    current_time = time.time()
                    attempts = [a for a in attempts if (current_time - a.timestamp) < 86400]
                    
                    logger.info(f"Загружено {len(attempts)} попыток авторизации за последние 24 часа")
                    return attempts
            else:
                # Создаем директорию если не существует
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                return []
        except Exception as e:
            logger.error(f"Ошибка загрузки истории попыток: {e}")
            return []

    def _save_attempts(self):
        """Сохранение истории попыток в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                data = [asdict(attempt) for attempt in self.attempts]
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("История попыток сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения истории попыток: {e}")

    def can_attempt_auth(self, phone: str) -> tuple[bool, str]:
        """
        Проверяет, можно ли выполнить попытку авторизации
        
        Returns:
            tuple: (можно_ли_попытаться, причина_блокировки_если_нельзя)
        """
        current_time = time.time()
        
        # Фильтруем попытки для данного номера
        phone_attempts = [a for a in self.attempts if a.phone == phone]
        
        # Проверяем попытки за последние 24 часа
        day_attempts = [a for a in phone_attempts if (current_time - a.timestamp) < 86400]
        
        if len(day_attempts) >= self.max_attempts_per_day:
            return False, f"Превышен дневной лимит попыток авторизации ({self.max_attempts_per_day}). Попробуйте завтра."
        
        # Проверяем попытки за последний час
        hour_attempts = [a for a in phone_attempts if (current_time - a.timestamp) < 3600]
        
        if len(hour_attempts) >= self.max_attempts_per_hour:
            next_attempt_time = datetime.fromtimestamp(hour_attempts[-1].timestamp + 3600)
            return False, f"Превышен часовой лимит попыток ({self.max_attempts_per_hour}). Следующая попытка: {next_attempt_time.strftime('%H:%M')}"
        
        # Проверяем активные блокировки от предыдущих FloodWaitError
        active_blocks = [a for a in phone_attempts if a.wait_time and (current_time - a.timestamp) < a.wait_time]
        
        if active_blocks:
            block = active_blocks[-1]
            unblock_time = datetime.fromtimestamp(block.timestamp + block.wait_time)
            remaining_seconds = int(block.timestamp + block.wait_time - current_time)
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            
            return False, f"Аккаунт заблокирован до {unblock_time.strftime('%H:%M:%S')} (осталось {hours}ч {minutes}м)"
        
        # Проверяем период охлаждения после неудачных попыток
        recent_failures = [a for a in phone_attempts if not a.success and (current_time - a.timestamp) < self.cooldown_period]
        
        if recent_failures:
            cooldown_end = datetime.fromtimestamp(recent_failures[-1].timestamp + self.cooldown_period)
            return False, f"Период охлаждения после неудачной попытки. Повторите после {cooldown_end.strftime('%H:%M')}"
        
        return True, ""

    def record_attempt(self, phone: str, success: bool, error_type: str = None, wait_time: int = None):
        """
        Записывает попытку авторизации
        
        Args:
            phone: номер телефона
            success: успешна ли попытка
            error_type: тип ошибки, если есть
            wait_time: время блокировки в секундах, если FloodWaitError
        """
        attempt = AuthAttempt(
            timestamp=time.time(),
            phone=phone,
            success=success,
            error_type=error_type,
            wait_time=wait_time
        )
        
        self.attempts.append(attempt)
        
        # Очищаем старые попытки (старше 24 часов)
        current_time = time.time()
        self.attempts = [a for a in self.attempts if (current_time - a.timestamp) < 86400]
        
        # Сохраняем
        self._save_attempts()
        
        status = "✅ успешно" if success else "❌ неудачно"
        logger.info(f"Зафиксирована попытка авторизации {phone}: {status}")
        
        if wait_time:
            hours = wait_time // 3600
            minutes = (wait_time % 3600) // 60
            logger.warning(f"⚠️ Установлена блокировка на {hours}ч {minutes}м")

    def get_stats(self, phone: str) -> Dict:
        """Получить статистику попыток для номера телефона"""
        current_time = time.time()
        phone_attempts = [a for a in self.attempts if a.phone == phone]
        
        day_attempts = [a for a in phone_attempts if (current_time - a.timestamp) < 86400]
        hour_attempts = [a for a in phone_attempts if (current_time - a.timestamp) < 3600]
        successful_attempts = [a for a in day_attempts if a.success]
        failed_attempts = [a for a in day_attempts if not a.success]
        
        # Проверяем активные блокировки
        active_blocks = [a for a in phone_attempts if a.wait_time and (current_time - a.timestamp) < a.wait_time]
        
        stats = {
            'phone': phone,
            'attempts_today': len(day_attempts),
            'max_attempts_per_day': self.max_attempts_per_day,
            'attempts_this_hour': len(hour_attempts),
            'max_attempts_per_hour': self.max_attempts_per_hour,
            'successful_today': len(successful_attempts),
            'failed_today': len(failed_attempts),
            'remaining_attempts_today': max(0, self.max_attempts_per_day - len(day_attempts)),
            'remaining_attempts_hour': max(0, self.max_attempts_per_hour - len(hour_attempts)),
            'is_blocked': len(active_blocks) > 0
        }
        
        if active_blocks:
            block = active_blocks[-1]
            remaining_block_time = int(block.timestamp + block.wait_time - current_time)
            stats['block_remaining_seconds'] = remaining_block_time
        
        return stats

    def reset_attempts(self, phone: str = None):
        """Сброс попыток (для экстренных случаев)"""
        if phone:
            self.attempts = [a for a in self.attempts if a.phone != phone]
            logger.info(f"Сброшены попытки для номера {phone}")
        else:
            self.attempts = []
            logger.info("Сброшены все попытки авторизации")
        
        self._save_attempts()

    def show_protection_status(self):
        """Показать текущий статус защиты"""
        print("🛡️ ЗАЩИТА ОТ МНОГОКРАТНЫХ ПОДКЛЮЧЕНИЙ")
        print("=" * 45)
        print(f"📊 Максимум попыток в день: {self.max_attempts_per_day}")
        print(f"📊 Максимум попыток в час: {self.max_attempts_per_hour}")
        print(f"⏰ Период охлаждения: {self.cooldown_period // 60} минут")
        print(f"📝 Всего записей: {len(self.attempts)}")
        
        if self.attempts:
            unique_phones = set(a.phone for a in self.attempts)
            print(f"📱 Отслеживаемые номера: {len(unique_phones)}")
            
            for phone in unique_phones:
                stats = self.get_stats(phone)
                print(f"\n📞 {phone}:")
                print(f"   Попыток сегодня: {stats['attempts_today']}/{stats['max_attempts_per_day']}")
                print(f"   Успешных: {stats['successful_today']}, Неудачных: {stats['failed_today']}")
                if stats['is_blocked']:
                    hours = stats['block_remaining_seconds'] // 3600
                    minutes = (stats['block_remaining_seconds'] % 3600) // 60
                    print(f"   🚫 ЗАБЛОКИРОВАН (осталось: {hours}ч {minutes}м)")
        else:
            print("📝 История пуста")
