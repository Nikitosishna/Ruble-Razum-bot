# Утилиты форматирования для отображения ключевой ставки.

def format_rate_html(value: float) -> str:
    """
    Форматирует float-ставку для HTML-сообщений с жирным числом.
    21.0  → '<b>21</b>%'
    21.5  → '<b>21,5</b>%'
    7.75  → '<b>7,75</b>%'
    """
    if value == int(value):
        return f"<b>{int(value)}</b>%"
    formatted = f"{value:.2f}".rstrip("0").replace(".", ",")
    return f"<b>{formatted}</b>%"
