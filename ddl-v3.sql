-- ==============================================================================
-- DDL v3 - Tabla unificada de ventas - Casa Matriz (Asunción)
-- Cátedra: Procesamiento de Datos (UCOM)
-- ==============================================================================
-- Idempotente: puede ejecutarse varias veces sin romper la estructura existente.

CREATE TABLE IF NOT EXISTS ventas_locales (
    id              SERIAL PRIMARY KEY,
    invoice_no      VARCHAR(20)     NOT NULL,
    stock_code      VARCHAR(20),
    description     VARCHAR(255),
    quantity        INTEGER         NOT NULL,
    invoice_date    TIMESTAMP,
    unit_price      NUMERIC(10, 2)  NOT NULL,
    customer_id     VARCHAR(20),
    country         VARCHAR(100),
    sucursal        VARCHAR(50)     NOT NULL,
    insertado_en    TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Índices de apoyo para las consultas de auditoría por sucursal y por fecha
CREATE INDEX IF NOT EXISTS idx_ventas_sucursal ON ventas_locales (sucursal);
CREATE INDEX IF NOT EXISTS idx_ventas_invoice ON ventas_locales (invoice_no);

-- Verificación rápida de la estructura creada
\d ventas_locales
