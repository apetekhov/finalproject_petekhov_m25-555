import os
from dataclasses import dataclass, field
from typing import Final


@dataclass
class ParserConfig:
    """Конфигурация API и параметров парсинга."""

    # --- API ключи и эндпоинты ---
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    COINGECKO_URL: Final[str] = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: Final[str] = "https://v6.exchangerate-api.com/v6"

    # --- Валюты ---
    BASE_CURRENCY: Final[str] = "USD"
    FIAT_CURRENCIES: tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple[str, ...] = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP: dict[str, str] = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    })

    # --- Пути ---
    RATES_FILE_PATH: Final[str] = "data/rates.json"
    HISTORY_FILE_PATH: Final[str] = "data/exchange_rates.json"

    # --- Сетевые параметры ---
    REQUEST_TIMEOUT: Final[int] = 10