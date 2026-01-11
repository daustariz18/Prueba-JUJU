import json
import logging
from pathlib import Path
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)

OUTPUT_BASE = Path("output")
RAW_PATH = OUTPUT_BASE / "raw"
CURATED_PATH = OUTPUT_BASE / "curated"


# -------------------------
# RAW ZONE
# -------------------------
def write_raw(records: List[dict], entity: str) -> None:
    """
    Escribe datos RAW como copia inmutable del input.
    """
    RAW_PATH.mkdir(parents=True, exist_ok=True)

    filename = RAW_PATH / f"{entity}.json"

    logger.info(f"Escribiendo RAW en {filename}")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# -------------------------
# CURATED ZONE
# -------------------------
def write_curated(df: pd.DataFrame, table: str) -> None:
    """
    Escribe datos CURATED aplicando:
    - Particionado por fecha (created_at)
    - Idempotencia (no duplica PKs)
    """
    if df.empty:
        logger.warning(f"No hay datos para escribir en {table}")
        return

    table_path = CURATED_PATH / table
    table_path.mkdir(parents=True, exist_ok=True)

    if "created_at" in df.columns:
        df["partition_date"] = df["created_at"].dt.date.astype(str)
    else:
        df["partition_date"] = "unknown"

    for partition_value, partition_df in df.groupby("partition_date"):
        partition_dir = table_path / f"date={partition_value}"
        partition_dir.mkdir(parents=True, exist_ok=True)

        file_path = partition_dir / f"{table}.parquet"

        # Idempotencia: si existe, merge por PK
        if file_path.exists():
            logger.info(f"Archivo existente encontrado: {file_path}")
            existing_df = pd.read_parquet(file_path)

            pk = _get_primary_key(table)
            if pk and pk in df.columns:
                combined = pd.concat([existing_df, partition_df])
                combined = (
                    combined.drop_duplicates(subset=[pk], keep="last")
                    .reset_index(drop=True)
                )
            else:
                combined = partition_df

            combined.to_parquet(file_path, index=False)
            logger.info(
                f"Actualizado {table} ({len(combined)} registros) en {partition_dir}"
            )
        else:
            partition_df.to_parquet(file_path, index=False)
            logger.info(
                f"Creado {table} ({len(partition_df)} registros) en {partition_dir}"
            )


# -------------------------
# Helpers
# -------------------------
def _get_primary_key(table: str) -> str:
    """
    Define PK por tabla para idempotencia.
    """
    mapping = {
        "fact_order": "order_id",
        "dim_user": "user_id",
        "dim_product": "sku",
    }
    return mapping.get(table)
