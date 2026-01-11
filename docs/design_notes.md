# Design Notes – ETL Pipeline

## Ajustes sobre los datos de la API Mock

Durante las pruebas iniciales, la API mock generó registros con la siguiente estructura genérica:

- `amount` como string
- `created_at` como timestamp Unix
- `items` vacío
- `metadata` sin información de contexto

Esta estructura no permitía una normalización adecuada ni el modelado dimensional requerido por el ejercicio.

Por esta razón, se realizaron ajustes controlados sobre los datos de entrada para:

- Normalizar tipos de datos (`amount` numérico, fechas ISO 8601)
- Garantizar la presencia de al menos un ítem por orden
- Incluir metadatos mínimos de contexto (`source`, `promo`)
- Alinear los identificadores al modelo dimensional

Este enfoque replica escenarios reales donde las APIs pueden entregar datos incompletos o inconsistentes que deben ser corregidos antes de su uso analítico.


## Elección del stack
Se utilizó **Python con pandas y duckdb** en lugar de PySpark debido a que:
- El volumen de datos del ejercicio es reducido.
- Permite una ejecución local simple y reproducible.
- DuckDB y Parquet mantienen un enfoque analítico similar a Redshift.
- Reduce complejidad operativa sin sacrificar claridad de diseño.

Esta elección es adecuada para un entorno de prueba técnica y fácilmente escalable a Spark o Glue en producción.

---

## Diseño del pipeline
El pipeline sigue un enfoque tipo **data lake** con dos zonas:

- **Raw zone**: copia inmutable del input original (JSON).
- **Curated zone**: datos limpios, deduplicados y listos para analítica.

Este enfoque permite:
- Reprocesamiento seguro.
- Auditoría de datos.
- Separación clara de responsabilidades.

---

## Particionado
Los datos curados se escriben en formato Parquet, particionados por fecha:

- `fact_order`: partición por `created_at` (`date=YYYY-MM-DD`)
- `dim_user`: partición por `created_at`
- `dim_product`: partición fija (`date=unknown`)

Este esquema es compatible con ingesta mediante `COPY` en Amazon Redshift y optimiza consultas por rango de fechas.

---

## Idempotencia
La idempotencia se garantiza mediante:
- Uso de claves naturales como identificadores únicos:
  - `order_id` (fact_order)
  - `user_id` (dim_user)
  - `sku` (dim_product)
- Antes de escribir en curated, los datos existentes se leen y se realiza un merge eliminando duplicados por clave primaria.

Ejecutar el job múltiples veces no genera duplicados.

---

## Incrementalidad
El pipeline soporta ejecución incremental mediante el parámetro:
```bash
--since YYYY-MM-DD
