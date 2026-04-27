-- ============================================================
-- MIGRACIÓN: Eliminar columnas de Tour Conductor de la tabla 'venta'
-- Ejecutar en Supabase > SQL Editor
-- Fecha: 2026-04-27
-- ============================================================

ALTER TABLE venta
    DROP COLUMN IF EXISTS tc_nombre,
    DROP COLUMN IF EXISTS tc_pasaporte,
    DROP COLUMN IF EXISTS tc_nacimiento,
    DROP COLUMN IF EXISTS tc_caducidad_pas,
    DROP COLUMN IF EXISTS tc_contacto_emergencia,
    DROP COLUMN IF EXISTS tc_tel_emergencia,
    DROP COLUMN IF EXISTS tc_vuelo_inter,
    DROP COLUMN IF EXISTS tc_correo;
