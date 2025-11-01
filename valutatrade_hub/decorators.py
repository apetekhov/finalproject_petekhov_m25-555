import datetime
import functools

from valutatrade_hub.logging_config import setup_logger

logger = setup_logger()


def log_action(action_name: str, verbose: bool = False):
    """
    Декоратор для логирования операций (BUY, SELL, REGISTER, LOGIN).
    Не подавляет исключения — только фиксирует их.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.datetime.now().isoformat(timespec="seconds")
            username = kwargs.get("username") or getattr(args[0], "username", "N/A")
            currency = kwargs.get("currency", "N/A")
            amount = kwargs.get("amount", "N/A")
            rate = kwargs.get("rate", "N/A")
            base = kwargs.get("base", "USD")

            try:
                result = func(*args, **kwargs)
                msg = (
                    f"{action_name.upper()} user='{username}' currency='{currency}' "
                    f"amount={amount} rate={rate} base='{base}' result=OK"
                )
                if verbose:
                    msg += f" context={kwargs}"
                logger.info(f"{timestamp} {msg}")
                return result

            except Exception as e:
                msg = (
                    f"{action_name.upper()} user='{username}' currency='{currency}' "
                    f"amount={amount} rate={rate} base='{base}' "
                    f"result=ERROR error_type='{type(e).__name__}' error_message='{e}'"
                )
                logger.error(f"{timestamp} {msg}")
                raise  # пробрасываем исключение дальше

        return wrapper
    return decorator