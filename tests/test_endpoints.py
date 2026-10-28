"""
Automated verification script for all FastAPI backend API endpoints
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

endpoints = [
    "/api/dashboard/kpis",
    "/api/dashboard/sales-trend",
    "/api/dashboard/top-products",
    "/api/categories",
    "/api/date-range",
    "/api/products",
    "/api/products/1/history",
    "/api/sales/top-products",
    "/api/sales/category-share",
    "/api/etl/status",
    "/api/warehouse/counts",
    "/api/warehouse/schema",
    "/api/olap/query?operation=rollup",
    "/api/olap/query?operation=drilldown&category_key=1",
    "/api/olap/query?operation=slice&slice_type=category&slice_val=1",
    "/api/olap/query?operation=dice&category_keys=1,2&start_ym=2024-01&end_ym=2024-06",
    "/api/olap/query?operation=pivot&metric=sales_amount",
    "/api/olap/export?operation=rollup",
    "/api/ml/predict/1?target_step=1",
    "/api/ml/prediction-history",
    "/api/ml/clustering?k=3",
    "/api/ml/clustering/saved",
    "/api/data-quality/summary",
    "/api/datasets/info",
    "/api/datasets/preview?limit=10"
]

all_passed = True
for ep in endpoints:
    res = client.get(ep)
    print(f"{ep:<70} -> Status: {res.status_code}")
    if res.status_code != 200:
        all_passed = False
        print("  Error output:", res.text[:200])

if all_passed:
    print("\nALL FASTAPI BACKEND API ENDPOINTS RETURNED HTTP 200 OK!")
else:
    print("\nSOME ENDPOINTS FAILED")
    sys.exit(1)
