```
-- 1. Категории товаров
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Производители
CREATE TABLE manufacturers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE
);

-- 3. Поставщики
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE
);

-- 4. Пункты выдачи (из последнего файла с адресами)
CREATE TABLE pickup_points (
    id SERIAL PRIMARY KEY,
    address VARCHAR(300) NOT NULL UNIQUE
);

-- 5. Пользователи (из файла с ролями)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    login VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'manager', 'client'))
);

-- 6. Товары (основная таблица)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(20) DEFAULT 'шт.',
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    discount INTEGER DEFAULT 0 CHECK (discount BETWEEN 0 AND 100),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    description TEXT,
    photo VARCHAR(500),
    -- Внешние ключи (вместо текстовых полей!)
    category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
    manufacturer_id INTEGER REFERENCES manufacturers(id) ON DELETE RESTRICT,
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE RESTRICT
);

-- 7. Заказы
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL,
    delivery_date DATE,
    status VARCHAR(20) DEFAULT 'Новый' CHECK (status IN ('Новый', 'Завершен')),
    pickup_code INTEGER UNIQUE,
    -- Внешние ключи
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    pickup_point_id INTEGER REFERENCES pickup_points(id) ON DELETE RESTRICT
);

-- 8. Состав заказа (связующая таблица для 1НФ!)
CREATE TABLE order_items (
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, product_id)
);
```

```
-- Подтверждение создания
TRUNCATE TABLE myapp_orderitem CASCADE;
TRUNCATE TABLE myapp_order CASCADE;
TRUNCATE TABLE myapp_product CASCADE;
TRUNCATE TABLE myapp_user CASCADE;
TRUNCATE TABLE myapp_pickuppoint CASCADE;
TRUNCATE TABLE myapp_supplier CASCADE;
TRUNCATE TABLE myapp_manufacturer CASCADE;
TRUNCATE TABLE myapp_category CASCADE;

-- 1. Категории (должно быть 2: Женская обувь, Мужская обувь)
SELECT * FROM myapp_category;

-- 2. Производители (должно быть 6)
SELECT * FROM myapp_manufacturer;

-- 3. Поставщики (должно быть 2)
SELECT * FROM myapp_supplier;

-- 4. Пункты выдачи (должно быть около 37)
SELECT * FROM myapp_pickuppoint;

-- 5. Пользователи (должно быть 10)
SELECT * FROM myapp_user;

-- 6. Товары (должно быть 30)
SELECT * FROM myapp_product;

-- 7. Заказы (должно быть 10)
SELECT * FROM myapp_order;

-- 8. Состав заказов (каждый заказ с несколькими товарами)
SELECT * FROM myapp_orderitem;
```