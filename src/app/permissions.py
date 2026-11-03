"""Права ролей (Приложение 1). user=None означает гостя."""
ROLE_ADMIN = "Администратор"
ROLE_MANAGER = "Менеджер"
ROLE_USER = "Авторизованный пользователь"


def can_use_filters(user):   # поиск, фильтр, сортировка
    return user is not None


def can_order(user):         # корзина и оформление собственного заказа
    return user is not None


def can_manage_orders(user):  # список всех заказов, создание и удаление заказа
    return user is not None and user.role in (ROLE_MANAGER, ROLE_ADMIN)


def can_edit_orders(user):   # изменение даты и состава заказа
    return user is not None and user.role == ROLE_ADMIN
