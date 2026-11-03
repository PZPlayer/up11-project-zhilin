"""Палитра, шрифты и форматирование (руководство по стилю, Приложение 3)."""
from datetime import date, datetime
from decimal import Decimal

from errors import AppError

COLOR_BG = "#FFFFFF"        # основной фон
COLOR_ALT = "#D2F6E7"       # дополнительный фон
COLOR_ACCENT = "#70B2AF"    # акцент целевого действия (текст на кнопке — чёрный)
COLOR_TEXT = "#000000"
COLOR_LOW = "#ff8080"       # подсветка модели с остатком <= 3 (включая 0)
LOW_STOCK_LIMIT = 3
FONT_NAME = "Calibri"
UNIT = "шт."


def font(size=11, bold=False):
    return (FONT_NAME, size, "bold" if bold else "normal")


def money(value):
    """Деньги: два знака после запятой и обозначение рубля. 14900 -> '14 900,00 руб.'"""
    s = format(Decimal(str(value)), ",.2f")
    return s.replace(",", "\u00a0").replace(".", ",") + " руб."


def fmt_date(value):
    """Дата заказа в формате ДД.ММ.ГГГГ (принимает date, datetime или строку ISO)."""
    if isinstance(value, str):
        value = date.fromisoformat(value[:10])
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d.%m.%Y")


def parse_date(text):
    try:
        return datetime.strptime(text.strip(), "%d.%m.%Y").date()
    except ValueError:
        raise AppError("Введите дату в формате ДД.ММ.ГГГГ, например 25.04.2026.")
