import json
import os
import tempfile
from datetime import datetime, timezone
from valutatrade_hub.parser_service.config import ParserConfig

config = ParserConfig()


def _atomic_write(file_path: str, data) -> None:
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


def read_json(path: str):
    if not os.path.exists(path):
        return {} if path.endswith(".json") else []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def append_exchange_history(rates: dict):
    """Добавляем новые записи в exchange_rates.json."""
    history = read_json(config.HISTORY_FILE_PATH)
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
    _atomic_write(config.HISTORY_FILE_PATH, history)


def update_rates_cache(rates: dict):
    """Перезаписываем актуальный кэш rates.json."""
    cache = {
        "pairs": rates,
        "last_refresh": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_write(config.RATES_FILE_PATH, cache)