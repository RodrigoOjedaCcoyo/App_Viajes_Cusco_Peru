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

-- Datos de ejemplo iniciales
INSERT INTO comunicado (titulo, mensaje, nivel, autor_area, area_destino) VALUES
  ('Bienvenidos al Tablero de Anuncios', 'Este es un canal para que todas las áreas se comuniquen alertas, problemas e incidencias importantes.', 'INFO', 'GERENCIA', 'TODOS');
