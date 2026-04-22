# Обработчики запуска и регистрации.
# /start, ввод имени и email, «Что умеет бот?», «Сообщество».

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from keyboards.reply import get_main_keyboard
from keyboards.inline import get_community_inline_keyboard
from services.db_service import create_user, get_user_by_telegram_id
from services.file_service import get_community_image_file, get_what_can_bot_image_file
from utils.validators import is_valid_name, is_valid_email
from states.registration import RegistrationState

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.
    Если пользователь уже зарегистрирован — показываем главное меню.
    Если новый — запускаем регистрацию (имя → email).
    """
    await state.clear()

    existing_user = await get_user_by_telegram_id(message.from_user.id)

    if existing_user:
        await message.answer(
            f"С возвращением, {existing_user.user_name}!\n"
            "Бот «Рубль Разум» готов к работе.",
            reply_markup=get_main_keyboard()
        )
        return

    await message.answer("Пожалуйста, введи своё имя.")
    await state.set_state(RegistrationState.waiting_for_name)


@router.message(RegistrationState.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Получаем имя пользователя и переходим к запросу email."""
    name = message.text.strip()

    if not is_valid_name(name):
        await message.answer("Имя введено некорректно.\nПожалуйста, попробуй ещё раз.")
        return

    await state.update_data(user_name=name)
    await message.answer(f"Привет, {name}!\nТеперь введи свою электронную почту.")
    await state.set_state(RegistrationState.waiting_for_email)


@router.message(RegistrationState.waiting_for_email)
async def process_email(message: Message, state: FSMContext) -> None:
    """Получаем email, создаём пользователя и показываем главное меню."""
    email = message.text.strip().lower()

    if not is_valid_email(email):
        await message.answer("Пожалуйста, введи корректную почту.")
        return

    data = await state.get_data()
    await create_user(
        telegram_user_id=message.from_user.id,
        user_name=data["user_name"],
        email=email
    )

    await message.answer(
        "Добро пожаловать в бот сообщества «Рубль Разум»!\n\n"
        "Здесь можно:\n"
        "• Приобрести гайд по финансовой грамотности;\n"
        "• Посмотреть актуальные курсы валют;\n"
        "• Узнать стоимость BTC и ETH;\n"
        "• Узнать текущую ключевую ставку ЦБ РФ;\n"
        "• Поучаствовать в прогнозах ключевой ставки.\n\n"
        "Что вас интересует?",
        reply_markup=get_main_keyboard()
    )
    await state.clear()


@router.message(lambda message: message.text == "Что умеет бот?")
async def what_can_bot_handler(message: Message) -> None:
    """Отправляет описание бота с изображением."""
    try:
        await message.answer_photo(
            photo=get_what_can_bot_image_file(),
            caption=(
                "Это бот сообщества «Рубль Разум»!\n\n"
                "Здесь можно:\n"
                "• Приобрести гайд по финансовой грамотности;\n"
                "• Посмотреть актуальные курсы валют;\n"
                "• Узнать стоимость BTC и ETH;\n"
                "• Узнать текущую ключевую ставку ЦБ РФ;\n"
                "• Поучаствовать в прогнозах ключевой ставки.\n\n"
                "Что вас интересует?"
            )
        )
    except Exception as e:
        await message.answer(f"Не удалось отправить изображение: {e}")


@router.message(lambda message: message.text == "Сообщество")
async def community_handler(message: Message) -> None:
    """Отправляет картинку сообщества с кнопкой-ссылкой."""
    try:
        await message.answer_photo(
            photo=get_community_image_file(),
            caption="Нажми на кнопку, чтобы перейти в сообщество.",
            reply_markup=get_community_inline_keyboard()
        )
    except Exception as e:
        await message.answer(f"Не удалось отправить изображение сообщества: {e}")
