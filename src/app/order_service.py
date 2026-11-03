"""Заказы: список, состав, создание, удаление, правка. Все изменения — в одной транзакции."""
from datetime import date
from decimal import Decimal

from cart import check_qty
from db import db_cursor
from errors import AppError
from models import D, OrderLine, OrderRow, User

CLIENT_ROLE = "Авторизованный пользователь"


def _fio(last, first, middle):
    return " ".join(p for p in (last, first, middle) if p)


def get_orders():
    with db_cursor() as cur:
        cur.execute("""
            SELECT o.id, o.order_date, u.last_name, u.first_name, u.middle_name
            FROM orders o JOIN users u ON u.id = o.client_id
            ORDER BY o.id
        """)
        return [OrderRow(r[0], r[1], _fio(*r[2:5])) for r in cur.fetchall()]


def get_order(order_id):
    with db_cursor() as cur:
        cur.execute("""
            SELECT o.id, o.order_date, u.last_name, u.first_name, u.middle_name
            FROM orders o JOIN users u ON u.id = o.client_id
            WHERE o.id = %s
        """, (order_id,))
        r = cur.fetchone()
        return OrderRow(r[0], r[1], _fio(*r[2:5])) if r else None


def get_order_lines(order_id):
    """Состав: модель, производство, вариант, количество, историческая цена."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT oi.id, m.name, mf.name, v.name, oi.quantity, oi.unit_price
            FROM order_items oi
            JOIN stock_items si   ON si.id = oi.stock_item_id
            JOIN models m         ON m.id  = si.model_id
            JOIN manufacturers mf ON mf.id = m.manufacturer_id
            JOIN variants v       ON v.id  = si.variant_id
            WHERE oi.order_id = %s
            ORDER BY oi.id
        """, (order_id,))
        return [OrderLine(r[0], r[1], r[2], r[3], r[4], D(r[5])) for r in cur.fetchall()]


def get_order_total(order_id):
    with db_cursor() as cur:
        cur.execute("SELECT SUM(quantity * unit_price) FROM order_items WHERE order_id = %s", (order_id,))
        row = cur.fetchone()
        return D(row[0]) if row and row[0] is not None else Decimal(0)


def list_clients():
    """Клиенты, для которых менеджер/администратор может создать заказ."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT u.id, u.login, u.last_name, u.first_name, u.middle_name, r.name
            FROM users u JOIN roles r ON r.id = u.role_id
            WHERE r.name = %s
            ORDER BY u.last_name, u.first_name
        """, (CLIENT_ROLE,))
        return [User(*r) for r in cur.fetchall()]


def get_stock_snapshot(item_ids):
    """Актуальные остатки и цены: {id: (quantity, price)} — для повторной проверки перед сохранением."""
    if not item_ids:
        return {}
    with db_cursor() as cur:
        cur.execute("SELECT id, quantity, price FROM stock_items WHERE id = ANY(%s)", (list(item_ids),))
        return {r[0]: (int(r[1]), D(r[2])) for r in cur.fetchall()}


def create_order(client_id, lines, order_date=None):
    """Создаёт заказ атомарно. lines: [(stock_item_id, quantity)].
    Остатки и цены перечитываются под блокировкой; при любой ошибке — откат (ничего не сохраняется).
    Возвращает (номер заказа, итог)."""
    merged = {}
    for sid, qty in lines:                       # повторная позиция объединяется
        merged[sid] = merged.get(sid, 0) + check_qty(qty)
    if not merged:
        raise AppError("Заказ пуст. Добавьте хотя бы одну позицию.")

    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE id = %s", (client_id,))
        if not cur.fetchone():
            raise AppError("Клиент не найден. Выберите клиента из списка.")
        cur.execute("INSERT INTO orders (order_date, client_id) VALUES (%s, %s) RETURNING id",
                    (order_date or date.today(), client_id))
        order_id = cur.fetchone()[0]
        total = Decimal(0)
        for sid in sorted(merged):               # единый порядок блокировок
            qty = merged[sid]
            cur.execute("""
                SELECT si.quantity, si.price, m.name, v.name
                FROM stock_items si
                JOIN models m   ON m.id = si.model_id
                JOIN variants v ON v.id = si.variant_id
                WHERE si.id = %s
                FOR UPDATE OF si
            """, (sid,))
            row = cur.fetchone()
            if not row:
                raise AppError("Товарная позиция не найдена. Обновите каталог.")
            available, price, mname, vname = int(row[0]), D(row[1]), row[2], row[3]
            if available <= 0:
                raise AppError(f"«{mname}», вариант «{vname}»: недоступно для заказа. Уберите позицию из заказа.")
            if qty > available:
                raise AppError(f"«{mname}», вариант «{vname}»: доступно только {available} шт., "
                               f"а запрошено {qty} шт. Уменьшите количество.")
            cur.execute("""
                INSERT INTO order_items (order_id, stock_item_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, sid, qty, price))     # цена фиксируется на момент заказа
            cur.execute("UPDATE stock_items SET quantity = quantity - %s WHERE id = %s", (qty, sid))
            total += qty * price
        return order_id, total


def delete_order(order_id):
    """Удаляет заказ; зарезервированное количество возвращается в остаток."""
    with db_cursor() as cur:
        cur.execute("""
            UPDATE stock_items AS si
            SET quantity = si.quantity + t.q
            FROM (SELECT stock_item_id, SUM(quantity) AS q
                  FROM order_items WHERE order_id = %s GROUP BY stock_item_id) t
            WHERE t.stock_item_id = si.id
        """, (order_id,))
        cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))   # строки удалятся каскадом
        if cur.rowcount == 0:
            raise AppError("Заказ не найден: возможно, он уже удалён. Обновите список.")


def count_lines(order_id):
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM order_items WHERE order_id = %s", (order_id,))
        return cur.fetchone()[0]


def delete_order_line(line_id):
    """Удаляет строку заказа и возвращает количество в остаток."""
    with db_cursor() as cur:
        cur.execute("SELECT stock_item_id, quantity FROM order_items WHERE id = %s", (line_id,))
        row = cur.fetchone()
        if not row:
            raise AppError("Строка заказа не найдена. Обновите состав заказа.")
        cur.execute("DELETE FROM order_items WHERE id = %s", (line_id,))
        cur.execute("UPDATE stock_items SET quantity = quantity + %s WHERE id = %s", (row[1], row[0]))


def update_order_date(order_id, new_date):
    with db_cursor() as cur:
        cur.execute("UPDATE orders SET order_date = %s WHERE id = %s", (new_date, order_id))
        if cur.rowcount == 0:
            raise AppError("Заказ не найден. Обновите список заказов.")
