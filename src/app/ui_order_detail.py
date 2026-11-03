import tkinter as tk
from tkinter import ttk

import dialogs
import order_service as osv
import permissions
from dialogs import safe_call
from styles import COLOR_BG, fmt_date, font, money, parse_date
from ui_common import accent_button, plain_button


class OrderDetailDialog(tk.Toplevel):
    """Состав заказа: модель, производство, вариант, количество, историческая цена, итог.
    Администратор дополнительно меняет дату и удаляет отдельные строки."""

    def __init__(self, app, order_id):
        super().__init__(app.root)
        self.app, self.order_id = app, order_id
        self.can_edit = permissions.can_edit_orders(app.user)
        self.title(f"Состав заказа №{order_id}")
        self.configure(bg=COLOR_BG)
        self.geometry("900x520")
        self.transient(app.root)

        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill="x", padx=14, pady=10)
        tk.Label(top, text="Дата заказа:", font=font(11, True), bg=COLOR_BG).pack(side="left")
        self.date_var = tk.StringVar()
        self.date_entry = tk.Entry(top, textvariable=self.date_var, width=12, font=font(12),
                                   state="normal" if self.can_edit else "readonly")
        self.date_entry.pack(side="left", padx=6)
        if self.can_edit:
            accent_button(top, "Сохранить дату", self.save_date).pack(side="left", padx=4)
        self.client_label = tk.Label(top, text="", font=font(12, True), bg=COLOR_BG)
        self.client_label.pack(side="right")

        cols = ("model", "maker", "variant", "qty", "price", "total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for c, t, w in (("model", "Модель", 230), ("maker", "Производство", 130), ("variant", "Вариант", 90),
                        ("qty", "Кол-во, шт.", 90), ("price", "Цена (на момент заказа)", 170), ("total", "Сумма", 130)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w" if c in ("model", "maker", "variant") else "e")
        self.tree.pack(fill="both", expand=True, padx=14)

        self.total_label = tk.Label(self, text="", font=font(15, True), bg=COLOR_BG)
        self.total_label.pack(anchor="e", padx=18, pady=6)
        row = tk.Frame(self, bg=COLOR_BG)
        row.pack(fill="x", padx=14, pady=10)
        if self.can_edit:
            plain_button(row, "Удалить строку", self.delete_line).pack(side="left", padx=4)
        plain_button(row, "Закрыть", self.destroy).pack(side="right", padx=4)
        self.load()

    def load(self):
        ok1, order = safe_call(osv.get_order, self.order_id, parent=self)
        ok2, lines = safe_call(osv.get_order_lines, self.order_id, parent=self)
        if not (ok1 and ok2) or order is None:
            return
        self.date_var.set(fmt_date(order.date))
        self.client_label.config(text=f"Клиент: {order.client}")
        for r in self.tree.get_children():
            self.tree.delete(r)
        for l in lines:
            self.tree.insert("", "end", iid=str(l.id),
                             values=(l.model, l.manufacturer, l.variant, l.quantity,
                                     money(l.unit_price), money(l.total)))
        self.total_label.config(text=f"Итого: {money(sum(l.total for l in lines))}")

    def save_date(self):
        ok, new_date = safe_call(parse_date, self.date_var.get(), parent=self)
        if not ok:
            return
        ok, _ = safe_call(osv.update_order_date, self.order_id, new_date, parent=self)
        if ok:
            self.app.refresh_all()
            dialogs.info("Дата заказа изменена.", self)

    def delete_line(self):
        sel = self.tree.selection()
        if not sel:
            dialogs.warning("Выберите строку заказа.", self)
            return
        line_id = int(sel[0])
        ok, n = safe_call(osv.count_lines, self.order_id, parent=self)
        if not ok:
            return
        if n <= 1:      # последняя строка: удаляется весь заказ, нужно подтверждение
            if not dialogs.confirm("Это последняя строка заказа. Удалить заказ целиком? "
                                   "Количество вернётся в остаток.", self):
                return
            ok, _ = safe_call(osv.delete_order, self.order_id, parent=self)
            if ok:
                self.app.refresh_all()
                dialogs.info("Заказ удалён. Остатки обновлены.", self.app.root)
                self.destroy()
            return
        if not dialogs.confirm("Удалить выбранную строку заказа? Количество вернётся в остаток.", self):
            return
        ok, _ = safe_call(osv.delete_order_line, line_id, parent=self)
        if ok:
            self.app.refresh_all()
            self.load()
