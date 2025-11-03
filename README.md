**ValutaTrade Hub** — консольное приложение для работы с валютами и криптовалютами.  
Проект реализует микросервисную архитектуру:
- **Core Service** — отвечает за бизнес-логику (регистрация, портфели, buy/sell, get-rate);
- **Parser Service** — обновляет курсы валют из внешних API (CoinGecko, ExchangeRate-API).

## Установка и запуск
### Установка зависимостей
```bash
make install
```
или вручную:
```bash
poetry install
```
Запуск приложения
```bash
make project
```
или напрямую:
```bash
poetry run project
```
## Основные команды CLI
| Команда | Описание | Пример |
|----------|-----------|---------|
| `register --username <имя> --password <пароль>` | Регистрация нового пользователя | `register --username test --password 1234` |
| `login --username <имя> --password <пароль>` | Авторизация пользователя | `login --username test --password 1234` |
| `buy --currency <код> --amount <число>` | Покупка валюты по текущему курсу | `buy --currency BTC --amount 0.05` |
| `sell --currency <код> --amount <число>` | Продажа валюты | `sell --currency BTC --amount 0.02` |
| `get-rate --from <валюта> --to <валюта>` | Получить актуальный курс валюты | `get-rate --from BTC --to USD` |
| `show-portfolio --base <валюта>` | Показать портфель пользователя в выбранной базе | `show-portfolio --base USD` |
| `update-rates` | Обновить курсы валют (Parser Service) | `update-rates` |
| `show-rates` | Показать кэшированные курсы из `rates.json` | `show-rates` |
| `exit` | Завершить работу приложения | `exit` |

## Parser Service
Parser Service обновляет курсы валют из двух источников:
CoinGecko — криптовалюты (BTC, ETH, SOL)
ExchangeRate-API — фиатные валюты (USD, EUR, GBP, RUB)
Хранилище данных:
data/rates.json — актуальные курсы (кэш для Core)
data/exchange_rates.json — история обновлений

## Кэш и TTL
Core Service использует rates.json для мгновенного доступа к данным.
Период актуальности данных задаётся в infra/settings.py параметром:
```bash
"RATES_TTL_SECONDS": 600  # 10 минут
```
## API-ключ (ExchangeRate-API)
Для получения фиатных валют требуется бесплатный API-ключ:
Зарегистрируйтесь на https://www.exchangerate-api.com/
Получите ключ (пример: 3b47a9b92e1b14c1f1234567)
Установите переменную окружения:
```bash
export EXCHANGERATE_API_KEY="ваш_ключ"
```
Parser продолжит работу и без ключа — будут обновлены только криптовалюты (CoinGecko).

## Планировщик (Scheduler)
Фоновое обновление курсов можно запустить вручную:
```bash
python -m valutatrade_hub.parser_service.scheduler
```
или в одноразовом режиме (например, для автотестов):
```bash
python -m valutatrade_hub.parser_service.scheduler --one-time
```

## Демонстрация (asciinema)

[![asciicast](https://asciinema.org/a/CU6Pjj2pR799mh4A7tngOM83c.svg)](https://asciinema.org/a/CU6Pjj2pR799mh4A7tngOM83c)