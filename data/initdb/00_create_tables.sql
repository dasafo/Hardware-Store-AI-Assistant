-- SQL script to create the initial tables for the hardware store database.

-- Categories Table
-- Stores product categories in a hierarchical structure.
CREATE TABLE category (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES category(id) ON DELETE SET NULL
);

-- Products Table
-- Contains all products available in the store.
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES category(id) ON DELETE SET NULL
);

-- Images Table
-- Stores URLs for product images.
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    alt_text TEXT
);

-- Stock Table
-- Manages the stock quantity for each product.
CREATE TABLE stock (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0
);

-- Invoices Table
-- Stores information about customer invoices.
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Representative Images Table
-- A specific image to represent each product.
CREATE TABLE representative_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    url TEXT NOT NULL
);