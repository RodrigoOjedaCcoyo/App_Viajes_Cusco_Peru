-- Migración para soportar multimoneda en pagos
-- Ejecutar este script en el SQL Editor de Supabase

ALTER TABLE pago 
ADD COLUMN IF NOT EXISTS tasa_cambio DECIMAL(10,4) DEFAULT 1;

ALTER TABLE pago 
ADD COLUMN IF NOT EXISTS monto_moneda_venta DECIMAL(10,2);

-- Actualizar registros existentes para que no tengan nulos (asumiendo que eran en la misma moneda)
UPDATE pago 
SET monto_moneda_venta = monto_pagado 
WHERE monto_moneda_venta IS NULL;

-- Asegurar que la columna sea NOT NULL después de la actualización
ALTER TABLE pago 
ALTER COLUMN monto_moneda_venta SET NOT NULL;

COMMENT ON COLUMN pago.tasa_cambio IS 'Tipo de cambio usado para este pago (Moneda Pago a Moneda Venta)';
COMMENT ON COLUMN pago.monto_moneda_venta IS 'Equivalente del pago en la moneda original de la venta';
