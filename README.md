#  ETL Orders Pipeline

   ##  Descripción general

   Este proyecto implementa una **ETL batch** que consume datos de órdenes desde una **API REST mock**, los transforma y los prepara en un **modelo analítico dimensional** listo para análisis.

   La solución está diseñada para ser:
   - Ejecutable localmente
   - Modular y mantenible
   - Testeable
   - Alineada a buenas prácticas de ingeniería de datos

   Cumple con todos los entregables obligatorios definidos en la prueba técnica.

---

## Arquitectura de la solución

   API Mock (REST - mockapi.io)
         ↓
   ETL Batch (Python)
         ↓
   output/raw        → JSON original
   output/curated    → Datos curados (CSV / Parquet)
         ↓
   Modelo dimensional (DDL SQL)


---

## Estructura del proyecto

etl-test/
├── README.md
├── requirements.txt
│
├── sample_data/
│ ├── api_orders.json # Ejemplo de payload de la API
│ ├── users.csv # Datos de referencia (dim_user)
│ └── products.csv # Datos de referencia (dim_product)
│
├── src/
│ ├── etl_job.py # Orquestador principal de la ETL
│ ├── api_client.py # Cliente para consumo de la API REST
│ ├── transforms.py # Lógica de transformación y normalización
│ └── db.py # Abstracción de carga / persistencia
│
├── sql/
│ └── redshift-ddl.sql # DDL compatible con Redshift / DuckDB
│
├── tests/
│ └── test_transforms.py # Tests unitarios (pytest)
│
├── output/
│ ├── raw/ # Datos originales desde la API
│ └── curated/ # Datos transformados para analítica
│
└── docs/
└── design_notes.md # Decisiones de diseño

---

## Cómo ejecutar la solución

 ###  Requisitos

   - Python 3.9 o superior
   - pip

   Instalar dependencias:

   ```bash
   pip install -r requirements.txt


   ## 2 Fuente de datos – API Mock

   La fuente de datos utilizada en este proyecto es una **API REST mock**, diseñada para simular un sistema transaccional de órdenes de compra.

   La API expone un endpoint que retorna un arreglo de órdenes en formato JSON, con estructuras anidadas que incluyen los ítems del pedido y metadatos asociados.

   ### Endpoint

   https://695fb97f7f037703a814a280.mockapi.io/api/v1/orders

   ### Ajustes sobre los datos generados por la API Mock

   La API mock generó inicialmente datos con una estructura genérica (campos vacíos, tipos inconsistentes y timestamps en formato Unix).  
   Posteriormente, estos datos fueron ajustados para alinearlos con el modelo esperado por la prueba técnica y permitir una correcta transformación analítica.

   Los ajustes incluyeron normalización de tipos, enriquecimiento del detalle de ítems y estandarización de formatos de fecha.

   ## 3 Ejecución del proceso ETL

      Desde la raíz del proyecto ejecutar:

      ```bash
      python src/etl_job.py
   

## El proceso ETL ejecuta las siguientes etapas:

   1. Consumo batch de órdenes desde la API REST mock
   2. Almacenamiento del JSON original en la capa `output/raw`
   3. Transformación y normalización de los datos (explosión del array `items`)
   4. Generación de datasets curados listos para análisis en `output/curated`

   ## Resultados generados

   ### output/raw

   Contiene los datos originales tal como son entregados por la API REST, sin aplicar transformaciones.
   Esta capa permite trazabilidad y auditoría del proceso ETL.

   ### output/curated

   Contiene los datos transformados y normalizados.
   El nivel de granularidad es **item de pedido**, permitiendo análisis por producto, usuario y tiempo.

##  Tests

Los tests están implementados utilizando **pytest** y cubren:

- Transformaciones de datos
- Normalización de estructuras anidadas (`items`)
- Validaciones básicas de consistencia

Para ejecutar los tests:
   ```bash
   pytest tests/ 

```

---

##  Modelo de datos

   El archivo `sql/redshift-ddl.sql` contiene el DDL del modelo analítico dimensional,
   compatible con **Amazon Redshift y DuckDB**.

   El modelo está compuesto por:

   - `dim_user`
   - `dim_product`
   - `fact_order` (tabla de hechos a nivel de item)

   Se utiliza un **Star Schema**, optimizado para consultas analíticas.

