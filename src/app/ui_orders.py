import tkinter as tk
from tkinter import ttk

import dialogs
import order_service as osv
from dialogs import safe_call
from styles import COLOR_BG, fmt_date, font
from ui_common import Header, accent_button, plain_button
from ui_order_create import OrderCreateDialog
from ui_order_detail import OrderDetailDialog


class OrdersFrame(tk.Frame):
    """Список заказов (менеджер и администратор): номер, дата, ФИО клиента."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        header = Header(self, app, "Заказы")
        header.pack(fill="x")
        header.add_button("← К каталогу", app.show_catalog)

        self.tree = ttk.Treeview(self, columns=("id", "date", "client"), show="headings", selectmode="browse")
        for c, t, w, a in (("id", "№ заказа", 90, "center"), ("date", "Дата", 130, "center"),
                           ("client", "Клиент", 520, "w")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=a)
        self.tree.pack(fill="both", expand=True, padx=14, pady=12)
        self.tree.bind("<Double-1>", lambda e: self.open_detail())

        row = tk.Frame(self, bg=COLOR_BG)
        row.pack(fill="x", padx=14, pady=12)
        accent_button(row, "Состав заказа", self.open_detail).pack(side="left", padx=4)
        plain_button(row, "Добавить заказ", self.add_order).pack(side="left", padx=4)
        plain_button(row, "Удалить заказ", self.delete_order).pack(side="left", padx=4)
        plain_button(row, "Обновить", self.refresh).pack(side="left", padx=4)
        self.refresh()

    def refresh(self):
        ok, orders = safe_call(osv.get_orders, parent=self.app.root)
        for r in self.tree.get_children():
            self.tree.delete(r)
        for o in (orders if ok else []):
            self.tree.insert("", "end", iid=str(o.id), values=(o.id, fmt_date(o.date), o.client))

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            dialogs.warning("Выберите заказ в списке.", self.app.root)
            return None
        return int(sel[0])

    def open_detail(self):
        oid = self._selected()
        if oid is not None:
            OrderDetailDialog(self.app, oid)

    def add_order(self):
        OrderCreateDialog(self.app)

    def delete_order(self):
        oid = self._selected()
        if oid is None:
            return
        vals = self.tree.item(str(oid), "values")
        if not dialogs.confirm(f"Удалить заказ №{oid} от {vals[1]} (клиент: {vals[2]})?\n"
                               f"Зарезервированное количество вернётся в остаток.", self.app.root):
            return                                   # отмена не меняет данные
        ok, _ = safe_call(osv.delete_order, oid, parent=self.app.root)
        if ok:
            self.app.refresh_all()
            dialogs.info(f"Заказ №{oid} удалён. Остатки обновлены.", self.app.root)
