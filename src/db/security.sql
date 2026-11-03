-- =====================================================================
--  Защита данных (ПК 11.6): отдельная учётная запись приложения с минимальными правами.
--  Выполняется под суперпользователем ПОСЛЕ mir_gadgetov.sql:
--     psql -U postgres -d gadgets_db -f src/db/security.sql
--  Затем в приложении: PGUSER=gadgets_app, PGPASSWORD=<ваш пароль>
-- =====================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gadgets_app') THEN
        CREATE ROLE gadgets_app LOGIN PASSWORD 'change_me_please';   -- ОБЯЗАТЕЛЬНО сменить пароль
    END IF;
END $$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM gadgets_app;
GRANT CONNECT ON DATABASE gadgets_db TO gadgets_app;
GRANT USAGE ON SCHEMA public TO gadgets_app;

-- справочники и каталог: только чтение
GRANT SELECT ON roles, users, categories, subcategories, manufacturers, variants, models TO gadgets_app;
-- остатки меняются при оформлении и удалении заказов
GRANT SELECT, UPDATE ON stock_items TO gadgets_app;
-- заказы: полный набор операций
GRANT SELECT, INSERT, UPDATE, DELETE ON orders, order_items TO gadgets_app;
-- счётчики идентификаторов нужны для INSERT
GRANT USAGE, SELECT ON SEQUENCE orders_id_seq, order_items_id_seq TO gadgets_app;
-- представления для отчётов
GRANT SELECT ON v_catalog, v_order_totals TO gadgets_app;

-- Учётная запись приложения не может создавать/удалять таблицы и менять каталог и пользователей.
