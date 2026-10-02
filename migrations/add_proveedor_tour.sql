-- =====================================================================================
-- Proveedores por tour: costo operativo + inclusiones de cada proveedor para cada tour.
-- Base del "proveedor por día" del Constructor de Itinerarios y del Directorio de
-- Operaciones (los dos sistemas leen y escriben esta MISMA tabla).
--
-- Cómo ejecutarlo: Supabase → SQL Editor → pegar todo este archivo → Run.
-- Es seguro ejecutarlo más de una vez (no duplica datos ni borra nada).
-- =====================================================================================

CREATE EXTENSION IF NOT EXISTS unaccent;

-- -------------------------------------------------------------------------------------
-- 1. Tabla de ofertas proveedor ↔ tour
-- -------------------------------------------------------------------------------------
-- Monedas (igual que el Constructor): *_nac en SOLES, *_ext y *_can en DÓLARES.
-- modalidad:
--   'PAX'   → los costos son por pasajero (tour compartido / endose).
--   'GRUPO' → costo_grupo_* es el precio de UNA unidad (van, guía privado) para hasta
--             capacidad_grupo pasajeros; el Constructor calcula cuántas unidades se
--             necesitan y lo reparte por pasajero.
-- Precios de estudiante / niño / PcD: NULL = se calculan con las reglas de siempre
--   (estudiante y PcD = adulto − 70 nac / − 20 ext; niño = adulto − 40 nac / − 15 ext).
CREATE TABLE IF NOT EXISTS proveedor_tour (
    id_proveedor_tour BIGSERIAL PRIMARY KEY,
    id_proveedor INTEGER NOT NULL REFERENCES proveedor(id_proveedor) ON DELETE CASCADE,
    id_tour INTEGER NOT NULL REFERENCES tour(id_tour) ON DELETE CASCADE,
    modalidad VARCHAR(10) NOT NULL DEFAULT 'PAX' CHECK (modalidad IN ('PAX', 'GRUPO')),

    costo_adulto_nac DECIMAL(10,2) NOT NULL DEFAULT 0,
    costo_adulto_ext DECIMAL(10,2) NOT NULL DEFAULT 0,
    costo_adulto_can DECIMAL(10,2) NOT NULL DEFAULT 0,
    costo_estudiante_nac DECIMAL(10,2),
    costo_estudiante_ext DECIMAL(10,2),
    costo_estudiante_can DECIMAL(10,2),
    costo_nino_nac DECIMAL(10,2),
    costo_nino_ext DECIMAL(10,2),
    costo_nino_can DECIMAL(10,2),
    costo_pcd_nac DECIMAL(10,2),
    costo_pcd_ext DECIMAL(10,2),
    costo_pcd_can DECIMAL(10,2),

    costo_grupo_nac DECIMAL(10,2),
    costo_grupo_ext DECIMAL(10,2),
    capacidad_grupo INTEGER CHECK (capacidad_grupo IS NULL OR capacidad_grupo > 0),

    incluye JSONB NOT NULL DEFAULT '[]',     -- ["Recojo del hotel", "Almuerzo", ...]
    no_incluye JSONB NOT NULL DEFAULT '[]',
    hora_recojo VARCHAR(20),                 -- "04:00 AM"
    notas TEXT,

    preferido BOOLEAN NOT NULL DEFAULT FALSE,
    vigente_desde DATE,
    vigente_hasta DATE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT proveedor_tour_unico UNIQUE (id_proveedor, id_tour)
);

CREATE INDEX IF NOT EXISTS idx_proveedor_tour_tour ON proveedor_tour(id_tour);
CREATE INDEX IF NOT EXISTS idx_proveedor_tour_proveedor ON proveedor_tour(id_proveedor);
-- Un solo proveedor preferido (activo) por tour.
CREATE UNIQUE INDEX IF NOT EXISTS proveedor_tour_un_preferido
    ON proveedor_tour(id_tour) WHERE preferido AND activo;

CREATE OR REPLACE FUNCTION proveedor_tour_touch() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_proveedor_tour_touch ON proveedor_tour;
CREATE TRIGGER trg_proveedor_tour_touch BEFORE UPDATE ON proveedor_tour
    FOR EACH ROW EXECUTE FUNCTION proveedor_tour_touch();

-- Mismos permisos que el resto de tablas del sistema (ver nota de seguridad al final).
ALTER TABLE proveedor_tour ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Acceso total" ON proveedor_tour;
CREATE POLICY "Acceso total" ON proveedor_tour FOR ALL USING (true) WITH CHECK (true);

-- -------------------------------------------------------------------------------------
-- 2. Cotizador de Costos: guardar los totales por moneda (antes se sumaban USD + PEN)
-- -------------------------------------------------------------------------------------
ALTER TABLE cotizacion_costos ADD COLUMN IF NOT EXISTS totales_por_moneda JSONB DEFAULT '{}';

-- -------------------------------------------------------------------------------------
-- 3. Pasar las tarifas de ENDOSE del tarifario (JSON) a la tabla nueva
--    Solo se vinculan las que coinciden CLARAMENTE con un tour del catálogo
--    (mismo nombre sin tildes, mayúsculas ni signos). Las demás quedan en el
--    tarifario marcadas "sin vincular" para hacerlo a mano desde el Directorio.
-- -------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION norm_nombre_tour(t TEXT) RETURNS TEXT AS $$
    SELECT trim(regexp_replace(lower(unaccent(coalesce(t, ''))), '[^a-z0-9]+', ' ', 'g'));
$$ LANGUAGE sql IMMUTABLE;

WITH items AS (
    SELECT p.id_proveedor, e.item, e.idx
    FROM proveedor p
    CROSS JOIN LATERAL jsonb_array_elements(coalesce(p.tarifario, '[]'::jsonb)) WITH ORDINALITY AS e(item, idx)
    WHERE upper(e.item->>'tipo_servicio') = 'ENDOSE'
),
tours_unicos AS (
    -- Solo nombres que identifican a UN tour (si hay duplicados, no se adivina).
    SELECT norm_nombre_tour(nombre) AS n, min(id_tour) AS id_tour
    FROM tour
    GROUP BY norm_nombre_tour(nombre)
    HAVING count(*) = 1
),
coincidencias AS (
    SELECT i.id_proveedor, t.id_tour, i.item
    FROM items i
    JOIN tours_unicos t ON t.n = norm_nombre_tour(i.item->>'nombre')
)
INSERT INTO proveedor_tour (id_proveedor, id_tour, modalidad,
                            costo_adulto_nac, costo_adulto_ext, costo_adulto_can,
                            incluye, notas)
SELECT DISTINCT ON (c.id_proveedor, c.id_tour)
       c.id_proveedor,
       c.id_tour,
       CASE WHEN c.item->>'unidad' = 'Por Grupo' THEN 'GRUPO' ELSE 'PAX' END,
       CASE WHEN upper(coalesce(c.item->>'moneda', 'USD')) = 'PEN' THEN coalesce((c.item->>'precio')::numeric, 0) ELSE 0 END,
       CASE WHEN upper(coalesce(c.item->>'moneda', 'USD')) <> 'PEN' THEN coalesce((c.item->>'precio')::numeric, 0) ELSE 0 END,
       CASE WHEN upper(coalesce(c.item->>'moneda', 'USD')) <> 'PEN' THEN coalesce((c.item->>'precio')::numeric, 0) ELSE 0 END,
       CASE WHEN coalesce(c.item->>'incluye', '') <> ''
            THEN to_jsonb(regexp_split_to_array(c.item->>'incluye', '\s*[,+\n]\s*'))
            ELSE '[]'::jsonb END,
       nullif(c.item->>'notas', '')
FROM coincidencias c
ON CONFLICT (id_proveedor, id_tour) DO NOTHING;

-- Para GRUPO, el precio migrado es el de la unidad completa.
UPDATE proveedor_tour
SET costo_grupo_nac = CASE WHEN costo_adulto_nac > 0 THEN costo_adulto_nac END,
    costo_grupo_ext = CASE WHEN costo_adulto_ext > 0 THEN costo_adulto_ext END,
    capacidad_grupo = coalesce(capacidad_grupo, 1)
WHERE modalidad = 'GRUPO' AND costo_grupo_nac IS NULL AND costo_grupo_ext IS NULL;

-- Quitar del tarifario JSON las tarifas ENDOSE que ya quedaron en la tabla nueva.
UPDATE proveedor p
SET tarifario = coalesce((
        SELECT jsonb_agg(e.item ORDER BY e.idx)
        FROM jsonb_array_elements(p.tarifario) WITH ORDINALITY AS e(item, idx)
        WHERE NOT (
            upper(e.item->>'tipo_servicio') = 'ENDOSE'
            AND EXISTS (
                SELECT 1 FROM proveedor_tour pt JOIN tour t ON t.id_tour = pt.id_tour
                WHERE pt.id_proveedor = p.id_proveedor
                  AND norm_nombre_tour(t.nombre) = norm_nombre_tour(e.item->>'nombre')
            )
        )
    ), '[]'::jsonb)
WHERE p.tarifario IS NOT NULL AND jsonb_typeof(p.tarifario) = 'array';

-- "Tours que opera" (usado por el Cotizador) = tours con oferta activa.
UPDATE proveedor p
SET tours_opera = coalesce((SELECT array_agg(DISTINCT pt.id_tour) FROM proveedor_tour pt
                            WHERE pt.id_proveedor = p.id_proveedor AND pt.activo), '{}')
WHERE EXISTS (SELECT 1 FROM proveedor_tour pt WHERE pt.id_proveedor = p.id_proveedor);

-- -------------------------------------------------------------------------------------
-- 4. Revisión: tarifas de ENDOSE que NO se pudieron vincular (hacerlo a mano en el
--    Directorio de Proveedores → "Vincular a tour").
-- -------------------------------------------------------------------------------------
SELECT p.nombre_comercial AS proveedor, e.item->>'nombre' AS tarifa_sin_vincular
FROM proveedor p
CROSS JOIN LATERAL jsonb_array_elements(coalesce(p.tarifario, '[]'::jsonb)) AS e(item)
WHERE upper(e.item->>'tipo_servicio') = 'ENDOSE'
ORDER BY 1, 2;

-- -------------------------------------------------------------------------------------
-- NOTA DE SEGURIDAD (pendiente, no se cambia aquí para no romper Operaciones):
-- Todas las tablas usan la política "Acceso total" (USING true). Como la clave anon
-- es pública en el Constructor (va en el navegador), cualquiera con esa clave podría
-- leer/escribir directamente en la base. Lo correcto es limitar las políticas al rol
-- "authenticated", pero antes hay que cambiar Operaciones para que cada usuario tenga
-- su propia sesión (hoy comparte un solo cliente de Supabase entre todos).
-- =====================================================================================
