import tkinter as tk
from tkinter import ttk

import dialogs
import order_service as osv
from dialogs import safe_call
from styles import COLOR_BG, UNIT, font, money
from ui_common import Header, accent_button, plain_button


class CartFrame(tk.Frame):
    """Корзина: добавление/удаление позиций, изменение количества, подтверждение заказа."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        header = Header(self, app, "Корзина")
        header.pack(fill="x")
        header.add_button("← К каталогу", app.show_catalog)

        cols = ("model", "maker", "variant", "qty", "price", "total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for c, t, w in (("model", "Модель", 260), ("maker", "Производство", 150), ("variant", "Вариант", 110),
                        ("qty", "Кол-во, шт.", 90), ("price", "Цена за шт.", 140), ("total", "Сумма", 150)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w" if c in ("model", "maker", "variant") else "e")
        self.tree.pack(fill="both", expand=True, padx=14, pady=12)

        self.total_label = tk.Label(self, text="", font=font(15, True), bg=COLOR_BG)
        self.total_label.pack(anchor="e", padx=18)

        row = tk.Frame(self, bg=COLOR_BG)
        row.pack(fill="x", padx=14, pady=12)
        plain_button(row, "Изменить количество", self.change_qty).pack(side="left", padx=4)
        plain_button(row, "Удалить позицию", self.remove_line).pack(side="left", padx=4)
        plain_button(row, "Очистить корзину", self.clear).pack(side="left", padx=4)
        accent_button(row, "Оформить заказ", self.checkout).pack(side="right", padx=4)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for l in self.app.cart.lines.values():
            self.tree.insert("", "end", iid=str(l.item.id),
                             values=(l.item.model_name, l.item.manufacturer, l.item.variant, l.qty,
                                     money(l.item.price), money(l.total)))
        self.total_label.config(text=f"Итого: {money(self.app.cart.total())}")

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            dialogs.warning("Выберите позицию в таблице.", self.app.root)
            return None
        return int(sel[0])

    def change_qty(self):
        sid = self._selected()
        if sid is None:
            return
        line = self.app.cart.lines[sid]
        value = dialogs.ask_quantity(self.app.root, f"{line.item.model_name}, {line.item.variant}",
                                     line.qty, line.item.quantity)
        if value is not None:          # при отмене данные не меняются
            self.app.cart.set_quantity(sid, value)
            self.refresh()
            self.app.on_cart_changed()

    def remove_line(self):
        sid = self._selected()
        if sid is not None and dialogs.confirm("Удалить выбранную позицию из корзины?", self.app.root):
            self.app.cart.remove(sid)
            self.refresh()

    def clear(self):
        if len(self.app.cart) and dialogs.confirm("Очистить корзину?", self.app.root):
            self.app.cart.clear()
            self.refresh()

    def checkout(self):
        cart, user = self.app.cart, self.app.user
        if not len(cart):
            dialogs.warning("Корзина пуста. Добавьте позиции в каталоге.", self.app.root)
            return
        # повторная проверка остатков и актуальных цен перед сохранением
        ok, snap = safe_call(osv.get_stock_snapshot, [l.item.id for l in cart.lines.values()],
                             parent=self.app.root)
        if not ok:
            return
        changed = [l for l in cart.lines.values()
                   if l.item.id in snap and snap[l.item.id][1] != l.item.price]
        if changed:
            new_total = sum(l.qty * snap[l.item.id][1] for l in cart.lines.values() if l.item.id in snap)
            if not dialogs.confirm(f"Цены некоторых позиций изменились. Новый итог заказа: "
                                   f"{money(new_total)}. Продолжить оформление?", self.app.root):
                return
        elif not dialogs.confirm(f"Оформить заказ на сумму {money(cart.total())}?", self.app.root):
            return
        ok, res = safe_call(osv.create_order, user.id, cart.as_pairs(), parent=self.app.root)
        if ok:
            order_id, total = res
            cart.clear()
            dialogs.info(f"Заказ №{order_id} оформлен. Итого: {money(total)}.", self.app.root)
            self.app.show_catalog()          # каталог и остатки обновляются автоматически
