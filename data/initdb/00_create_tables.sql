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
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES category(id) ON DELETE SET NULL,
    price DECIMAL(10,2),
    brand TEXT,
    spec_json JSONB
);

-- Warehouses Table
-- Stores warehouse information.
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    warehouse_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    address TEXT
);

-- Stock Table
-- Manages the stock quantity for each product in each warehouse.
CREATE TABLE stock (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id TEXT NOT NULL REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    UNIQUE(product_id, warehouse_id)
);

-- Customers Table
-- Stores customer information.
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Invoices Table
-- Stores information about customer invoices.
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_id TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    total DECIMAL(10,2) NOT NULL,
    pdf_url TEXT,
    created_at DATE NOT NULL
);

-- Images Table
-- Stores the representative image for each product.
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    alt_text TEXT
);