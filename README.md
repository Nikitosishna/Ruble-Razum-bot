# 🪙 Рубль Разум — Telegram-бот по финансовой грамотности

Телеграм-бот для сообщества «Рубль Разум». Помогает следить за финансовыми показателями, участвовать в прогнозах ключевой ставки ЦБ РФ и приобрести гайд по финансовой грамотности.

---

## Функционал

- 💱 **Актуальные курсы валют** — USD, EUR, CNY, AED, TRY, GBP, GEL, BYN, KZT, CHF через API ЦБ РФ
- ₿ **Курс криптовалют** — Bitcoin и Ethereum через Binance API
- 🔑 **Ключевая ставка ЦБ РФ** — актуальное значение через официальный SOAP-сервис ЦБ
- 🎯 **Прогнозы по ключевой ставке** — за 2 дня до заседания бот открывает окно для прогнозов; после заседания сравнивает с решением ЦБ и рассылает персональный результат каждому участнику
- 🔔 **Напоминания** — подписка на уведомления накануне каждого заседания ЦБ
- 📚 **Покупка гайда** — оплата через ЮKassa, автоматическая доставка PDF после подтверждения платежа
- 📊 **Статистика прогнозов** — сколько раз в году пользователь угадал решение ЦБ

---

## Как это работает

### Курсы валют
Фиатные валюты (USD, EUR, CNY и др.) запрашиваются у ЦБ РФ через XML-эндпоинт `cbr.ru/scripts/XML_daily.asp`. Ответ парсится, курс приводится к 1 единице валюты с учётом номинала. Криптовалюты (BTC, ETH) — через REST API Binance, цена в рублях рассчитывается через курс USD/RUB от ЦБ. При недоступности сервисов выполняется до 3 повторных попыток.

### Ключевая ставка
Получается через официальный SOAP/WSDL-сервис ЦБ РФ с помощью библиотеки `zeep`. Клиент инициализируется один раз при холодном старте и переиспользуется между запросами.

### Система прогнозов ключевой ставки
1. Администратор добавляет даты заседаний ЦБ командой `/update_dates`
2. За 2 дня до каждого заседания открывается «окно прогнозов»
3. Пользователи делают прогноз в формате `21`, `21.5`, `21,5%` и т.д.
4. В день заседания в 13:30 МСК функция `yc-results` автоматически получает новую ставку через SOAP ЦБ и рассылает персональный результат всем участникам
5. Администратор может выполнить рассылку вручную через `/set_rate 2026-04-25 21.0` — на случай если автоматика не сработала
6. Накануне заседания (10:00 МСК) функция `yc-reminders` напоминает подписчикам о прогнозе

### Платёжная система
Интегрирована **ЮKassa** (основной вариант). При нажатии «Перейти к оплате» бот создаёт платёж через REST API ЮKassa и отправляет ссылку. Статус проверяется по нажатию кнопки «Проверить оплату». При успешной оплате файл гайда отправляется автоматически. Также запланирована интеграция **Робокасса** как альтернативный платёжный шлюз.

Webhook от ЮKassa обрабатывает функция `yc-payment` — она верифицирует событие, обновляет запись в БД и доставляет гайд пользователю.

---

## Архитектура

```
handlers/
  routes.py          — все обработчики Telegram (сообщения, callback, команды)
services/
  currency_service.py   — курсы валют (ЦБ РФ + Binance)
  key_rate_service.py   — ключевая ставка (SOAP/zeep)
  forecast_service.py   — логика прогнозов и заседаний ЦБ
  payment_service.py    — интеграция с ЮKassa
  scheduler_service.py  — APScheduler (локальный режим) + cron-логика для YC
  db_service.py         — CRUD-операции с БД
  file_service.py       — PDF/изображения
models/
  forecast.py           — CBRMeeting, RateForecast, RateSubscription
  payment.py            — Payment
keyboards/
  reply.py              — главная клавиатура
  inline.py             — inline-кнопки (валюты, оплата, прогноз)
states/
  registration.py       — FSM-состояния (регистрация, прогноз)
utils/
  validators.py         — валидация имени и email
  constants.py          — общие константы (месяцы и др.)
yc/
  webhook.py    — обработка Telegram-обновлений (точка входа в YC Functions)
  payment.py    — webhook ЮKassa (автодоставка гайда)
  reminders.py  — cron 10:00 МСК (напоминания подписчикам)
  results.py    — cron 13:30 МСК (итоги заседания ЦБ)
```

### Поток данных (продакшн)

```
Telegram  → POST /webhook   → yc/webhook.py    — обрабатывает все обновления бота
ЮKassa    → POST /payment   → yc/payment.py    — автодоставка гайда после оплаты
Scheduler → GET  /reminders → yc/reminders.py  — 10:00 МСК, напоминания подписчикам
Scheduler → GET  /results   → yc/results.py    — 13:30 МСК, итоги заседания ЦБ
```

Каждый файл в папке `yc/` — отдельная Yandex Cloud Function с точкой входа `handler(event, context)`.

---

## Стек технологий

| Категория | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Telegram-фреймворк | aiogram 3.x |
| База данных | PostgreSQL (Supabase) |
| ORM | SQLAlchemy (async) |
| FSM-хранилище | Redis (Upstash) |
| Хостинг функций | Yandex Cloud Functions (serverless) |
| Cron-задачи | Yandex Cloud Scheduler |
| CI/CD | Sourcecraft |
| API ЦБ РФ | SOAP/WSDL через zeep |
| Платёжная система | ЮKassa REST API |

---

## Локальный запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Nikitosishna/Ruble-Razum-bot.git
cd Ruble-Razum-bot
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

```bash
cp .env.example .env
# Открыть .env и заполнить: BOT_TOKEN, DATABASE_URL, YOOKASSA_*, ADMIN_ID
# REDIS_URL и WEBHOOK_URL для локального запуска не нужны
```

### 5. Запустить бота

```bash
python main.py
```

Локально бот работает в режиме **polling** — `REDIS_URL` и `WEBHOOK_URL` можно не заполнять.

---

## Переменные окружения

Все переменные описаны в файле [`.env.example`](.env.example).

| Переменная | Где взять |
|-----------|-----------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) в Telegram |
| `DATABASE_URL` | [Supabase](https://supabase.com) → Connect → Session pooler → URI |
| `YOOKASSA_SHOP_ID` | [ЮKassa](https://yookassa.ru) → Интеграция |
| `YOOKASSA_SECRET_KEY` | [ЮKassa](https://yookassa.ru) → Интеграция |
| `ADMIN_ID` | [@userinfobot](https://t.me/userinfobot) |
| `REDIS_URL` | [Upstash](https://upstash.com) → Redis → Connect → TCP |
| `WEBHOOK_URL` | URL функции `tg-webhook` из Yandex Cloud (после деплоя) |
| `CRON_SECRET` | Любая случайная строка |

---

## Деплой: Вариант 1 — Sourcecraft + Yandex Cloud (рекомендуется)

GitOps-деплой: одна команда — и всё разворачивается автоматически.

### Подготовка (один раз)

1. Зарегистрироваться на [sourcecraft.dev](https://sourcecraft.dev) и активировать грант
2. Создать репозиторий в Sourcecraft, добавить remote:

```bash
git remote add sourcecraft https://git@git.sourcecraft.dev/YOUR_ORG/YOUR_REPO.git
```

3. Настроить одновременный пуш на GitHub и Sourcecraft:

```bash
git remote set-url --add --push origin https://github.com/Nikitosishna/Ruble-Razum-bot.git
git remote set-url --add --push origin https://git@git.sourcecraft.dev/YOUR_ORG/YOUR_REPO.git
```

После этого `git push` отправляет код в оба места одновременно.

4. В Sourcecraft привязать **Service Connection** к Yandex Cloud (раздел Настройки организации)

### Деплой

```bash
git push
```

Sourcecraft автоматически запускает пайплайн из `.sourcecraft/ci.yaml`:
- Разворачивает 4 Yandex Cloud Functions (`tg-webhook`, `yc-payment`, `yc-reminders`, `yc-results`)
- Регистрирует webhook у Telegram
- Сбрасывает очередь старых апдейтов (`drop_pending_updates=true`)

При первом запуске пайплайн нужно запустить вручную (CI/CD → deploy-bot → Запустить) и ввести параметры: токен бота, строку подключения к БД, ключи ЮKassa и Redis.

### Cron-триггеры (настраиваются один раз в YC Console)

| Расписание | Функция | Время МСК |
|-----------|---------|-----------|
| `0 7 * * *` | `yc-reminders` | 10:00 |
| `30 10 * * *` | `yc-results` | 13:30 |

### ЮKassa webhook

В настройках ЮKassa указать URL функции `yc-payment` для получения уведомлений об оплате.

---

## Деплой: Вариант 2 — Serverless на других платформах

Бот может быть развёрнут на любом serverless-хостинге с поддержкой Python:

- **Vercel** — через `vercel.json` с маршрутизацией на `yc/webhook.py`
- **Railway / Render** — запуск `main.py` в режиме polling (без webhook)
- **AWS Lambda / Google Cloud Functions** — аналогичная архитектура, адаптация точек входа

В режиме **polling** (`main.py`) Redis и webhook не нужны — бот сам опрашивает Telegram. Подходит для разработки и деплоя на платформы без поддержки входящих HTTP-запросов.

---

## Команды администратора

| Команда | Описание |
|---------|---------|
| `/update_dates 2026-04-25 2026-06-06` | Добавить даты заседаний ЦБ |
| `/list_dates` | Показать все даты заседаний в БД |
| `/set_rate 2026-04-25 21.0` | Сохранить ставку и разослать итоги вручную |

---

## Автор

Pet project — [@rub_and_razum](https://t.me/rub_and_razum)
