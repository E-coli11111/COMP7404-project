-- 创建测试数据库表结构和数据
-- 适用于电商销售场景

-- 1. 创建产品表
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建客户表
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    country VARCHAR(50),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 4. 创建订单详情表
CREATE TABLE IF NOT EXISTS order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 5. 创建库存表
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INTEGER PRIMARY KEY,
    product_id INTEGER,
    stock_quantity INTEGER DEFAULT 0,
    warehouse_location VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 插入产品测试数据
INSERT INTO products (product_id, product_name, category, price, description) VALUES
(1, 'iPhone 15 Pro', 'Electronics', 999.99, 'Latest iPhone with advanced features'),
(2, 'MacBook Pro 16"', 'Electronics', 2499.99, 'High-performance laptop for professionals'),
(3, 'AirPods Pro', 'Electronics', 249.99, 'Wireless noise-cancelling earbuds'),
(4, 'Samsung Galaxy S24', 'Electronics', 899.99, 'Flagship Android smartphone'),
(5, 'iPad Air', 'Electronics', 599.99, 'Versatile tablet for work and entertainment'),
(6, 'Nike Air Max', 'Fashion', 129.99, 'Comfortable running shoes'),
(7, 'Adidas Ultraboost', 'Fashion', 179.99, 'Premium athletic footwear'),
(8, 'Levi\'s Jeans', 'Fashion', 89.99, 'Classic denim jeans'),
(9, 'The Great Gatsby', 'Books', 12.99, 'Classic American novel'),
(10, 'Python Programming', 'Books', 45.99, 'Learn Python programming'),
(11, 'Coffee Maker', 'Home', 89.99, 'Automatic drip coffee maker'),
(12, 'Blender', 'Home', 129.99, 'High-speed blender for smoothies'),
(13, 'Yoga Mat', 'Sports', 29.99, 'Non-slip exercise mat'),
(14, 'Dumbbells Set', 'Sports', 199.99, 'Adjustable weight dumbbells'),
(15, 'Gaming Mouse', 'Electronics', 79.99, 'High-precision gaming mouse');

-- 插入客户测试数据
INSERT INTO customers (customer_id, customer_name, email, phone, address, city, country) VALUES
(1, 'John Smith', 'john.smith@email.com', '+1-555-0101', '123 Main St', 'New York', 'USA'),
(2, 'Emma Johnson', 'emma.johnson@email.com', '+1-555-0102', '456 Oak Ave', 'Los Angeles', 'USA'),
(3, 'Michael Brown', 'michael.brown@email.com', '+1-555-0103', '789 Pine St', 'Chicago', 'USA'),
(4, 'Sarah Davis', 'sarah.davis@email.com', '+1-555-0104', '321 Elm St', 'Houston', 'USA'),
(5, 'David Wilson', 'david.wilson@email.com', '+1-555-0105', '654 Maple Ave', 'Phoenix', 'USA'),
(6, 'Lisa Anderson', 'lisa.anderson@email.com', '+1-555-0106', '987 Cedar St', 'Philadelphia', 'USA'),
(7, 'James Taylor', 'james.taylor@email.com', '+1-555-0107', '147 Birch Ave', 'San Antonio', 'USA'),
(8, 'Jennifer Lee', 'jennifer.lee@email.com', '+1-555-0108', '258 Walnut St', 'San Diego', 'USA'),
(9, 'Robert Garcia', 'robert.garcia@email.com', '+1-555-0109', '369 Cherry Ave', 'Dallas', 'USA'),
(10, 'Maria Martinez', 'maria.martinez@email.com', '+1-555-0110', '741 Ash St', 'San Jose', 'USA');

-- 插入订单测试数据（最近3个月的数据）
INSERT INTO orders (order_id, customer_id, order_date, total_amount, status, shipping_address) VALUES
-- 2024年4月订单
(1, 1, '2024-04-15 10:30:00', 1249.98, 'completed', '123 Main St, New York, USA'),
(2, 2, '2024-04-16 14:45:00', 999.99, 'completed', '456 Oak Ave, Los Angeles, USA'),
(3, 3, '2024-04-18 09:15:00', 179.99, 'completed', '789 Pine St, Chicago, USA'),
(4, 4, '2024-04-20 16:20:00', 42.98, 'completed', '321 Elm St, Houston, USA'),
(5, 5, '2024-04-22 11:30:00', 329.98, 'completed', '654 Maple Ave, Phoenix, USA'),

-- 2024年5月订单
(6, 6, '2024-05-01 13:45:00', 2749.98, 'completed', '987 Cedar St, Philadelphia, USA'),
(7, 7, '2024-05-03 10:00:00', 899.99, 'completed', '147 Birch Ave, San Antonio, USA'),
(8, 8, '2024-05-05 15:30:00', 849.97, 'completed', '258 Walnut St, San Diego, USA'),
(9, 9, '2024-05-07 12:15:00', 229.98, 'completed', '369 Cherry Ave, Dallas, USA'),
(10, 1, '2024-05-10 09:45:00', 249.99, 'completed', '123 Main St, New York, USA'),
(11, 2, '2024-05-12 14:20:00', 599.99, 'completed', '456 Oak Ave, Los Angeles, USA'),
(12, 10, '2024-05-15 16:30:00', 309.98, 'completed', '741 Ash St, San Jose, USA'),

-- 2024年6月订单（最近一个月）
(13, 3, '2024-06-01 11:00:00', 1379.97, 'completed', '789 Pine St, Chicago, USA'),
(14, 4, '2024-06-03 13:30:00', 219.98, 'completed', '321 Elm St, Houston, USA'),
(15, 5, '2024-06-05 10:45:00', 79.99, 'processing', '654 Maple Ave, Phoenix, USA'),
(16, 6, '2024-06-08 15:15:00', 999.99, 'shipped', '987 Cedar St, Philadelphia, USA'),
(17, 7, '2024-06-10 12:30:00', 129.99, 'completed', '147 Birch Ave, San Antonio, USA'),
(18, 8, '2024-06-12 14:45:00', 58.98, 'completed', '258 Walnut St, San Diego, USA'),
(19, 9, '2024-06-15 09:30:00', 2499.99, 'processing', '369 Cherry Ave, Dallas, USA'),
(20, 10, '2024-06-18 16:00:00', 379.98, 'shipped', '741 Ash St, San Jose, USA'),
(21, 1, '2024-06-20 11:15:00', 45.99, 'completed', '123 Main St, New York, USA'),
(22, 2, '2024-06-22 13:45:00', 159.98, 'pending', '456 Oak Ave, Los Angeles, USA');

-- 插入订单详情测试数据
INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, total_price) VALUES
-- 订单1的商品
(1, 1, 1, 1, 999.99, 999.99),
(2, 1, 3, 1, 249.99, 249.99),

-- 订单2的商品
(3, 2, 1, 1, 999.99, 999.99),

-- 订单3的商品
(4, 3, 7, 1, 179.99, 179.99),

-- 订单4的商品
(5, 4, 9, 1, 12.99, 12.99),
(6, 4, 13, 1, 29.99, 29.99),

-- 订单5的商品
(7, 5, 11, 1, 89.99, 89.99),
(8, 5, 12, 1, 129.99, 129.99),
(9, 5, 6, 1, 129.99, 129.99),

-- 订单6的商品
(10, 6, 2, 1, 2499.99, 2499.99),
(11, 6, 3, 1, 249.99, 249.99),

-- 订单7的商品
(12, 7, 4, 1, 899.99, 899.99),

-- 订单8的商品
(13, 8, 5, 1, 599.99, 599.99),
(14, 8, 3, 1, 249.99, 249.99),

-- 订单9的商品
(15, 9, 14, 1, 199.99, 199.99),
(16, 9, 13, 1, 29.99, 29.99),

-- 订单10的商品
(17, 10, 3, 1, 249.99, 249.99),

-- 订单11的商品
(18, 11, 5, 1, 599.99, 599.99),

-- 订单12的商品
(19, 12, 14, 1, 199.99, 199.99),
(20, 12, 6, 1, 129.99, 129.99),

-- 6月订单商品
(21, 13, 2, 1, 2499.99, 2499.99),
(22, 13, 15, 1, 79.99, 79.99),

(23, 14, 11, 1, 89.99, 89.99),
(24, 14, 12, 1, 129.99, 129.99),

(25, 15, 15, 1, 79.99, 79.99),

(26, 16, 1, 1, 999.99, 999.99),

(27, 17, 6, 1, 129.99, 129.99),

(28, 18, 9, 2, 12.99, 25.98),
(29, 18, 10, 1, 45.99, 45.99),

(30, 19, 2, 1, 2499.99, 2499.99),

(31, 20, 4, 1, 899.99, 899.99),
(32, 20, 7, 1, 179.99, 179.99),

(33, 21, 10, 1, 45.99, 45.99),

(34, 22, 6, 1, 129.99, 129.99),
(35, 22, 13, 1, 29.99, 29.99);

-- 插入库存测试数据
INSERT INTO inventory (inventory_id, product_id, stock_quantity, warehouse_location) VALUES
(1, 1, 150, 'Warehouse A - New York'),
(2, 2, 75, 'Warehouse A - New York'),
(3, 3, 200, 'Warehouse B - California'),
(4, 4, 120, 'Warehouse A - New York'),
(5, 5, 90, 'Warehouse B - California'),
(6, 6, 300, 'Warehouse C - Texas'),
(7, 7, 250, 'Warehouse C - Texas'),
(8, 8, 180, 'Warehouse C - Texas'),
(9, 9, 500, 'Warehouse D - Illinois'),
(10, 10, 100, 'Warehouse D - Illinois'),
(11, 11, 80, 'Warehouse E - Florida'),
(12, 12, 60, 'Warehouse E - Florida'),
(13, 13, 400, 'Warehouse F - Washington'),
(14, 14, 50, 'Warehouse F - Washington'),
(15, 15, 150, 'Warehouse B - California');

-- 创建一些有用的视图
CREATE VIEW IF NOT EXISTS sales_summary AS
SELECT 
    p.product_name,
    p.category,
    SUM(oi.quantity) as total_quantity_sold,
    SUM(oi.total_price) as total_revenue,
    COUNT(DISTINCT o.order_id) as total_orders,
    AVG(oi.unit_price) as avg_price
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY p.product_id, p.product_name, p.category;

CREATE VIEW IF NOT EXISTS monthly_sales AS
SELECT 
    strftime('%Y-%m', o.order_date) as month,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value
FROM orders o
WHERE o.status = 'completed'
GROUP BY strftime('%Y-%m', o.order_date)
ORDER BY month;

-- 添加一些索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
