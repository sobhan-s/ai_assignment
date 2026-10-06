-- 04_seed_business.sql
SET search_path TO business;

INSERT INTO customers (name, email, signup_date) VALUES
    ('Alice Smith', 'alice@example.com', '2023-01-15'),
    ('Bob Jones', 'bob@example.com', '2023-03-22'),
    ('Charlie Brown', 'charlie@example.com', '2023-06-10');

INSERT INTO products (name, category, price) VALUES
    ('Laptop Pro', 'Electronics', 1299.99),
    ('Wireless Mouse', 'Accessories', 49.99),
    ('Mechanical Keyboard', 'Accessories', 149.99),
    ('Coffee Mug', 'Merchandise', 15.00);

INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
    (1, '2023-02-01 10:00:00', 1349.98, 'COMPLETED'),
    (2, '2023-04-15 14:30:00', 149.99, 'COMPLETED'),
    (1, '2023-07-20 09:15:00', 15.00, 'PENDING');

INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
    (1, 1, 1, 1299.99),
    (1, 2, 1, 49.99),
    (2, 3, 1, 149.99),
    (3, 4, 1, 15.00);
