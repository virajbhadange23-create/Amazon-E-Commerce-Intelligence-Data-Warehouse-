"""
Configuration Module for Amazon E-Commerce Intelligence & Data Warehouse
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database & Data Files
DB_PATH = DB_DIR / "warehouse.db"
DATASET_CSV = BASE_DIR / "amazon_ecommerce_dataset.csv"
RAW_PRODUCTS_CSV = RAW_DATA_DIR / "amazon_products.csv"
SCHEMA_PATH = DB_DIR / "schema.sql"
LOG_FILE = LOGS_DIR / "app.log"
ETL_LOG_FILE = LOGS_DIR / "etl.log"

# Server Configuration
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
SECRET_KEY = os.environ.get("SECRET_KEY", "dwm-amazon-dw-secret-key-2026")

# ETL & Simulation Settings
SIMULATION_MONTHS = 18  # 12 to 24 months per product
RANDOM_SEED = 42
FESTIVE_MONTHS = [10, 11]  # October & November festive sales (Great Indian Festival / Black Friday)
SUMMER_SALE_MONTHS = [5]   # May Summer sale

# ML Settings
DEFAULT_K_CLUSTERS = 3
CLUSTERING_RANDOM_STATE = 42
PREDICTION_TEST_SIZE = 0.2
