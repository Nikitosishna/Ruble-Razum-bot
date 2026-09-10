# 🪙 Рубль Разум — Telegram-бот по финансовой грамотности

Телеграм-бот для сообщества «Рубль Разум». Помогает следить за финансовыми показателями, участвовать в прогнозах ключевой ставки ЦБ РФ и приобрести гайд по финансовой грамотности.

---

## Функционал

- 💱 **Актуальные курсы фиатных валют** — USD, EUR, CNY, AED, TRY, GBP, GEL, BYN, CHF через API ЦБ РФ
- ₿ **Курс криптовалют** — Bitcoin и Ethereum через Binance API
- 🔑 **Ключевая ставка ЦБ РФ** — актуальное значение через официальный SOAP-сервис ЦБ
- 🎯 **Прогнозы по ключевой ставке** — за 2 дня до заседания бот открывает окно для прогнозов; после заседания сравнивает с решением ЦБ и рассылает персональный результат каждому участнику
- 🔔 **Напоминания** — подписка на уведомления накануне каждого заседания ЦБ
- 📚 **Покупка гайда** — оплата через ЮKassa, автоматическая доставка PDF после подтверждения платежа

---

## Как это работает

### 💱 Курсы валют

**Фиатные валюты** запрашиваются у ЦБ РФ через XML-эндпоинт `cbr.ru/scripts/XML_daily.asp`:
- Ответ парсится в словарь `{код → курс}`
- Курс приводится к 1 единице валюты с учётом номинала (например, у BYN номинал 100)
- При недоступности сервиса — до **3 повторных попыток** с паузой

**Криптовалюты** (BTC, ETH) — через REST API Binance:
- Цена в USD берётся с Binance
- Переводится в рубли через курс USD/RUB от ЦБ

---

### 🔑 Ключевая ставка

Получается через официальный **SOAP/WSDL-сервис ЦБ РФ** (библиотека `zeep`):
- Клиент `zeep` инициализируется один раз при холодном старте
- Ответ кэшируется в **Redis на 2 часа** — повторные запросы не идут к ЦБ
- После `/set_rate` новая ставка записывается в кэш немедленно, не дожидаясь обновления SOAP ЦБ

---

### 🎯 Прогнозы по ключевой ставке

| Когда | Что происходит |
|-------|----------------|
| Заранее | Администратор добавляет даты заседаний командой `/update_dates` |
| За 2 дня до заседания | Открывается окно — пользователи вводят прогноз (`21`, `21.5`, `21,5%`) |
| 10:00 МСК накануне | `/reminders` напоминает подписчикам, у кого ещё нет прогноза |
| 13:30 МСК в день заседания | `/results` получает новую ставку через SOAP ЦБ и рассылает **персональный результат** каждому участнику |
| Резерв | Администратор может запустить рассылку вручную: `/set_rate 2026-04-25 21.0` |

---

### 💳 Платёжная система

Интегрирована **ЮKassa**:
1. Пользователь нажимает «Перейти к оплате»
2. Бот создаёт платёж через REST API и отправляет ссылку
3. После оплаты ЮKassa присылает webhook → `api/payment.py` верифицирует событие, обновляет статус в БД и автоматически доставляет PDF гайда в чат

---

## Архитектура

```
handlers/
  start.py       — /start, регистрация (имя → email), «Что умеет бот?», «Сообщество»
  currency.py    — курсы валют (выбор валюты + обработчики callback)
  key_rate.py    — ключевая ставка + блок прогноза
  forecast.py    — ввод прогноза, изменение, подписка на напоминания
  guide.py       — покупка гайда, оплата, юридические документы
  admin.py       — /update_dates, /list_dates, /set_rate
services/
  currency_service.py   — курсы валют (ЦБ РФ + Binance)
  key_rate_service.py   — ключевая ставка (SOAP/zeep + Redis-кэш)
  forecast_service.py   — логика прогнозов и заседаний ЦБ
  payment_service.py    — интеграция с ЮKassa
  scheduler_service.py  — логика рассылки напоминаний и итогов
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
  constants.py          — русские названия месяцев
  formatters.py         — форматирование ключевой ставки для HTML-сообщений
api/
  webhook.py    — Telegram-обновления (точка входа Vercel)
  payment.py    — webhook ЮKassa (автодоставка гайда)
  reminders.py  — cron 10:00 МСК (напоминания подписчикам)
  results.py    — cron 13:30 МСК (итоги заседания ЦБ)
```

### Поток данных (продакшн)

```
Telegram     → POST /webhook   → api/webhook.py   — обрабатывает все обновления бота
ЮKassa       → POST /payment   → api/payment.py   — автодоставка гайда после оплаты
Vercel Cron  → GET  /reminders → api/reminders.py — 10:00 МСК, напоминания подписчикам
Vercel Cron  → GET  /results   → api/results.py   — 13:30 МСК, итоги заседания ЦБ
```

---

## Стек технологий

| Категория | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Telegram-фреймворк | aiogram 3.x |
| База данных | PostgreSQL (Supabase) |
| ORM | SQLAlchemy (async) |
| FSM-хранилище | Redis (Upstash) |
| Хостинг | Vercel Serverless Functions |
| Cron-задачи | Vercel Cron Jobs |
| CI/CD | Vercel Git Integration (GitHub) |
| API ЦБ РФ | SOAP/WSDL через zeep |
| Платёжная система | ЮKassa REST API |

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
| `WEBHOOK_URL` | URL бота на Vercel (после деплоя: `https://YOUR_PROJECT.vercel.app/webhook`) |
| `CRON_SECRET` | Любая случайная строка |

---

## Деплой: Vercel + Supabase + Upstash

Vercel автоматически деплоит бота при каждом push в GitHub.

### Первый деплой (один раз)

1. Зарегистрироваться на [vercel.com](https://vercel.com) и подключить GitHub-репозиторий
2. Добавить переменные окружения в настройках проекта на Vercel
3. Нажать **Deploy** — Vercel соберёт проект автоматически

### Последующие деплои

```bash
git push
```

Vercel подхватит push и задеплоит обновлённую версию автоматически.

### После первого деплоя: зарегистрировать webhook

```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://YOUR_PROJECT.vercel.app/webhook&drop_pending_updates=true
```

### Webhook ЮKassa

В настройках ЮKassa указать `https://YOUR_PROJECT.vercel.app/payment`.

### Cron-задачи

Vercel автоматически запускает задачи по расписанию из `vercel.json`:

| Расписание | Путь | Время МСК |
|-----------|------|-----------|
| `0 7 * * *` | `/reminders` | 10:00 |
| `30 10 * * *` | `/results` | 13:30 |

---

## Локальный запуск (разработка)

```bash
python main.py
```

В этом режиме:
- Telegram-апдейты получаются через **polling** (бот сам опрашивает Telegram)
- FSM-состояния хранятся в памяти процесса (`MemoryStorage`)
- Cron-задачи выполняются через **APScheduler** внутри того же процесса

> Достаточно `.env` с `BOT_TOKEN` и `DATABASE_URL`. Redis и webhook не нужны.

---

## Команды администратора

| Команда | Описание |
|---------|---------|
| `/update_dates 2026-04-25 2026-06-06` | Добавить даты заседаний ЦБ |
| `/list_dates` | Показать все даты заседаний в БД |
| `/set_rate 2026-04-25 21.0` | Сохранить ставку и разослать итоги вручную |

---

## Автор

Pet project — [@rub_and_razum](https://t.me/rub_and_razum) | [@Nikitososhna](https://t.me/Nikitososhna)
