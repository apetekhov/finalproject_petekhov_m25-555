#!/usr/bin/env python3
"""
ValutaTrade — основной вход в приложение.
Запускает CLI-интерфейс для управления валютными операциями.
"""

from valutatrade_hub.cli.interface import run_app


def main():
    """Точка входа в систему."""
    print("ValutaTrade запущен.")
    run_app()


if __name__ == "__main__":
    main()