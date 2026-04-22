# Обработчики покупки гайда и юридических документов.
# Продажа PDF через ЮKassa. Доставка гайда — автоматически через yc/payment.py.

from aiogram import Router
from aiogram.types import Message, CallbackQuery

from keyboards.inline import get_guide_payment_inline_keyboard, get_documents_inline_keyboard
from services.db_service import create_payment_record, get_succeeded_guide_payment
from services.payment_service import create_payment
from services.file_service import get_guide_file, get_privacy_policy_file, get_offer_file

router = Router()


@router.message(lambda message: message.text == "Купить гайд")
async def guide_handler(message: Message) -> None:
    """
    Описание гайда с ценой и кнопкой оплаты.
    Второе сообщение — ссылки на юридические документы.
    """
    guide_text = (
        "<b>📚 Гайд по финансовой грамотности</b>\n\n"
        "Практический гайд по финансовой грамотности, который поможет разобраться "
        "в личных финансах, навести в них порядок и заложить понятную базу для "
        "накоплений, целей и первых инвестиций.\n\n"
        "Гайд будет полезен тем, кто хочет:\n"
        "🎯 Понять своё текущее финансовое положение;\n"
        "🎯 Выстроить финансовые цели;\n"
        "🎯 Сформировать полезные привычки;\n"
        "🎯 Спокойнее относиться к накоплениям, кредитам и инвестициям.\n\n"
        "Внутри раскрыты следующие темы:\n"
        "1. Что такое финансовая грамотность\n"
        "2. Как устроены отношения с деньгами\n"
        "3. Как оценить своё финансовое состояние\n"
        "4. Как поставить финансовые цели\n"
        "5. Какие привычки помогают управлять деньгами\n"
        "6. Как работают вклады, накопительные счета и кредиты\n"
        "7. Что важно знать перед началом инвестирования\n"
        "8. Чем отличаются облигации и акции\n"
        "9. Как выстроить финансовый план на несколько лет вперёд\n\n"
        "🌐 Бонусный раздел по криптовалютам: основы крипты и блокчейна,"
        " базовые виды активов, кошельки, риски и принципы безопасности\n\n"
        "💰 Стоимость: <s>1490₽</s> <b>990₽</b>\n\n"
        "Без лишней теории и громких обещаний — база, которая поможет лучше понимать,"
        " как работают финансовые инструменты."
    )

    await message.answer(
        text=guide_text,
        reply_markup=get_guide_payment_inline_keyboard(),
        parse_mode="HTML"
    )
    await message.answer(
        text="📄✍🏼 Переходя к оплате, вы соглашаетесь с офертой и политикой конфиденциальности.",
        reply_markup=get_documents_inline_keyboard()
    )


@router.callback_query(lambda c: c.data == "buy_guide")
async def buy_guide_callback(callback: CallbackQuery) -> None:
    """
    Создаёт платёж в ЮKassa и отправляет ссылку на оплату.
    Если пользователь уже купил гайд — отправляет его повторно.
    После успешной оплаты гайд доставляется автоматически через yc/payment.py.
    """
    await callback.answer()

    # Повторная покупка — просто отправляем гайд ещё раз
    existing = await get_succeeded_guide_payment(callback.from_user.id)
    if existing:
        await callback.message.answer(
            "📚 Вы уже приобретали этот гайд ранее. Отправляю его повторно!"
        )
        await callback.message.answer_document(get_guide_file())
        return

    try:
        payment_data = await create_payment(
            amount=990.00,
            description="Гайд по финансовой грамотности"
        )

        await create_payment_record(
            telegram_user_id=callback.from_user.id,
            product_name="guide_financial_literacy",
            amount=990.00,
            payment_id=payment_data["payment_id"],
            status=payment_data["status"]
        )

        confirmation_url = payment_data.get("confirmation_url")
        if confirmation_url:
            await callback.message.answer(
                "✅ <b>Платёж создан!</b>\n\n"
                f"🔗 <a href='{confirmation_url}'>Перейти к оплате</a>\n\n"
                "После оплаты гайд придёт в этот чат автоматически.",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("❌ Ошибка при создании платежа")

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(lambda c: c.data == "open_privacy_policy")
async def open_privacy_policy_callback(callback: CallbackQuery) -> None:
    """Отправляет PDF политики конфиденциальности."""
    try:
        await callback.message.answer_document(get_privacy_policy_file())
        await callback.answer()
    except Exception as e:
        print("Ошибка при отправке политики конфиденциальности:", repr(e))
        await callback.answer("Не удалось отправить файл", show_alert=True)


@router.callback_query(lambda c: c.data == "open_offer")
async def open_offer_callback(callback: CallbackQuery) -> None:
    """Отправляет PDF оферты."""
    try:
        await callback.message.answer_document(get_offer_file())
        await callback.answer()
    except Exception as e:
        print("Ошибка при отправке оферты:", repr(e))
        await callback.answer("Не удалось отправить файл", show_alert=True)
