# Собирает все роутеры обработчиков в один.
# main.py импортирует отсюда: from handlers import router

from aiogram import Router

from handlers.start import router as start_router
from handlers.currency import router as currency_router
from handlers.key_rate import router as key_rate_router
from handlers.forecast import router as forecast_router
from handlers.guide import router as guide_router
from handlers.admin import router as admin_router

router = Router()
for _r in [start_router, currency_router, key_rate_router, forecast_router, guide_router, admin_router]:
    router.include_router(_r)
