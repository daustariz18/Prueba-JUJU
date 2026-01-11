-- =====================================================
-- DDL Analítico compatible con Amazon Redshift / DuckDB
-- Modelo en estrella: dimensiones + tabla de hechos
-- =====================================================

-- =========================
-- DIMENSION: USERS
-- =========================
CREATE TABLE IF NOT EXISTS dim_user (
    user_id     VARCHAR(64)   NOT NULL,
    email       VARCHAR(255),
    country     VARCHAR(8),
    created_at  DATE,
    PRIMARY KEY (user_id)
)
-- En Redshift:
-- DISTSTYLE KEY
-- DISTKEY (user_id)
;

-- =========================
-- DIMENSION: PRODUCTS
-- =========================
CREATE TABLE IF NOT EXISTS dim_product (
    sku         VARCHAR(64)   NOT NULL,
    name        VARCHAR(255),
    category    VARCHAR(100),
    price       DECIMAL(12,2),
    PRIMARY KEY (sku)
)
-- En Redshift:
-- DISTSTYLE ALL
;

-- =========================
-- FACT TABLE: ORDERS
-- =========================
CREATE TABLE IF NOT EXISTS fact_order (
    order_id     VARCHAR(64)   NOT NULL,
    user_id      VARCHAR(64)   NOT NULL,
    total_amount DECIMAL(12,2),
    currency     VARCHAR(8),
    created_at   TIMESTAMP,
    PRIMARY KEY (order_id)
)
-- En Redshift:
-- DISTSTYLE KEY
-- DISTKEY (user_id)
-- SORTKEY (created_at)
;

-- =====================================================
-- Notas de diseño:
-- - Claves naturales usadas como PK (order_id, user_id, sku)
-- - fact_order:
--     - DISTKEY por user_id (joins frecuentes con dim_user)
--     - SORTKEY por created_at (queries por rango de fechas)
-- - dim_product con DISTSTYLE ALL (tabla pequeña, broadcast)
-- =====================================================
