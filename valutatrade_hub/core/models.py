import hashlib
import os
from datetime import datetime

class User:
    """
    Класс, описывающий пользователя системы ValutaTrade Hub.
    """

    def __init__(self, user_id: int, username: str, password: str, registration_date: datetime | None = None):
        # Приватные атрибуты
        self._user_id = user_id
        self._username = None
        self._hashed_password = None
        self._salt = os.urandom(8).hex()  # генерируем соль
        self._registration_date = registration_date or datetime.now()

        # Устанавливаем через сеттеры
        self.username = username
        self.password = password

    # ----------------------------
    # Геттеры и сеттеры
    # ----------------------------
    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value: str):
        if not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def password(self):
        return self._hashed_password

    @password.setter
    def password(self, plain_password: str):
        if len(plain_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        # Хешируем пароль с солью
        self._hashed_password = self._hash_password(plain_password)

    # ----------------------------
    # Вспомогательные методы
    # ----------------------------
    def _hash_password(self, password: str) -> str:
        """
        Возвращает SHA256-хэш пароля с солью.
        """
        return hashlib.sha256((password + self._salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """
        Проверяет введённый пароль.
        """
        return self._hashed_password == hashlib.sha256((password + self._salt).encode()).hexdigest()

    def change_password(self, new_password: str):
        """
        Меняет пароль с пересозданием соли.
        """
        if len(new_password) < 4:
            raise ValueError("Новый пароль должен быть не короче 4 символов.")
        self._salt = os.urandom(8).hex()
        self._hashed_password = self._hash_password(new_password)

    def get_user_info(self) -> dict:
        """
        Возвращает словарь с публичной информацией о пользователе.
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

class Wallet:
    """
    Класс кошелька для одной конкретной валюты.
    Управляет балансом и обеспечивает проверки на корректность операций.
    """

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code:
            raise ValueError("Код валюты должен быть непустой строкой.")

        if not isinstance(balance, (int, float)) or balance < 0:
            raise ValueError("Начальный баланс должен быть числом >= 0.")

        self.currency_code = currency_code.upper()
        self._balance = float(balance)

    # --- Геттер для баланса ---
    @property
    def balance(self) -> float:
        return self._balance

    # --- Сеттер для баланса ---
    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    # --- Метод пополнения ---
    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма пополнения должна быть числом.")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной.")
        self._balance += float(amount)

    # --- Метод снятия ---
    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма снятия должна быть числом.")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной.")
        if amount > self._balance:
            raise ValueError("Недостаточно средств для снятия.")
        self._balance -= float(amount)

    # --- Метод для вывода информации ---
    def get_balance_info(self) -> dict:
        """Возвращает информацию о валюте и текущем балансе."""
        return {
            "currency_code": self.currency_code,
            "balance": round(self._balance, 2),
        }