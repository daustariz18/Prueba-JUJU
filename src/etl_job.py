import argparse
import logging
from pathlib import Path
from datetime import datetime

from src.api_client import fetch_orders
from src.transforms import (
    clean_orders,
    dedupe_orders,
    build_fact_orders,
    build_dim_users,
    build_dim_products,
)
from src.db import write_raw, write_curated


# -------------------------
# Configuración de logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# -------------------------
# Argumentos CLI
# -------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="ETL Job - Orders Pipeline")
    parser.add_argument(
        "--since",
        required=False,
        help="Fecha ISO (YYYY-MM-DD) para ejecución incremental",
    )
    return parser.parse_args()


# -------------------------
# Pipeline principal
# -------------------------
def main():
    args = parse_args()

    since_date = None
    if args.since:
        since_date = datetime.fromisoformat(args.since)
        logger.info(f"Ejecutando ETL incremental desde {since_date.date()}")

    logger.info("Iniciando ingesta desde API mock")

    # 1. Ingesta API
    orders_raw = fetch_orders(since=since_date)

    if not orders_raw:
        logger.warning("No se encontraron órdenes para procesar")
        return

    # 2. Guardar RAW (inmutable)
    write_raw(orders_raw, entity="orders")

    # 3. Limpieza y normalización
    orders_clean = clean_orders(orders_raw)

    # 4. Dedupe (idempotencia)
    orders_deduped = dedupe_orders(orders_clean)

    # 5. Construcción modelo analítico
    fact_orders = build_fact_orders(orders_deduped)
    dim_users = build_dim_users()
    dim_products = build_dim_products()

    # 6. Escritura CURATED
    write_curated(fact_orders, table="fact_order")
    write_curated(dim_users, table="dim_user")
    write_curated(dim_products, table="dim_product")

    logger.info("ETL finalizado correctamente")


if __name__ == "__main__":
    main()
