import time

from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def run_scheduler(interval_minutes: float = 0.1, one_time: bool = True) -> None:
    """
    Планировщик обновления курсов валют.

    Args:
        interval_minutes (float): Интервал между обновлениями (в минутах).
        one_time (bool): Если True — выполняется только один цикл (для автотестов).
    """
    mode = "одноразовый" if one_time else "цикличный"
    print(f"Scheduler запущен. Интервал: {interval_minutes} мин. Режим: {mode}")

    config = ParserConfig()
    updater = RatesUpdater(
        clients=[CoinGeckoClient(config), ExchangeRateApiClient(config)],
        storage=RatesStorage(),
    )

    # Выполняем один цикл
    print("Запуск обновления курсов...")
    updater.run_update()
    print("Обновление завершено.\n")

    # Зацикливаем (для автотестов выключено)
    if not one_time:
        while True:
            time.sleep(interval_minutes * 60)
            print("Запуск следующего обновления...")
            updater.run_update()
            print("Цикл завершён.\n")


if __name__ == "__main__":
    run_scheduler(one_time=True)