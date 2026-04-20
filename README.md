# 🪙 Рубль Разум — Telegram-бот по финансовой грамотности

Телеграм-бот для сообщества «Рубль Разум». Помогает следить за финансовыми показателями, участвовать в прогнозах ключевой ставки ЦБ РФ и приобрести гайд по финансовой грамотности.

---

## Функционал

- 💱 **Актуальные курсы валют** — USD, EUR, CNY, AED, TRY, GBP, GEL через API ЦБ РФ
- ₿ **Курс криптовалют** — Bitcoin и Ethereum через Binance API
- 🔑 **Ключевая ставка ЦБ РФ** — актуальное значение через официальный SOAP-сервис
- 🎯 **Прогнозы по ключевой ставке** — пользователи делают прогноз перед заседанием ЦБ, после заседания бот сравнивает с фактическим решением и присылает персональный результат
- 🔔 **Напоминания** — подписка на уведомления за 1-2 дня до заседания
- 📚 **Покупка гайда** — оплата через ЮKassa, автоматическая доставка PDF после оплаты
- 📊 **Статистика прогнозов** — сколько раз в году пользователь угадал решение ЦБ

---

## Стек технологий

| Категория | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Telegram-фреймворк | aiogram 3.x |
| База данных | PostgreSQL (Supabase) |
| ORM | SQLAlchemy (async) |
| FSM-хранилище | Redis (Upstash) |
| Хостинг бота | Yandex Cloud Functions (serverless) |
| Cron-задачи | Yandex Cloud Scheduler |
| API ЦБ РФ | SOAP/WSDL через zeep |
| Платёжная система | ЮKassa REST API |

---

## Структура деплоя (Yandex Cloud)

```
Telegram  → POST /webhook   → yc/webhook.py    — обрабатывает все обновления бота
ЮKassa    → POST /payment   → yc/payment.py    — автодоставка гайда после оплаты
Scheduler → GET  /reminders → yc/reminders.py  — 10:00 МСК, напоминания подписчикам
Scheduler → GET  /results   → yc/results.py    — 13:30 МСК, итоги заседания ЦБ
```

Каждый файл в папке `yc/` — отдельная Yandex Cloud Function с точкой входа `handler(event, context)`.

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

Локально бот работает в режиме **polling** — REDIS_URL и WEBHOOK_URL можно не заполнять.

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
| `WEBHOOK_URL` | Yandex API Gateway → URL функции после деплоя |
| `CRON_SECRET` | Любая случайная строка |

---

## Деплой на Yandex Cloud (через Sourcecraft)

1. Зарегистрироваться на [sourcecraft.dev](https://sourcecraft.dev) и активировать грант (6 000 ₽, 180 дней)
2. Создать 4 Cloud Functions: `webhook`, `payment`, `reminders`, `results`
3. Для каждой функции загрузить код (zip весь проект), указать точку входа: `yc.webhook.handler` и т.д.
4. Создать Yandex API Gateway → привязать к функции `webhook` → получить HTTPS-URL
5. Прописать `WEBHOOK_URL` в переменных окружения функции
6. Зарегистрировать webhook у Telegram: `setWebhook?url=https://[id].apigw.yandexcloud.net/webhook`
7. Создать 2 триггера Yandex Cloud Scheduler:
   - `0 7 * * *` → функция `reminders` (10:00 МСК)
   - `30 10 * * *` → функция `results` (13:30 МСК)
8. В ЮKassa настроить HTTP-уведомления на URL функции `payment`

---

## Автор

Pet project — [@rub_and_razum](https://t.me/rub_and_razum)
