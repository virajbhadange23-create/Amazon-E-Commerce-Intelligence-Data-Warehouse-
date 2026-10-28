-- ============================================================================
-- Amazon E-Commerce Intelligence & Data Warehouse
-- Star Schema DDL with Surrogate Keys, Foreign Keys, and Indexes
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Dimension: Category (dim_category)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_category (
    category_key INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. Dimension: Product (dim_product)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_product (
    product_key INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT UNIQUE NOT NULL,
    product_name TEXT NOT NULL,
    category_key INTEGER NOT NULL,
    rating REAL DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    base_actual_price REAL NOT NULL,
    base_discount_price REAL NOT NULL,
    FOREIGN KEY (category_key) REFERENCES dim_category (category_key) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. Dimension: Date (dim_date)
-- date_key format: YYYYMM (e.g., 202401)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    day INTEGER DEFAULT 1,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    year_month TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. Fact Table: Sales (fact_sales)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    category_key INTEGER NOT NULL,
    actual_price REAL NOT NULL,
    discount_price REAL NOT NULL,
    discount_percent REAL NOT NULL,
    units_sold INTEGER NOT NULL,
    sales_amount REAL NOT NULL,
    is_sample INTEGER DEFAULT 1,
    FOREIGN KEY (product_key) REFERENCES dim_product (product_key) ON DELETE CASCADE,
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key) ON DELETE CASCADE,
    FOREIGN KEY (category_key) REFERENCES dim_category (category_key) ON DELETE CASCADE
);

-- Indexes on Fact Table Foreign Keys and date_key
CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON fact_sales (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_category ON fact_sales (category_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_sales_unique ON fact_sales (product_key, date_key);

-- ----------------------------------------------------------------------------
-- 5. Operational Table: ETL Log (etl_log)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS etl_log (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    rows_extracted INTEGER DEFAULT 0,
    rows_cleaned INTEGER DEFAULT 0,
    rows_loaded INTEGER DEFAULT 0,
    duplicates_removed INTEGER DEFAULT 0,
    nulls_fixed INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    details TEXT
);

-- ----------------------------------------------------------------------------
-- 6. Analytical Table: Price Predictions (price_predictions)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS price_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_key INTEGER NOT NULL,
    predicted_for_month TEXT NOT NULL,
    predicted_price REAL NOT NULL,
    model_name TEXT NOT NULL,
    mae REAL NOT NULL,
    r2 REAL NOT NULL,
    created_at TEXT NOT NULL,
    forecast_json TEXT,
    FOREIGN KEY (product_key) REFERENCES dim_product (product_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_predictions_product ON price_predictions (product_key);

-- ----------------------------------------------------------------------------
-- 7. Analytical Table: Product Clusters (product_clusters)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_clusters (
    cluster_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_key INTEGER NOT NULL,
    cluster_id INTEGER NOT NULL,
    cluster_label TEXT NOT NULL,
    k_value INTEGER NOT NULL,
    silhouette_score REAL NOT NULL,
    run_date TEXT NOT NULL,
    FOREIGN KEY (product_key) REFERENCES dim_product (product_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_clusters_product ON product_clusters (product_key);
