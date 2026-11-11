-- Создание таблиц
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    last_name VARCHAR(50),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    role_id INTEGER
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    article VARCHAR(50) UNIQUE,
    price NUMERIC CHECK (price > 0)
);

CREATE TABLE variants (
    variant_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    variant_name VARCHAR(50),
    UNIQUE(product_id, variant_name)
);

CREATE TABLE stock_items (
    stock_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER CHECK (quantity >= 0)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    order_date DATE
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER CHECK (quantity > 0)
);

-- Заполнение данными (8 пользователей)
INSERT INTO users (login, last_name, first_name, role_id) 
SELECT 'user' || i, 'Фамилия', 'Имя', 1 FROM generate_series(1, 8) i;

-- Заполнение (24 товара)
INSERT INTO products (name, article, price) 
SELECT 'Товар ' || i, 'ART-' || i, 1000 FROM generate_series(1, 24) i;

-- 2 варианта
INSERT INTO variants (product_id, variant_name) VALUES (1, 'Красный'), (2, 'Синий');

-- 48 складских позиций
INSERT INTO stock_items (product_id, quantity) 
SELECT (i % 24) + 1, i FROM generate_series(1, 48) i;

-- 18 заказов
INSERT INTO orders (user_id, order_date) 
SELECT (i % 8) + 1, CURRENT_DATE FROM generate_series(1, 18) i;

-- 24 строки состава заказов
INSERT INTO order_items (order_id, product_id, quantity) 
SELECT (i % 18) + 1, (i % 24) + 1, 2 FROM generate_series(1, 24) i;