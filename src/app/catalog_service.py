from db import db_cursor
from models import D, Model, StockItem

ALL_CATEGORIES = "Все категории"


def load_categories():
    with db_cursor() as cur:
        cur.execute("SELECT name FROM categories ORDER BY id")
        return [r[0] for r in cur.fetchall()]


def load_models():
    """Модели с категорией, производством и суммарным остатком по всем вариантам."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT m.id, m.name, mf.name, c.name, sc.name, m.image, m.description, m.composition,
                   m.base_price, COALESCE(SUM(si.quantity), 0)
            FROM models m
            JOIN manufacturers mf ON mf.id = m.manufacturer_id
            JOIN subcategories sc ON sc.id = m.subcategory_id
            JOIN categories c     ON c.id  = sc.category_id
            LEFT JOIN stock_items si ON si.model_id = m.id
            GROUP BY m.id, m.name, mf.name, c.name, sc.name, m.image, m.description,
                     m.composition, m.base_price
            ORDER BY m.id
        """)
        return [Model(r[0], r[1], r[2], r[3], r[4], r[5] or "", r[6] or "", r[7] or "",
                      D(r[8]), int(r[9])) for r in cur.fetchall()]


def load_stock_items():
    """Все товарные позиции, сгруппированные по id модели: {model_id: [StockItem, ...]}."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT si.id, si.model_id, m.name, mf.name, v.name, si.quantity, si.price
            FROM stock_items si
            JOIN models m         ON m.id  = si.model_id
            JOIN manufacturers mf ON mf.id = m.manufacturer_id
            JOIN variants v       ON v.id  = si.variant_id
            ORDER BY si.model_id, v.id
        """)
        out = {}
        for r in cur.fetchall():
            out.setdefault(r[1], []).append(StockItem(r[0], r[1], r[2], r[3], r[4], int(r[5]), D(r[6])))
        return out


def filter_models(models, search="", category=ALL_CATEGORIES, descending=False):
    """Поиск по наименованию + фильтр категории + сортировка по базовой цене (совместно)."""
    s = (search or "").strip().casefold()
    result = [m for m in models
              if (not s or s in m.name.casefold())
              and (category in (None, "", ALL_CATEGORIES) or m.category == category)]
    result.sort(key=lambda m: (m.base_price, m.name.casefold()), reverse=descending)
    return result
