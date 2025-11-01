import hashlib
import json
import os
import random
import shlex
import string
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
CURRENT_USER: dict | None = None


def load_json(file_path: str) -> list | dict:
    """Безопасная загрузка JSON с возвратом пустого списка/словаря при ошибке."""
    if not os.path.exists(file_path):
        return [] if file_path.endswith("users.json") else {}
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return [] if file_path.endswith("users.json") else {}


def save_json(file_path: str, data) -> None:
    """Безопасное сохранение JSON."""
    with open(file_path, "w", encoding="utf-8") as f:
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


def buy(args: list[str]) -> None:
    """
    Покупка валюты.
    Пример: buy --currency BTC --amount 0.05
    """
    global CURRENT_USER

    # --- Проверка логина ---
    if not CURRENT_USER:
        print("Сначала выполните login.")
        return

    # --- Парсинг аргументов ---
    try:
        args_dict = {}
        for i in range(0, len(args), 2):
            key, value = args[i], args[i + 1]
            args_dict[key] = value
    except (IndexError, ValueError):
        print("Ошибка: неправильный формат. Пример: buy --currency BTC --amount 0.05")
        return

    currency = args_dict.get("--currency")
    amount_str = args_dict.get("--amount")

    # --- Валидация аргументов ---
    if not currency:
        print("Ошибка: не указана валюта (--currency).")
        return
    currency = currency.upper()

    try:
        amount = float(amount_str)
    except (TypeError, ValueError):
        print("Ошибка: 'amount' должен быть числом.")
        return

    if amount <= 0:
        print("'amount' должен быть положительным числом.")
        return

    # --- Загрузка портфеля ---
    portfolios = load_json(PORTFOLIOS_FILE)
    portfolio = next((p for p in portfolios if p["user_id"] == CURRENT_USER["user_id"]), None)

    if not portfolio:
        print("Ошибка: портфель пользователя не найден.")
        return

    wallets = portfolio.get("wallets", {})

    # --- Если кошелька ещё нет, создаём ---
    if currency not in wallets:
        wallets[currency] = {"currency_code": currency, "balance": 0.0}

    old_balance = wallets[currency]["balance"]
    new_balance = old_balance + amount
    wallets[currency]["balance"] = new_balance

    # --- Заглушка курса ---
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59300.00,
        "ETH": 3720.00,
        "RUB": 0.01016,
    }

    rate = exchange_rates.get(currency)
    if rate is None:
        print(f"Не удалось получить курс для {currency}→USD.")
        return

    value_usd = amount * rate

    # --- Сохранение портфеля ---
    portfolio["wallets"] = wallets
    save_json(PORTFOLIOS_FILE, portfolios)

    # --- Вывод ---
    print(
        f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:,.2f} USD/{currency}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
        f"Оценочная стоимость покупки: {value_usd:,.2f} USD"
    )

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
                    "register, login, show-portfolio, buy, sell, get-rate, exit"
                )
            elif command == "register":
                register(args)
            elif command == "login":
                login(args)
            elif command == "show-portfolio":
                show_portfolio(args)
            elif command == "buy":
                buy(args)
            else:
                print(f"Неизвестная команда: {command}")

        except (KeyboardInterrupt, EOFError):
            print("\nВыход из программы.")
            break

if __name__ == "__main__":
    run_app()