-- Migración para crear la tabla meta_mensual
CREATE TABLE IF NOT EXISTS public.meta_mensual (
    id_meta SERIAL PRIMARY KEY,
    periodo VARCHAR(7) UNIQUE NOT NULL, -- Formato "AAAA-MM" (Ej: "2026-05")
    monto_meta NUMERIC(12, 2) NOT NULL DEFAULT 10000.0,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Comentario para documentación
COMMENT ON TABLE public.meta_mensual IS 'Almacena las metas de ventas B2C congeladas por cada mes/año.';
