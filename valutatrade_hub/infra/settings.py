from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class SettingsLoader:
    """Singleton: хранит конфиг путей и TTL и выдаёт их всем слоям."""

    _instance: "SettingsLoader | None" = None

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # type: ignore
            cls._instance._init_values()
        return cls._instance

    def _init_values(self) -> None:
        data_dir = self._resolve_data_dir()

        self._values: dict[str, Any] = {
            # директория с данными
            "DATA_DIR": str(data_dir),

            # файлы данных
            "USERS_FILE": str(data_dir / "users.json"),
            "PORTFOLIOS_FILE": str(data_dir / "portfolios.json"),
            "RATES_FILE": str(data_dir / "rates.json"),

            # TTL курсов в секундах
            "RATES_TTL_SECONDS": int(os.getenv("VALUTATRADE_RATES_TTL", "600")),
        }

    def _resolve_data_dir(self) -> Path:
        """Приоритет:
        1) VALUTATRADE_DATA_DIR (если задана)
        2) ./data в текущей рабочей директории (если существует)
        3) ~/.valutatrade_hub/data (создаём при необходимости)
        """
        # 1) окружение
        env_dir = os.getenv("VALUTATRADE_DATA_DIR")
        if env_dir:
            p = Path(env_dir).expanduser().resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p

        # 2) ./data рядом с тем местом, откуда запускают процесс
        cwd_data = Path.cwd() / "data"
        if cwd_data.exists() and cwd_data.is_dir():
            return cwd_data.resolve()

        # 3) дефолт: домашняя директория
        home_data = Path.home() / ".valutatrade_hub" / "data"
        home_data.mkdir(parents=True, exist_ok=True)
        return home_data

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._values.get(key, default)