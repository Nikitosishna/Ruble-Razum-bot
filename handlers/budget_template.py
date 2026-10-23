# Обработчик кнопки «Получить таблицу бюджета».
# Отправляет фото таблицы, описание и ссылку для копирования.

from aiogram import Router
from aiogram.types import Message

from keyboards.inline import get_budget_template_keyboard
from services.file_service import BUDGET_TEMPLATE_IMAGE_PATH, get_budget_template_image_file

router = Router()

_CAPTION = (
    "📊 Шаблон таблицы для ведения бюджета — бесплатно!\n\n"
    "Сделай копию и начни контролировать свои финансы уже сегодня.\n\n"
    "Что внутри:\n"
    "• Лист «Общее» — доходы, расходы и накопления по месяцам с разбивкой по категориям и сравнительным графиком за год\n\n"
    "• Лист «Транзакции» — журнал всех операций: дата, тип, категория, сумма и заметка\n\n"
    "• Лист «Справочник» — список категорий, который легко адаптировать под себя\n\n"
    "Итоги и диаграммы обновляются автоматически — нужно только регулярно вносить операции.\n\n"
    "Ведёшь таблицу регулярно - и постепенно начинаешь видеть, куда реально уходят деньги. "
    "Если захочешь разобраться в управлении финансами глубже, в боте можно получить гайд по финансовой грамотности 📖"
)


@router.message(lambda message: message.text == "Получить таблицу бюджета")
async def budget_template_handler(message: Message) -> None:
    """Отправляет фото шаблона таблицы и кнопку для копирования."""
    keyboard = get_budget_template_keyboard()

    if BUDGET_TEMPLATE_IMAGE_PATH.exists():
        await message.answer_photo(
            photo=get_budget_template_image_file(),
            caption=_CAPTION,
            reply_markup=keyboard
        )
    else:
        await message.answer(_CAPTION, reply_markup=keyboard)
