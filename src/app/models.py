from dataclasses import dataclass
from decimal import Decimal


def D(value):
    return Decimal(str(value))


@dataclass
class User:
    id: int
    login: str
    last_name: str
    first_name: str
    middle_name: str
    role: str

    @property
    def fio(self):
        return " ".join(p for p in (self.last_name, self.first_name, self.middle_name) if p)


@dataclass
class Model:
    id: int
    name: str
    manufacturer: str
    category: str
    subcategory: str
    image: str
    description: str
    composition: str
    base_price: Decimal
    total_stock: int


@dataclass
class StockItem:
    id: int
    model_id: int
    model_name: str
    manufacturer: str
    variant: str
    quantity: int
    price: Decimal


@dataclass
class OrderRow:
    id: int
    date: object
    client: str


@dataclass
class OrderLine:
    id: int
    model: str
    manufacturer: str
    variant: str
    quantity: int
    unit_price: Decimal

    @property
    def total(self):
        return self.quantity * self.unit_price
