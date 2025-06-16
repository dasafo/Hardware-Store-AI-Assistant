-- SQL script to load initial data from CSV files into the database tables.

-- Load data into the 'category' table.
\COPY category(id, name, parent_id) FROM '/docker-entrypoint-initdb.d/category.csv' DELIMITER ',' CSV HEADER;

-- Load data into the 'products' table.
\COPY products(id, name, description, category_id) FROM '/docker-entrypoint-initdb.d/products.csv' DELIMITER ',' CSV HEADER;

-- Load data into the 'images' table.
\COPY images(id, product_id, url, alt_text) FROM '/docker-entrypoint-initdb.d/images.csv' DELIMITER ',' CSV HEADER;

-- Load data into the 'stock' table.
\COPY stock(id, product_id, quantity) FROM '/docker-entrypoint-initdb.d/stock.csv' DELIMITER ',' CSV HEADER;

-- Load data into the 'invoices' table.
\COPY invoices(id, customer_name, created_at) FROM '/docker-entrypoint-initdb.d/invoices.csv' DELIMITER ',' CSV HEADER;

-- Load data into the 'representative_images' table.
\COPY representative_images(id, product_id, url) FROM '/docker-entrypoint-initdb.d/representative_images.csv' DELIMITER ',' CSV HEADER;
