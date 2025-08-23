#!/usr/bin/env python3
"""
Восстанавливает ghost_code_reader.session из Base64 переменной окружения
Для использования на Render
"""

import os
import base64
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def restore_reader_session():
    """Восстанавливает reader сессию из переменной окружения"""
    
    # Имя переменной окружения с base64 данными
    env_var = 'GHOST_READER_SESSION_B64'
    
    try:
        # Получаем данные из переменной окружения
        session_data_b64 = os.getenv(env_var)
        
        if not session_data_b64:
            logger.warning(f"⚠️ Переменная окружения {env_var} не найдена")
            return False
        
        logger.info(f"✅ Переменная {env_var} найдена, восстанавливаем сессию...")
        
        # Декодируем base64
        session_data = base64.b64decode(session_data_b64)
        
        # Записываем в файл
        session_file = 'ghost_code_reader.session'
        with open(session_file, 'wb') as f:
            f.write(session_data)
        
        logger.info(f"✅ Сессия восстановлена: {session_file} ({len(session_data)} байт)")
        
        # Проверяем что файл создался
        if os.path.exists(session_file):
            size = os.path.getsize(session_file)
            logger.info(f"📁 Размер файла: {size} байт")
            
            # Устанавливаем правильные права доступа
            os.chmod(session_file, 0o600)
            logger.info("🔒 Права доступа установлены (600)")
            
            return True
        else:
            logger.error("❌ Файл не создался")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка восстановления сессии: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Восстановление ghost_code_reader.session...")
    print("=" * 50)
    
    success = restore_reader_session()
    
    if success:
        print("🎉 READER СЕССИЯ ВОССТАНОВЛЕНА!")
    else:
        print("❌ ОШИБКА ВОССТАНОВЛЕНИЯ СЕССИИ")
        print("💡 Убедитесь что переменная GHOST_READER_SESSION_B64 установлена")
    
    print("=" * 50)
