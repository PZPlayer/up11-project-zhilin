import tkinter as tk
from tkinter import ttk

import catalog_service as cs
import permissions
from dialogs import safe_call
from styles import COLOR_BG, COLOR_LOW, LOW_STOCK_LIMIT, UNIT, font, money
from ui_common import Header, model_photo
from ui_product_dialog import ProductDialog

SORT_ASC = "Цена: по возрастанию"
SORT_DESC = "Цена: по убыванию"


class ModelCard(tk.Frame):
    """Карточка модели. Остаток <= 3 подсвечивается #ff8080. Клик по карточке открывает окно модели."""

    def __init__(self, parent, app, model, items):
        bg = COLOR_LOW if model.total_stock <= LOW_STOCK_LIMIT else COLOR_BG
        super().__init__(parent, bg=bg, highlightbackground="#555555", highlightthickness=1)
        self.app, self.model, self.items, self.bg = app, model, items, bg

        # --- изображение (вписано в область 150x150 без искажения) ---
        photo_box = tk.Frame(self, bg=bg, width=160, height=160)
        photo_box.pack(side="left", padx=10, pady=10)
        photo_box.pack_propagate(False)
        photo = model_photo(model.image, (150, 150))
        tk.Label(photo_box, image=photo, bg=bg).pack(expand=True)

        # --- справа: цена «от» и подсказка ---
        right = tk.Frame(self, bg=bg)
        right.pack(side="right", padx=14, pady=10, anchor="n")
        tk.Label(right, text=f"от {money(model.base_price)}", font=font(15, True), bg=bg).pack(anchor="e")
        hint = "Нажмите, чтобы посмотреть и заказать" if permissions.can_order(app.user) else "Нажмите, чтобы посмотреть"
        tk.Label(right, text=hint, font=font(10), bg=bg, fg="#333333").pack(anchor="e", pady=(10, 0))

        # --- центр: описание ---
        mid = tk.Frame(self, bg=bg)
        mid.pack(side="left", fill="both", expand=True, pady=10)
        tk.Label(mid, text=model.name, font=font(15, True), bg=bg, anchor="w").pack(fill="x")
        self._line(mid, f"Категория: {model.category} / {model.subcategory}")
        self._line(mid, f"Производство: {model.manufacturer}")
        self._line(mid, f"Описание: {model.description}", wrap=True)
        self._line(mid, f"Состав: {model.composition}", wrap=True)
        stock = "; ".join(f"{i.variant} — {i.quantity} {UNIT}" for i in items)
        self._line(mid, f"Варианты и остатки: {stock}", wrap=True, bold=True)
        if model.total_stock <= 0:
            self._line(mid, "Недоступно для заказа", bold=True)

        self._make_clickable(self)

    def _line(self, parent, text, wrap=False, bold=False):
        tk.Label(parent, text=text, font=font(11, bold), bg=self.bg, anchor="w", justify="left",
                 wraplength=520 if wrap else 0).pack(fill="x")

    def _make_clickable(self, widget):
        """Клик срабатывает на карточке и на всех вложенных элементах."""
        widget.bind("<Button-1>", self._open)
        widget.config(cursor="hand2")
        for child in widget.winfo_children():
            self._make_clickable(child)

    def _open(self, _event=None):
        ProductDialog(self.app, self.model, self.items)


class CatalogFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        self.models, self.stock, self.categories = [], {}, []

        header = Header(self, app, "Каталог")
        header.pack(fill="x")
        if permissions.can_order(app.user):
            self.cart_btn = header.add_button("Корзина", app.show_cart, accent=True)
            self.on_cart_changed()
        if permissions.can_manage_orders(app.user):
            header.add_button("Заказы", app.show_orders)

        st = app.catalog_state          # поиск, категория и сортировка сохраняются между формами
        self.search_var = tk.StringVar(value=st["search"])
        self.cat_var = tk.StringVar(value=st["category"])
        self.sort_var = tk.StringVar(value=st["sort"])

        if permissions.can_use_filters(app.user):
            bar = tk.Frame(self, bg=COLOR_BG)
            bar.pack(fill="x", padx=14, pady=8)
            tk.Label(bar, text="Поиск по наименованию:", font=font(11), bg=COLOR_BG).pack(side="left")
            tk.Entry(bar, textvariable=self.search_var, font=font(12), width=26).pack(side="left", padx=(6, 18))
            tk.Label(bar, text="Категория:", font=font(11), bg=COLOR_BG).pack(side="left")
            self.cat_combo = ttk.Combobox(bar, textvariable=self.cat_var, state="readonly", width=26)
            self.cat_combo.pack(side="left", padx=(6, 18))
            tk.Label(bar, text="Сортировка:", font=font(11), bg=COLOR_BG).pack(side="left")
            ttk.Combobox(bar, textvariable=self.sort_var, state="readonly", width=22,
                         values=[SORT_ASC, SORT_DESC]).pack(side="left", padx=6)
            self.count_label = tk.Label(bar, text="", font=font(11, True), bg=COLOR_BG)
            self.count_label.pack(side="right")
        else:
            self.count_label = tk.Label(self, text="Для поиска, заказа и корзины выполните вход.",
                                        font=font(11), bg=COLOR_BG)
            self.count_label.pack(anchor="w", padx=14, pady=8)

        # --- прокручиваемая область карточек ---
        wrap = tk.Frame(self, bg=COLOR_BG)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, bg=COLOR_BG, highlightthickness=0)
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.cards = tk.Frame(self.canvas, bg=COLOR_BG)
        self._win = self.canvas.create_window((0, 0), window=self.cards, anchor="nw")
        self.cards.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.bind("<Destroy>", lambda e: self.canvas.unbind_all("<MouseWheel>") if e.widget is self else None)

        self.reload()
        # поиск, фильтр и сортировка применяются сразу после изменения
        for var in (self.search_var, self.cat_var, self.sort_var):
            var.trace_add("write", lambda *a: self.render())

    def _wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def on_cart_changed(self):
        if hasattr(self, "cart_btn"):
            self.cart_btn.config(text=f"Корзина ({self.app.cart.count()})")

    def reload(self):
        """Читает каталог и остатки из БД и перерисовывает карточки."""
        ok1, models = safe_call(cs.load_models, parent=self.app.root)
        ok2, stock = safe_call(cs.load_stock_items, parent=self.app.root)
        ok3, cats = safe_call(cs.load_categories, parent=self.app.root)
        if not (ok1 and ok2 and ok3):
            models, stock, cats = [], {}, []
        self.models, self.stock, self.categories = models, stock, cats
        if hasattr(self, "cat_combo"):
            self.cat_combo.config(values=[cs.ALL_CATEGORIES] + cats)
            if self.cat_var.get() not in [cs.ALL_CATEGORIES] + cats:
                self.cat_var.set(cs.ALL_CATEGORIES)
        self.render()

    refresh = reload

    def render(self):
        st = self.app.catalog_state
        st.update(search=self.search_var.get(), category=self.cat_var.get(), sort=self.sort_var.get())
        if permissions.can_use_filters(self.app.user):
            shown = cs.filter_models(self.models, st["search"], st["category"], st["sort"] == SORT_DESC)
        else:
            shown = sorted(self.models, key=lambda m: m.id)
        for w in self.cards.winfo_children():
            w.destroy()
        for m in shown:
            ModelCard(self.cards, self.app, m, self.stock.get(m.id, [])).pack(fill="x", padx=14, pady=6)
        if not shown:
            tk.Label(self.cards, text="Ничего не найдено. Измените условия поиска или фильтра.",
                     font=font(13), bg=COLOR_BG).pack(pady=40)
        if permissions.can_use_filters(self.app.user):
            self.count_label.config(text=f"Найдено моделей: {len(shown)} из {len(self.models)}")
        self.canvas.yview_moveto(0)
