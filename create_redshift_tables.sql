-- Redshift Table Creation Script for ETL Pipeline
-- This script creates the necessary tables for the sales data warehouse

-- Drop existing table if needed (use with caution in production)
-- DROP TABLE IF EXISTS sales_fact;

-- Create the main sales fact table
CREATE TABLE IF NOT EXISTS sales_fact (
    transaction_id VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20),
    product_id VARCHAR(20),
    sales_amount DECIMAL(10, 2),
    quantity INTEGER,
    discount DECIMAL(5, 2),
    tax DECIMAL(5, 2),
    transaction_date TIMESTAMP,
    store_id VARCHAR(20),
    processed_at TIMESTAMP,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    hour INTEGER,
    PRIMARY KEY (transaction_id)
)
DISTSTYLE KEY
DISTKEY (customer_id)
SORTKEY (transaction_date, customer_id);

-- Create aggregated sales summary table (optional)
CREATE TABLE IF NOT EXISTS sales_summary (
    summary_date DATE NOT NULL,
    store_id VARCHAR(20),
    total_sales DECIMAL(15, 2),
    total_quantity INTEGER,
    total_transactions INTEGER,
    avg_transaction_value DECIMAL(10, 2),
    PRIMARY KEY (summary_date, store_id)
)
DISTSTYLE ALL
SORTKEY (summary_date);

-- Create customer dimension table (optional)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id VARCHAR(20) NOT NULL,
    first_transaction_date TIMESTAMP,
    last_transaction_date TIMESTAMP,
    total_lifetime_value DECIMAL(15, 2),
    total_orders INTEGER,
    PRIMARY KEY (customer_id)
)
DISTSTYLE ALL
SORTKEY (customer_id);

-- Create product dimension table (optional)
CREATE TABLE IF NOT EXISTS dim_product (
    product_id VARCHAR(20) NOT NULL,
    total_sales DECIMAL(15, 2),
    total_quantity_sold INTEGER,
    avg_price DECIMAL(10, 2),
    first_sale_date TIMESTAMP,
    last_sale_date TIMESTAMP,
    PRIMARY KEY (product_id)
)
DISTSTYLE ALL
SORTKEY (product_id);

-- Create store dimension table (optional)
CREATE TABLE IF NOT EXISTS dim_store (
    store_id VARCHAR(20) NOT NULL,
    total_sales DECIMAL(15, 2),
    total_transactions INTEGER,
    avg_transaction_value DECIMAL(10, 2),
    PRIMARY KEY (store_id)
)
DISTSTYLE ALL
SORTKEY (store_id);

-- Grant permissions (adjust schema/user as needed)
-- GRANT ALL ON sales_fact TO your_redshift_user;
-- GRANT ALL ON sales_summary TO your_redshift_user;
-- GRANT ALL ON dim_customer TO your_redshift_user;
-- GRANT ALL ON dim_product TO your_redshift_user;
-- GRANT ALL ON dim_store TO your_redshift_user;

-- Verify tables were created
SELECT 
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name IN ('sales_fact', 'sales_summary', 'dim_customer', 'dim_product', 'dim_store')
ORDER BY table_name;
