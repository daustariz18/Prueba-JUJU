import pandas as pd
from datetime import datetime

from src.transforms import (
    clean_orders,
    dedupe_orders,
    build_fact_orders,
)


# -------------------------
# FIXTURES SIMPLES
# -------------------------
def sample_orders():
    return [
        {
            "order_id": "o_1",
            "user_id": "u_1",
            "currency": "USD",
            "created_at": "2025-08-20T10:00:00Z",
            "items": [{"sku": "p_1", "qty": 2, "price": 10.0}],
        },
        # Duplicado (misma order_id)
        {
            "order_id": "o_1",
            "user_id": "u_1",
            "currency": "USD",
            "created_at": "2025-08-20T12:00:00Z",
            "items": [{"sku": "p_1", "qty": 2, "price": 10.0}],
        },
        # Orden inválida (sin items)
        {
            "order_id": "o_2",
            "user_id": "u_2",
            "currency": "USD",
            "created_at": "2025-08-20T11:00:00Z",
            "items": [],
        },
    ]


# -------------------------
# TEST: CLEAN ORDERS
# -------------------------
def test_clean_orders_filters_invalid_orders():
    orders = sample_orders()
    df = clean_orders(orders)

    # Solo 2 órdenes válidas antes de dedupe
    assert len(df) == 2
    assert "order_id" in df.columns
    assert "items" in df.columns


# -------------------------
# TEST: DEDUPE
# -------------------------
def test_dedupe_orders_removes_duplicates():
    orders = sample_orders()
    df = clean_orders(orders)
    deduped = dedupe_orders(df)

    # Solo queda 1 por order_id
    assert len(deduped) == 1
    assert deduped.iloc[0]["order_id"] == "o_1"


# -------------------------
# TEST: FACT TOTAL CALCULATION
# -------------------------
def test_build_fact_orders_calculates_total_amount(tmp_path, monkeypatch):
    # Mock products.csv
    products_df = pd.DataFrame(
        {
            "sku": ["p_1"],
            "name": ["Product 1"],
            "category": ["test"],
            "price": [10.0],
        }
    )

    products_path = tmp_path / "products.csv"
    products_df.to_csv(products_path, index=False)

    # Monkeypatch path
    monkeypatch.setattr(
        "src.transforms.PRODUCTS_PATH",
        products_path,
    )

    orders = [
        {
            "order_id": "o_1",
            "user_id": "u_1",
            "currency": "USD",
            "created_at": "2025-08-20T10:00:00Z",
            "items": [{"sku": "p_1", "qty": 3, "price": None}],
        }
    ]

    df = clean_orders(orders)
    fact = build_fact_orders(df)

    assert len(fact) == 1
    assert fact.iloc[0]["total_amount"] == 30.0
