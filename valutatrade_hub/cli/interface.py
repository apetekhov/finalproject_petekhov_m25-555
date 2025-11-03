import hashlib
import json
import random
import shlex
import string
from datetime import datetime
from pathlib import Path

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import buy, get_rate, sell
from valutatrade_hub.infra.settings import SettingsLoader

settings = SettingsLoader()
USERS_FILE = settings.get("USERS_FILE")
PORTFOLIOS_FILE = settings.get("PORTFOLIOS_FILE")
CURRENT_USER: dict | None = None


def load_json(file_path) -> list | dict:
    file_path = Path(file_path)
    if not file_path.exists():
        if file_path.name in ("users.json", "portfolios.json"):
            return []
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            if file_path.name in ("users.json", "portfolios.json"):
                return []
            return {}


def save_json(file_path, data) -> None:
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def register(args: list[str]) -> None:
    """
    Регистрирует нового пользователя.
    Пример: register --username alice --password 1234
    """
    # --- Парсинг аргументов ---
    try:
        args_dict = {}
        for i in range(0, len(args), 2):
            key, value = args[i], args[i + 1]
            args_dict[key] = value
    except (IndexError, ValueError):
        print(
            "Ошибка: неправильный формат. "
            "Пример: register --username alice --password 1234"
        )
        return

    username = args_dict.get("--username")
    password = args_dict.get("--password")

    # --- Проверки ---
    if not username:
        print("Ошибка: имя пользователя не указано.")
        return
    if not password or len(password) < 4:
        print("Ошибка: пароль должен быть не короче 4 символов.")
        return

    # --- Загрузка существующих пользователей ---
    users = load_json(USERS_FILE)

    # --- Проверка уникальности ---
    if any(u["username"] == username for u in users):
        print(f"Имя пользователя '{username}' уже занято.")
        return

    # --- Генерация id и соли ---
    new_id = max((u["user_id"] for u in users), default=0) + 1
    salt = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()

    # --- Создание пользователя ---
    user = {
        "user_id": new_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": datetime.now().isoformat(),
    }
    users.append(user)
    save_json(USERS_FILE, users)

    # --- Создание пустого портфеля ---
    portfolios = load_json(PORTFOLIOS_FILE)
    portfolios.append({"user_id": new_id, "wallets": {}})
    save_json(PORTFOLIOS_FILE, portfolios)

    print(
        f"Пользователь '{username}' зарегистрирован (id={new_id}). "
        f"Войдите: login --username {username} --password ****"
    )


def login(args: list[str]) -> None:
    """
    Авторизация пользователя.
    Пример: login --username alice --password 1234
    """
    # --- Парсинг аргументов ---
    try:
        args_dict = {}
        for i in range(0, len(args), 2):
            key, value = args[i], args[i + 1]
            args_dict[key] = value
    except (IndexError, ValueError):
        print(
            "Ошибка: неправильный формат. "
            "Пример: login --username alice --password 1234"
        )
        return

    username = args_dict.get("--username")
    password = args_dict.get("--password")

    if not username or not password:
        print("Ошибка: укажите и имя пользователя, и пароль.")
        return

    # --- Загрузка пользователей ---
    users = load_json(USERS_FILE)
    user = next((u for u in users if u["username"] == username), None)

    if not user:
        print(f"Пользователь '{username}' не найден.")
        return

    # --- Проверка пароля ---
    hashed_input = hashlib.sha256((password + user["salt"]).encode()).hexdigest()
    if hashed_input != user["hashed_password"]:
        print("Неверный пароль.")
        return

    # --- Если всё ок ---
    print(f"Вы вошли как '{username}'")

    global CURRENT_USER
    CURRENT_USER = user


def show_portfolio(args: list[str]) -> None:
    """
    Показывает портфель пользователя.
    Пример: show-portfolio --base USD
    """
    global CURRENT_USER

    if not CURRENT_USER:
        print("Сначала выполните login.")
        return

    # --- Парсинг аргументов ---
    base_currency = "USD"
    if "--base" in args:
        try:
            base_currency = args[args.index("--base") + 1].upper()
        except IndexError:
            print("Ошибка: не указана базовая валюта после --base.")
            return

    # --- Проверка известной валюты ---
    known_currencies = ["USD", "EUR", "BTC", "ETH", "RUB"]
    if base_currency not in known_currencies:
        print(f"Неизвестная базовая валюта '{base_currency}'.")
        return

    # --- Загрузка портфелей и курсов ---
    portfolios = load_json(PORTFOLIOS_FILE)
    # rates = load_json(os.path.join(DATA_DIR, "rates.json")) #пока не используется

    portfolio = next(
        (p for p in portfolios if p["user_id"] == CURRENT_USER["user_id"]),
        None,
    )

    if not portfolio or not portfolio["wallets"]:
        print("У вас пока нет кошельков.")
        return

    # --- Заглушка для курсов ---
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59337.21,
        "ETH": 3720.00,
        "RUB": 0.01016,
    }

    total_value = 0.0
    print(
        f"Портфель пользователя '{CURRENT_USER['username']}' "
        f"(база: {base_currency}):"
    )

    for code, data in portfolio["wallets"].items():
        balance = data.get("balance", 0.0)
        rate = exchange_rates.get(code, 0)
        base_rate = exchange_rates.get(base_currency, 1)
        value_in_base = (balance * rate) / base_rate if base_rate != 0 else 0

        print(f"- {code}: {balance:.4f}  →  {value_in_base:.2f} {base_currency}")
        total_value += value_in_base

    print("-" * 40)
    print(f"ИТОГО: {total_value:,.2f} {base_currency}")


def run_app() -> None:
    """Главный цикл CLI."""
    print("ValutaTrade CLI — введите команду (help для справки).")

    while True:
        try:
            command_line = input("> ").strip()
            if not command_line:
                continue

            parts = shlex.split(command_line)
            command, args = parts[0], parts[1:]

            if command == "exit":
                print("Выход из программы.")
                break

            elif command == "help":
                print(
                    "Доступные команды: "
                    "register, login, show-portfolio, buy, sell, "
                    "get-rate, update-rates, show-rates, exit"
                )

            elif command == "register":
                register(args)

            elif command == "login":
                login(args)

            elif command == "show-portfolio":
                show_portfolio(args)

            elif command == "buy":
                try:
                    args_dict = {args[i]: args[i + 1] for i in range(0, len(args), 2)}
                    currency = args_dict.get("--currency")
                    amount = float(args_dict.get("--amount", 0))

                    if not CURRENT_USER:
                        print("Сначала выполните login.")
                        continue

                    buy(CURRENT_USER["user_id"], currency, amount)
                    print(f"Покупка {amount:.4f} {currency} успешно выполнена.")

                except ValueError as e:
                    print(f"Ошибка ввода: {e}")
                except CurrencyNotFoundError as e:
                    print(str(e))
                except ApiRequestError as e:
                    print(f"Не удалось получить курс: {e}")
                except Exception as e:
                    print(f"Неожиданная ошибка: {e}")

            elif command == "sell":
                try:
                    args_dict = {args[i]: args[i + 1] for i in range(0, len(args), 2)}
                    currency = args_dict.get("--currency")
                    amount = float(args_dict.get("--amount", 0))

                    if not CURRENT_USER:
                        print("Сначала выполните login.")
                        continue

                    sell(CURRENT_USER["user_id"], currency, amount)
                    print(f"Продажа {amount:.4f} {currency} успешно выполнена.")

                except InsufficientFundsError as e:
                    print(str(e))
                except CurrencyNotFoundError as e:
                    print(str(e))
                except ApiRequestError as e:
                    print(f"Ошибка получения курса: {e}")
                except ValueError as e:
                    print(f"Ошибка ввода: {e}")
                except Exception as e:
                    print(f"Неожиданная ошибка: {e}")

            elif command == "get-rate":
                try:
                    args_dict = {args[i]: args[i + 1] for i in range(0, len(args), 2)}
                    from_code = args_dict.get("--from")
                    to_code = args_dict.get("--to")

                    if not from_code or not to_code:
                        print("Ошибка: укажите валюты через --from и --to.")
                        continue

                    rate, updated_at = get_rate(from_code, to_code)
                    print(
                        f"Курс {from_code}→{to_code}: {rate:.8f} "
                        f"(обновлено: {updated_at})"
                    )

                except CurrencyNotFoundError as e:
                    print(str(e))
                    print(
                        "Попробуйте команду help "
                        "или проверьте список доступных валют."
                    )
                except ApiRequestError as e:
                    print(f"Ошибка API: {e}. Повторите попытку позже.")
                except Exception as e:
                    print(f"Неожиданная ошибка: {e}")

            elif command == "update-rates":
                from valutatrade_hub.parser_service.updater import RatesUpdater
                try:
                    updater = RatesUpdater()
                    updater.run_update()
                except Exception as e:
                    print(f"Ошибка обновления: {e}")

            elif command == "show-rates":
                from valutatrade_hub.parser_service.storage import RatesStorage

                try:
                    storage = RatesStorage()
                    data = storage.read_json(storage.config.RATES_FILE_PATH)

                    if not data or "pairs" not in data or not data["pairs"]:
                        print("Локальный кеш курсов пуст. Выполните 'update-rates'.")
                        continue

                    print(f"Rates from cache (updated at {data['last_refresh']}):")
                    for pair, info in data["pairs"].items():
                        print(f"- {pair}: {info['rate']:.5f} ({info['source']})")

                except FileNotFoundError:
                    print("Файл кеша не найден. Выполните 'update-rates'.")
                except Exception as e:
                    print(f"Ошибка при чтении кеша: {e}")

            else:
                print(f"Неизвестная команда: {command}")

        except (KeyboardInterrupt, EOFError):
            print("\nВыход из программы.")
            break
        
if __name__ == "__main__":
    run_app()