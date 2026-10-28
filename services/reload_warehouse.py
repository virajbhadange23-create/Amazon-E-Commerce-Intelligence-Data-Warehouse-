"""
Warehouse Reload and Idempotency Verification Script
"""
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.database import get_db_connection, get_table_counts
from services.etl import run_etl

def clean_and_reload():
    print("=" * 60)
    print("STEP 1: Resetting warehouse tables for clean reload...")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = OFF;")
        cur.execute("DELETE FROM fact_sales;")
        cur.execute("DELETE FROM dim_product;")
        cur.execute("DELETE FROM dim_category;")
        cur.execute("DELETE FROM dim_date;")
        cur.execute("DELETE FROM price_predictions;")
        cur.execute("DELETE FROM product_clusters;")
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('fact_sales', 'dim_product', 'dim_category', 'price_predictions', 'product_clusters');")
        cur.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
    finally:
        conn.close()

    print("Cleared existing tables. Current table counts:")
    print(get_table_counts())

    print("\n" + "=" * 60)
    print("STEP 2: Running ETL Pipeline (Run 1)...")
    t0 = time.time()
    rep1 = run_etl()
    t1 = time.time()
    print(f"ETL Run 1 completed in {t1 - t0:.2f} seconds.")
    print("Quality Report 1:", rep1)
    counts1 = get_table_counts()
    print("Warehouse counts after Run 1:", counts1)

    print("\n" + "=" * 60)
    print("STEP 3: Testing Idempotency - Re-running ETL Pipeline (Run 2)...")
    t2 = time.time()
    rep2 = run_etl()
    t3 = time.time()
    print(f"ETL Run 2 completed in {t3 - t2:.2f} seconds.")
    print("Quality Report 2:", rep2)
    counts2 = get_table_counts()
    print("Warehouse counts after Run 2:", counts2)

    # Verify counts are identical (idempotent)
    assert counts1["dim_product"] == counts2["dim_product"], "Idempotency failed: dim_product changed"
    assert counts1["fact_sales"] == counts2["fact_sales"], "Idempotency failed: fact_sales changed"
    assert counts1["dim_category"] == counts2["dim_category"], "Idempotency failed: dim_category changed"
    print("\nIDEMPOTENCY CONFIRMED: Table counts are 100% identical between successive runs!")

if __name__ == "__main__":
    clean_and_reload()
