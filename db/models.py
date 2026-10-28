"""
SQLAlchemy 2.0 Declarative Models for Amazon E-Commerce Data Warehouse
Maps the Star Schema:
- Dimensions: DimCategory, DimProduct, DimDate
- Fact: FactSales
- Analytical / Operational: EtlLog, PricePrediction, ProductCluster
"""
from typing import Optional, List
from sqlalchemy import Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DimCategory(Base):
    __tablename__ = "dim_category"

    category_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    products: Mapped[List["DimProduct"]] = relationship("DimProduct", back_populates="category")
    sales: Mapped[List["FactSales"]] = relationship("FactSales", back_populates="category")


class DimProduct(Base):
    __tablename__ = "dim_product"

    product_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    category_key: Mapped[int] = mapped_column(ForeignKey("dim_category.category_key", ondelete="CASCADE"), nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    base_actual_price: Mapped[float] = mapped_column(Float, nullable=False)
    base_discount_price: Mapped[float] = mapped_column(Float, nullable=False)

    category: Mapped["DimCategory"] = relationship("DimCategory", back_populates="products")
    sales: Mapped[List["FactSales"]] = relationship("FactSales", back_populates="product")
    predictions: Mapped[List["PricePrediction"]] = relationship("PricePrediction", back_populates="product")
    clusters: Mapped[List["ProductCluster"]] = relationship("ProductCluster", back_populates="product")


class DimDate(Base):
    __tablename__ = "dim_date"

    date_key: Mapped[int] = mapped_column(Integer, primary_key=True)  # YYYYMM
    day: Mapped[int] = mapped_column(Integer, default=1)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    month_name: Mapped[str] = mapped_column(String, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    year_month: Mapped[str] = mapped_column(String, nullable=False)

    sales: Mapped[List["FactSales"]] = relationship("FactSales", back_populates="date_dim")


class FactSales(Base):
    __tablename__ = "fact_sales"

    sale_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_key: Mapped[int] = mapped_column(ForeignKey("dim_product.product_key", ondelete="CASCADE"), nullable=False)
    date_key: Mapped[int] = mapped_column(ForeignKey("dim_date.date_key", ondelete="CASCADE"), nullable=False)
    category_key: Mapped[int] = mapped_column(ForeignKey("dim_category.category_key", ondelete="CASCADE"), nullable=False)
    actual_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
    units_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    sales_amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_sample: Mapped[int] = mapped_column(Integer, default=1)

    product: Mapped["DimProduct"] = relationship("DimProduct", back_populates="sales")
    date_dim: Mapped["DimDate"] = relationship("DimDate", back_populates="sales")
    category: Mapped["DimCategory"] = relationship("DimCategory", back_populates="sales")


class EtlLog(Base):
    __tablename__ = "etl_log"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[str] = mapped_column(String, nullable=False)
    completed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rows_extracted: Mapped[int] = mapped_column(Integer, default=0)
    rows_cleaned: Mapped[int] = mapped_column(Integer, default=0)
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_removed: Mapped[int] = mapped_column(Integer, default=0)
    nulls_fixed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PricePrediction(Base):
    __tablename__ = "price_predictions"

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_key: Mapped[int] = mapped_column(ForeignKey("dim_product.product_key", ondelete="CASCADE"), nullable=False)
    predicted_for_month: Mapped[str] = mapped_column(String, nullable=False)
    predicted_price: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    mae: Mapped[float] = mapped_column(Float, nullable=False)
    r2: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    forecast_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product: Mapped["DimProduct"] = relationship("DimProduct", back_populates="predictions")


class ProductCluster(Base):
    __tablename__ = "product_clusters"

    cluster_run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_key: Mapped[int] = mapped_column(ForeignKey("dim_product.product_key", ondelete="CASCADE"), nullable=False)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cluster_label: Mapped[str] = mapped_column(String, nullable=False)
    k_value: Mapped[int] = mapped_column(Integer, nullable=False)
    silhouette_score: Mapped[float] = mapped_column(Float, nullable=False)
    run_date: Mapped[str] = mapped_column(String, nullable=False)

    product: Mapped["DimProduct"] = relationship("DimProduct", back_populates="clusters")

