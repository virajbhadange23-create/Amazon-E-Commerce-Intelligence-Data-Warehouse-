"""
Test script for ML Price Prediction and K-Means Clustering modules
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.predictor import predict_price_for_product, train_all_product_predictions
from ml.clustering import cluster_products
from db.database import get_table_counts, query_db

print("1. Testing Single Prediction for Product 1...")
res_pred = predict_price_for_product(1, save_to_db=True)
print("  Success:", res_pred["success"])
print("  Best Model:", res_pred["best_model"])
print("  MAE:", res_pred["mae"], "| R2:", res_pred["r2"])
print("  Predicted Next Month:", res_pred["predicted_for_month"], "-> Price:", res_pred["predicted_price"])
print("  3-Month Forecast Steps:", len(res_pred["forecast"]))

print("\n2. Testing K-Means Clustering (K=3)...")
res_cluster = cluster_products(k=3, save_to_db=True)
print("  Success:", res_cluster["success"])
print("  Silhouette Score:", res_cluster["silhouette_score"])
print("  Elbow points calculated:", len(res_cluster["elbow_curve"]))
print("  Scatter points:", len(res_cluster["scatter_points"]))
for c in res_cluster["cluster_summaries"]:
    print(f"    Cluster {c['cluster_id']} [{c['cluster_label']}]: Count={c['member_count']}, Avg Price={c['avg_price']}")

print("\n3. Testing Pre-calculating Predictions for all products...")
batch_res = train_all_product_predictions()
print("  Batch Results:", batch_res)

print("\n4. Verifying SQLite Database Persistence...")
counts = get_table_counts()
print("  Live Table Counts:", counts)

assert counts["price_predictions"] > 0, "price_predictions table is empty!"
assert counts["product_clusters"] > 0, "product_clusters table is empty!"

sample_pred = query_db("SELECT * FROM price_predictions LIMIT 1")[0]
print("\nSample Saved Prediction Record:")
for k, v in sample_pred.items():
    print(f"  {k}: {v}")

sample_cluster = query_db("SELECT * FROM product_clusters LIMIT 1")[0]
print("\nSample Saved Cluster Record:")
for k, v in sample_cluster.items():
    print(f"  {k}: {v}")

print("\nALL ML PREDICTION AND CLUSTERING TESTS PASSED WITH DATABASE PERSISTENCE VERIFIED!")
