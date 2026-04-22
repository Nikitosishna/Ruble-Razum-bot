# 🪙 Рубль Разум — Telegram-бот по финансовой грамотности

Телеграм-бот для сообщества «Рубль Разум». Помогает следить за финансовыми показателями, участвовать в прогнозах ключевой ставки ЦБ РФ и приобрести гайд по финансовой грамотности.

---

## Функционал

- 💱 **Актуальные курсы валют** — USD, EUR, CNY, AED, TRY, GBP, GEL, BYN, CHF через API ЦБ РФ
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
- Кэш сбрасывается автоматически в день объявления новой ставки

---

### 🎯 Прогнозы по ключевой ставке

| Когда | Что происходит |
|-------|----------------|
| Заранее | Администратор добавляет даты заседаний командой `/update_dates` |
| За 2 дня до заседания | Открывается окно — пользователи вводят прогноз (`21`, `21.5`, `21,5%`) |
| 10:00 МСК накануне | `yc-reminders` напоминает подписчикам, у кого ещё нет прогноза |
| 13:30 МСК в день заседания | `yc-results` получает новую ставку через SOAP ЦБ и рассылает **персональный результат** каждому участнику |
| Резерв | Администратор может запустить рассылку вручную: `/set_rate 2026-04-25 21.0` |

---

### 💳 Платёжная система

Интегрирована **ЮKassa**:
1. Пользователь нажимает «Перейти к оплате»
2. Бот создаёт платёж через REST API и отправляет ссылку
3. После оплаты ЮKassa присылает webhook → функция `yc-payment` верифицирует событие, обновляет статус в БД и автоматически доставляет PDF гайда в чат

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
  constants.py          — русские названия месяцев
  formatters.py         — форматирование ключевой ставки для HTML-сообщений
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

## Деплой: Вариант 2 — Vercel + Supabase + Upstash (международные сервисы)

Архитектурно идентичен Варианту 1, но на общедоступных западных платформах. Подходит, если нет доступа к Yandex Cloud или нужна глобальная инфраструктура.

| Компонент | Вариант 1 (RU) | Вариант 2 (INT) |
|-----------|---------------|-----------------|
| Serverless-функции | Yandex Cloud Functions | Vercel Serverless Functions |
| Cron-задачи | Yandex Cloud Scheduler | Vercel Cron Jobs |
| CI/CD | Sourcecraft | Vercel Git Integration (GitHub) |
| PostgreSQL | Supabase | Supabase (то же самое) |
| Redis | Upstash | Upstash (то же самое) |

### Подготовка (один раз)

1. Зарегистрироваться на [vercel.com](https://vercel.com), подключить GitHub-репозиторий
2. Добавить `vercel.json` в корень проекта с маршрутизацией функций:

```json
{
  "functions": {
    "yc/webhook.py":  { "memory": 512 },
    "yc/payment.py":  { "memory": 512 },
    "yc/reminders.py": { "memory": 256 },
    "yc/results.py":   { "memory": 256 }
  },
  "routes": [
    { "src": "/webhook",  "dest": "yc/webhook.py"  },
    { "src": "/payment",  "dest": "yc/payment.py"  },
    { "src": "/reminders","dest": "yc/reminders.py" },
    { "src": "/results",  "dest": "yc/results.py"   }
  ],
  "crons": [
    { "path": "/reminders", "schedule": "0 7 * * *"  },
    { "path": "/results",   "schedule": "30 10 * * *" }
  ]
}
```

3. В настройках проекта на Vercel добавить все переменные окружения из `.env.example`

### Деплой

```bash
git push
```

Vercel автоматически подхватывает пуш в GitHub и деплоит функции.

### Webhook и ЮKassa

После первого деплоя зарегистрировать webhook у Telegram:

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://YOUR_PROJECT.vercel.app/webhook&drop_pending_updates=true
```

В настройках ЮKassa указать `https://YOUR_PROJECT.vercel.app/payment` для уведомлений об оплате.

---

## Деплой: Вариант 3 — Локальный запуск (polling)

Для разработки и тестирования бот запускается локально через long polling — без webhook и без Redis:

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
