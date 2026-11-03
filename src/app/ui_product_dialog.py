import tkinter as tk
from tkinter import ttk

import dialogs
import permissions
from cart import check_qty
from styles import COLOR_BG, COLOR_LOW, LOW_STOCK_LIMIT, UNIT, font, money
from ui_common import accent_button, model_photo, plain_button


class ProductDialog(tk.Toplevel):
    """Окно модели (открывается по клику на карточку): полное описание, варианты с ценой и остатком
    и заказ выбранного варианта (кнопка «В корзину» — для авторизованных пользователей)."""

    def __init__(self, app, model, items):
        super().__init__(app.root)
        self.app, self.model, self.items = app, model, items
        self.selected = None
        self.title(f"{model.name} — {model.manufacturer}")
        self.configure(bg=COLOR_BG)
        self.geometry("900x700")
        self.transient(app.root)

        # --- верх: изображение и основные сведения ---
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill="x", padx=18, pady=(16, 6))
        box = tk.Frame(top, bg=COLOR_BG, width=250, height=250)
        box.pack(side="left")
        box.pack_propagate(False)
        photo = model_photo(model.image, (240, 240))       # вписано без искажения; нет файла — заглушка
        tk.Label(box, image=photo, bg=COLOR_BG).pack(expand=True)

        info = tk.Frame(top, bg=COLOR_BG)
        info.pack(side="left", fill="both", expand=True, padx=(18, 0))
        tk.Label(info, text=model.name, font=font(20, True), bg=COLOR_BG, anchor="w").pack(fill="x")
        for text in (f"Категория: {model.category} / {model.subcategory}",
                     f"Производство: {model.manufacturer}"):
            tk.Label(info, text=text, font=font(12), bg=COLOR_BG, anchor="w").pack(fill="x", pady=1)
        tk.Label(info, text=f"от {money(model.base_price)}", font=font(18, True), bg=COLOR_BG,
                 anchor="w").pack(fill="x", pady=(8, 4))
        if model.total_stock <= LOW_STOCK_LIMIT:           # та же подсветка, что и в каталоге
            text = ("Недоступно для заказа" if model.total_stock <= 0
                    else f"Мало на складе: всего {model.total_stock} {UNIT}")
            tk.Label(info, text=text, font=font(12, True), bg=COLOR_LOW, anchor="w",
                     padx=8, pady=4).pack(fill="x", pady=(4, 0))

        # --- описание и состав ---
        self._field("Описание:", model.description)
        self._field("Состав:", model.composition)

        # --- варианты ---
        tk.Label(self, text="Варианты исполнения", font=font(12, True), bg=COLOR_BG,
                 anchor="w").pack(fill="x", padx=18, pady=(10, 2))
        self.tree = ttk.Treeview(self, columns=("variant", "price", "stock"), show="headings",
                                 height=max(len(items), 1), selectmode="none")
        for c, t, w, a in (("variant", "Вариант", 200, "w"), ("price", "Цена", 200, "e"),
                           ("stock", "Остаток", 200, "e")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=a)
        for i in items:
            self.tree.insert("", "end", values=(i.variant, money(i.price),
                                                f"{i.quantity} {UNIT}" if i.quantity > 0 else "Недоступно"))
        self.tree.pack(fill="x", padx=18)

        # --- заказ ---
        order = tk.Frame(self, bg=COLOR_BG)
        order.pack(fill="x", padx=18, pady=14)
        if permissions.can_order(app.user):
            tk.Label(order, text="Вариант:", font=font(12, True), bg=COLOR_BG).pack(side="left")
            self.variant_var = tk.StringVar()
            self.variant_combo = ttk.Combobox(order, textvariable=self.variant_var, state="readonly",
                                              width=16, values=[i.variant for i in items])
            self.variant_combo.pack(side="left", padx=8)
            self.variant_combo.bind("<<ComboboxSelected>>", self._on_variant)
            self.qty_var = tk.StringVar(value="1")
            tk.Spinbox(order, from_=1, to=999, textvariable=self.qty_var, width=5,
                       font=font(12)).pack(side="left", padx=4)
            self.add_btn = accent_button(order, "В корзину", self._add, state="disabled")
            self.add_btn.pack(side="left", padx=8)
            self.info_label = tk.Label(order, text="Выберите вариант", font=font(12), bg=COLOR_BG,
                                       justify="left")
            self.info_label.pack(side="left", padx=10)
        else:
            tk.Label(order, text="Чтобы заказать, войдите в систему.", font=font(12),
                     bg=COLOR_BG).pack(side="left")
        plain_button(self, "Закрыть", self.destroy).pack(anchor="e", padx=18, pady=(0, 14))

    def _field(self, title, text):
        row = tk.Frame(self, bg=COLOR_BG)
        row.pack(fill="x", padx=18, pady=3)
        tk.Label(row, text=title, font=font(12, True), bg=COLOR_BG, width=10, anchor="nw").pack(side="left")
        tk.Label(row, text=text, font=font(12), bg=COLOR_BG, anchor="w", justify="left",
                 wraplength=720).pack(side="left", fill="x", expand=True)

    def _on_variant(self, _event=None):
        self.selected = next((i for i in self.items if i.variant == self.variant_var.get()), None)
        if not self.selected:
            return
        if self.selected.quantity > 0:       # после выбора варианта — его цена и доступное количество
            self.info_label.config(
                text=f"Цена: {money(self.selected.price)}   Доступно: {self.selected.quantity} {UNIT}")
            self.add_btn.config(state="normal")
        else:
            self.info_label.config(text=f"Цена: {money(self.selected.price)}   Недоступно для заказа")
            self.add_btn.config(state="disabled")

    def _add(self):
        if not self.selected:
            dialogs.warning("Сначала выберите вариант исполнения.", self)
            return
        try:
            qty = check_qty(self.qty_var.get())
            self.app.cart.add(self.selected, qty)
        except Exception as e:               # AppError — понятное сообщение; приложение не падает
            dialogs.warning(str(e), self)
            return
        in_cart = self.app.cart.lines[self.selected.id].qty
        self.info_label.config(text=f"Добавлено в корзину: {qty} {UNIT}. Всего этого варианта: {in_cart} {UNIT}")
        self.app.on_cart_changed()
