#!/usr/bin/env python3
"""
GHOST Telegram Listener - Обновленная версия

Purpose:
- Подключается к Telegram через Telethon
- Слушает сигналы из разрешенных каналов  
- Фильтрует по типу/триггерам
- Логирует сырые сообщения
- Передает сигналы в signal_router для обработки

Dependencies:
- telethon
- PyYAML
- python-dotenv

Environment:
- TELEGRAM_API_ID
- TELEGRAM_API_HASH
- TELEGRAM_SESSION_NAME (default: "ghost_trader")

GHOST-META:
- Module: telegram_listener
- Version: 2.0
- Author: GHOST System
- Dependencies: telethon, PyYAML, python-dotenv
- Config: config/telegram_channels.yaml, config/telethon.yaml
"""

import os
import json
import yaml
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("telegram_listener")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

RAW_LOG_PATH = os.path.join(OUTPUT_DIR, "raw_logbook.json")
STATUS_PATH = os.path.join(OUTPUT_DIR, "module_status.json")
CHANNELS_CONFIG = os.path.join(CONFIG_DIR, "telegram_channels.yaml")


class TelegramListener:
    def __init__(self):
        """Initialize Telegram listener with config"""
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.session_name = os.getenv("TELEGRAM_SESSION_NAME", "ghost_trader")
        
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH required")
        
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        self.allowed_channels = {}
        self.channel_configs = {}
        
        # Load channels config
        self.load_channels_config()
        
        # Initialize status
        self.update_status("initializing", "Loading configuration")

    def load_channels_config(self):
        """Load channels configuration from YAML"""
        try:
            if os.path.exists(CHANNELS_CONFIG):
                with open(CHANNELS_CONFIG, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                channels = config.get('channels', [])
                for channel in channels:
                    chat_id = channel.get('id')
                    if chat_id:
                        self.allowed_channels[chat_id] = True
                        self.channel_configs[chat_id] = {
                            'type': channel.get('type', 'universal'),
                            'trigger': channel.get('trigger'),
                            'name': channel.get('name', f"Channel_{chat_id}")
                        }
                        
                logger.info(f"Loaded {len(self.allowed_channels)} channels from config")
            else:
                logger.warning(f"Config file not found: {CHANNELS_CONFIG}")
                self.create_example_config()
                
        except Exception as e:
            logger.error(f"Error loading channels config: {e}")
            self.create_example_config()

    def create_example_config(self):
        """Create example configuration file"""
        example_config = {
            'channels': [
                {
                    'id': -1001234567890,
                    'name': 'Example Trading Channel',
                    'type': 'trade',
                    'trigger': 'LONG'
                },
                {
                    'id': -1001111111111,
                    'name': 'Example News Channel', 
                    'type': 'news',
                    'trigger': None
                }
            ]
        }
        
        try:
            with open(CHANNELS_CONFIG, 'w', encoding='utf-8') as f:
                yaml.dump(example_config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Created example config: {CHANNELS_CONFIG}")
        except Exception as e:
            logger.error(f"Error creating example config: {e}")

    def log_raw_message(self, message_data: Dict):
        """Log raw message to JSON file"""
        try:
            if os.path.exists(RAW_LOG_PATH):
                with open(RAW_LOG_PATH, "r", encoding='utf-8') as f:
                    raw_log = json.load(f)
            else:
                raw_log = []
                
            raw_log.append(message_data)
            
            # Keep only last 1000 messages to prevent file bloat
            if len(raw_log) > 1000:
                raw_log = raw_log[-1000:]
                
            with open(RAW_LOG_PATH, "w", encoding='utf-8') as f:
                json.dump(raw_log, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging raw message: {e}")

    def update_status(self, status: str, message: str = ""):
        """Update module status"""
        try:
            status_data = {
                "telegram_listener": {
                    "status": status,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_channels": len(self.allowed_channels)
                }
            }
            
            # Load existing status
            existing_status = {}
            if os.path.exists(STATUS_PATH):
                with open(STATUS_PATH, "r", encoding='utf-8') as f:
                    existing_status = json.load(f)
            
            # Update telegram_listener section
            existing_status.update(status_data)
            
            with open(STATUS_PATH, "w", encoding='utf-8') as f:
                json.dump(existing_status, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating status: {e}")

    async def handle_new_message(self, event):
        """Handle new Telegram message"""
        try:
            message = event.message
            chat_id = message.chat_id
            
            # Check if channel is allowed
            if chat_id not in self.allowed_channels:
                return
                
            # Get channel config
            channel_config = self.channel_configs.get(chat_id, {})
            channel_name = channel_config.get('name', f"Unknown_{chat_id}")
            
            # Prepare message data
            message_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'chat_id': chat_id,
                'channel_name': channel_name,
                'message_id': message.id,
                'text': message.text or '',
                'from_user': getattr(message.sender, 'username', None) if message.sender else None
            }
            
            # Log raw message
            self.log_raw_message(message_data)
            
            # Check if message should trigger signal processing
            should_process = False
            message_text = message.text or ''
            
            channel_type = channel_config.get('type', 'universal')
            trigger = channel_config.get('trigger')
            
            if channel_type in ['test', 'trade', 'universal']:
                should_process = True
            elif trigger and trigger.lower() in message_text.lower():
                should_process = True
                
            if should_process and message_text.strip():
                logger.info(f"Processing signal from {channel_name}: {message_text[:100]}...")
                
                # Here you would call your signal router
                # await self.route_signal(message_text, channel_name, chat_id)
                
                # For now, just log it
                signal_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': channel_name,
                    'chat_id': chat_id,
                    'text': message_text,
                    'type': channel_type,
                    'trigger': trigger
                }
                
                signal_log_path = os.path.join(OUTPUT_DIR, "signals.json")
                try:
                    if os.path.exists(signal_log_path):
                        with open(signal_log_path, "r", encoding='utf-8') as f:
                            signals = json.load(f)
                    else:
                        signals = []
                        
                    signals.append(signal_data)
                    
                    # Keep only last 100 signals
                    if len(signals) > 100:
                        signals = signals[-100:]
                        
                    with open(signal_log_path, "w", encoding='utf-8') as f:
                        json.dump(signals, f, ensure_ascii=False, indent=2)
                        
                except Exception as e:
                    logger.error(f"Error saving signal: {e}")
            
            # Update activity status
            self.update_status("active", f"Last message from {channel_name}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def start_listening(self):
        """Start the Telegram listener"""
        try:
            await self.client.start()
            logger.info("Telegram client started successfully")
            
            # Register message handler
            self.client.add_event_handler(
                self.handle_new_message,
                events.NewMessage()
            )
            
            # Get account info
            me = await self.client.get_me()
            logger.info(f"Logged in as: {me.username or me.first_name}")
            
            self.update_status("listening", f"Active as {me.username or me.first_name}")
            
            # Run until disconnected
            logger.info("Starting to listen for messages...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error in listener: {e}")
            self.update_status("error", str(e))
        finally:
            await self.client.disconnect()

    async def stop_listening(self):
        """Stop the listener gracefully"""
        logger.info("Stopping Telegram listener...")
        self.update_status("stopping", "Graceful shutdown")
        await self.client.disconnect()


async def main():
    """Main function"""
    logger.info("Starting GHOST Telegram Listener v2.0")
    
    try:
        listener = TelegramListener()
        await listener.start_listening()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Telegram listener shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
