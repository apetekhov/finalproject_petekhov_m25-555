import json
import os
from datetime import datetime

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import setup_logger

logger = setup_logger()
settings = SettingsLoader()

USERS_FILE = settings.get("USERS_FILE")
PORTFOLIOS_FILE = settings.get("PORTFOLIOS_FILE")
RATES_FILE = settings.get("RATES_FILE")


# ---------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---------------------- #

def load_json(file_path: str) -> list | dict:
    if not os.path.exists(file_path):
        name = os.path.basename(file_path)
        if name in ("users.json", "portfolios.json"):
            return []
        if name == "rates.json":
            return {}
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            name = os.path.basename(file_path)
            if name in ("users.json", "portfolios.json"):
                return []
            if name == "rates.json":
                return {}
            return {}


def save_json(file_path: str, data) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_user_portfolio(user_id: int) -> dict | None:
    portfolios = load_json(PORTFOLIOS_FILE)
    return next((p for p in portfolios if p["user_id"] == user_id), None)


def _refresh_rate(pair_key: str) -> dict | None:
    """Фейтовое обновление курса (вместо Parser Service). Возвращает dict или None."""
    now = datetime.now().isoformat(timespec="seconds")
    fake_rates = {
        "USD_BTC": {"rate": 1 / 59337.21, "updated_at": now},
        "BTC_USD": {"rate": 59337.21, "updated_at": now},
        "EUR_USD": {"rate": 1.0786, "updated_at": now},
        "USD_EUR": {"rate": 1 / 1.0786, "updated_at": now},
        "RUB_USD": {"rate": 0.01016, "updated_at": now},
        "USD_RUB": {"rate": 98.42, "updated_at": now},
        "ETH_USD": {"rate": 3720.00, "updated_at": now},
        "USD_ETH": {"rate": 1 / 3720.00, "updated_at": now},
    }
    return fake_rates.get(pair_key)


# ---------------------- ОСНОВНЫЕ ОПЕРАЦИИ ---------------------- #

@log_action("BUY")
def buy(user_id: int, currency_code: str, amount: float) -> None:
    """Покупка валюты с логированием и валидацией."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError as e:
        logger.error(str(e))
        raise

    # Загружаем весь список портфелей
    portfolios = load_json(PORTFOLIOS_FILE)

    # Ищем нужный портфель пользователя
    portfolio = next((p for p in portfolios if p["user_id"] == user_id), None)
    if not portfolio:
        portfolio = {"user_id": user_id, "wallets": {}}

    wallets = portfolio["wallets"]
    if currency_code not in wallets:
        wallets[currency_code] = {"currency_code": currency_code, "balance": 0.0}

    old_balance = wallets[currency_code]["balance"]
    new_balance = old_balance + amount
    wallets[currency_code]["balance"] = new_balance

    # Загружаем курсы и рассчитываем стоимость
    rate = None
    estimated_value = None
    try:
        rate, _updated = get_rate(currency_code, "USD")
        estimated_value = amount * rate
    except ApiRequestError:
        # курса нет — покупку не блокируем, просто без оценки
        pass

    # Сохраняем обновлённый список портфелей
    portfolios = load_json(PORTFOLIOS_FILE)
    if not isinstance(portfolios, list):
        portfolios = []
    existing = next((p for p in portfolios if p["user_id"] == user_id), None)
    if existing:
        existing.update(portfolio)
    else:
        portfolios.append(portfolio)
    save_json(PORTFOLIOS_FILE, portfolios)

    logger.info(
        f"Покупка {currency_code}: {amount} @ {rate} → {estimated_value:.2f} USD "
        f"(user_id={user_id})"
    )


@log_action("SELL")
def sell(user_id: int, currency_code: str, amount: float) -> None:
    """Продажа валюты с валидацией и логированием."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError as e:
        logger.error(str(e))
        raise

    portfolios = load_json(PORTFOLIOS_FILE)
    portfolio = next((p for p in portfolios if p["user_id"] == user_id), None)
    if not portfolio:
        raise ValueError(f"Портфель для user_id={user_id} не найден")

    wallets = portfolio["wallets"]
    if currency_code not in wallets:
        raise CurrencyNotFoundError(f"У вас нет кошелька '{currency_code}'")

    balance = wallets[currency_code]["balance"]
    if balance < amount:
        raise InsufficientFundsError(balance, amount, currency_code)

    wallets[currency_code]["balance"] -= amount

    rate = None
    estimated_revenue = None
    try:
        rate, _updated = get_rate(currency_code, "USD")
        estimated_revenue = amount * rate
    except ApiRequestError:
        # курса нет — продажу не блокируем, просто без оценки
        pass

    save_json(PORTFOLIOS_FILE, portfolios)

    logger.info(
        f"Продажа {currency_code}: {amount} @ {rate} → {estimated_revenue:.2f} USD "
        f"(user_id={user_id})"
    )


@log_action("GET_RATE")
def get_rate(from_code: str, to_code: str) -> tuple[float, str]:
    # валидируем коды
    get_currency(from_code)
    get_currency(to_code)

    rates = load_json(RATES_FILE)
    key = f"{from_code}_{to_code}"
    rate_info = rates.get(key)
    ttl_seconds = settings.get("RATES_TTL_SECONDS")

    def is_fresh(info: dict) -> bool:
        try:
            updated_at = datetime.fromisoformat(info["updated_at"])
            return (datetime.now() - updated_at).total_seconds() <= ttl_seconds
        except Exception:
            return False

    # если курса нет — пробуем обновить
    if not rate_info:
        new_info = _refresh_rate(key)
        if not new_info:
            raise ApiRequestError(f"Курс {from_code}->{to_code} недоступен.")
        rates[key] = new_info
        save_json(RATES_FILE, rates)
        return new_info["rate"], new_info["updated_at"]

    # если курс есть, но устарел — тоже пробуем обновить
    if not is_fresh(rate_info):
        new_info = _refresh_rate(key)
        if not new_info:
            raise ApiRequestError("Данные курсов устарели. Повторите попытку позже.")
        rates[key] = new_info
        save_json(RATES_FILE, rates)
        return new_info["rate"], new_info["updated_at"]

    # актуально — отдаём как есть
    return rate_info["rate"], rate_info["updated_at"]