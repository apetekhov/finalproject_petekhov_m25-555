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