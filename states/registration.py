# Состояния регистрации:
# ожидание имени
# ожидание email

from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    """
    Группа состояний для пошаговой регистрации.
    waiting_for_name  -> бот ждёт имя
    waiting_for_email -> бот ждёт email
    """

    waiting_for_name = State()
    waiting_for_email = State()

#State() - Отдельный шаг сценария.
#Когда пользователь вводит имя, бот переключает его в следующее
# состояние — ввод email.

class ForecastState(StatesGroup):
    """Состояние ожидания прогноза по ключевой ставке."""
    waiting_for_forecast = State()
