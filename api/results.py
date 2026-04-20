# Cron-эндпоинт для рассылки итогов заседания ЦБ.
# Vercel вызывает GET /api/results каждый день в 10:30 UTC (= 13:30 МСК).
# Расписание задано в vercel.json.

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bot_instance import bot
from config import config
from services.scheduler_service import send_meeting_results

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/api/results")
async def run_results(request: Request) -> JSONResponse:
    """
    В день заседания ЦБ: получает фактическую ставку из API,
    сравнивает с прогнозами и рассылает персональные итоги.
    В обычные дни — ничего не делает (проверяет наличие необработанных заседаний).
    Защищён токеном Vercel.
    """
    auth = request.headers.get("authorization", "")
    if config.CRON_SECRET and auth != f"Bearer {config.CRON_SECRET}":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        await send_meeting_results(bot)
        logger.info("Итоги заседания обработаны")
    except Exception as e:
        logger.error(f"Ошибка при рассылке итогов: {e}")

    return JSONResponse({"ok": True})
