"""
Machine Learning K-Means Clustering Service for Amazon E-Commerce Data Warehouse
Segments products on Price, Discount %, Rating, and Sales Quantity using StandardScaler.
Computes WCSS (Inertia) elbow curve and Silhouette scores across K=2..8,
generates dynamic business cluster labels and descriptive summaries,
and persists cluster memberships to SQLite product_clusters table.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
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
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

import config
from db.database import query_db, execute_db, execute_many

logger = logging.getLogger(__name__)


def generate_cluster_business_interpretation(
    c_stat: Dict[str, Any],
    overall_avg_price: float,
    overall_avg_disc: float,
    overall_avg_units: float
) -> Dict[str, str]:
    """Generates a business profile name and plain-English description for a cluster."""
    avg_p = c_stat["avg_price"]
    avg_d = c_stat["avg_discount"]
    avg_u = c_stat["avg_units"]
    avg_r = c_stat["avg_rating"]

    # Price tier
    if avg_p >= overall_avg_price * 1.75:
        tier = "Premium / Flagship"
        desc = (
            f"High-end luxury and flagship products (avg ₹{avg_p:,.2f}) with conservative discounting "
            f"({avg_d:.1f}%), strong average rating ({avg_r:.1f}★), and selective unit volume."
        )
    elif avg_p <= overall_avg_price * 0.65:
        tier = "Budget / Value Essentials"
        desc = (
            f"High-velocity everyday essentials with entry-level pricing (avg ₹{avg_p:,.2f}), "
            f"steep discounts ({avg_d:.1f}%), and high customer sales volume (avg {avg_u:,.0f} units)."
        )
    else:
        if avg_u >= overall_avg_units:
            tier = "Mid-Range Mass Bestsellers"
            desc = (
                f"Core volume drivers (avg ₹{avg_p:,.2f}) that blend competitive pricing with healthy discounts "
                f"({avg_d:.1f}%) and consistent customer demand across categories."
            )
        else:
            tier = "Upper Mid-Range Performance"
            desc = (
                f"Quality-focused mid-tier products (avg ₹{avg_p:,.2f}) commanding balanced discounts "
                f"({avg_d:.1f}%) and dependable buyer ratings ({avg_r:.1f}★)."
            )

    return {"label": tier, "description": desc}


def cluster_products(k: int = 3, save_to_db: bool = True) -> Dict[str, Any]:
    """
    Performs multidimensional K-Means clustering across all warehouse products using:
    - Average Selling Price (₹)
    - Average Discount (%)
    - Customer Star Rating (1-5)
    - Total Sales Quantity (units sold)
    
    Applies StandardScaler, computes the Elbow Curve & Silhouette Scores across K=2..8,
    fits the model, assigns clusters, and persists results to SQLite product_clusters table.
    """
    k = max(2, min(8, int(k)))

    # 1. Fetch aggregated product metrics from database
    sql = """
        SELECT 
            p.product_key,
            p.product_id,
            p.product_name,
            c.category_name,
            COALESCE(p.rating, 4.0) as rating,
            COALESCE(p.rating_count, 100) as rating_count,
            ROUND(AVG(f.discount_price), 2) as avg_price,
            ROUND(AVG(f.discount_percent), 2) as avg_discount,
            ROUND(SUM(f.sales_amount), 2) as total_sales,
            SUM(f.units_sold) as total_units
        FROM dim_product p
        JOIN dim_category c ON p.category_key = c.category_key
        JOIN fact_sales f ON p.product_key = f.product_key
        GROUP BY p.product_key, p.product_id, p.product_name, c.category_name, p.rating, p.rating_count
        ORDER BY p.product_key ASC
    """
    rows = query_db(sql)
    if not rows or len(rows) < k:
        return {
            "success": False,
            "error": f"Insufficient product records for clustering (found {len(rows) if rows else 0}, need at least {k})."
        }

    df = pd.DataFrame(rows)

    # 2. Data Cleaning & Type Enforcement
    df["avg_price"] = pd.to_numeric(df["avg_price"], errors="coerce").fillna(500.0).clip(lower=10.0)
    df["avg_discount"] = pd.to_numeric(df["avg_discount"], errors="coerce").fillna(20.0).clip(0.0, 95.0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(4.0).clip(1.0, 5.0)
    df["total_units"] = pd.to_numeric(df["total_units"], errors="coerce").fillna(50.0).clip(lower=1.0)
    df["total_sales"] = pd.to_numeric(df["total_sales"], errors="coerce").fillna(df["avg_price"] * df["total_units"])

    # 3. Selected Multidimensional Numerical Features
    feature_cols = ["avg_price", "avg_discount", "rating", "total_units"]
    X = df[feature_cols].values

    # Feature Scaling: StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Compute Elbow Curve & Silhouette Scores for K = 2..8
    elbow_curve = []
    max_k_eval = min(8, len(df) - 1)
    best_sil = -1.0
    optimal_k = 3

    for test_k in range(2, max_k_eval + 1):
        km_test = KMeans(
            n_clusters=test_k,
            random_state=config.CLUSTERING_RANDOM_STATE,
            n_init=10
        )
        test_labels = km_test.fit_predict(X_scaled)
        test_sil = float(silhouette_score(X_scaled, test_labels))
        wcss = round(float(km_test.inertia_), 2)

        if test_sil > best_sil:
            best_sil = test_sil
            optimal_k = test_k

        elbow_curve.append({
            "k": test_k,
            "inertia": wcss,
            "silhouette_score": round(test_sil, 3)
        })

    # 5. Fit Final K-Means with chosen K
    km_final = KMeans(
        n_clusters=k,
        random_state=config.CLUSTERING_RANDOM_STATE,
        n_init=10
    )
    labels = km_final.fit_predict(X_scaled)
    final_sil_score = round(float(silhouette_score(X_scaled, labels)), 3)

    df["cluster_id"] = labels

    # Overall dataset averages for benchmarking
    ovr_price = float(df["avg_price"].mean())
    ovr_disc = float(df["avg_discount"].mean())
    ovr_units = float(df["total_units"].mean())

    # 6. Compute Cluster Statistics and Profiles
    raw_cluster_stats = []
    for c_id in range(k):
        c_sub = df[df["cluster_id"] == c_id]
        raw_cluster_stats.append({
            "cluster_id": c_id,
            "member_count": int(len(c_sub)),
            "avg_price": float(c_sub["avg_price"].mean()),
            "avg_discount": float(c_sub["avg_discount"].mean()),
            "avg_rating": float(c_sub["rating"].mean()),
            "avg_units": float(c_sub["total_units"].mean()),
            "avg_sales": float(c_sub["total_sales"].mean()),
            "total_sales": float(c_sub["total_sales"].sum())
        })

    # Rank clusters by average price ascending to assign intuitive tier names
    raw_cluster_stats.sort(key=lambda c: c["avg_price"])
    labels_map = {}
    descriptions_map = {}

    tier_titles = [
        "Budget Essentials",
        "Mid-Range Bestsellers",
        "Upper Mid-Range Quality",
        "Premium Flagship",
        "Ultra Luxury / Flagship Pro",
        "Niche / Collector",
        "High Volume Clearance",
        "Specialty Catalog"
    ]

    for rank, c_stat in enumerate(raw_cluster_stats):
        c_id = c_stat["cluster_id"]
        auto_title = tier_titles[min(rank, len(tier_titles) - 1)]
        interp = generate_cluster_business_interpretation(c_stat, ovr_price, ovr_disc, ovr_units)
        
        # Prefer structured rank title if unique, otherwise fallback to interpretation label
        title = f"{auto_title} (Tier {rank+1})" if k > 4 else auto_title
        labels_map[c_id] = title
        descriptions_map[c_id] = interp["description"]

    df["cluster_label"] = df["cluster_id"].map(labels_map)

    # 7. Cluster Summaries Table Data
    cluster_summaries = []
    for c_stat in raw_cluster_stats:
        c_id = c_stat["cluster_id"]
        c_sub = df[df["cluster_id"] == c_id]
        top_prods = c_sub.sort_values(by="total_sales", ascending=False)["product_name"].head(3).tolist()
        cluster_summaries.append({
            "cluster_id": c_id,
            "cluster_label": labels_map[c_id],
            "description": descriptions_map[c_id],
            "member_count": c_stat["member_count"],
            "avg_price": round(c_stat["avg_price"], 2),
            "avg_discount": round(c_stat["avg_discount"], 2),
            "avg_rating": round(c_stat["avg_rating"], 1),
            "avg_units": int(round(c_stat["avg_units"])),
            "avg_sales": round(c_stat["avg_sales"], 2),
            "total_sales": round(c_stat["total_sales"], 2),
            "sample_products": top_prods
        })

    # Centroids in original scale
    centroids_scaled = km_final.cluster_centers_
    centroids_orig = scaler.inverse_transform(centroids_scaled)
    centroids_list = []
    for c_id in range(k):
        centroids_list.append({
            "cluster_id": c_id,
            "cluster_label": labels_map[c_id],
            "centroid_price": round(float(centroids_orig[c_id][0]), 2),
            "centroid_discount": round(float(centroids_orig[c_id][1]), 2),
            "centroid_rating": round(float(centroids_orig[c_id][2]), 1),
            "centroid_units": int(round(centroids_orig[c_id][3]))
        })

    # 8. Scatter points for 2D visualization
    scatter_points = []
    for _, r in df.iterrows():
        scatter_points.append({
            "product_key": int(r["product_key"]),
            "product_id": str(r["product_id"]),
            "product_name": str(r["product_name"]),
            "category_name": str(r["category_name"]),
            "avg_price": float(r["avg_price"]),
            "avg_discount": float(r["avg_discount"]),
            "rating": float(r["rating"]),
            "total_sales": float(r["total_sales"]),
            "total_units": int(r["total_units"]),
            "cluster_id": int(r["cluster_id"]),
            "cluster_label": str(r["cluster_label"])
        })

    # 9. Save to Database product_clusters table
    run_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if save_to_db:
        # Clear existing records for this k to keep idempotent
        execute_db("DELETE FROM product_clusters WHERE k_value = ?", (k,))
        insert_records = [
            (
                int(r["product_key"]),
                int(r["cluster_id"]),
                str(r["cluster_label"]),
                k,
                final_sil_score,
                run_date
            )
            for _, r in df.iterrows()
        ]
        execute_many(
            """
            INSERT INTO product_clusters 
            (product_key, cluster_id, cluster_label, k_value, silhouette_score, run_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            insert_records
        )
        logger.info(f"Saved {len(df)} product cluster assignments for K={k} into product_clusters.")

    return {
        "success": True,
        "k": k,
        "optimal_k": optimal_k,
        "features_used": ["avg_price", "avg_discount", "rating", "total_units"],
        "silhouette_score": final_sil_score,
        "elbow_curve": elbow_curve,
        "cluster_summaries": cluster_summaries,
        "centroids": centroids_list,
        "scatter_points": scatter_points,
        "total_products_clustered": len(df),
        "run_date": run_date
    }


def get_saved_clusters(k: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves saved clustering records from product_clusters table."""
    if k:
        sql = """
            SELECT 
                c.cluster_run_id,
                c.product_key,
                p.product_id,
                p.product_name,
                cat.category_name,
                c.cluster_id,
                c.cluster_label,
                c.k_value,
                c.silhouette_score,
                c.run_date
            FROM product_clusters c
            JOIN dim_product p ON c.product_key = p.product_key
            JOIN dim_category cat ON p.category_key = cat.category_key
            WHERE c.k_value = ?
            ORDER BY c.cluster_id ASC, p.product_name ASC
        """
        return query_db(sql, (k,))
    else:
        sql = """
            SELECT 
                c.cluster_run_id,
                c.product_key,
                p.product_id,
                p.product_name,
                cat.category_name,
                c.cluster_id,
                c.cluster_label,
                c.k_value,
                c.silhouette_score,
                c.run_date
            FROM product_clusters c
            JOIN dim_product p ON c.product_key = p.product_key
            JOIN dim_category cat ON p.category_key = cat.category_key
            ORDER BY c.cluster_id ASC, p.product_name ASC
        """
        return query_db(sql)


if __name__ == "__main__":
    res = cluster_products(k=3)
    print("\n--- K-Means Clustering Result (K=3) ---")
    print(f"Features: {res['features_used']}")
    print(f"Optimal K: {res['optimal_k']} | Silhouette Score: {res['silhouette_score']}")
    print("Cluster Summaries:")
    for c in res["cluster_summaries"]:
        print(f"  [{c['cluster_id']}] {c['cluster_label']}: Count={c['member_count']}, Avg Price=₹{c['avg_price']}, Avg Units={c['avg_units']}")
        print(f"      Description: {c['description']}")
