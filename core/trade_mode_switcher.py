"""
GHOST TRADE MODE SWITCHER
Управление переключением режимов торговли трейдеров
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.trader_registry import TraderRegistry, TraderMode, get_trader_registry

logger = logging.getLogger(__name__)

class SwitchResult(Enum):
    SUCCESS = "success"
    TRADER_NOT_FOUND = "trader_not_found"
    INVALID_MODE = "invalid_mode"
    RISK_CHECK_FAILED = "risk_check_failed"
    DATABASE_ERROR = "database_error"
    ALREADY_IN_MODE = "already_in_mode"

@dataclass
class SwitchResponse:
    """Ответ на переключение режима"""
    result: SwitchResult
    trader_id: str
    old_mode: Optional[str] = None
    new_mode: Optional[str] = None
    message: str = ""
    warnings: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class RiskCheckResult:
    """Результат проверки рисков"""
    passed: bool
    warnings: List[str]
    blocking_issues: List[str]
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.blocking_issues is None:
            self.blocking_issues = []

class TradeModeSwitch:
    """Основной класс для переключения режимов торговли"""
    
    def __init__(self):
        self.trader_registry: Optional[TraderRegistry] = None
        
        # Правила переключения режимов
        self.switch_rules = {
            # Из какого режима в какой можно переключиться
            TraderMode.OBSERVE: [TraderMode.PAPER, TraderMode.LIVE],
            TraderMode.PAPER: [TraderMode.OBSERVE, TraderMode.LIVE],
            TraderMode.LIVE: [TraderMode.OBSERVE, TraderMode.PAPER]
        }
        
        # Требования для каждого режима
        self.mode_requirements = {
            TraderMode.OBSERVE: {
                'min_signals': 0,
                'min_winrate': 0.0,
                'min_confidence': 0.0,
                'risk_profile_required': False
            },
            TraderMode.PAPER: {
                'min_signals': 10,
                'min_winrate': 0.0,
                'min_confidence': 70.0,
                'risk_profile_required': True
            },
            TraderMode.LIVE: {
                'min_signals': 50,
                'min_winrate': 60.0,
                'min_confidence': 80.0,
                'risk_profile_required': True,
                'min_paper_trades': 20,
                'min_paper_winrate': 55.0
            }
        }
    
    async def initialize(self):
        """Инициализация компонента"""
        self.trader_registry = await get_trader_registry()
        logger.info("TradeModeSwitch initialized")
    
    async def switch_mode(self, trader_id: str, new_mode: TraderMode, 
                         force: bool = False) -> SwitchResponse:
        """Главная функция переключения режима"""
        try:
            if not self.trader_registry:
                await self.initialize()
            
            # Получаем текущие данные трейдера
            trader = await self.trader_registry.get_trader(trader_id)
            if not trader:
                return SwitchResponse(
                    result=SwitchResult.TRADER_NOT_FOUND,
                    trader_id=trader_id,
                    message=f"Trader {trader_id} not found"
                )
            
            old_mode = trader.mode
            
            # Проверяем, не находится ли уже в нужном режиме
            if old_mode == new_mode:
                return SwitchResponse(
                    result=SwitchResult.ALREADY_IN_MODE,
                    trader_id=trader_id,
                    old_mode=old_mode.value,
                    new_mode=new_mode.value,
                    message=f"Trader {trader_id} is already in {new_mode.value} mode"
                )
            
            # Проверяем возможность переключения
            if new_mode not in self.switch_rules.get(old_mode, []):
                return SwitchResponse(
                    result=SwitchResult.INVALID_MODE,
                    trader_id=trader_id,
                    old_mode=old_mode.value,
                    new_mode=new_mode.value,
                    message=f"Cannot switch from {old_mode.value} to {new_mode.value}"
                )
            
            # Проверка рисков (если не форсированно)
            if not force:
                risk_check = await self._check_risks(trader_id, new_mode)
                if not risk_check.passed:
                    return SwitchResponse(
                        result=SwitchResult.RISK_CHECK_FAILED,
                        trader_id=trader_id,
                        old_mode=old_mode.value,
                        new_mode=new_mode.value,
                        message="Risk check failed",
                        warnings=risk_check.warnings + risk_check.blocking_issues
                    )
            else:
                risk_check = RiskCheckResult(passed=True, warnings=[], blocking_issues=[])
            
            # Выполняем переключение
            success = await self.trader_registry.set_trader_mode(trader_id, new_mode)
            
            if success:
                # Логируем переключение
                await self._log_mode_switch(trader_id, old_mode, new_mode, force)
                
                return SwitchResponse(
                    result=SwitchResult.SUCCESS,
                    trader_id=trader_id,
                    old_mode=old_mode.value,
                    new_mode=new_mode.value,
                    message=f"Successfully switched trader {trader_id} from {old_mode.value} to {new_mode.value}",
                    warnings=risk_check.warnings
                )
            else:
                return SwitchResponse(
                    result=SwitchResult.DATABASE_ERROR,
                    trader_id=trader_id,
                    old_mode=old_mode.value,
                    new_mode=new_mode.value,
                    message="Database update failed"
                )
                
        except Exception as e:
            logger.error(f"Error switching mode for trader {trader_id}: {e}")
            return SwitchResponse(
                result=SwitchResult.DATABASE_ERROR,
                trader_id=trader_id,
                message=f"Internal error: {str(e)}"
            )
    
    async def _check_risks(self, trader_id: str, new_mode: TraderMode) -> RiskCheckResult:
        """Проверка рисков перед переключением режима"""
        warnings = []
        blocking_issues = []
        
        try:
            requirements = self.mode_requirements.get(new_mode, {})
            
            # Получаем статистику трейдера
            trader_stats = await self._get_trader_statistics(trader_id)
            
            # Проверка минимального количества сигналов
            min_signals = requirements.get('min_signals', 0)
            if trader_stats.get('total_signals', 0) < min_signals:
                blocking_issues.append(
                    f"Insufficient signals: {trader_stats.get('total_signals', 0)} < {min_signals}"
                )
            
            # Проверка винрейта
            min_winrate = requirements.get('min_winrate', 0.0)
            current_winrate = trader_stats.get('winrate_30d', 0.0)
            if current_winrate < min_winrate:
                blocking_issues.append(
                    f"Low winrate: {current_winrate:.1f}% < {min_winrate:.1f}%"
                )
            
            # Проверка уверенности в сигналах
            min_confidence = requirements.get('min_confidence', 0.0)
            avg_confidence = trader_stats.get('avg_confidence', 0.0)
            if avg_confidence < min_confidence:
                warnings.append(
                    f"Low signal confidence: {avg_confidence:.1f}% < {min_confidence:.1f}%"
                )
            
            # Проверка профиля риска
            if requirements.get('risk_profile_required', False):
                trader = await self.trader_registry.get_trader(trader_id)
                if not trader or not trader.risk_profile:
                    blocking_issues.append("Risk profile not configured")
                elif trader.risk_profile.size_usd <= 0:
                    blocking_issues.append("Invalid risk profile: position size must be > 0")
            
            # Специальные проверки для LIVE режима
            if new_mode == TraderMode.LIVE:
                # Проверка paper trading статистики
                min_paper_trades = requirements.get('min_paper_trades', 0)
                paper_trades = trader_stats.get('paper_trades_count', 0)
                if paper_trades < min_paper_trades:
                    blocking_issues.append(
                        f"Insufficient paper trades: {paper_trades} < {min_paper_trades}"
                    )
                
                min_paper_winrate = requirements.get('min_paper_winrate', 0.0)
                paper_winrate = trader_stats.get('paper_winrate', 0.0)
                if paper_winrate < min_paper_winrate:
                    blocking_issues.append(
                        f"Low paper trading winrate: {paper_winrate:.1f}% < {min_paper_winrate:.1f}%"
                    )
                
                # Предупреждения для LIVE
                if trader_stats.get('max_drawdown_30d', 0) > 20:
                    warnings.append("High drawdown in last 30 days")
                
                if trader_stats.get('signals_7d', 0) == 0:
                    warnings.append("No recent signals in last 7 days")
            
            return RiskCheckResult(
                passed=len(blocking_issues) == 0,
                warnings=warnings,
                blocking_issues=blocking_issues
            )
            
        except Exception as e:
            logger.error(f"Error checking risks for trader {trader_id}: {e}")
            return RiskCheckResult(
                passed=False,
                warnings=[],
                blocking_issues=[f"Risk check error: {str(e)}"]
            )
    
    async def _get_trader_statistics(self, trader_id: str) -> Dict[str, Any]:
        """Получение статистики трейдера"""
        try:
            # Здесь должен быть запрос к БД для получения статистики
            # Пока возвращаем mock данные
            return {
                'total_signals': 50,
                'winrate_30d': 65.5,
                'avg_confidence': 85.3,
                'paper_trades_count': 25,
                'paper_winrate': 62.1,
                'max_drawdown_30d': 15.2,
                'signals_7d': 3
            }
        except Exception as e:
            logger.error(f"Error getting statistics for trader {trader_id}: {e}")
            return {}
    
    async def _log_mode_switch(self, trader_id: str, old_mode: TraderMode, 
                              new_mode: TraderMode, forced: bool):
        """Логирование переключения режима"""
        try:
            log_entry = {
                'timestamp': datetime.now(),
                'trader_id': trader_id,
                'old_mode': old_mode.value,
                'new_mode': new_mode.value,
                'forced': forced,
                'action': 'mode_switch'
            }
            
            # Здесь можно сохранить в БД для аудита
            logger.info(f"Mode switch: {trader_id} {old_mode.value} -> {new_mode.value} (forced: {forced})")
            
        except Exception as e:
            logger.error(f"Error logging mode switch: {e}")
    
    async def get_switch_eligibility(self, trader_id: str) -> Dict[str, Any]:
        """Получение информации о возможности переключения режимов"""
        try:
            if not self.trader_registry:
                await self.initialize()
            
            trader = await self.trader_registry.get_trader(trader_id)
            if not trader:
                return {'error': 'Trader not found'}
            
            current_mode = trader.mode
            eligible_modes = {}
            
            # Проверяем каждый возможный режим
            for mode in TraderMode:
                if mode == current_mode:
                    eligible_modes[mode.value] = {
                        'eligible': True,
                        'current': True,
                        'message': 'Current mode'
                    }
                elif mode in self.switch_rules.get(current_mode, []):
                    # Проверяем риски
                    risk_check = await self._check_risks(trader_id, mode)
                    eligible_modes[mode.value] = {
                        'eligible': risk_check.passed,
                        'current': False,
                        'message': 'Eligible' if risk_check.passed else 'Risk check failed',
                        'warnings': risk_check.warnings,
                        'blocking_issues': risk_check.blocking_issues
                    }
                else:
                    eligible_modes[mode.value] = {
                        'eligible': False,
                        'current': False,
                        'message': f'Cannot switch from {current_mode.value} to {mode.value}'
                    }
            
            return {
                'trader_id': trader_id,
                'current_mode': current_mode.value,
                'modes': eligible_modes,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting switch eligibility for trader {trader_id}: {e}")
            return {'error': str(e)}
    
    async def batch_switch_mode(self, switches: List[Dict[str, Any]]) -> List[SwitchResponse]:
        """Пакетное переключение режимов"""
        results = []
        
        for switch_request in switches:
            trader_id = switch_request.get('trader_id')
            new_mode_str = switch_request.get('mode')
            force = switch_request.get('force', False)
            
            try:
                new_mode = TraderMode(new_mode_str)
                result = await self.switch_mode(trader_id, new_mode, force)
                results.append(result)
            except ValueError:
                results.append(SwitchResponse(
                    result=SwitchResult.INVALID_MODE,
                    trader_id=trader_id,
                    message=f"Invalid mode: {new_mode_str}"
                ))
            except Exception as e:
                results.append(SwitchResponse(
                    result=SwitchResult.DATABASE_ERROR,
                    trader_id=trader_id,
                    message=f"Error: {str(e)}"
                ))
        
        return results

# Глобальный экземпляр переключателя
trade_mode_switcher: Optional[TradeModeSwitch] = None

async def get_trade_mode_switcher() -> TradeModeSwitch:
    """Получение глобального экземпляра переключателя"""
    global trade_mode_switcher
    if trade_mode_switcher is None:
        trade_mode_switcher = TradeModeSwitch()
        await trade_mode_switcher.initialize()
    return trade_mode_switcher

# Convenience функции
async def switch_to_live(trader_id: str, force: bool = False) -> SwitchResponse:
    """Переключение трейдера в live режим"""
    switcher = await get_trade_mode_switcher()
    return await switcher.switch_mode(trader_id, TraderMode.LIVE, force)

async def switch_to_paper(trader_id: str, force: bool = False) -> SwitchResponse:
    """Переключение трейдера в paper режим"""
    switcher = await get_trade_mode_switcher()
    return await switcher.switch_mode(trader_id, TraderMode.PAPER, force)

async def switch_to_observe(trader_id: str, force: bool = False) -> SwitchResponse:
    """Переключение трейдера в observe режим"""
    switcher = await get_trade_mode_switcher()
    return await switcher.switch_mode(trader_id, TraderMode.OBSERVE, force)
