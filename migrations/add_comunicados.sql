-- Migración: Tablero de Comunicados Internos (Alertas entre Áreas)
-- Ejecutar en el SQL Editor de Supabase

-- Si ya existe la versión anterior, la eliminamos para aplicar los nuevos cambios limpios
DROP TABLE IF EXISTS comunicado;

CREATE TABLE comunicado (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    nivel TEXT NOT NULL DEFAULT 'INFO',               -- 'URGENTE', 'AVISO', 'INFO'
    autor_area TEXT NOT NULL,                         -- 'VENTAS', 'OPERACIONES', 'CONTABILIDAD', 'GERENCIA'
    area_destino TEXT NOT NULL,                       -- 'VENTAS', 'OPERACIONES', 'CONTABILIDAD', 'GERENCIA', 'TODOS'
    activo BOOLEAN DEFAULT TRUE,
    leido_ventas BOOLEAN DEFAULT FALSE,
    leido_operaciones BOOLEAN DEFAULT FALSE,
    leido_contabilidad BOOLEAN DEFAULT FALSE,
    leido_gerencia BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_expiracion DATE
);

-- Índice para consultas rápidas
CREATE INDEX idx_comunicado_activo_destino ON comunicado(activo, area_destino);

-- ── SEGURIDAD (RLS) ──
-- Deshabilitar RLS para permitir accesos directos desde la API anon/authenticated
ALTER TABLE comunicado DISABLE ROW LEVEL SECURITY;

-- Por si acaso RLS se activa en el futuro, creamos las políticas permisivas para lectura, escritura y actualización:
DROP POLICY IF EXISTS "Permitir select público" ON comunicado;
DROP POLICY IF EXISTS "Permitir insert público" ON comunicado;
DROP POLICY IF EXISTS "Permitir update público" ON comunicado;

CREATE POLICY "Permitir select público" ON comunicado FOR SELECT USING (true);
CREATE POLICY "Permitir insert público" ON comunicado FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir update público" ON comunicado FOR UPDATE USING (true) WITH CHECK (true);

-- Datos de ejemplo iniciales
INSERT INTO comunicado (titulo, mensaje, nivel, autor_area, area_destino) VALUES
  ('Bienvenidos al Tablero de Anuncios', 'Este es un canal para que todas las áreas se comuniquen alertas, problemas e incidencias importantes.', 'INFO', 'GERENCIA', 'TODOS');
