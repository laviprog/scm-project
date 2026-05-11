BEGIN;

-- Справочник заказчиков
INSERT INTO customers (customer_id, customer_group_id, customer_name) VALUES
(1, NULL, 'ПМХ'),
(2, NULL, 'НЛМК Европа'),
(3, NULL, 'ТМК'),
(4, NULL, 'Инпром'),
(5, NULL, 'Синара'),
(6, NULL, 'АвтоВАЗ'),
(7, NULL, 'FIAT'),
(8, NULL, 'VAI');

-- Справочник продуктов
INSERT INTO products (
    product_id,
    product_desc,
    product_min_weight,
    product_max_weight,
    product_group,
    product_type
) VALUES
(1, 'Рулон х/к дресс.', 8.00, 11.00, 'х/к', 'дрессированный рулон'),
(2, 'Рулон х/к АНО', 15.00, 15.00, 'х/к', 'АНО рулон'),
(3, 'Рулон х/к с АНО', 8.00, 8.00, 'х/к', 'с АНО рулон'),
(4, 'Рулон г/к травленный', 10.00, 11.00, 'г/к', 'травленный рулон'),
(5, 'Рулон г/к', 13.00, 13.00, 'г/к', 'горячекатаный рулон');

-- Агрегаты
INSERT INTO resources (resource_id, resource_desc, wearout) VALUES
(1, 'Прокатный стан г/п', NULL),
(2, 'Прокатный стан х/п', NULL),
(3, 'Агрегат резки', NULL),
(4, 'Линия упаковки', NULL),
(5, 'Агрегат травления', NULL),
(6, 'Линия АНО', NULL),
(7, 'Отжиг в КП', NULL),
(8, 'Линия дрессировки', NULL);

-- Сбытовые заказы
INSERT INTO sales_orders (
    sales_order_id,
    customer_id,
    product_id,
    target_weight,
    tolerance,
    unit_weight,
    due_date,
    priority,
    status
) VALUES
(1001, 1, 1, 2900.00, 15.00, 11.00, DATE '2025-04-15', 2, 0),
(1002, 2, 1, 1010.00, 10.00, 8.00,  DATE '2025-04-17', 1, 0),
(1003, 3, 2, 1040.00, 20.00, 15.00, DATE '2025-04-28', 2, 0),
(1004, 4, 3, 2200.00, 10.00, 8.00,  DATE '2025-04-30', 1, 0),
(1005, 5, 4, 2900.00, 15.00, 10.00, DATE '2025-04-21', 3, 0),
(1006, 6, 5, 3100.00, 15.00, 13.00, DATE '2025-04-10', 4, 0),
(1007, 7, 1, 1700.00, 10.00, 9.00,  DATE '2025-04-04', 3, 0),
(1008, 8, 4, 3000.00, 15.00, 11.00, DATE '2025-04-12', 1, 0);

-- Рулон х/к дресс.
INSERT INTO standard_operations (
    operation_ref, product_id, resource_id, alternate_pref, operation_id, performance, yield
) VALUES
(100101, 1, 1, 1, 10, 160, 1.0), -- Прокатный стан г/п
(100102, 1, 5, 1, 20, 150, 1.0), -- Агрегат травления
(100103, 1, 2, 1, 30, 185, 1.0), -- Прокатный стан х/п
(100104, 1, 7, 1, 40, 90,  1.0), -- Отжиг в КП
(100105, 1, 8, 1, 50, 180, 1.0), -- Линия дрессировки
(100106, 1, 4, 1, 60, 180, 1.0); -- Линия упаковки

-- Рулон х/к АНО
INSERT INTO standard_operations (
    operation_ref, product_id, resource_id, alternate_pref, operation_id, performance, yield
) VALUES
(100201, 2, 1, 1, 10, 160, 1.0),
(100202, 2, 5, 1, 20, 150, 1.0),
(100203, 2, 2, 1, 30, 185, 1.0),
(100204, 2, 6, 1, 40, 170, 1.0),
(100205, 2, 4, 1, 50, 180, 1.0);

-- Рулон х/к с АНО
INSERT INTO standard_operations (
    operation_ref, product_id, resource_id, alternate_pref, operation_id, performance, yield
) VALUES
(100301, 3, 1, 1, 10, 160, 1.0),
(100302, 3, 5, 1, 20, 150, 1.0),
(100303, 3, 2, 1, 30, 185, 1.0),
(100304, 3, 6, 1, 40, 170, 1.0),
(100305, 3, 4, 1, 50, 180, 1.0);

-- Рулон г/к травленный
INSERT INTO standard_operations (
    operation_ref, product_id, resource_id, alternate_pref, operation_id, performance, yield
) VALUES
(100401, 4, 1, 1, 10, 160, 1.0),
(100402, 4, 5, 1, 20, 150, 1.0),
(100403, 4, 4, 1, 30, 180, 1.0);

-- Рулон г/к
INSERT INTO standard_operations (
    operation_ref, product_id, resource_id, alternate_pref, operation_id, performance, yield
) VALUES
(100501, 5, 1, 1, 10, 160, 1.0),
(100502, 5, 4, 1, 20, 180, 1.0);

-- Производственный календарь: 23 доступных часа в сутки на каждый агрегат
INSERT INTO calendar (production_date, resource_id, available_hours)
SELECT production_date::date, resource_id, 23.00
FROM generate_series(DATE '2025-04-01', DATE '2025-04-30', INTERVAL '1 day') AS production_date
CROSS JOIN resources;

COMMIT;
