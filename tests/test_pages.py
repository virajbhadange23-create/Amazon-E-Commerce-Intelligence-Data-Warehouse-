"""
Test HTML Page Rendering for all 10 Frontend Views
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

pages = [
    ("/", "Executive KPI Dashboard"),
    ("/product-analysis", "Product Analysis"),
    ("/price-prediction", "Product Price Prediction"),
    ("/price-history", "Product Price Prediction"),
    ("/sales-analysis", "Sales Performance & Category Analytics"),
    ("/clustering", "K-Means Product Clustering"),
    ("/olap", "OLAP Multidimensional Cube Analysis"),
    ("/etl", "ETL Process & Data Quality Audit"),
    ("/data-quality", "Data Quality Center"),
    ("/datasets", "Dataset Management"),
    ("/warehouse", "Data Warehouse Architecture & Star Schema")
]

all_passed = True
for url, expected_title in pages:
    res = client.get(url)
    print(f"Page {url:<22} -> Status: {res.status_code}")
    if res.status_code != 200:
        all_passed = False
        print("  Error:", res.text[:200])
    html = res.text
    if expected_title not in html:
        print(f"  Warning: Expected keyword '{expected_title}' not found in HTML response.")
    if "data-theme" not in html or "theme-toggle" not in html:
        all_passed = False
        print("  Error: Theme elements missing from page!")

if all_passed:
    print("\nALL FRONTEND VIEWS RENDERED WITH HTTP 200 OK AND COMPLETE THEME INTEGRATION!")
else:
    print("\nSOME PAGES FAILED RENDERING!")
    sys.exit(1)
