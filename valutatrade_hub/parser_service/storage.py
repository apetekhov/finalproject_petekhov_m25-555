import json
import os
import tempfile
from datetime import datetime, timezone

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    """Хранилище курсов: история и текущие значения (rates.json)."""

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()

    # ------------------------------
    # Универсальное чтение JSON
    # ------------------------------
    def read_json(self, path: str):
        """Публичный метод для безопасного чтения JSON."""
        if not os.path.exists(path):
            return [] if "exchange_rates" in path else {}
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] if "exchange_rates" in path else {}

    # ------------------------------
    # Безопасная запись (атомарная)
    # ------------------------------
    def _atomic_write(self, file_path: str, data) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        fd, tmp = tempfile.mkstemp()
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(tmp, file_path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    # ------------------------------
    # Добавление в историю
    # ------------------------------
    def append_exchange_history(self, rates: dict):
        """Добавляем новые записи в exchange_rates.json."""
        history = self.read_json(self.config.HISTORY_FILE_PATH)
        if not isinstance(history, list):
            history = []

        for pair, info in rates.items():
            from_code, to_code = pair.split("_")
            entry = {
                "id": f"{pair}_{datetime.now(timezone.utc).isoformat()}",
                "from_currency": from_code,
                "to_currency": to_code,
                "rate": info["rate"],
                "timestamp": info["updated_at"],
                "source": info["source"],
            }
            history.append(entry)

        self._atomic_write(self.config.HISTORY_FILE_PATH, history)

    # ------------------------------
    # Обновление кэша
    # ------------------------------
    def update_rates_cache(self, rates: dict):
        """Перезаписываем актуальный кэш rates.json."""
        cache = {
            "pairs": rates,
            "last_refresh": datetime.now(timezone.utc).isoformat(),
        }
        self._atomic_write(self.config.RATES_FILE_PATH, cache)