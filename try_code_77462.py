#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

load_dotenv()

async def try_code():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    print(f"🔢 Пробуем код 77462 для {phone}")
    
    client = TelegramClient('ghost_session', api_id, api_hash)
    
    try:
        await client.connect()
        
        # Отправляем запрос на код
        print("📞 Запрашиваем код...")
        sent = await client.send_code_request(phone)
        print(f"✅ Код запрошен: {sent.phone_code_hash}")
        
        # Используем код из скриншота
        code = "77462"
        print(f"🔐 Пробуем код: {code}")
        
        try:
            await client.sign_in(phone, code)
            
            me = await client.get_me()
            print(f"✅ УСПЕХ! Авторизован: {me.first_name}")
            
            # Тестируем доступ к каналам
            test_channels = ['@ghostsignaltest', '@whalesguide', '@cryptoattack24']
            print("\n📺 Тестируем каналы:")
            
            for channel in test_channels:
                try:
                    entity = await client.get_entity(channel)
                    print(f"✅ {channel}: {entity.title}")
                except Exception as e:
                    print(f"⚠️ {channel}: {str(e)}")
            
            print(f"\n🎉 Сессия ghost_session.session создана!")
            return True
            
        except SessionPasswordNeededError:
            print("🔐 Требуется пароль 2FA")
            password = input("Введите пароль 2FA: ")
            await client.sign_in(password=password)
            print("✅ Успешная авторизация с 2FA!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка с кодом: {e}")
            # Пробуем другие коды из скриншота
            for alt_code in ["94879", "74660"]:
                print(f"🔄 Пробуем код {alt_code}...")
                try:
                    await client.sign_in(phone, alt_code)
                    me = await client.get_me()
                    print(f"✅ Успех с кодом {alt_code}! {me.first_name}")
                    return True
                except:
                    print(f"❌ Код {alt_code} не подошел")
            return False
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(try_code())
    if success:
        print("\n🚀 Готово! Запускаем start_all.py...")
    else:
        print("\n❌ Нужно настроить email в Telegram")
