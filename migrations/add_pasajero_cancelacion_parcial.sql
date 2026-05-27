-- Cancelación parcial: estado por pasajero dentro de una misma venta/paquete
ALTER TABLE pasajero
    ADD COLUMN IF NOT EXISTS estado_pasajero VARCHAR(20) DEFAULT 'ACTIVO'
        CHECK (estado_pasajero IN ('ACTIVO', 'CANCELADO'));

ALTER TABLE pasajero
    ADD COLUMN IF NOT EXISTS fecha_cancelacion TIMESTAMP WITH TIME ZONE;

ALTER TABLE pasajero
    ADD COLUMN IF NOT EXISTS monto_reembolso_pax DECIMAL(10,2);

ALTER TABLE pasajero
    ADD COLUMN IF NOT EXISTS observaciones_cancelacion TEXT;

COMMENT ON COLUMN pasajero.estado_pasajero IS 'ACTIVO = sigue en el viaje; CANCELADO = baja parcial del grupo';
