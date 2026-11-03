import tkinter as tk
from tkinter import ttk

import catalog_service as cs
import dialogs
import order_service as osv
from cart import Cart, check_qty
from dialogs import safe_call
from styles import COLOR_BG, UNIT, font, money
from ui_common import accent_button, plain_button


class OrderCreateDialog(tk.Toplevel):
    """Добавление заказа для выбранного клиента (менеджер и администратор)."""

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.cart = Cart()
        self.title("Добавление заказа")
        self.configure(bg=COLOR_BG)
        self.geometry("900x600")
        self.transient(app.root)

        ok1, self.clients = safe_call(osv.list_clients, parent=self)
        ok2, self.models = safe_call(cs.load_models, parent=self)
        ok3, self.stock = safe_call(cs.load_stock_items, parent=self)
        if not (ok1 and ok2 and ok3):
            self.after(10, self.destroy)
            return
        self.models_by_label = {f"{m.name} — {m.manufacturer}": m for m in self.models}
        self.items = []

        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(top, text="Клиент:", font=font(11, True), bg=COLOR_BG).pack(side="left")
        self.client_var = tk.StringVar()
        self.client_label_to_user = {f"{c.fio} ({c.login})": c for c in self.clients}
        ttk.Combobox(top, textvariable=self.client_var, state="readonly", width=48,
                     values=list(self.client_label_to_user)).pack(side="left", padx=8)

        pick = tk.Frame(self, bg=COLOR_BG)
        pick.pack(fill="x", padx=14, pady=6)
        self.model_var, self.variant_var, self.qty_var = tk.StringVar(), tk.StringVar(), tk.StringVar(value="1")
        tk.Label(pick, text="Модель:", font=font(11), bg=COLOR_BG).pack(side="left")
        mc = ttk.Combobox(pick, textvariable=self.model_var, state="readonly", width=34,
                          values=list(self.models_by_label))
        mc.pack(side="left", padx=6)
        mc.bind("<<ComboboxSelected>>", self._on_model)
        tk.Label(pick, text="Вариант:", font=font(11), bg=COLOR_BG).pack(side="left")
        self.variant_combo = ttk.Combobox(pick, textvariable=self.variant_var, state="readonly", width=22)
        self.variant_combo.pack(side="left", padx=6)
        tk.Spinbox(pick, from_=1, to=999, textvariable=self.qty_var, width=5, font=font(11)).pack(side="left", padx=4)
        accent_button(pick, "Добавить позицию", self.add_item).pack(side="left", padx=6)

        cols = ("model", "variant", "qty", "price", "total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for c, t, w in (("model", "Модель", 300), ("variant", "Вариант", 110), ("qty", "Кол-во, шт.", 90),
                        ("price", "Цена за шт.", 140), ("total", "Сумма", 140)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w" if c in ("model", "variant") else "e")
        self.tree.pack(fill="both", expand=True, padx=14, pady=6)
        self.total_label = tk.Label(self, text="Итого: " + money(0), font=font(15, True), bg=COLOR_BG)
        self.total_label.pack(anchor="e", padx=18)

        row = tk.Frame(self, bg=COLOR_BG)
        row.pack(fill="x", padx=14, pady=10)
        plain_button(row, "Удалить позицию", self.remove_item).pack(side="left", padx=4)
        accent_button(row, "Сохранить заказ", self.save).pack(side="right", padx=4)
        plain_button(row, "Отмена", self.destroy).pack(side="right", padx=4)

    def _on_model(self, _e=None):
        m = self.models_by_label.get(self.model_var.get())
        self.items = self.stock.get(m.id, []) if m else []
        labels = [f"{i.variant} — {i.quantity} {UNIT}" if i.quantity > 0 else f"{i.variant} — недоступно"
                  for i in self.items]
        self.variant_combo.config(values=labels)
        self.variant_var.set("")

    def add_item(self):
        idx = self.variant_combo.current()
        if idx < 0:
            dialogs.warning("Выберите модель и вариант исполнения.", self)
            return
        try:
            self.cart.add(self.items[idx], check_qty(self.qty_var.get()))
        except Exception as e:
            dialogs.warning(str(e), self)
            return
        self._redraw()

    def remove_item(self):
        sel = self.tree.selection()
        if not sel:
            dialogs.warning("Выберите позицию в таблице.", self)
        elif dialogs.confirm("Удалить выбранную позицию?", self):
            self.cart.remove(int(sel[0]))
            self._redraw()

    def _redraw(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for l in self.cart.lines.values():
            self.tree.insert("", "end", iid=str(l.item.id),
                             values=(l.item.model_name, l.item.variant, l.qty, money(l.item.price), money(l.total)))
        self.total_label.config(text=f"Итого: {money(self.cart.total())}")

    def save(self):
        client = self.client_label_to_user.get(self.client_var.get())
        if client is None:
            dialogs.warning("Выберите клиента, для которого создаётся заказ.", self)
            return
        if not len(self.cart):
            dialogs.warning("Добавьте хотя бы одну позицию.", self)
            return
        ok, res = safe_call(osv.create_order, client.id, self.cart.as_pairs(), parent=self)
        if ok:
            self.app.refresh_all()
            dialogs.info(f"Заказ №{res[0]} для клиента «{client.fio}» сохранён. Итого: {money(res[1])}.", self.app.root)
            self.destroy()
