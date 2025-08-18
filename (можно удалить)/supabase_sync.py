#!/usr/bin/env python3
"""
GHOST Supabase Sync Module
Синхронизация локальных данных с Supabase
"""

import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupabaseSync:
    """Синхронизация с Supabase"""
    
    def __init__(self):
        # Инициализация Supabase клиента - пробуем новые ключи, потом старые
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        
        # Пробуем новые API ключи
        self.supabase_secret_key = os.getenv('SUPABASE_SECRET_KEY')
        if not self.supabase_secret_key:
            # Fallback к старым ключам
            self.supabase_secret_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_secret_key:
            logger.error("❌ Supabase credentials not found in environment variables")
            logger.error("Required: NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY")
            self.supabase = None
        else:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_secret_key)
            logger.info("✅ Supabase client initialized with new API keys")
    
    def get_local_news(self, db_path: str = None) -> List[Dict]:
        """Получение новостей из локальной SQLite"""
        try:
            # Use in-memory database for cloud deployment
            if db_path is None:
                # Try to find database in several locations
                possible_paths = [
                    "ghost_news.db",
                    "../ghost_news.db", 
                    "/tmp/ghost_news.db",
                    "/opt/render/project/src/ghost_news.db"
                ]
                
                db_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        db_path = path
                        break
                
                # If no database found, create in-memory database
                if db_path is None:
                    logger.warning("⚠️ No SQLite database found, using in-memory database")
                    db_path = ":memory:"
            
            # Добавляем отладочную информацию
            import os
            current_dir = os.getcwd()
            
            if db_path != ":memory:":
                full_db_path = os.path.abspath(db_path)
                logger.info(f"🔍 Current directory: {current_dir}")
                logger.info(f"🔍 Database path: {full_db_path}")
                logger.info(f"🔍 Database exists: {os.path.exists(full_db_path)}")
            else:
                logger.info(f"🔍 Using in-memory SQLite database")
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем существующие таблицы
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                logger.info(f"🔍 Available tables: {[table[0] for table in tables]}")
                
                # Получаем критические новости (все, не только за 5 минут)
                cursor.execute("""
                    SELECT id, source_name, title, content, url, published_at,
                           sentiment, urgency, is_critical, priority, market_impact
                    FROM critical_news 
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                
                critical_news = []
                for row in cursor.fetchall():
                    critical_news.append({
                        'id': row[0],
                        'source_name': row[1],
                        'title': row[2],
                        'content': row[3],
                        'url': row[4],
                        'published_at': row[5],
                        'sentiment': row[6],
                        'urgency': row[7],
                        'is_critical': bool(row[8]),
                        'priority': row[9],
                        'market_impact': row[10],
                        'local_id': row[0]  # Сохраняем локальный ID
                    })
                
                # Получаем обычные новости (все, не только за 5 минут)
                cursor.execute("""
                    SELECT id, source_name, title, content, url, published_at,
                           sentiment, urgency, is_important, priority_level
                    FROM news_items 
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                
                regular_news = []
                for row in cursor.fetchall():
                    regular_news.append({
                        'id': row[0],
                        'source_name': row[1],
                        'title': row[2],
                        'content': row[3],
                        'url': row[4],
                        'published_at': row[5],
                        'sentiment': row[6],
                        'urgency': row[7],
                        'is_important': bool(row[8]),
                        'priority_level': row[9],
                        'local_id': row[0]  # Сохраняем локальный ID
                    })
                
                logger.info(f"📊 Found {len(critical_news)} critical news, {len(regular_news)} regular news")
                
                return {
                    'critical_news': critical_news,
                    'regular_news': regular_news
                }
                
        except Exception as e:
            logger.error(f"❌ Error reading local database: {e}")
            return {'critical_news': [], 'regular_news': []}
    
    async def sync_to_supabase(self, news_data: Dict):
        """Синхронизация новостей в Supabase"""
        if not self.supabase:
            logger.warning("⚠️ Supabase not configured, skipping sync")
            return
        
        try:
            # Синхронизация критических новостей
            if news_data['critical_news']:
                for news in news_data['critical_news']:
                    # Проверяем, не существует ли уже такая новость
                    existing = self.supabase.table('critical_news').select('id').eq('local_id', news['local_id']).execute()
                    
                    if not existing.data:
                        # Вставляем новую критическую новость
                        supabase_news = {
                            'local_id': news['local_id'],
                            'source_name': news['source_name'],
                            'title': news['title'],
                            'content': news['content'],
                            'url': news['url'],
                            'published_at': news['published_at'],
                            'sentiment': news['sentiment'],
                            'urgency': news['urgency'],
                            'is_critical': news['is_critical'],
                            'priority': news['priority'],
                            'market_impact': news['market_impact'],
                            'synced_at': datetime.now().isoformat()
                        }
                        
                        result = self.supabase.table('critical_news').insert(supabase_news).execute()
                        logger.info(f"✅ Synced critical news: {news['title'][:50]}...")
            
            # Синхронизация обычных новостей
            if news_data['regular_news']:
                for news in news_data['regular_news']:
                    # Проверяем, не существует ли уже такая новость
                    existing = self.supabase.table('news_items').select('id').eq('local_id', news['local_id']).execute()
                    
                    if not existing.data:
                        # Вставляем новую обычную новость
                        supabase_news = {
                            'local_id': news['local_id'],
                            'source_name': news['source_name'],
                            'title': news['title'],
                            'content': news['content'],
                            'url': news['url'],
                            'published_at': news['published_at'],
                            'sentiment': news['sentiment'],
                            'urgency': news['urgency'],
                            'is_important': news['is_important'],
                            'priority_level': news['priority_level'],
                            'synced_at': datetime.now().isoformat()
                        }
                        
                        result = self.supabase.table('news_items').insert(supabase_news).execute()
                        logger.info(f"✅ Synced regular news: {news['title'][:50]}...")
            
            logger.info(f"🔄 Sync completed: {len(news_data['critical_news'])} critical, {len(news_data['regular_news'])} regular")
            
        except Exception as e:
            logger.error(f"❌ Error syncing to Supabase: {e}")
    
    async def sync_loop(self, interval: int = 30):
        """Цикл синхронизации"""
        logger.info(f"🔄 Starting Supabase sync loop (every {interval} seconds)")
        
        while True:
            try:
                # Получаем локальные данные
                news_data = self.get_local_news()
                
                # Синхронизируем с Supabase
                await self.sync_to_supabase(news_data)
                
                # Пауза перед следующей синхронизацией
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Error in sync loop: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке

async def main():
    """Главная функция"""
    sync = SupabaseSync()
    await sync.sync_loop()

if __name__ == "__main__":
    asyncio.run(main())
