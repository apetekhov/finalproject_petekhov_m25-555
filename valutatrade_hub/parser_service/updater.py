from valutatrade_hub.logging_config import setup_logger
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import (
    append_exchange_history,
    update_rates_cache,
)
from valutatrade_hub.core.exceptions import ApiRequestError

logger = setup_logger()
config = ParserConfig()


class RatesUpdater:
    """Координация обновления курсов валют."""

    def __init__(self):
        self.clients = [
            CoinGeckoClient(config),
            ExchangeRateApiClient(config),
        ]

    def run_update(self):
        logger.info("Starting rates update...")
        all_rates = {}
        total = 0
        errors = 0

        for client in self.clients:
            name = client.__class__.__name__
            try:
                logger.info(f"Fetching from {name}...")
                result = client.fetch_rates()
                logger.info(f"{name}: OK ({len(result)} rates)")
                all_rates.update(result)
                total += len(result)
            except ApiRequestError as e:
                logger.error(f"{name} failed: {e}")
                errors += 1
            except Exception as e:
                logger.error(f"{name} unexpected error: {e}")
                errors += 1

        if all_rates:
            append_exchange_history(all_rates)
            update_rates_cache(all_rates)
            logger.info(f"Updated {total} rates successfully.")
        else:
            logger.warning("No rates fetched.")

        if errors:
            logger.warning(f"Update completed with {errors} errors.")
        else:
            logger.info("Update successful.")