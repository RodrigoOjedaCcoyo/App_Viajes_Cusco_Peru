-- Migración: Cotizaciones de Costos (Cotizador interno de Operaciones)

CREATE TABLE IF NOT EXISTS cotizacion_costos (
    id_cotizacion UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    creado_por TEXT,
    items JSONB NOT NULL DEFAULT '[]', -- Lista de líneas: tipo_servicio, proveedor, tarifa, pax, subtotal
    moneda VARCHAR(10) DEFAULT 'USD',
    total_estimado DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
