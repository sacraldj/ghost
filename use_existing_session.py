#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def use_existing():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    print("🔍 ПОИСК СУЩЕСТВУЮЩЕЙ АВТОРИЗАЦИИ")
    print("=" * 50)
    
    # Проверяем стандартные места сессий Telegram Desktop
    possible_locations = [
        os.path.expanduser("~/Library/Application Support/Telegram Desktop/tdata"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Desktop"),
        ".",
    ]
    
    print("📂 Ищем сессии в:")
    for location in possible_locations:
        print(f"  {location}")
        if os.path.exists(location):
            session_files = []
            try:
                for file in os.listdir(location):
                    if file.endswith('.session'):
                        session_files.append(os.path.join(location, file))
                if session_files:
                    print(f"  ✅ Найдено: {session_files}")
            except:
                pass
    
    # Создаем простую сессию без email требований
    print("\n🔧 Создаем новую сессию...")
    
    # Пробуем разные имена сессий
    session_names = ['ghost_session', 'main_session', 'primary_session']
    
    for session_name in session_names:
        try:
            print(f"\n🔑 Пробуем {session_name}...")
            client = TelegramClient(session_name, api_id, api_hash)
            
            await client.connect()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                print(f"✅ УЖЕ АВТОРИЗОВАН: {me.first_name}")
                
                # Копируем как ghost_session если это не он
                if session_name != 'ghost_session':
                    import shutil
                    shutil.copy2(f'{session_name}.session', 'ghost_session.session')
                    print("✅ Скопировано в ghost_session.session")
                
                await client.disconnect()
                return True
            
            await client.disconnect()
            
        except Exception as e:
            print(f"⚠️ {session_name}: {e}")
    
    # Если ничего не найдено, создаем новую сессию с упрощенной авторизацией
    print("\n🆕 Создаем новую сессию...")
    
    try:
        client = TelegramClient('ghost_session', api_id, api_hash)
        await client.connect()
        
        print("✅ Подключен к Telegram")
        print("📱 Если появится окно авторизации в браузере - подтвердите")
        print("🔢 Или введите код из SMS...")
        
        # Автоматически начинаем процесс авторизации
        if not await client.is_user_authorized():
            await client.send_code_request(os.getenv('TELEGRAM_PHONE'))
            print(f"📞 Код отправлен на {os.getenv('TELEGRAM_PHONE')}")
            
            # Пробуем без ввода - может авторизуется автоматически
            await asyncio.sleep(2)
            
            if await client.is_user_authorized():
                print("✅ Автоматическая авторизация!")
            else:
                print("💡 Проверьте Telegram приложение на коды")
                return False
        
        me = await client.get_me()
        print(f"✅ ГОТОВО: {me.first_name}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(use_existing())
    if success:
        print("\n🚀 Сессия готова! Запускаем start_all.py")
    else:
        print("\n❌ Нужна ручная авторизация")
