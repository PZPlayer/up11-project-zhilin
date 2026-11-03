"""Общие элементы интерфейса: шапка с логотипом, кнопки, картинки."""
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from config import IMAGES_DIR, LOGO_PATH, PLACEHOLDER_PATH
from styles import COLOR_ACCENT, COLOR_ALT, COLOR_BG, font

_RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
_cache = {}


def load_photo(path, box):
    """Картинка, вписанная в область box без искажения пропорций."""
    key = (str(path), box)
    if key not in _cache:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(box, _RESAMPLE)
        _cache[key] = ImageTk.PhotoImage(img)
    return _cache[key]


def model_photo(image_name, box=(150, 150)):
    """Изображение модели; если имя пустое или файла нет — заглушка picture.png."""
    path = IMAGES_DIR / image_name if image_name else None
    if path is None or not path.exists():
        path = PLACEHOLDER_PATH
    return load_photo(path, box)


def accent_button(parent, text, command, width=None, state="normal"):
    """Кнопка целевого действия: фон #70B2AF, чёрный текст."""
    return tk.Button(parent, text=text, command=command, bg=COLOR_ACCENT, fg="black",
                     activebackground="#5c9f9c", relief="flat", font=font(11, True),
                     padx=12, pady=4, width=width, state=state, cursor="hand2")


def plain_button(parent, text, command, width=None, bg=COLOR_BG):
    return tk.Button(parent, text=text, command=command, bg=bg, fg="black", relief="groove",
                     font=font(11), padx=10, pady=3, width=width, cursor="hand2")


def setup_styles():
    st = ttk.Style()
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    st.configure("Treeview", font=font(11), rowheight=28, background=COLOR_BG, fieldbackground=COLOR_BG)
    st.configure("Treeview.Heading", font=font(11, True), background=COLOR_ALT)
    st.map("Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "black")])
    st.configure("TCombobox", font=font(11))


class Header(tk.Frame):
    """Шапка формы: логотип, заголовок, пользователь и кнопки (возврат / выход)."""

    def __init__(self, parent, app, title):
        super().__init__(parent, bg=COLOR_ALT)
        self.app = app
        logo = load_photo(LOGO_PATH, (210, 58))     # пропорции логотипа сохраняются
        tk.Label(self, image=logo, bg=COLOR_ALT).pack(side="left", padx=14, pady=8)
        tk.Label(self, text=title, font=font(20, True), bg=COLOR_ALT).pack(side="left", padx=10)
        who = app.user.fio + f" ({app.user.role})" if app.user else "Гость"
        tk.Button(self, text="Выйти" if app.user else "Войти", command=app.show_login,
                  bg=COLOR_BG, relief="groove", font=font(11), padx=10).pack(side="right", padx=14)
        tk.Label(self, text=who, font=font(11), bg=COLOR_ALT).pack(side="right", padx=8)

    def add_button(self, text, command, accent=False):
        make = accent_button if accent else plain_button
        btn = make(self, text, command)
        btn.pack(side="right", padx=4)
        return btn
