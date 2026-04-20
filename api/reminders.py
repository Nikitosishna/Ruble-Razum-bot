# Cron-эндпоинт для отправки напоминаний о прогнозе.
# Vercel вызывает GET /api/reminders каждый день в 07:00 UTC (= 10:00 МСК).
# Расписание задано в vercel.json.

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bot_instance import bot
from config import config
from services.scheduler_service import send_forecast_reminders

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/api/reminders")
async def run_reminders(request: Request) -> JSONResponse:
    """
    Отправляет напоминания подписчикам без прогноза (за 1-2 дня до заседания).
    Защищён токеном Vercel — только сам Vercel может вызвать этот эндпоинт.
    """
    # Проверяем, что запрос пришёл от Vercel Cron (не от посторонних)
    auth = request.headers.get("authorization", "")
    if config.CRON_SECRET and auth != f"Bearer {config.CRON_SECRET}":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        await send_forecast_reminders(bot)
        logger.info("Напоминания отправлены")
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {e}")

    return JSONResponse({"ok": True})
