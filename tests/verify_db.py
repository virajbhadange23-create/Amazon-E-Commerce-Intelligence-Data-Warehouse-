import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sqlite3
import pandas as pd
from db.database import get_db_connection

conn = get_db_connection()
try:
    df_p = pd.read_sql_query("SELECT count(*) as count FROM dim_product", conn)
    df_f = pd.read_sql_query("SELECT count(*) as count FROM fact_sales", conn)
    df_c = pd.read_sql_query("SELECT count(*) as count FROM dim_category", conn)
    print("dim_product count:", df_p["count"].iloc[0])
    print("fact_sales count:", df_f["count"].iloc[0])
    print("dim_category count:", df_c["count"].iloc[0])
    
    # Check breakdown by product_id prefix
    df_prefix = pd.read_sql_query("SELECT substr(product_id, 1, 4) as prefix, count(*) as count FROM dim_product GROUP BY prefix", conn)
    print("\nProduct ID prefix breakdown:\n", df_prefix)

    # Check categories and pricing
    df_stats = pd.read_sql_query("""
        SELECT 
            c.category_name,
            COUNT(p.product_key) AS product_count,
            MIN(p.base_actual_price) AS min_actual_price,
            MAX(p.base_actual_price) AS max_actual_price,
            ROUND(AVG(p.base_actual_price), 2) AS avg_actual_price,
            ROUND(AVG(p.base_discount_price), 2) AS avg_discount_price
        FROM dim_product p
        JOIN dim_category c ON p.category_key = c.category_key
        GROUP BY c.category_name
        ORDER BY product_count DESC
    """, conn)
    print("\nCategory Stats:\n", df_stats.to_string())

finally:
    conn.close()
