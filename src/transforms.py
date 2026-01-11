import logging
from typing import List, Dict
from datetime import datetime
import pandas as pd
from dateutil import parser as date_parser
from pathlib import Path

logger = logging.getLogger(__name__)

USERS_PATH = Path("sample_data/users.csv")
PRODUCTS_PATH = Path("sample_data/products.csv")


# -------------------------
# Limpieza de órdenes
# -------------------------
def clean_orders(orders: List[Dict]) -> pd.DataFrame:
    """
    Normaliza las órdenes:
    - Valida campos mínimos
    - Parsea fechas
    - Asegura estructura consistente
    """
    cleaned = []

    for o in orders:
        order_id = o.get("order_id")
        user_id = o.get("user_id")
        created_at = o.get("created_at")

        if not order_id or not user_id or not created_at:
            logger.warning(f"Orden inválida, se descarta: {o}")
            continue

        try:
            created_at_dt = date_parser.isoparse(created_at)
        except Exception:
            logger.warning(
                f"created_at inválido, se descarta. order_id={order_id}"
            )
            continue

        items = o.get("items", [])
        if not items:
            logger.warning(
                f"Orden sin items, se descarta. order_id={order_id}"
            )
            continue

        cleaned.append(
            {
                "order_id": order_id,
                "user_id": user_id,
                "currency": o.get("currency"),
                "created_at": created_at_dt,
                "items": items,
                "metadata": o.get("metadata", {}),
            }
        )

    df = pd.DataFrame(cleaned)
    logger.info(f"Órdenes válidas después de limpieza: {len(df)}")
    return df


# -------------------------
# Dedupe (idempotencia)
# -------------------------
def dedupe_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina duplicados por order_id conservando el más reciente.
    """
    if df.empty:
        return df

    before = len(df)
    df = (
        df.sort_values("created_at")
        .drop_duplicates(subset=["order_id"], keep="last")
        .reset_index(drop=True)
    )
    after = len(df)

    logger.info(f"Dedupe aplicado: {before - after} duplicados eliminados")
    return df


# -------------------------
# FACT ORDERS
# -------------------------
def build_fact_orders(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Construye la fact_order agregando el total por orden.
    """
    products = _load_products()

    records = []

    for _, row in df_orders.iterrows():
        total_amount = 0.0

        for item in row["items"]:
            sku = item.get("sku")
            qty = item.get("qty", 0)
            price = item.get("price")

            if price is None:
                price = products.get(sku)
                if price is None:
                    logger.warning(
                        f"Precio no encontrado para sku={sku}, se omite item"
                    )
                    continue

            total_amount += qty * price

        records.append(
            {
                "order_id": row["order_id"],
                "user_id": row["user_id"],
                "total_amount": round(total_amount, 2),
                "currency": row["currency"],
                "created_at": row["created_at"],
            }
        )

    fact_df = pd.DataFrame(records)
    return fact_df


# -------------------------
# DIM USERS
# -------------------------
def build_dim_users() -> pd.DataFrame:
    if not USERS_PATH.exists():
        raise FileNotFoundError(f"No existe {USERS_PATH}")

    df = pd.read_csv(USERS_PATH)

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df.drop_duplicates(subset=["user_id"]).reset_index(drop=True)


# -------------------------
# DIM PRODUCTS
# -------------------------
def build_dim_products() -> pd.DataFrame:
    if not PRODUCTS_PATH.exists():
        raise FileNotFoundError(f"No existe {PRODUCTS_PATH}")

    df = pd.read_csv(PRODUCTS_PATH)
    return df.drop_duplicates(subset=["sku"]).reset_index(drop=True)


# -------------------------
# Helpers
# -------------------------
def _load_products() -> Dict[str, float]:
    """
    Carga productos en un diccionario sku -> price
    """
    df = pd.read_csv(PRODUCTS_PATH)
    return dict(zip(df["sku"], df["price"]))
