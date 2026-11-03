"""Мир гаджетов: каталог, корзина и заказы. Запуск:  python src/app/main.py"""
import tkinter as tk

from cart import Cart
from catalog_service import ALL_CATEGORIES
from config import APP_TITLE, ICON_PATH
from styles import COLOR_BG
from ui_cart import CartFrame
from ui_catalog import SORT_ASC, CatalogFrame
from ui_common import setup_styles
from ui_login import LoginFrame
from ui_orders import OrdersFrame


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1180x780")
        self.root.minsize(1000, 640)
        self.root.configure(bg=COLOR_BG)
        try:
            self.root.iconbitmap(str(ICON_PATH))
        except tk.TclError:
            pass  # на Linux/macOS .ico не поддерживается
        setup_styles()

        self.user = None                       # None — гость
        self.cart = Cart()
        self.catalog_state = {"search": "", "category": ALL_CATEGORIES, "sort": SORT_ASC}
        self.current = None
        self.container = tk.Frame(self.root, bg=COLOR_BG)
        self.container.pack(fill="both", expand=True)
        self.root.report_callback_exception = self._on_error   # ошибки интерфейса не завершают приложение
        self.show_login()

    # --- навигация ---
    def _show(self, frame_class):
        if self.current is not None:
            self.current.destroy()
        self.current = frame_class(self.container, self)
        self.current.pack(fill="both", expand=True)

    def show_login(self):
        self.user = None
        self.cart.clear()
        self._show(LoginFrame)

    def show_catalog(self):
        self._show(CatalogFrame)

    def show_cart(self):
        self._show(CartFrame)

    def show_orders(self):
        self._show(OrdersFrame)

    # --- обновление данных на экране ---
    def refresh_all(self):
        if hasattr(self.current, "refresh"):
            self.current.refresh()

    def on_cart_changed(self):
        if hasattr(self.current, "on_cart_changed"):
            self.current.on_cart_changed()

    def _on_error(self, exc, val, tb):
        from tkinter import messagebox
        messagebox.showerror("Ошибка", f"Произошла непредвиденная ошибка. Приложение продолжит работу.\n\n{val}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
