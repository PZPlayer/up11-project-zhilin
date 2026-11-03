"""Диалоги: у каждого типа свой заголовок и пиктограмма; ошибки не завершают приложение."""
import tkinter as tk
from tkinter import messagebox

from cart import check_qty
from errors import AppError
from styles import COLOR_ACCENT, COLOR_BG, font


def info(text, parent=None):
    messagebox.showinfo("Информация", text, parent=parent)


def warning(text, parent=None):
    messagebox.showwarning("Предупреждение", text, parent=parent)


def error(text, parent=None):
    messagebox.showerror("Ошибка", text, parent=parent)


def confirm(text, parent=None):
    return messagebox.askyesno("Подтверждение", text, icon="question", parent=parent)


def safe_call(func, *args, parent=None, **kwargs):
    """Выполняет операцию; возвращает (успех, результат). Любая ошибка объясняется пользователю."""
    try:
        return True, func(*args, **kwargs)
    except AppError as e:
        warning(str(e), parent)
    except Exception as e:  # ошибки БД и прочие
        error("Не удалось выполнить операцию с базой данных. Данные не изменены.\n"
              "Проверьте, что сервер PostgreSQL запущен и параметры подключения (config.py, "
              "переменные PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD) указаны верно.\n\n"
              f"Подробности: {e}", parent)
    return False, None


def ask_quantity(parent, prompt, current, maximum):
    """Модальный ввод количества. Возвращает целое число или None (отмена — данные не меняются)."""
    win = tk.Toplevel(parent)
    win.title("Количество")
    win.configure(bg=COLOR_BG)
    win.transient(parent)
    win.resizable(False, False)
    result = [None]

    tk.Label(win, text=prompt, font=font(11), bg=COLOR_BG).pack(padx=20, pady=(16, 6))
    var = tk.StringVar(value=str(current))
    spin = tk.Spinbox(win, from_=1, to=max(maximum, 1), textvariable=var, width=8, font=font(12))
    spin.pack(pady=4)
    tk.Label(win, text=f"Доступно: {maximum} шт.", font=font(10), bg=COLOR_BG).pack()

    def ok(_event=None):
        try:
            value = check_qty(var.get())
            if value > maximum:
                raise AppError(f"Нельзя заказать больше доступного остатка: доступно {maximum} шт.")
        except AppError as e:
            warning(str(e), win)
            return
        result[0] = value
        win.destroy()

    row = tk.Frame(win, bg=COLOR_BG)
    row.pack(pady=12)
    tk.Button(row, text="OK", command=ok, bg=COLOR_ACCENT, fg="black", relief="flat",
              font=font(11, True), width=10).pack(side="left", padx=6)
    tk.Button(row, text="Отмена", command=win.destroy, relief="flat", font=font(11),
              width=10).pack(side="left", padx=6)
    win.bind("<Return>", ok)
    win.bind("<Escape>", lambda e: win.destroy())
    spin.focus_set()
    win.grab_set()
    win.wait_window()
    return result[0]
