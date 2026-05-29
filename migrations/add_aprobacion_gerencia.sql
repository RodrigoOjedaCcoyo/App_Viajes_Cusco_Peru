-- Migración: Agregar campos de aprobación de Gerencia a la tabla venta
-- Ejecutar en el SQL Editor de Supabase

ALTER TABLE public.venta 
  ADD COLUMN IF NOT EXISTS aprobado_gerencia BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS fecha_aprobacion_gerencia DATE;

COMMENT ON COLUMN public.venta.aprobado_gerencia IS 'True cuando Gerencia revisó y aprobó la operación del pasajero. Cambia el color del tablero a Gris (⬜).';
COMMENT ON COLUMN public.venta.fecha_aprobacion_gerencia IS 'Fecha en que Gerencia marcó la aprobación del pasajero.';
