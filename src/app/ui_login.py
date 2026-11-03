import tkinter as tk

import auth_service
from config import LOGO_PATH
from dialogs import safe_call
from styles import COLOR_ALT, COLOR_BG, font
from ui_common import accent_button, load_photo, plain_button


class LoginFrame(tk.Frame):
    """Форма входа: только логин, без пароля."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        box = tk.Frame(self, bg=COLOR_ALT, padx=40, pady=30)
        box.place(relx=0.5, rely=0.45, anchor="center")

        logo = load_photo(LOGO_PATH, (380, 104))
        tk.Label(box, image=logo, bg=COLOR_ALT).pack(pady=(0, 14))
        tk.Label(box, text="Вход в систему", font=font(20, True), bg=COLOR_ALT).pack()
        tk.Label(box, text="Введите логин (пароль не требуется)", font=font(11),
                 bg=COLOR_ALT).pack(pady=(10, 4))

        self.login_var = tk.StringVar()
        entry = tk.Entry(box, textvariable=self.login_var, font=font(14), width=24)
        entry.pack(pady=4)
        entry.bind("<Return>", lambda e: self.login())
        entry.focus_set()

        accent_button(box, "Войти", self.login, width=22).pack(pady=(12, 6))
        plain_button(box, "Продолжить как гость", self.guest, width=24).pack()
        tk.Label(box, text="Например: admin, manager1, client01", font=font(10),
                 fg="#444444", bg=COLOR_ALT).pack(pady=(12, 0))

    def login(self):
        ok, user = safe_call(auth_service.login, self.login_var.get(), parent=self.app.root)
        if ok:
            self.app.user = user
            self.app.cart.clear()
            self.app.show_catalog()

    def guest(self):
        self.app.user = None
        self.app.cart.clear()
        self.app.show_catalog()
