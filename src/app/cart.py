from dataclasses import dataclass
from decimal import Decimal

from errors import AppError
from models import StockItem


def check_qty(value):
    """Положительное целое количество или AppError."""
    try:
        qty = int(str(value).strip())
    except (TypeError, ValueError):
        raise AppError("Количество должно быть целым положительным числом. Введите, например, 1.")
    if qty <= 0:
        raise AppError("Количество должно быть больше нуля. Введите целое положительное число.")
    return qty


@dataclass
class CartLine:
    item: StockItem
    qty: int

    @property
    def total(self):
        return self.qty * self.item.price


class Cart:
    """Корзина текущего сеанса (хранится в памяти)."""

    def __init__(self):
        self.lines = {}

    def add(self, item, qty):
        qty = check_qty(qty)
        if item.quantity <= 0:
            raise AppError("Недоступно для заказа: остаток этого варианта равен нулю.")
        in_cart = self.lines[item.id].qty if item.id in self.lines else 0
        if in_cart + qty > item.quantity:
            raise AppError(f"Нельзя заказать больше доступного остатка: доступно {item.quantity} шт., "
                           f"в корзине уже {in_cart} шт. Уменьшите количество.")
        if item.id in self.lines:          # повторное добавление объединяет количество
            self.lines[item.id].qty += qty
        else:
            self.lines[item.id] = CartLine(item, qty)

    def set_quantity(self, item_id, qty):
        qty = check_qty(qty)
        line = self.lines[item_id]
        if qty > line.item.quantity:
            raise AppError(f"Нельзя заказать больше доступного остатка: доступно {line.item.quantity} шт.")
        line.qty = qty

    def remove(self, item_id):
        self.lines.pop(item_id, None)

    def clear(self):
        self.lines.clear()

    def total(self):
        return sum((l.total for l in self.lines.values()), Decimal(0))

    def count(self):
        return sum(l.qty for l in self.lines.values())

    def as_pairs(self):
        return [(l.item.id, l.qty) for l in self.lines.values()]

    def __len__(self):
        return len(self.lines)
