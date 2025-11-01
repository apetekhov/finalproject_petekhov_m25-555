import logging
import os
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logger() -> logging.Logger:
    """Создаёт и настраивает ротацию логов для доменных операций."""
    settings = SettingsLoader()
    logs_dir = settings.get("LOGS_DIR")

    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "actions.log")

    logger = logging.getLogger("valutatrade")
    logger.setLevel(logging.INFO)

    # Проверка на дублирование хендлеров при повторных вызовах
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(levelname)s %(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger