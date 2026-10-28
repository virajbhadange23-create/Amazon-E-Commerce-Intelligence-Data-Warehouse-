"""
ETL Pipeline Service for Amazon E-Commerce Intelligence & Data Warehouse
Implements extract(), transform(), and load() with data quality auditing,
supports both full historical monthly datasets (amazon_ecommerce_dataset.csv)
and catalog CSVs with idempotent Star Schema loading.
"""
import re
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import config
from db.database import get_db_connection, execute_db

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.ETL_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ETLService")


# ============================================================================
# Helper Cleaning Functions
# ============================================================================

def clean_currency_string(val: Any) -> Optional[float]:
    """Cleans currency strings like '₹24,990', '$1,299.99', '2,499' into positive floats."""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    cleaned = re.sub(r"[^\d.]", "", s)
    try:
        f = float(cleaned)
        return round(f, 2) if f > 0 else None
    except ValueError:
        return None


def clean_percentage_string(val: Any) -> Optional[float]:
    """Cleans percentage strings like '24%', ' 50 % ' into float percentages."""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    cleaned = re.sub(r"[^\d.]", "", s)
    try:
        f = float(cleaned)
        return round(f, 2)
    except ValueError:
        return None


def clean_numeric_int(val: Any, default: int = 100) -> int:
    """Cleans counts like '45,890' into positive integers."""
    if pd.isna(val) or val is None:
        return default
    s = str(val).strip()
    cleaned = re.sub(r"[^\d]", "", s)
    try:
        return max(1, int(cleaned)) if cleaned else default
    except ValueError:
        return default


def clean_numeric_float(val: Any, default: float = 4.0) -> float:
    """Cleans ratings like '4.5' into float values bounded between 1.0 and 5.0."""
    if pd.isna(val) or val is None:
        return default
    s = str(val).strip()
    cleaned = re.sub(r"[^\d.]", "", s)
    try:
        f = float(cleaned)
        return round(max(1.0, min(5.0, f)), 1)
    except ValueError:
        return default


# ============================================================================
# 1. EXTRACT
# ============================================================================

def extract(file_path: Optional[Path] = None) -> Tuple[pd.DataFrame, int]:
    """
    Extracts raw product data from CSV file.
    Prefers amazon_ecommerce_dataset.csv if available, otherwise raw product seed.
    """
    if file_path:
        path = Path(file_path)
    elif config.DATASET_CSV.exists():
        path = config.DATASET_CSV
    else:
        path = config.RAW_PRODUCTS_CSV

    if not path.exists():
        raise FileNotFoundError(f"Source file not found at {path}")

    logger.info(f"Extracting raw data from: {path}")
    df_raw = pd.read_csv(path, dtype=str)
    rows_extracted = len(df_raw)
    logger.info(f"Extracted {rows_extracted} raw records.")
    return df_raw, rows_extracted


# ============================================================================
# 2. TRANSFORM
# ============================================================================

def transform(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw strings, fixes nulls, deduplicates, and produces Star Schema tables:
    df_categories, df_products, df_dates, df_sales along with a comprehensive quality_report.
    Supports both direct historical monthly datasets and catalog-only files.
    """
    logger.info("Starting data transformation and quality auditing...")

    raw_count = len(df_raw)
    quality_report = {
        "rows_extracted": raw_count,
        "duplicates_removed": 0,
        "nulls_fixed": 0,
        "rows_rejected": 0,
        "rows_cleaned": 0,
        "monthly_records_generated": 0
    }

    # Normalize column names (handle case variations and synonyms)
    col_map = {}
    for col in df_raw.columns:
        c_lower = col.strip().lower().replace(" ", "_")
        if "product_name" in c_lower or ("name" in c_lower and "cat" not in c_lower) or "title" in c_lower:
            col_map[col] = "product_name"
        elif "category" in c_lower:
            col_map[col] = "category"
        elif "actual" in c_lower or "mrp" in c_lower or "original" in c_lower:
            col_map[col] = "actual_price"
        elif "discounted" in c_lower or "discount_price" in c_lower or "selling" in c_lower or ("price" in c_lower and "actual" not in c_lower):
            col_map[col] = "discounted_price"
        elif "discount" in c_lower and ("%" in c_lower or "percent" in c_lower):
            col_map[col] = "discount_percentage"
        elif "rating_count" in c_lower or "reviews" in c_lower:
            col_map[col] = "rating_count"
        elif "rating" in c_lower or "stars" in c_lower:
            col_map[col] = "rating"
        elif "product_id" in c_lower or "asin" in c_lower or "sku" in c_lower:
            col_map[col] = "product_id"
        elif "sales_quantity" in c_lower or "units_sold" in c_lower or "units" in c_lower or "quantity" in c_lower:
            col_map[col] = "sales_quantity"
        elif "date" in c_lower or "year_month" in c_lower or "month" in c_lower:
            col_map[col] = "date"

    df = df_raw.rename(columns=col_map).copy()

    # Ensure critical columns exist
    for col in ["product_name", "category", "actual_price", "discounted_price"]:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' could not be identified in the dataset.")

    # 1. Clean whitespace from strings
    for str_col in ["product_name", "category"]:
        df[str_col] = df[str_col].astype(str).str.strip()

    # 2. Reject unrecoverable rows
    initial_len = len(df)
    valid_mask = (df["product_name"].str.len() > 2) & (df["category"].str.len() > 1)
    df = df[valid_mask].copy()
    rejected_crit = initial_len - len(df)
    quality_report["rows_rejected"] += rejected_crit

    # Check whether dataset already has historical date records
    has_date_history = "date" in df.columns and df["date"].notna().sum() > 0

    if not has_date_history:
        # Deduplication on product_name for single-record catalog files
        dedup_len = len(df)
        df = df.drop_duplicates(subset=["product_name"]).copy()
        duplicates_count = dedup_len - len(df)
        quality_report["duplicates_removed"] += duplicates_count
    else:
        # For historical time-series datasets, deduplicate on (product_name, date)
        dedup_len = len(df)
        df = df.drop_duplicates(subset=["product_name", "date"]).copy()
        duplicates_count = dedup_len - len(df)
        quality_report["duplicates_removed"] += duplicates_count

    # Clean Price, Rating, and Quantity fields
    nulls_fixed_count = 0

    cleaned_actual = []
    cleaned_discounted = []
    cleaned_discpct = []
    cleaned_ratings = []
    cleaned_rcounts = []
    cleaned_units = []
    valid_rows_mask = []

    for _, row in df.iterrows():
        act = clean_currency_string(row.get("actual_price"))
        disc = clean_currency_string(row.get("discounted_price"))
        pct = clean_percentage_string(row.get("discount_percentage")) if "discount_percentage" in df.columns else None
        rat = clean_numeric_float(row.get("rating", 4.0))
        rcnt = clean_numeric_int(row.get("rating_count", 100))
        units = clean_numeric_int(row.get("sales_quantity", 50)) if "sales_quantity" in df.columns else 50

        # Reconcile missing prices
        if act is None and disc is not None:
            act = round(disc * 1.25, 2)
            nulls_fixed_count += 1
        elif disc is None and act is not None:
            disc = round(act * 0.80, 2)
            nulls_fixed_count += 1
        elif act is None and disc is None:
            valid_rows_mask.append(False)
            continue

        # If discount price > actual price, fix inverted prices
        if disc > act:
            act, disc = disc, act
            nulls_fixed_count += 1

        # Calculate or fix discount %
        if pct is None or pct <= 0 or pct >= 100:
            pct = round(((act - disc) / act) * 100, 2)
            nulls_fixed_count += 1

        cleaned_actual.append(act)
        cleaned_discounted.append(disc)
        cleaned_discpct.append(pct)
        cleaned_ratings.append(rat)
        cleaned_rcounts.append(rcnt)
        cleaned_units.append(units)
        valid_rows_mask.append(True)

    df = df[valid_rows_mask].copy()
    df["base_actual_price"] = cleaned_actual
    df["base_discount_price"] = cleaned_discounted
    df["discount_percent"] = cleaned_discpct
    df["rating"] = cleaned_ratings
    df["rating_count"] = cleaned_rcounts
    df["units_sold"] = cleaned_units

    quality_report["nulls_fixed"] += nulls_fixed_count
    quality_report["rows_cleaned"] = len(df)

    # Generate stable product_id if not present
    if "product_id" not in df.columns:
        # Stable deterministic product ID based on product_name rank
        unique_names = sorted(df["product_name"].unique())
        name_to_id = {name: f"AMZN-{i+1001}" for i, name in enumerate(unique_names)}
        df["product_id"] = df["product_name"].map(name_to_id)
    else:
        df["product_id"] = df["product_id"].fillna("").astype(str).str.strip()
        df["product_id"] = [
            f"AMZN-{idx+1001}" if not pid else pid
            for idx, pid in enumerate(df["product_id"])
        ]

    # --- Dimension: Categories ---
    unique_categories = sorted(df["category"].unique())
    df_categories = pd.DataFrame({"category_name": unique_categories})

    # --- Dimension: Products ---
    # Aggregate or pick base catalog prices for dim_product
    df_products_unique = df.groupby("product_id").agg({
        "product_name": "first",
        "category": "first",
        "rating": "mean",
        "rating_count": "max",
        "base_actual_price": "mean",
        "base_discount_price": "mean"
    }).reset_index()

    df_products_unique["rating"] = df_products_unique["rating"].round(1)
    df_products_unique["rating_count"] = df_products_unique["rating_count"].astype(int)
    df_products_unique["base_actual_price"] = df_products_unique["base_actual_price"].round(2)
    df_products_unique["base_discount_price"] = df_products_unique["base_discount_price"].round(2)
    df_products = df_products_unique

    # --- Dimension: Dates & Fact Table Generation ---
    if has_date_history:
        # Parse date values directly from CSV
        date_entries = {}
        sales_records = []

        for _, row in df.iterrows():
            d_raw = str(row["date"]).strip()
            # Parse YYYY-MM or YYYYMM or YYYY-MM-DD
            m_match = re.search(r"(\d{4})[-/]?(\d{2})", d_raw)
            if m_match:
                yr = int(m_match.group(1))
                mo = int(m_match.group(2))
            else:
                yr, mo = 2024, 1

            d_key = yr * 100 + mo
            ym_str = f"{yr}-{mo:02d}"

            if d_key not in date_entries:
                dt = datetime.date(yr, mo, 1)
                date_entries[d_key] = {
                    "date_key": d_key,
                    "day": 1,
                    "month": mo,
                    "month_name": dt.strftime("%B"),
                    "quarter": (mo - 1) // 3 + 1,
                    "year": yr,
                    "year_month": ym_str
                }

            act_p = float(row["base_actual_price"])
            disc_p = float(row["base_discount_price"])
            disc_pct = float(row["discount_percent"])
            u_sold = int(row["units_sold"])
            s_amt = round(u_sold * disc_p, 2)

            sales_records.append({
                "product_id": row["product_id"],
                "category_name": row["category"],
                "date_key": d_key,
                "actual_price": act_p,
                "discount_price": disc_p,
                "discount_percent": disc_pct,
                "units_sold": u_sold,
                "sales_amount": s_amt,
                "is_sample": 0
            })

        df_dates = pd.DataFrame(list(date_entries.values())).sort_values(by="date_key").reset_index(drop=True)
        df_sales = pd.DataFrame(sales_records)
        quality_report["monthly_records_generated"] = len(df_sales)

    else:
        # Generate 18 months of historical records (2024-01 to 2025-06)
        dates_list = []
        start_year, start_month = 2024, 1
        total_months = config.SIMULATION_MONTHS  # 18

        curr_year, curr_month = start_year, start_month
        month_keys = []

        for _ in range(total_months):
            date_key = curr_year * 100 + curr_month
            dt = datetime.date(curr_year, curr_month, 1)
            month_name = dt.strftime("%B")
            quarter = (curr_month - 1) // 3 + 1
            year_month = f"{curr_year}-{curr_month:02d}"

            month_keys.append((curr_year, curr_month, date_key, year_month))
            dates_list.append({
                "date_key": date_key,
                "day": 1,
                "month": curr_month,
                "month_name": month_name,
                "quarter": quarter,
                "year": curr_year,
                "year_month": year_month
            })

            curr_month += 1
            if curr_month > 12:
                curr_month = 1
                curr_year += 1

        df_dates = pd.DataFrame(dates_list)

        # Fact Sales Simulation
        np.random.seed(config.RANDOM_SEED)
        sales_records = []

        for _, prod in df_products.iterrows():
            base_act = float(prod["base_actual_price"])
            base_disc = float(prod["base_discount_price"])
            base_pct = ((base_act - base_disc) / base_act) * 100.0
            r_count = int(prod["rating_count"])
            rating = float(prod["rating"])
            popularity = np.log10(max(10, r_count)) * (rating / 4.0)

            for yr, m_num, d_key, ym in month_keys:
                if m_num in config.FESTIVE_MONTHS:  # Oct, Nov
                    festive_boost = np.random.uniform(10.0, 18.0)
                    m_disc_pct = min(85.0, base_pct + festive_boost)
                    demand_mult = np.random.uniform(2.4, 3.6)
                elif m_num in config.SUMMER_SALE_MONTHS:  # May
                    summer_boost = np.random.uniform(5.0, 9.0)
                    m_disc_pct = min(80.0, base_pct + summer_boost)
                    demand_mult = np.random.uniform(1.4, 1.8)
                elif m_num == 1:  # Jan New Year Sale
                    ny_boost = np.random.uniform(3.0, 7.0)
                    m_disc_pct = min(75.0, base_pct + ny_boost)
                    demand_mult = np.random.uniform(1.2, 1.5)
                else:
                    fluct = np.random.uniform(-3.0, 3.0)
                    m_disc_pct = max(5.0, min(80.0, base_pct + fluct))
                    demand_mult = np.random.uniform(0.85, 1.15)

                m_actual = round(base_act * (1.0 + np.random.uniform(-0.02, 0.02)), 2)
                m_disc_price = round(m_actual * (1.0 - (m_disc_pct / 100.0)), 2)
                m_disc_pct_final = round(((m_actual - m_disc_price) / m_actual) * 100.0, 2)

                price_tier_scale = 1200.0 / (np.sqrt(max(50.0, m_disc_price)))
                raw_units = popularity * price_tier_scale * demand_mult * np.random.uniform(0.9, 1.1)
                units_sold = int(max(10, round(raw_units)))
                sales_amount = round(units_sold * m_disc_price, 2)

                sales_records.append({
                    "product_id": prod["product_id"],
                    "category_name": prod["category"],
                    "date_key": d_key,
                    "actual_price": m_actual,
                    "discount_price": m_disc_price,
                    "discount_percent": m_disc_pct_final,
                    "units_sold": units_sold,
                    "sales_amount": sales_amount,
                    "is_sample": 1
                })

        df_sales = pd.DataFrame(sales_records)
        quality_report["monthly_records_generated"] = len(df_sales)

    logger.info(
        f"Transformation complete. Products: {len(df_products)}, "
        f"Dates: {len(df_dates)}, Fact Rows: {len(df_sales)}"
    )

    return df_categories, df_products, df_dates, df_sales, quality_report


# ============================================================================
# 3. LOAD
# ============================================================================

def load(
    df_categories: pd.DataFrame,
    df_products: pd.DataFrame,
    df_dates: pd.DataFrame,
    df_sales: pd.DataFrame
) -> int:
    """
    Loads transformed dimension and fact data into the SQLite Star Schema.
    Ensures idempotency (INSERT OR IGNORE / ON CONFLICT DO UPDATE).
    Returns total fact sales rows loaded.
    """
    logger.info("Loading transformed data into Star Schema database...")
    total_loaded = 0

    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # 1. Load Categories Dimension
        cat_map = {}
        for cat_name in df_categories["category_name"]:
            cur.execute(
                "INSERT OR IGNORE INTO dim_category (category_name) VALUES (?)",
                (cat_name,)
            )
        cur.execute("SELECT category_name, category_key FROM dim_category")
        for row in cur.fetchall():
            cat_map[row["category_name"]] = row["category_key"]

        # 2. Load Dates Dimension
        date_records = [
            (
                int(r["date_key"]),
                int(r["day"]),
                int(r["month"]),
                str(r["month_name"]),
                int(r["quarter"]),
                int(r["year"]),
                str(r["year_month"])
            )
            for _, r in df_dates.iterrows()
        ]
        cur.executemany(
            """
            INSERT OR IGNORE INTO dim_date
            (date_key, day, month, month_name, quarter, year, year_month)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            date_records
        )

        # 3. Load Products Dimension
        prod_map = {}
        prod_records = [
            (
                str(r["product_id"]),
                str(r["product_name"]),
                cat_map[r["category"]],
                float(r["rating"]),
                int(r["rating_count"]),
                float(r["base_actual_price"]),
                float(r["base_discount_price"])
            )
            for _, r in df_products.iterrows()
        ]
        cur.executemany(
            """
            INSERT INTO dim_product
            (product_id, product_name, category_key, rating, rating_count, base_actual_price, base_discount_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                product_name = excluded.product_name,
                category_key = excluded.category_key,
                rating = excluded.rating,
                rating_count = excluded.rating_count,
                base_actual_price = excluded.base_actual_price,
                base_discount_price = excluded.base_discount_price
            """,
            prod_records
        )

        # Fetch surrogate product keys
        cur.execute("SELECT product_id, product_key FROM dim_product")
        for row in cur.fetchall():
            prod_map[row["product_id"]] = row["product_key"]

        # 4. Load Fact Sales in Batches (5,000 rows per batch)
        fact_records = [
            (
                prod_map[r["product_id"]],
                int(r["date_key"]),
                cat_map[r["category_name"]],
                float(r["actual_price"]),
                float(r["discount_price"]),
                float(r["discount_percent"]),
                int(r["units_sold"]),
                float(r["sales_amount"]),
                int(r["is_sample"])
            )
            for _, r in df_sales.iterrows()
            if r["product_id"] in prod_map and r["category_name"] in cat_map
        ]

        batch_size = 5000
        for i in range(0, len(fact_records), batch_size):
            batch = fact_records[i:i + batch_size]
            cur.executemany(
                """
                INSERT INTO fact_sales
                (product_key, date_key, category_key, actual_price, discount_price, discount_percent, units_sold, sales_amount, is_sample)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_key, date_key) DO UPDATE SET
                    category_key = excluded.category_key,
                    actual_price = excluded.actual_price,
                    discount_price = excluded.discount_price,
                    discount_percent = excluded.discount_percent,
                    units_sold = excluded.units_sold,
                    sales_amount = excluded.sales_amount,
                    is_sample = excluded.is_sample
                """,
                batch
            )

        total_loaded = len(fact_records)
        conn.commit()
    finally:
        conn.close()

    logger.info(f"Successfully loaded {total_loaded} fact records into fact_sales.")
    return total_loaded


# ============================================================================
# Complete ETL Pipeline Execution with Logging
# ============================================================================

def run_etl(file_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Executes the full extract, transform, and load pipeline,
    recording execution metrics and quality statistics in etl_log.
    """
    started_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("=" * 60)
    logger.info(f"ETL Pipeline execution started at {started_at}")

    run_id = execute_db(
        """
        INSERT INTO etl_log (started_at, status, details)
        VALUES (?, 'IN_PROGRESS', 'ETL Run Initiated')
        """,
        (started_at,)
    )

    try:
        df_raw, rows_extracted = extract(file_path)
        df_categories, df_products, df_dates, df_sales, quality_report = transform(df_raw)
        rows_loaded = load(df_categories, df_products, df_dates, df_sales)

        completed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        quality_report["rows_loaded"] = rows_loaded
        quality_report["run_id"] = run_id
        quality_report["status"] = "SUCCESS"
        quality_report["completed_at"] = completed_at

        execute_db(
            """
            UPDATE etl_log
            SET completed_at = ?,
                rows_extracted = ?,
                rows_cleaned = ?,
                rows_loaded = ?,
                duplicates_removed = ?,
                nulls_fixed = ?,
                status = 'SUCCESS',
                details = ?
            WHERE run_id = ?
            """,
            (
                completed_at,
                rows_extracted,
                quality_report["rows_cleaned"],
                rows_loaded,
                quality_report["duplicates_removed"],
                quality_report["nulls_fixed"],
                json.dumps(quality_report),
                run_id
            )
        )

        logger.info(f"ETL Pipeline finished successfully in Run #{run_id}.")
        return quality_report

    except Exception as e:
        completed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = str(e)
        logger.error(f"ETL Pipeline failed: {error_msg}", exc_info=True)
        execute_db(
            """
            UPDATE etl_log
            SET completed_at = ?,
                status = 'FAILED',
                details = ?
            WHERE run_id = ?
            """,
            (completed_at, json.dumps({"error": error_msg}), run_id)
        )
        raise e


if __name__ == "__main__":
    result = run_etl()
    print("\n--- ETL Execution Summary ---")
    for k, v in result.items():
        print(f"{k}: {v}")
