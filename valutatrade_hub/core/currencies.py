from abc import ABC, abstractmethod
from dataclasses import dataclass

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


@dataclass
class Currency(ABC):
    """
    Абстрактный базовый класс валюты.
    """

    name: str
    code: str

    def __post_init__(self):
        # Валидация кода валюты
        if not self.code or not self.code.isupper() or not (2 <= len(self.code) <= 5):
            raise ValueError("Некорректный код валюты.")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Название валюты не может быть пустым.")

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты (для UI и логов)."""
        pass


@dataclass
class FiatCurrency(Currency):
    """
    Фиатная валюта (USD, EUR, RUB и т.д.)
    """

    issuing_country: str

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


@dataclass
class CryptoCurrency(Currency):
    """
    Криптовалюта (BTC, ETH и т.д.)
    """

    algorithm: str
    market_cap: float

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# --- Реестр валют (фабрика) ---
def get_currency(code: str) -> Currency:
    """
    Возвращает экземпляр валюты по коду.
    Если код неизвестен — выбрасывает CurrencyNotFoundError.
    """

    code = code.upper()
    registry = {
        "USD": FiatCurrency("US Dollar", "USD", "United States"),
        "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
        "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
        "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.45e11),
    }

    if code not in registry:
        raise CurrencyNotFoundError(f"Неизвестная валюта: {code}")

    return registry[code]