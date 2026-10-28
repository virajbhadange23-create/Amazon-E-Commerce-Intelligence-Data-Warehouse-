"""
Machine Learning Price Predictor for Amazon E-Commerce Data Warehouse
Implements chronological time-series price forecasting comparing Linear Regression
and Random Forest, calculates MAE and RMSE, generates multi-month forward predictions,
calculates price differences (₹ and %), produces plain-English explanations,
and saves prediction history to SQLite price_predictions table.
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
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import config
from db.database import query_db, execute_db

logger = logging.getLogger(__name__)


def generate_plain_english_explanation(
    product_name: str,
    target_month_label: str,
    latest_price: float,
    predicted_price: float,
    diff_rupees: float,
    diff_pct: float,
    is_festive: bool,
    recent_trend_slope: float
) -> str:
    """Generates an intuitive, natural-language explanation of the price prediction."""
    short_name = product_name[:40] + ("..." if len(product_name) > 40 else "")
    
    if abs(diff_rupees) < 2.0 or abs(diff_pct) < 0.5:
        trend_desc = "remain relatively stable"
        reason = "reflecting steady customer demand and consistent inventory pricing."
    elif diff_rupees < 0:
        trend_desc = f"drop by ₹{abs(diff_rupees):,.2f} ({abs(diff_pct):.1f}%)"
        if is_festive:
            reason = "driven by competitive seasonal festival promotional discounts and high sales volume."
        elif recent_trend_slope < 0:
            reason = "continuing the recent downward pricing trend observed over recent months."
        else:
            reason = "as post-sale discount adjustments and competitive seller pricing take effect."
    else:
        trend_desc = f"increase by ₹{diff_rupees:,.2f} (+{diff_pct:.1f}%)"
        if not is_festive and recent_trend_slope >= 0:
            reason = "as festival discount windows close and prices return toward catalog retail levels."
        else:
            reason = "aligned with normal market fluctuations and strong baseline category demand."

    return (
        f"For {target_month_label}, the selling price of '{short_name}' is projected to {trend_desc}, "
        f"moving from ₹{latest_price:,.2f} to ₹{predicted_price:,.2f}, {reason}"
    )


def predict_price_for_product(
    product_key: int,
    target_step: int = 1,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    Trains Linear Regression and Random Forest models on historical monthly pricing data
    using chronological time-series splitting.
    Evaluates MAE, RMSE, and R2, forecasts future price for the chosen step (1..6 months),
    calculates difference metrics, produces plain-English explanation, and persists to DB.
    """
    target_step = max(1, min(12, int(target_step)))

    # 1. Fetch product metadata
    prod_row = query_db(
        """
        SELECT 
            p.product_key,
            p.product_id,
            p.product_name,
            c.category_name,
            p.rating,
            p.rating_count,
            p.base_actual_price,
            p.base_discount_price
        FROM dim_product p
        JOIN dim_category c ON p.category_key = c.category_key
        WHERE p.product_key = ?
        """,
        (product_key,),
        one=True
    )
    if not prod_row:
        return {"success": False, "eligible": False, "error": f"Product with key {product_key} not found."}

    # 2. Fetch historical sales data
    history = query_db(
        """
        SELECT 
            f.sale_id,
            f.product_key,
            f.date_key,
            d.year_month,
            d.month,
            d.year,
            d.month_name,
            f.actual_price,
            f.discount_price,
            f.discount_percent,
            f.units_sold,
            f.sales_amount
        FROM fact_sales f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE f.product_key = ?
        ORDER BY f.date_key ASC
        """,
        (product_key,)
    )

    if not history or len(history) < 4:
        count_found = len(history) if history else 0
        return {
            "success": False,
            "eligible": False,
            "product": prod_row,
            "product_key": product_key,
            "message": (
                f"Insufficient historical data ({count_found} months found). "
                f"At least 4 monthly price records are required to perform reliable machine learning time-series forecasting."
            )
        }

    df = pd.DataFrame(history)
    n_samples = len(df)

    # 3. Latest Actual & Discount Prices
    latest_record = df.iloc[-1]
    latest_actual_price = float(latest_record["actual_price"])
    latest_discount_price = float(latest_record["discount_price"])
    latest_discount_pct = float(latest_record["discount_percent"])
    last_year = int(latest_record["year"])
    last_month = int(latest_record["month"])

    # 4. Feature Engineering for Time-Series
    df["time_idx"] = np.arange(n_samples)
    df["is_festive"] = df["month"].isin(config.FESTIVE_MONTHS).astype(int)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)

    feature_cols = ["time_idx", "discount_percent", "units_sold", "is_festive", "month_sin", "month_cos"]
    X = df[feature_cols].values
    y = df["discount_price"].values

    # 5. Strict Chronological Train/Test Split (No shuffling)
    test_size = max(2, min(4, int(n_samples * config.PREDICTION_TEST_SIZE)))
    train_size = n_samples - test_size

    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # Model 1: Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)
    mae_lr = float(mean_absolute_error(y_test, y_pred_lr))
    rmse_lr = float(np.sqrt(mean_squared_error(y_test, y_pred_lr)))
    r2_lr = float(r2_score(y_test, y_pred_lr))

    # Model 2: Random Forest Regressor
    rf = RandomForestRegressor(n_estimators=35, max_depth=4, random_state=config.RANDOM_SEED)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    mae_rf = float(mean_absolute_error(y_test, y_pred_rf))
    rmse_rf = float(np.sqrt(mean_squared_error(y_test, y_pred_rf)))
    r2_rf = float(r2_score(y_test, y_pred_rf))

    # Model 3: Ridge Regression (L2 regularization)
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    y_pred_ridge = ridge.predict(X_test)
    mae_ridge = float(mean_absolute_error(y_test, y_pred_ridge))
    rmse_ridge = float(np.sqrt(mean_squared_error(y_test, y_pred_ridge)))
    r2_ridge = float(r2_score(y_test, y_pred_ridge))

    # Model Selection: Prioritize Lower RMSE / MAE
    candidates = [
        ("Linear Regression", lr, mae_lr, rmse_lr, r2_lr),
        ("Random Forest Regressor", rf, mae_rf, rmse_rf, r2_rf),
        ("Ridge Regression", ridge, mae_ridge, rmse_ridge, r2_ridge)
    ]
    candidates.sort(key=lambda c: c[3])  # Sort by lowest RMSE
    best_model_name, best_model, best_mae, best_rmse, best_r2 = candidates[0]

    # Refit chosen model on full historical dataset
    best_model.fit(X, y)

    # 6. Generate 6-Month Forward Forecast Outlook
    recent_discount = float(df["discount_percent"].tail(3).mean())
    recent_units = float(df["units_sold"].tail(3).mean())
    min_bound = float(df["discount_price"].min()) * 0.70
    max_bound = float(df["actual_price"].max()) * 1.05

    forecast_steps = []
    future_y = last_year
    future_m = last_month

    for step in range(1, 7):
        future_m += 1
        if future_m > 12:
            future_m = 1
            future_y += 1

        f_time_idx = n_samples + step - 1
        f_is_festive = 1 if future_m in config.FESTIVE_MONTHS else 0
        f_sin = np.sin(2 * np.pi * future_m / 12.0)
        f_cos = np.cos(2 * np.pi * future_m / 12.0)
        ym_str = f"{future_y}-{future_m:02d}"

        feat = np.array([[f_time_idx, recent_discount, recent_units, f_is_festive, f_sin, f_cos]])
        raw_pred = float(best_model.predict(feat)[0])
        bounded_pred = round(max(min_bound, min(max_bound, raw_pred)), 2)

        dt = datetime.date(future_y, future_m, 1)
        m_label = dt.strftime("%B %Y")

        step_diff_rupees = round(bounded_pred - latest_discount_price, 2)
        step_diff_pct = round((step_diff_rupees / latest_discount_price) * 100.0, 2)

        forecast_steps.append({
            "step": step,
            "year_month": ym_str,
            "month_label": m_label,
            "predicted_price": bounded_pred,
            "diff_rupees": step_diff_rupees,
            "diff_percent": step_diff_pct,
            "is_festive": bool(f_is_festive)
        })

    # Pick the target month requested
    target_idx = min(len(forecast_steps) - 1, target_step - 1)
    target_prediction = forecast_steps[target_idx]
    predicted_price = target_prediction["predicted_price"]
    predicted_for_month = target_prediction["year_month"]
    target_month_label = target_prediction["month_label"]
    is_target_festive = target_prediction["is_festive"]

    # Calculate difference from latest actual price & latest selling price
    diff_rupees = round(predicted_price - latest_discount_price, 2)
    diff_percent = round((diff_rupees / latest_discount_price) * 100.0, 2)

    diff_from_actual_rupees = round(predicted_price - latest_actual_price, 2)
    diff_from_actual_percent = round((diff_from_actual_rupees / latest_actual_price) * 100.0, 2)

    # Approximate price slope over last 3 records
    recent_slope = float(df["discount_price"].iloc[-1] - df["discount_price"].iloc[-3]) if len(df) >= 3 else 0.0

    # 7. Generate Plain-English Explanation
    explanation = generate_plain_english_explanation(
        product_name=str(prod_row["product_name"]),
        target_month_label=target_month_label,
        latest_price=latest_discount_price,
        predicted_price=predicted_price,
        diff_rupees=diff_rupees,
        diff_pct=diff_percent,
        is_festive=is_target_festive,
        recent_trend_slope=recent_slope
    )

    # 8. Save to Database price_predictions table
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if save_to_db:
        # Avoid duplicate prediction entries for the same product and target month
        execute_db(
            "DELETE FROM price_predictions WHERE product_key = ? AND predicted_for_month = ?",
            (product_key, predicted_for_month)
        )
        execute_db(
            """
            INSERT INTO price_predictions 
            (product_key, predicted_for_month, predicted_price, model_name, mae, r2, created_at, forecast_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_key,
                predicted_for_month,
                predicted_price,
                best_model_name,
                round(best_mae, 2),
                round(max(-1.0, min(0.999, best_r2)), 3),
                created_at,
                json.dumps(forecast_steps)
            )
        )

    # 9. Fetch recent prediction history for this product
    saved_history = query_db(
        """
        SELECT 
            prediction_id,
            predicted_for_month,
            predicted_price,
            model_name,
            mae,
            r2,
            created_at
        FROM price_predictions
        WHERE product_key = ?
        ORDER BY prediction_id DESC
        LIMIT 5
        """,
        (product_key,)
    )

    return {
        "success": True,
        "eligible": True,
        "product_key": product_key,
        "product": prod_row,
        "latest_metrics": {
            "latest_actual_price": latest_actual_price,
            "latest_discount_price": latest_discount_price,
            "latest_discount_percent": latest_discount_pct,
            "latest_year_month": str(latest_record["year_month"])
        },
        "target_step": target_step,
        "target_month": predicted_for_month,
        "target_month_label": target_month_label,
        "predicted_price": predicted_price,
        "diff_rupees": diff_rupees,
        "diff_percent": diff_percent,
        "estimated_change": {
            "diff_rupees": diff_rupees,
            "diff_percent": diff_percent,
            "is_drop": diff_rupees < 0,
            "diff_from_actual_rupees": diff_from_actual_rupees,
            "diff_from_actual_percent": diff_from_actual_percent
        },
        "explanation": explanation,
        "best_model": best_model_name,
        "mae": round(best_mae, 2),
        "rmse": round(best_rmse, 2),
        "r2": round(max(-1.0, min(0.999, best_r2)), 3),
        "forecast": forecast_steps,
        "evaluation": {
            "best_model": best_model_name,
            "mae": round(best_mae, 2),
            "rmse": round(best_rmse, 2),
            "r2": round(max(-1.0, min(0.999, best_r2)), 3),
            "train_months": train_size,
            "test_months": test_size,
            "comparison": {
                "linear_regression": {"mae": round(mae_lr, 2), "rmse": round(rmse_lr, 2), "r2": round(r2_lr, 3)},
                "random_forest": {"mae": round(mae_rf, 2), "rmse": round(rmse_rf, 2), "r2": round(r2_rf, 3)},
                "ridge": {"mae": round(mae_ridge, 2), "rmse": round(rmse_ridge, 2), "r2": round(r2_ridge, 3)}
            }
        },
        "forecast_outlook": forecast_steps,
        "monthly_history": history,
        "prediction_history": saved_history,
        "created_at": created_at
    }


def get_prediction_history(product_key: Optional[int] = None, limit: int = 15) -> List[Dict[str, Any]]:
    """Returns recent prediction records from price_predictions table."""
    limit = max(1, min(100, limit))
    if product_key:
        sql = """
            SELECT 
                pr.prediction_id,
                pr.product_key,
                p.product_name,
                c.category_name,
                pr.predicted_for_month,
                pr.predicted_price,
                pr.model_name,
                pr.mae,
                pr.r2,
                pr.created_at
            FROM price_predictions pr
            JOIN dim_product p ON pr.product_key = p.product_key
            JOIN dim_category c ON p.category_key = c.category_key
            WHERE pr.product_key = ?
            ORDER BY pr.prediction_id DESC
            LIMIT ?
        """
        return query_db(sql, (product_key, limit))
    else:
        sql = """
            SELECT 
                pr.prediction_id,
                pr.product_key,
                p.product_name,
                c.category_name,
                pr.predicted_for_month,
                pr.predicted_price,
                pr.model_name,
                pr.mae,
                pr.r2,
                pr.created_at
            FROM price_predictions pr
            JOIN dim_product p ON pr.product_key = p.product_key
            JOIN dim_category c ON p.category_key = c.category_key
            ORDER BY pr.prediction_id DESC
            LIMIT ?
        """
        return query_db(sql, (limit,))


def train_all_product_predictions() -> Dict[str, Any]:
    """Pre-calculates price predictions for all products in warehouse."""
    products = query_db("SELECT product_key FROM dim_product ORDER BY product_key ASC")
    total = len(products)
    success_count = 0

    logger.info(f"Starting batch price prediction generation for {total} products...")
    for prod in products:
        try:
            res = predict_price_for_product(prod["product_key"], save_to_db=True)
            if res.get("success"):
                success_count += 1
        except Exception as e:
            logger.warning(f"Prediction failed for product_key {prod['product_key']}: {e}")

    logger.info(f"Batch prediction completed: {success_count}/{total} products predicted.")
    return {
        "total_products": total,
        "predictions_generated": success_count
    }


if __name__ == "__main__":
    res = predict_price_for_product(1, target_step=1)
    print("\n--- ML Prediction for Product 1 (Next Month) ---")
    print(f"Product: {res['product']['product_name']}")
    print(f"Latest Price: ₹{res['latest_metrics']['latest_discount_price']}")
    print(f"Predicted Price ({res['target_month_label']}): ₹{res['predicted_price']}")
    print(f"Estimated Change: ₹{res['estimated_change']['diff_rupees']} ({res['estimated_change']['diff_percent']}%)")
    print(f"Explanation: {res['explanation']}")
    print(f"MAE: {res['evaluation']['mae']} | RMSE: {res['evaluation']['rmse']}")
