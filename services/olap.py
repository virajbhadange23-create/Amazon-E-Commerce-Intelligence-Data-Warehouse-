"""
OLAP Analysis Service for Amazon E-Commerce Data Warehouse
Provides pure SQL-based implementations of core OLAP operations:
Roll-up, Drill-down, Slice, Dice, and Pivot with CSV export formatting.
"""
import io
import csv
import logging
from typing import Any, Dict, List, Optional
from db.database import query_db

logger = logging.getLogger(__name__)


def get_categories_list() -> List[Dict[str, Any]]:
    """Returns all available product categories."""
    return query_db(
        "SELECT category_key, category_name FROM dim_category ORDER BY category_name"
    )


def get_date_range() -> Dict[str, Any]:
    """Returns minimum and maximum available dates in the warehouse."""
    row = query_db(
        """
        SELECT 
            MIN(date_key) as min_date_key,
            MAX(date_key) as max_date_key,
            MIN(year_month) as min_ym,
            MAX(year_month) as max_ym
        FROM dim_date
        """,
        one=True
    )
    return row or {}


# ----------------------------------------------------------------------------
# 1. ROLL-UP (Month -> Quarter -> Year)
# ----------------------------------------------------------------------------
def rollup_sales(level: str = "quarter", category_key: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Roll-up aggregates sales from month to quarter or year level.
    Levels: 'month', 'quarter', 'year'.
    """
    cat_filter = "AND f.category_key = ?" if category_key else ""
    args = (category_key,) if category_key else ()

    if level == "year":
        sql = f"""
            SELECT 
                d.year,
                COUNT(DISTINCT f.product_key) as product_count,
                SUM(f.units_sold) as total_units_sold,
                ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
                ROUND(AVG(f.discount_price), 2) as avg_selling_price,
                ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE 1=1 {cat_filter}
            GROUP BY d.year
            ORDER BY d.year ASC
        """
    elif level == "month":
        sql = f"""
            SELECT 
                d.year_month,
                d.month_name,
                d.year,
                COUNT(DISTINCT f.product_key) as product_count,
                SUM(f.units_sold) as total_units_sold,
                ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
                ROUND(AVG(f.discount_price), 2) as avg_selling_price,
                ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE 1=1 {cat_filter}
            GROUP BY d.year_month, d.month_name, d.year
            ORDER BY d.year_month ASC
        """
    else:  # 'quarter' default
        sql = f"""
            SELECT 
                d.year,
                d.quarter,
                'Q' || d.quarter || ' ' || d.year as quarter_label,
                COUNT(DISTINCT f.product_key) as product_count,
                SUM(f.units_sold) as total_units_sold,
                ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
                ROUND(AVG(f.discount_price), 2) as avg_selling_price,
                ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE 1=1 {cat_filter}
            GROUP BY d.year, d.quarter
            ORDER BY d.year ASC, d.quarter ASC
        """
    return query_db(sql, args)


# ----------------------------------------------------------------------------
# 2. DRILL-DOWN (Category -> Product)
# ----------------------------------------------------------------------------
def drilldown_sales(category_key: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Drill-down navigates from summary category level down to individual product performance.
    """
    if category_key:
        sql = """
            SELECT 
                c.category_name,
                p.product_id,
                p.product_name,
                p.rating,
                p.rating_count,
                SUM(f.units_sold) as total_units_sold,
                ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
                ROUND(AVG(f.actual_price), 2) as avg_actual_price,
                ROUND(AVG(f.discount_price), 2) as avg_discount_price,
                ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
            FROM fact_sales f
            JOIN dim_product p ON f.product_key = p.product_key
            JOIN dim_category c ON f.category_key = c.category_key
            WHERE f.category_key = ?
            GROUP BY p.product_key, p.product_id, p.product_name, c.category_name, p.rating, p.rating_count
            ORDER BY total_sales_amount DESC
        """
        return query_db(sql, (category_key,))
    else:
        # Category summary level before drilling down
        sql = """
            SELECT 
                c.category_key,
                c.category_name,
                COUNT(DISTINCT p.product_key) as total_products,
                SUM(f.units_sold) as total_units_sold,
                ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
                ROUND(AVG(f.discount_price), 2) as avg_selling_price,
                ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
            FROM fact_sales f
            JOIN dim_category c ON f.category_key = c.category_key
            JOIN dim_product p ON f.product_key = p.product_key
            GROUP BY c.category_key, c.category_name
            ORDER BY total_sales_amount DESC
        """
        return query_db(sql)


# ----------------------------------------------------------------------------
# 3. SLICE (Single Category OR Single Month)
# ----------------------------------------------------------------------------
def slice_sales(slice_type: str, slice_val: Any) -> List[Dict[str, Any]]:
    """
    Slices the data warehouse along a single dimension (category or month).
    """
    if slice_type == "category":
        sql = """
            SELECT 
                d.year_month,
                d.month_name,
                d.year,
                c.category_name,
                COUNT(DISTINCT f.product_key) as active_products,
                SUM(f.units_sold) as total_units_sold,
                ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
                ROUND(AVG(f.discount_price), 2) as avg_selling_price,
                ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            JOIN dim_category c ON f.category_key = c.category_key
            WHERE c.category_key = ? OR c.category_name = ?
            GROUP BY d.year_month, c.category_name, d.month_name, d.year
            ORDER BY d.year_month ASC
        """
        return query_db(sql, (slice_val, str(slice_val)))
    else:  # 'month' slice
        sql = """
            SELECT 
                c.category_name,
                d.year_month,
                COUNT(DISTINCT f.product_key) as active_products,
                SUM(f.units_sold) as total_units_sold,
                ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
                ROUND(AVG(f.discount_price), 2) as avg_selling_price,
                ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
            FROM fact_sales f
            JOIN dim_date d ON f.date_key = d.date_key
            JOIN dim_category c ON f.category_key = c.category_key
            WHERE d.year_month = ? OR d.date_key = ?
            GROUP BY c.category_name, d.year_month
            ORDER BY total_sales_amount DESC
        """
        return query_db(sql, (str(slice_val), slice_val))


# ----------------------------------------------------------------------------
# 4. DICE (Multiple Categories + Month Range)
# ----------------------------------------------------------------------------
def dice_sales(
    category_keys: Optional[List[int]] = None,
    start_ym: Optional[str] = None,
    end_ym: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Dices data across multiple dimensions (selected categories AND month range).
    """
    clauses = ["1=1"]
    params: List[Any] = []

    if category_keys and len(category_keys) > 0:
        placeholders = ",".join("?" for _ in category_keys)
        clauses.append(f"f.category_key IN ({placeholders})")
        params.extend(category_keys)

    if start_ym:
        clauses.append("d.year_month >= ?")
        params.append(start_ym)

    if end_ym:
        clauses.append("d.year_month <= ?")
        params.append(end_ym)

    where_sql = " AND ".join(clauses)

    sql = f"""
        SELECT 
            c.category_name,
            d.year_month,
            SUM(f.units_sold) as total_units_sold,
            ROUND(SUM(f.sales_amount), 2) as total_sales_amount,
            ROUND(AVG(f.discount_price), 2) as avg_selling_price,
            ROUND(AVG(f.discount_percent), 2) as avg_discount_percent
        FROM fact_sales f
        JOIN dim_category c ON f.category_key = c.category_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE {where_sql}
        GROUP BY c.category_name, d.year_month
        ORDER BY d.year_month ASC, c.category_name ASC
    """
    return query_db(sql, tuple(params))


# ----------------------------------------------------------------------------
# 5. PIVOT (Category x Month -> Total Sales or Avg Price)
# ----------------------------------------------------------------------------
def pivot_sales(metric: str = "sales_amount") -> Dict[str, Any]:
    """
    Generates a 2D Pivot table cross-tabulating Categories (rows) x Months (columns).
    Supported metrics: 'sales_amount', 'units_sold', 'avg_price'.
    """
    agg_expr = "ROUND(SUM(f.sales_amount), 2)"
    if metric == "units_sold":
        agg_expr = "SUM(f.units_sold)"
    elif metric == "avg_price":
        agg_expr = "ROUND(AVG(f.discount_price), 2)"

    # Get sorted distinct months
    months_rows = query_db("SELECT DISTINCT year_month FROM dim_date ORDER BY year_month ASC")
    months = [r["year_month"] for r in months_rows]

    # Get distinct categories
    cats_rows = query_db("SELECT DISTINCT category_name FROM dim_category ORDER BY category_name ASC")
    categories = [r["category_name"] for r in cats_rows]

    # Query aggregated cells
    sql = f"""
        SELECT 
            c.category_name,
            d.year_month,
            {agg_expr} as val
        FROM fact_sales f
        JOIN dim_category c ON f.category_key = c.category_key
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY c.category_name, d.year_month
    """
    rows = query_db(sql)

    # Build matrix map
    data_map: Dict[str, Dict[str, float]] = {c: {} for c in categories}
    for r in rows:
        c_name = r["category_name"]
        ym = r["year_month"]
        data_map[c_name][ym] = r["val"]

    # Construct complete grid with row totals
    grid = []
    col_totals = {m: 0.0 for m in months}

    for c in categories:
        row_vals = []
        row_sum = 0.0
        for m in months:
            v = data_map[c].get(m, 0.0) or 0.0
            row_vals.append(v)
            row_sum += v
            col_totals[m] += v
        grid.append({
            "category": c,
            "values": row_vals,
            "total": round(row_sum, 2)
        })

    return {
        "metric": metric,
        "months": months,
        "categories": categories,
        "rows": grid,
        "column_totals": [round(col_totals[m], 2) for m in months],
        "grand_total": round(sum(col_totals.values()), 2)
    }


# ----------------------------------------------------------------------------
# 6. CSV EXPORT HELPER
# ----------------------------------------------------------------------------
def export_to_csv_string(data: List[Dict[str, Any]]) -> str:
    """Converts a list of dictionary rows into standard CSV string."""
    if not data:
        return ""
    output = io.StringIO()
    headers = list(data[0].keys())
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()
