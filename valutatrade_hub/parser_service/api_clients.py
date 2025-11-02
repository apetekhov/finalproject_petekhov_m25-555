from abc import ABC, abstractmethod
from datetime import datetime, timezone

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    @abstractmethod
    def fetch_rates(self) -> dict:
        """Возвращает словарь пар: {'BTC_USD': {...}, ...}."""
        pass


class CoinGeckoClient(BaseApiClient):
    """Получение криптокурсов из CoinGecko."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> dict:
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        url = f"{self.config.COINGECKO_URL}?ids={ids}&vs_currencies=usd"
        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ApiRequestError(f"Ошибка при обращении к CoinGecko: {e}")

        result = {}
        now = datetime.now(timezone.utc).isoformat()
        for code, coin_id in self.config.CRYPTO_ID_MAP.items():
            usd_value = data.get(coin_id, {}).get("usd")
            if usd_value:
                result[f"{code}_USD"] = {
                    "rate": float(usd_value),
                    "updated_at": now,
                    "source": "CoinGecko",
                }
        return result


class ExchangeRateApiClient(BaseApiClient):
    """Получение фиатных курсов из ExchangeRate-API."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> dict:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("Не найден ключ EXCHANGERATE_API_KEY")

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )
        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ApiRequestError(f"Ошибка при обращении к ExchangeRate-API: {e}")

        if data.get("result") != "success":
            raise ApiRequestError(f"Некорректный ответ от API: {data}")

        timestamp = datetime.now(timezone.utc).isoformat()
        rates = data.get("rates", {})

        result = {}
        for code in self.config.FIAT_CURRENCIES:
            rate = rates.get(code)
            if rate:
                result[f"{code}_USD"] = {
                    "rate": float(rate),
                    "updated_at": timestamp,
                    "source": "ExchangeRate-API",
                }
        return result