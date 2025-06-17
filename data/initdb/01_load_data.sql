-- SQL script to load initial data into the database.

-- Load Categories
\COPY category(id, name, parent_id) FROM '/docker-entrypoint-initdb.d/category.csv' DELIMITER ',' CSV HEADER;

-- Fix category sequence after loading data with explicit IDs
SELECT setval('category_id_seq', (SELECT MAX(id) FROM category));

-- Load Products
\COPY products(sku, category_id, name, description, price, brand, spec_json) FROM '/docker-entrypoint-initdb.d/products.csv' DELIMITER ',' CSV HEADER;

-- Load Customers
\COPY customers(customer_id, name, email, phone, address) FROM '/docker-entrypoint-initdb.d/customers.csv' DELIMITER ',' CSV HEADER;

-- Load Invoices
\COPY invoices(invoice_id, customer_id, total, pdf_url, created_at) FROM '/docker-entrypoint-initdb.d/invoices.csv' DELIMITER ',' CSV HEADER;

-- Load Warehouses
\COPY warehouses(warehouse_id, name, address) FROM '/docker-entrypoint-initdb.d/warehouses.csv' DELIMITER ',' CSV HEADER;

-- Load Stock (using a temporary table to convert SKU to product_id)
CREATE TEMP TABLE temp_stock (
    sku TEXT,
    warehouse_id TEXT,
    quantity INTEGER
);

\COPY temp_stock(sku, warehouse_id, quantity) FROM '/docker-entrypoint-initdb.d/stock.csv' DELIMITER ',' CSV HEADER;

INSERT INTO stock (product_id, warehouse_id, quantity)
SELECT p.id, ts.warehouse_id, ts.quantity
FROM temp_stock ts
JOIN products p ON p.sku = ts.sku;

DROP TABLE temp_stock;

-- Load Images
\COPY images(product_id, url, alt_text) FROM '/docker-entrypoint-initdb.d/images.csv' DELIMITER ',' CSV HEADER;
