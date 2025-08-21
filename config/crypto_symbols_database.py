"""
Криптовалютная база символов для разных бирж
Поддержка исправления опечаток и нормализации
"""

from typing import List, Dict, Optional, Set
import difflib
import re

class CryptoSymbolsDatabase:
    """База данных криптовалютных символов с поддержкой исправления опечаток"""
    
    def __init__(self):
        # Основные базовые валюты
        self.base_currencies = {
            'BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK',
            'UNI', 'LTC', 'BCH', 'XLM', 'VET', 'TRX', 'EOS', 'ATOM', 'ALGO', 'DOGE',
            'SHIB', 'APT', 'ARB', 'OP', 'NEAR', 'FTM', 'SAND', 'MANA', 'AXS', 'ICP',
            'THETA', 'MKR', 'AAVE', 'CRV', 'SUSHI', 'COMP', 'YFI', 'SNX', 'BAL', 'ZRX',
            'ORDI', 'WIF', 'PEPE', 'FLOKI', 'BONK', 'MEME', 'BOME', 'JUP', 'WEN', 'MYRO',
            'ETHFI', 'ENA', 'W', 'TNSR', 'AEVO', 'REZ', 'BB', 'LISTA', 'ZK', 'ZRO',
            'HMSTR', 'CATI', 'NEIRO', 'EIGEN', 'GRASS', 'SCR', 'LUMIA', 'KAIA'
        }
        
        # Котировочные валюты
        self.quote_currencies = {'USDT', 'USD', 'USDC', 'BUSD', 'BTC', 'ETH', 'BNB'}
        
        # Популярные пары по биржам
        self.exchange_pairs = {
            'binance': self._generate_pairs(['USDT', 'BTC', 'ETH', 'BNB']),
            'bybit': self._generate_pairs(['USDT', 'USD']),
            'okx': self._generate_pairs(['USDT', 'USD']),
            'bitget': self._generate_pairs(['USDT']),
            'kucoin': self._generate_pairs(['USDT'])
        }
        
        # Все возможные пары
        self.all_pairs = set()
        for pairs in self.exchange_pairs.values():
            self.all_pairs.update(pairs)
        
        # Альтернативные написания
        self.alternative_names = {
            'BTC': ['BITCOIN', 'BITCOINS', 'BTCOIN', 'BITCION'],
            'ETH': ['ETHEREUM', 'ETHER', 'ETHERIUM', 'ETHH', 'ETHE'],
            'BNB': ['BINANCE', 'BINANCECOIN', 'BNB'],
            'ADA': ['CARDANO', 'ADAA'],
            'XRP': ['RIPPLE', 'XRPP'],
            'SOL': ['SOLANA', 'SOLL'],
            'DOT': ['POLKADOT', 'DOTT'],
            'AVAX': ['AVALANCHE', 'AVAXX'],
            'MATIC': ['POLYGON', 'MATICC'],
            'DOGE': ['DOGECOIN', 'DOGGE'],
            'SHIB': ['SHIBAINU', 'SHIBA'],
            'PEPE': ['PEPECOIN', 'PEPEE'],
            'WIF': ['DOGWIFHAT', 'WIFF'],
        }
        
        # Часто встречающиеся опечатки
        self.common_typos = {
            'BTTC': 'BTC',
            'ETTH': 'ETH', 
            'ETHH': 'ETH',
            'ETHE': 'ETH',
            'BTCC': 'BTC',
            'BTCCC': 'BTC',
            'SOLL': 'SOL',
            'ADAA': 'ADA',
            'XRPP': 'XRP'
        }
        
        # Разделители для парсинга
        self.separators = ['/', '-', '_', ' ', '']
    
    def _generate_pairs(self, quote_currencies: List[str]) -> Set[str]:
        """Генерация пар для заданных котировочных валют"""
        pairs = set()
        for base in self.base_currencies:
            for quote in quote_currencies:
                pairs.add(f"{base}{quote}")
        return pairs
    
    def normalize_symbol(self, raw_symbol: str) -> Optional[str]:
        """Продвинутая нормализация символа с исправлением любых опечаток"""
        if not raw_symbol:
            return None
        
        # Очищаем от лишних символов
        cleaned = raw_symbol.upper().strip()
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c in self.separators)
        
        # Убираем # $ и другие префиксы
        if cleaned.startswith(('#', '$')):
            cleaned = cleaned[1:]
        
        if not cleaned:
            return None
        
        # Используем новый мощный алгоритм поиска
        match_result = self.find_best_match(cleaned)
        
        if match_result:
            symbol, confidence, match_type = match_result
            
            # Логируем найденное совпадение
            if match_type == "exact":
                # Точное совпадение - не логируем
                pass
            elif confidence >= 0.8:
                print(f"🎯 Symbol auto-corrected: '{cleaned}' → '{symbol}' (confidence: {confidence:.2f}, type: {match_type})")
            elif confidence >= 0.6:
                print(f"🔧 Symbol suggestion: '{cleaned}' → '{symbol}' (confidence: {confidence:.2f}, type: {match_type})")
            
            return symbol
        
        # Если ничего не найдено, пробуем извлечь базовую валюту и добавить USDT
        base_currency = self._extract_base_currency(cleaned)
        if base_currency:
            candidate = f"{base_currency}USDT"
            if candidate in self.all_pairs:
                print(f"💡 Base currency detected: '{cleaned}' → '{candidate}'")
                return candidate
        
        return None
    
    def _extract_base_currency(self, symbol: str) -> Optional[str]:
        """Извлечение базовой валюты из символа"""
        # Сначала проверяем точные совпадения
        for base in self.base_currencies:
            if symbol.startswith(base):
                return base
        
        # Проверяем альтернативные названия
        for base, alternatives in self.alternative_names.items():
            for alt in alternatives:
                if alt in symbol.upper():
                    return base
            
            # Проверяем начало строки на альтернативы
            for alt in alternatives:
                if symbol.startswith(alt):
                    return base
        
        # Пробуем найти через similarity для коротких символов
        for base in self.base_currencies:
            if len(base) <= 4:  # Только короткие символы
                ratio = difflib.SequenceMatcher(None, symbol[:len(base)+1], base).ratio()
                if ratio >= 0.8:  # 80% похожести
                    return base
        
        return None
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Вычисление расстояния Левенштейна между двумя строками"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _fuzzy_match_score(self, symbol: str, candidate: str) -> float:
        """Продвинутый скор схожести с учетом разных типов опечаток"""
        if not symbol or not candidate:
            return 0.0
        
        # Базовое расстояние Левенштейна
        lev_dist = self._levenshtein_distance(symbol.upper(), candidate.upper())
        max_len = max(len(symbol), len(candidate))
        lev_score = 1.0 - (lev_dist / max_len) if max_len > 0 else 0.0
        
        # Бонус за совпадение начала (часто опечатки в конце)
        start_match = 0
        for i in range(min(len(symbol), len(candidate))):
            if symbol[i].upper() == candidate[i].upper():
                start_match += 1
            else:
                break
        start_score = start_match / max(len(symbol), len(candidate))
        
        # Бонус за совпадение длины (часто опечатки не меняют длину)
        length_score = 1.0 - abs(len(symbol) - len(candidate)) / max(len(symbol), len(candidate))
        
        # Бонус за содержание базовых букв (BTC, ETH и тд)
        base_score = 0.0
        for base in self.base_currencies:
            if base in symbol.upper() and base in candidate.upper():
                base_score = 0.3
                break
        
        # Комбинированный скор
        total_score = (lev_score * 0.5 + start_score * 0.3 + length_score * 0.2 + base_score)
        
        return min(1.0, total_score)
    
    def _generate_typo_variants(self, symbol: str) -> List[str]:
        """Генерация возможных вариантов с опечатками для поиска"""
        if not symbol or len(symbol) < 2:
            return []
        
        variants = set()
        symbol = symbol.upper()
        
        # 1. Удаление одного символа
        for i in range(len(symbol)):
            variant = symbol[:i] + symbol[i+1:]
            if len(variant) >= 2:
                variants.add(variant)
        
        # 2. Добавление одного символа
        for i in range(len(symbol) + 1):
            for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                variant = symbol[:i] + char + symbol[i:]
                if len(variant) <= 15:  # Разумный лимит
                    variants.add(variant)
        
        # 3. Замена одного символа
        for i in range(len(symbol)):
            for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if char != symbol[i]:
                    variant = symbol[:i] + char + symbol[i+1:]
                    variants.add(variant)
        
        # 4. Перестановка соседних символов
        for i in range(len(symbol) - 1):
            variant = symbol[:i] + symbol[i+1] + symbol[i] + symbol[i+2:]
            variants.add(variant)
        
        return list(variants)
    
    def _find_similar_symbol(self, symbol: str) -> Optional[str]:
        """Улучшенный поиск похожего символа с приоритетом USDT пар"""
        if not symbol:
            return None
        
        symbol = symbol.upper()
        best_match = None
        best_score = 0.0
        
        # ПРИОРИТЕТ 1: Ищем точное совпадение базы + USDT
        for base in self.base_currencies:
            if base in symbol:
                usdt_candidate = f"{base}USDT"
                if usdt_candidate in self.all_pairs:
                    score = self._fuzzy_match_score(symbol, usdt_candidate)
                    if score >= 0.6:  # Более низкий порог для USDT пар
                        return usdt_candidate
        
        # ПРИОРИТЕТ 2: Ищем похожие USDT пары
        usdt_pairs = [pair for pair in self.all_pairs if pair.endswith('USDT')]
        for pair in usdt_pairs:
            score = self._fuzzy_match_score(symbol, pair)
            if score > best_score:
                best_score = score
                best_match = pair
        
        # ПРИОРИТЕТ 3: Ищем другие USD пары
        if best_score < 0.7:
            usd_pairs = [pair for pair in self.all_pairs if pair.endswith(('USD', 'USDC'))]
            for pair in usd_pairs:
                score = self._fuzzy_match_score(symbol, pair)
                if score > best_score:
                    best_score = score
                    best_match = pair
        
        # ПРИОРИТЕТ 4: Только в крайнем случае - другие пары
        if best_score < 0.8:
            for pair in self.all_pairs:
                if not pair.endswith(('USDT', 'USD', 'USDC')):
                    score = self._fuzzy_match_score(symbol, pair)
                    if score > best_score:
                        best_score = score
                        best_match = pair
        
        # Возвращаем только если достаточно уверены
        return best_match if best_score >= 0.65 else None
    
    def get_suggestions(self, symbol: str, limit: int = 5) -> List[str]:
        """Получение умных предложений для символа с исправлением опечаток"""
        if not symbol:
            return []
            
        symbol = symbol.upper().strip()
        suggestions = []
        
        # Список всех кандидатов с их скорами
        candidates = []
        
        # Проверяем все пары с продвинутым scoring
        for pair in self.all_pairs:
            score = self._fuzzy_match_score(symbol, pair)
            if score >= 0.3:  # Минимальный порог для предложений
                candidates.append((pair, score))
        
        # Дополнительный бонус для пар с известными базами
        for base in self.base_currencies:
            if base in symbol:
                for pair in self.all_pairs:
                    if pair.startswith(base):
                        # Увеличиваем скор если база совпадает
                        score = self._fuzzy_match_score(symbol, pair) + 0.2
                        candidates.append((pair, min(1.0, score)))
        
        # Убираем дубликаты и сортируем по скору
        unique_candidates = {}
        for pair, score in candidates:
            if pair not in unique_candidates or unique_candidates[pair] < score:
                unique_candidates[pair] = score
        
        sorted_candidates = sorted(unique_candidates.items(), key=lambda x: x[1], reverse=True)
        
        # Берем топ предложений
        suggestions = [pair for pair, score in sorted_candidates[:limit]]
        
        return suggestions
    
    def find_best_match(self, symbol: str) -> Optional[tuple]:
        """Найти лучшее совпадение с приоритетом USDT пар"""
        if not symbol:
            return None
        
        symbol = symbol.upper().strip()
        best_match = None
        best_score = 0.0
        match_type = "unknown"
        
        # 1. Точное совпадение
        if symbol in self.all_pairs:
            return (symbol, 1.0, "exact")
        
        # 2. Известная опечатка → USDT
        if symbol in self.common_typos:
            base = self.common_typos[symbol]
            candidate = f"{base}USDT"
            if candidate in self.all_pairs:
                return (candidate, 0.95, "known_typo")
        
        # 3. Альтернативное название → USDT
        for base, alternatives in self.alternative_names.items():
            if symbol in alternatives:
                candidate = f"{base}USDT"
                if candidate in self.all_pairs:
                    return (candidate, 0.90, "alternative_name")
        
        # 4. ПРИОРИТЕТНЫЙ поиск базовой валюты + USDT
        for base in self.base_currencies:
            if base in symbol or symbol.startswith(base):
                candidate = f"{base}USDT"
                if candidate in self.all_pairs:
                    score = self._fuzzy_match_score(symbol, candidate)
                    if score >= 0.6:  # Низкий порог для USDT
                        return (candidate, max(0.8, score), "base_currency_usdt")
        
        # 5. Fuzzy matching с приоритетом USDT
        # Сначала USDT пары
        usdt_pairs = [pair for pair in self.all_pairs if pair.endswith('USDT')]
        for pair in usdt_pairs:
            score = self._fuzzy_match_score(symbol, pair)
            # Бонус для USDT пар
            adjusted_score = score + 0.1 if score > 0.5 else score
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_match = pair
                if adjusted_score >= 0.9:
                    match_type = "high_similarity_usdt"
                elif adjusted_score >= 0.7:
                    match_type = "medium_similarity_usdt"
                else:
                    match_type = "low_similarity_usdt"
        
        # Затем USD/USDC пары (если USDT не подошло)
        if best_score < 0.8:
            usd_pairs = [pair for pair in self.all_pairs if pair.endswith(('USD', 'USDC'))]
            for pair in usd_pairs:
                score = self._fuzzy_match_score(symbol, pair)
                if score > best_score:
                    best_score = score
                    best_match = pair
                    if score >= 0.9:
                        match_type = "high_similarity_usd"
                    elif score >= 0.7:
                        match_type = "medium_similarity_usd"
                    else:
                        match_type = "low_similarity_usd"
        
        # В крайнем случае - другие пары
        if best_score < 0.8:
            other_pairs = [pair for pair in self.all_pairs if not pair.endswith(('USDT', 'USD', 'USDC'))]
            for pair in other_pairs:
                score = self._fuzzy_match_score(symbol, pair)
                if score > best_score:
                    best_score = score
                    best_match = pair
                    if score >= 0.9:
                        match_type = "high_similarity"
                    elif score >= 0.7:
                        match_type = "medium_similarity"
                    else:
                        match_type = "low_similarity"
        
        if best_match and best_score >= 0.6:
            return (best_match, best_score, match_type)
        
        return None
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Проверка валидности символа"""
        return symbol.upper() in self.all_pairs

# Глобальный экземпляр
_crypto_db = None

def get_crypto_symbols_db() -> CryptoSymbolsDatabase:
    """Получение глобального экземпляра базы символов"""
    global _crypto_db
    if _crypto_db is None:
        _crypto_db = CryptoSymbolsDatabase()
    return _crypto_db
