# Amazon E-Commerce Intelligence & Data Warehouse

A full-stack College Data Warehousing and Data Mining (DWM) project. The application features an end-to-end dimensional data warehouse with a Star Schema, an idempotent ETL pipeline with automated data quality auditing, multidimensional OLAP operations (Roll-up, Drill-down, Slice, Dice, Pivot), dual Machine Learning models (Linear Regression vs. Random Forest price prediction and K-Means product segmentation), and a responsive dual Light/Dark theme user interface running at `http://localhost:8000`.

---

## 🏛️ Architecture & Dimensional Star Schema

```
                           +----------------------+
                           |       dim_date       |
                           +----------------------+
                           | PK: date_key         |
                           | day, month, quarter  |
                           | year, year_month     |
                           +----------+-----------+
                                      |
                                      | 1:N
                                      v
+----------------------+   1:N     +----------------------+   N:1     +----------------------+
|     dim_product      | --------> |      fact_sales      | <-------- |     dim_category     |
+----------------------+           +----------------------+           +----------------------+
| PK: product_key      |           | PK: sale_id          |           | PK: category_key     |
| product_id (ASIN)    |           | FK: product_key      |           | category_name        |
| product_name         |           | FK: date_key         |           +----------------------+
| category_key (FK)    |           | FK: category_key     |
| rating, rating_count |           | actual_price (MRP)   |
| base_prices          |           | discount_price       |
+----------------------+           | discount_percent     |
                                   | units_sold           |
                                   | sales_amount         |
                                   | is_sample = 1        |
                                   +----------------------+
```

### Warehouse Tables:
1. **`fact_sales`** (Fact Table): Central table with transactional sales measures (`actual_price`, `discount_price`, `discount_percent`, `units_sold`, `sales_amount`, `is_sample`).
2. **`dim_product`** (Dimension): Catalog products with surrogate keys, titles, review popularity weights, and ratings.
3. **`dim_date`** (Dimension): 18-month historical time calendar (January 2024 to June 2025).
4. **`dim_category`** (Dimension): 9 distinct product departments.
5. **`etl_log`** (Operational Audit Table): Historical record of each ETL execution, rows extracted/cleaned/loaded, duplicate counts, and timestamps.
6. **`price_predictions`** (Analytical Table): ML model predictions, evaluation metrics (MAE, $R^2$), winning model name, and 3-month forecast JSON.
7. **`product_clusters`** (Data Mining Table): K-Means cluster memberships, silhouette scores, and cluster labels.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.13** (or Python 3.10+)
- Pip package manager

### 2. Install Dependencies
```bash
py -3.13 -m pip install -r requirements.txt
```

### 3. Generate Seed Data & Run ETL Pipeline
The seed dataset contains **164 products across 9 categories** with realistic rupee prices (`₹`), commas, percentages, star ratings, and review counts.
```bash
# 1. Generate Raw CSV dataset (Kaggle Amazon format)
py -3.13 data/raw/seed_data.py

# 2. Execute Idempotent ETL Pipeline
py -3.13 services/etl.py
```

### 4. Run Automated Unit Tests
```bash
py -3.13 -m unittest tests/test_app.py
```

### 5. Launch the Web Application
```bash
py -3.13 app.py
```
Open your browser and navigate to: **[http://localhost:8000](http://localhost:8000)**

---

## 📦 Detailed Module Walkthrough

### Module 1: Executive KPI Dashboard (`/`)
- **4 Warehouse KPI Cards**: Total Products (`163`), Average Selling Price, Average Discount (`%`), and Total Sales Revenue computed from live SQL on `fact_sales`.
- **Monthly Sales Trend Chart**: Dual-axis Chart.js visualization mapping monthly sales revenue vs. units sold volume.
- **Top 5 Bestsellers Chart**: Horizontal bar chart ranking products by generated revenue.
- **Dynamic Filter Bar**: Real-time filtering by Product Category and Month Range (Start/End month).

### Module 2 & 3: Product Price History & ML Price Prediction (`/price-history`)
- **Searchable Product Dropdown**: Select any product to inspect historical pricing and forecasts.
- **Price History Line Chart**: Plots actual MRP vs. discounted selling price with the **next-month predicted target point highlighted**.
- **ML Winning Model Card**:
  - Compares **Linear Regression** vs. **Random Forest Regressor** (50 estimators, max depth 4).
  - Evaluates Mean Absolute Error (**MAE**) and Coefficient of Determination (**$R^2$**); selects and persists the winning model name.
  - Displays the predicted next-month price and a **3-Month Forward Forecast Outlook**.
  - Handles products with fewer than 4 months of data gracefully without crashing.
- **Granular History Table**: Tabular breakdown of monthly prices, units sold, and revenues marked with simulated data badges.

### Module 4: Sales Performance Analytics (`/sales-analysis`)
- **Monthly Revenue & Volume Trajectory**: Historical bar chart with seasonal festive spikes (Oct–Nov) and summer sale boost (May).
- **Category Sales Share**: Doughnut chart breaking down market revenue share across 9 departments.
- **Top 10 Best-Selling Products**: Table and bar chart ranking top revenue generators.

### Module 5: ETL Process & Data Quality Audit (`/etl`)
- **Three-Tier Architecture**: Clearly named `extract()`, `transform()`, and `load()` functions in `services/etl.py`.
- **Data Quality Auditing**: Strips currency symbols (`₹`, `$`), commas, whitespace; converts discount percentages; prunes duplicate products; handles nulls.
- **Realistic Monthly Simulation**: Simulates 18 months per product using popularity weighting (`rating_count`), seasonal festive surges (Oct–Nov), and flags rows with `is_sample = 1`.
- **Strict Idempotency**: `ON CONFLICT DO UPDATE` ensures re-running the ETL does not duplicate records.
- **Execution History**: Full audit trail of every run logged to `etl_log`.

### Module 6: Star Schema Architecture (`/warehouse`)
- **Interactive Visual Topology**: Clear star schema diagram with `fact_sales` at the center connected to `dim_product`, `dim_date`, and `dim_category`.
- **Live Row Counters**: Displays real-time database row counts across all 7 tables.
- **DDL Schema Reference**: Documented surrogate keys, foreign keys, and unique composite indexes.

### Module 7: Multidimensional OLAP Analysis (`/olap`)
Pure SQL-based implementations of core data warehousing operations:
1. **Roll-up**: Aggregates from Month $\rightarrow$ Quarter $\rightarrow$ Year.
2. **Drill-down**: Navigates from Category summary down to individual product performance.
3. **Slice**: Isolates a single dimension (e.g. single category or specific month).
4. **Dice**: Multi-dimensional filtering across selected categories and custom date intervals.
5. **Pivot**: 2D Cross-Tabulation Matrix (Categories $\times$ Months) with row and column totals for Total Sales, Units Sold, or Average Price.
- **Download CSV**: Streams live CSV exports for any executed OLAP query.

### Module 8: Data Mining - K-Means Clustering (`/clustering`)
- **Standardized Features**: Product clustering on `[avg_price, avg_discount, total_sales]` normalized with `StandardScaler`.
- **Interactive K Selection**: Test $K = 2 \dots 5$ (default $K=3$).
- **Model Evaluation**: Displays **Silhouette Score** (e.g. `0.434`) and an **Elbow Curve** chart (Inertia & Silhouette across $K=2 \dots 8$).
- **2D Scatter Projection**: Interactive scatter plot ($X=\text{Avg Price}, Y=\text{Total Sales}$) colored by cluster.
- **Business Segmentation**: Meaningful cluster names (`Budget / Value Essentials`, `Mid-Range Bestsellers`, `Premium / Flagship`).
- **Database Persistence**: Saves cluster assignments to `product_clusters`.

### Module 9 & 10: Dual Light/Dark Theme & SQLite Storage
- **Theme Engine**: Seamless Sun/Moon toggle with zero visual flash (instant `localStorage` + `prefers-color-scheme` resolution).
- **Dynamic Chart.js Re-coloring**: All charts re-color grid lines, ticks, legends, and tooltips on theme toggle **without requiring a page reload**.
- **WCAG AA Compliance**: High-contrast, polished typography and card designs in both themes.
- **Storage**: SQLite database (`db/warehouse.db`) storing all raw and analytical computed results.

---

## 🧪 Automated Test Verification

Run all test suites:
```bash
py -3.13 -m unittest tests/test_app.py
py -3.13 tests/test_endpoints.py
py -3.13 tests/test_pages.py
py -3.13 tests/test_ml.py
```
**Test Results**: All 14 test cases pass with 100% success rate.
