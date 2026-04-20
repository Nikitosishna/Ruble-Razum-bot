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
| Хостинг бота | Vercel (serverless) |
| Cron-задачи | Vercel Cron Jobs |
| API ЦБ РФ | SOAP/WSDL через zeep |
| Платёжная система | ЮKassa REST API |

---

## Локальный запуск

### 1. Клонировать репозиторий
```bash
git clone https://github.com/ВАШ_ЛОГИН/rubl-razum-bot.git
cd rubl-razum-bot
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
# Открыть .env и заполнить реальными значениями
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
| `DATABASE_URL` | [Supabase](https://supabase.com) → Settings → Database |
| `YOOKASSA_SHOP_ID` | [ЮKassa](https://yookassa.ru) → Интеграция |
| `YOOKASSA_SECRET_KEY` | [ЮKassa](https://yookassa.ru) → Интеграция |
| `ADMIN_ID` | [@userinfobot](https://t.me/userinfobot) |
| `REDIS_URL` | [Upstash](https://upstash.com) → Redis |
| `WEBHOOK_URL` | URL Vercel-проекта после деплоя |
| `CRON_SECRET` | Любая случайная строка |

---

## Деплой на Vercel

1. Создать аккаунты: [Supabase](https://supabase.com), [Upstash](https://upstash.com), [Vercel](https://vercel.com)
2. Подключить репозиторий к Vercel (Import Project → GitHub)
3. Добавить все переменные окружения в настройках Vercel
4. После деплоя прописать `WEBHOOK_URL` с URL проекта
5. В кабинете ЮKassa настроить HTTP-уведомления на `https://ваш-проект.vercel.app/api/payment`

---

## Автор

Pet project — [@rub_and_razum](https://t.me/rub_and_razum) / @Nikitosishna
