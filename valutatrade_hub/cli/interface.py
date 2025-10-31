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
            else:
                print(f"Неизвестная команда: {command}")

        except (KeyboardInterrupt, EOFError):
            print("\nВыход из программы.")
            break