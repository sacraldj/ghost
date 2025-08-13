"""
GHOST Trader Registry
Управление реестром трейдеров
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TraderProfile:
    """Профиль трейдера"""
    trader_id: str
    name: str
    source_type: str
    source_handle: Optional[str] = None
    mode: str = "observe"  # observe, paper, live
    risk_profile: Dict = None
    parsing_profile: str = "standard_v1"
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.risk_profile is None:
            self.risk_profile = {
                "size_usd": 100,
                "leverage": 10,
                "max_concurrent": 3,
                "sl_cap": 0.02
            }
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class TraderRegistry:
    """Реестр трейдеров"""
    
    def __init__(self):
        self.traders: Dict[str, TraderProfile] = {}
    
    def register_trader(self, trader: TraderProfile) -> bool:
        """Регистрация нового трейдера"""
        try:
            self.traders[trader.trader_id] = trader
            logger.info(f"Registered trader: {trader.trader_id} ({trader.name})")
            return True
        except Exception as e:
            logger.error(f"Error registering trader: {e}")
            return False
    
    def get_trader(self, trader_id: str) -> Optional[TraderProfile]:
        """Получение профиля трейдера"""
        return self.traders.get(trader_id)
    
    def list_traders(self, mode: Optional[str] = None, active_only: bool = False) -> List[TraderProfile]:
        """Список трейдеров с фильтрацией"""
        traders = list(self.traders.values())
        
        if mode:
            traders = [t for t in traders if t.mode == mode]
        
        if active_only:
            traders = [t for t in traders if t.is_active]
        
        return traders
    
    def update_trader_mode(self, trader_id: str, new_mode: str) -> bool:
        """Обновление режима трейдера"""
        try:
            if trader_id in self.traders:
                self.traders[trader_id].mode = new_mode
                self.traders[trader_id].updated_at = datetime.now()
                logger.info(f"Updated trader {trader_id} mode to {new_mode}")
                return True
            else:
                logger.warning(f"Trader {trader_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error updating trader mode: {e}")
            return False

# Глобальный экземпляр
_trader_registry: Optional[TraderRegistry] = None

def get_trader_registry() -> TraderRegistry:
    """Получение глобального экземпляра реестра"""
    global _trader_registry
    if _trader_registry is None:
        _trader_registry = TraderRegistry()
    return _trader_registry