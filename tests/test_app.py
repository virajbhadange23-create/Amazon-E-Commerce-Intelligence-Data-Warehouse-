"""
Comprehensive Automated Test Suite for Amazon E-Commerce Data Warehouse
Tests:
1. ETL transform, string cleaning, currency normalization, and idempotency.
2. Machine Learning Price Prediction (Linear Regression vs RF vs Ridge, MAE, R2, and edge cases).
3. K-Means Clustering (StandardScaler, silhouette score, elbow curve).
4. SQL-based OLAP operations (Roll-up, Drill-down, Slice, Dice, Pivot).
5. FastAPI Web Endpoints and Template Rendering.
"""
import unittest
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from fastapi.testclient import TestClient
from app import app
from db.database import init_db, query_db, get_table_counts
from services.etl import clean_currency_string, clean_percentage_string, transform, run_etl
from services import olap
from ml.predictor import predict_price_for_product
from ml.clustering import cluster_products


class TestETLPipeline(unittest.TestCase):
    """Test ETL data cleaning and transformation functions."""

    def test_clean_currency_string(self):
        self.assertEqual(clean_currency_string("₹24,990"), 24990.0)
        self.assertEqual(clean_currency_string(" $ 1,299.50 "), 1299.5)
        self.assertEqual(clean_currency_string("₹ 499"), 499.0)
        self.assertIsNone(clean_currency_string(None))
        self.assertIsNone(clean_currency_string(""))

    def test_clean_percentage_string(self):
        self.assertEqual(clean_percentage_string("24%"), 24.0)
        self.assertEqual(clean_percentage_string(" 50 % "), 50.0)
        self.assertIsNone(clean_percentage_string(None))

    def test_transform_data_quality(self):
        # Create test raw DataFrame with duplicates and messy prices
        raw_data = {
            "product_name": [
                "Sony WH-1000XM5 Headphones",
                "Sony WH-1000XM5 Headphones",  # Duplicate
                "Apple MacBook Air M2",
                "Short",  # Should be rejected
                "Samsung Galaxy S24"
            ],
            "category": [
                "Audio & Headphones",
                "Audio & Headphones",
                "Computers & Accessories",
                "E",  # Rejected
                "Electronics"
            ],
            "actual_price": ["₹34,990", "₹34,990", "₹1,14,900", "₹100", "₹1,34,999"],
            "discounted_price": ["₹26,990", "₹26,990", "₹89,990", "₹50", "₹1,19,999"],
            "discount_percentage": ["23%", "23%", "22%", "50%", "11%"],
            "rating": [4.6, 4.6, 4.7, 1.0, 4.6],
            "rating_count": ["21,450", "21,450", "18,400", "10", "21,800"]
        }
        df_raw = pd.DataFrame(raw_data)
        cats, prods, dates, sales, report = transform(df_raw)

        # Assert duplicate was pruned
        self.assertEqual(report["duplicates_removed"], 1)
        # Assert rejected row was dropped
        self.assertEqual(report["rows_rejected"], 1)
        # Cleaned products should be 3
        self.assertEqual(len(prods), 3)
        # 18 months per product generated
        self.assertEqual(len(sales), 3 * 18)
        # Check audit flag
        self.assertTrue((sales["is_sample"] == 1).all())


class TestMLPredictor(unittest.TestCase):
    """Test Price Prediction ML algorithms."""

    def test_price_prediction_product_1(self):
        res = predict_price_for_product(1, target_step=1, save_to_db=False)
        self.assertTrue(res["success"])
        self.assertTrue(res["eligible"])
        self.assertIn(res["best_model"], ["Linear Regression", "Random Forest Regressor", "Ridge Regression"])
        self.assertGreater(res["predicted_price"], 0)
        self.assertEqual(len(res["forecast"]), 6)
        self.assertIn("mae", res)
        self.assertIn("rmse", res)
        self.assertIn("r2", res)
        self.assertIn("diff_rupees", res)
        self.assertIn("diff_percent", res)
        self.assertIn("explanation", res)

    def test_prediction_nonexistent_product(self):
        # Product key 999999 does not exist
        res = predict_price_for_product(999999, save_to_db=False)
        self.assertFalse(res["success"])
        self.assertFalse(res["eligible"])
        self.assertIn("not found", res.get("error", "").lower())


class TestMLClustering(unittest.TestCase):
    """Test K-Means Product Clustering."""

    def test_clustering_k3(self):
        res = cluster_products(k=3, save_to_db=False)
        self.assertTrue(res["success"])
        self.assertEqual(res["k"], 3)
        self.assertGreaterEqual(res["silhouette_score"], -1.0)
        self.assertLessEqual(res["silhouette_score"], 1.0)
        self.assertEqual(len(res["cluster_summaries"]), 3)
        self.assertGreater(len(res["scatter_points"]), 0)
        self.assertEqual(len(res["elbow_curve"]), 7)  # K = 2..8


class TestOLAPEngine(unittest.TestCase):
    """Test SQL-based OLAP operations."""

    def test_rollup(self):
        q_data = olap.rollup_sales("quarter")
        self.assertGreater(len(q_data), 0)
        self.assertIn("quarter_label", q_data[0])
        self.assertIn("total_sales_amount", q_data[0])

        y_data = olap.rollup_sales("year")
        self.assertGreater(len(y_data), 0)
        self.assertIn("year", y_data[0])

    def test_drilldown(self):
        summary = olap.drilldown_sales()
        self.assertGreater(len(summary), 0)
        self.assertIn("category_name", summary[0])

        prods = olap.drilldown_sales(1)
        self.assertGreater(len(prods), 0)
        self.assertIn("product_name", prods[0])

    def test_slice_and_dice(self):
        slice_res = olap.slice_sales("category", 1)
        self.assertGreater(len(slice_res), 0)

        dice_res = olap.dice_sales([1, 2], "2024-01", "2024-06")
        self.assertGreater(len(dice_res), 0)

    def test_pivot(self):
        p_res = olap.pivot_sales("sales_amount")
        self.assertGreater(len(p_res["categories"]), 0)
        self.assertGreater(len(p_res["months"]), 0)
        self.assertEqual(len(p_res["rows"]), len(p_res["categories"]))


class TestFastAPIEndpoints(unittest.TestCase):
    """Test all Web and API routes."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_html_views(self):
        views = [
            "/",
            "/price-prediction",
            "/price-history",
            "/product-analysis",
            "/sales-analysis",
            "/etl",
            "/warehouse",
            "/olap",
            "/clustering",
            "/data-quality",
            "/datasets",
        ]
        for v in views:
            res = self.client.get(v)
            self.assertEqual(res.status_code, 200, f"View {v} failed with status {res.status_code}")

    def test_api_dashboard_kpis(self):
        res = self.client.get("/api/dashboard/kpis")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["kpis"]["total_products"], 0)
        self.assertGreater(data["kpis"]["total_sales_amount"], 0)

    def test_api_product_history(self):
        res = self.client.get("/api/products/1/history")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["history"]), 18)
        self.assertIsNotNone(data["prediction"])

    def test_api_olap_export(self):
        res = self.client.get("/api/olap/export?operation=rollup&level=quarter")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers.get("content-type", ""))
        self.assertIn("quarter_label", res.text)


if __name__ == "__main__":
    unittest.main()
