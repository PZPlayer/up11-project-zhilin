from contextlib import contextmanager

import psycopg2

from config import DB_CONFIG


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@contextmanager
def db_cursor():
    """Курсор внутри транзакции: commit при успехе, rollback при любой ошибке."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()
