import os
from typing import Any


class SettingsLoader:
    """
    Singleton-класс для загрузки и хранения конфигурации проекта.
    Используется __new__, чтобы гарантировать существование только одного экземпляра.
    """

    _instance = None  # хранит единственный экземпляр класса

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Инициализация при первом создании
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return  # предотвратить повторную инициализацию

        self.config = self._load_default_config()
        self._initialized = True

    def _load_default_config(self) -> dict[str, Any]:
        """Загружает конфигурацию проекта (можно расширить для чтения config.json)."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        data_dir = os.path.join(base_dir, "data")
        logs_dir = os.path.join(base_dir, "logs")

        return {
            "DATA_DIR": data_dir,
            "USERS_FILE": os.path.join(data_dir, "users.json"),
            "PORTFOLIOS_FILE": os.path.join(data_dir, "portfolios.json"),
            "RATES_FILE": os.path.join(data_dir, "rates.json"),
            "LOGS_DIR": logs_dir,
            "BASE_CURRENCY": "USD",
            "RATES_TTL_SECONDS": 300,  # 5 минут
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Возвращает значение по ключу из конфигурации."""
        return self.config.get(key, default)

    def reload(self) -> None:
        """Перезагрузка конфигурации (на будущее — если будет внешний config.json)."""
        self.config = self._load_default_config()