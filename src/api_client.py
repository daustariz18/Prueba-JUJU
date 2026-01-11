import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dateutil import parser as date_parser


logger = logging.getLogger(__name__)

# Ruta al mock de la API
API_MOCK_PATH = Path("sample_data/api_orders.json")


def fetch_orders(
    since: Optional[datetime] = None,
    max_retries: int = 3,
) -> List[dict]:
    """
    Simula la llamada a una API REST leyendo un archivo JSON local.
    Incluye retry básico y filtro incremental por fecha.
    """
    attempt = 0

    while attempt < max_retries:
        try:
            logger.info("Leyendo órdenes desde API mock")
            orders = _read_mock_file()

            if since:
                orders = _filter_since(orders, since)
                logger.info(f"Órdenes después del filtro incremental: {len(orders)}")

            return orders

        except Exception as exc:
            attempt += 1
            logger.warning(
                f"Error leyendo API mock (intento {attempt}/{max_retries}): {exc}"
            )

            if attempt >= max_retries:
                logger.error("Se agotaron los reintentos leyendo la API mock")
                raise


def _read_mock_file() -> List[dict]:
    if not API_MOCK_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo {API_MOCK_PATH}")

    with open(API_MOCK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("El mock de la API debe ser una lista de órdenes")

    return data


def _filter_since(orders: List[dict], since: datetime) -> List[dict]:
    filtered = []

    for order in orders:
        created_at = order.get("created_at")

        if not created_at:
            logger.warning(
                f"Orden sin created_at, se descarta. order_id={order.get('order_id')}"
            )
            continue

        try:
            created_at_dt = date_parser.isoparse(created_at)
        except Exception:
            logger.warning(
                f"created_at inválido, se descarta. order_id={order.get('order_id')}"
            )
            continue

        if created_at_dt >= since:
            filtered.append(order)

    return filtered
