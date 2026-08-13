-- Migración: Tarifario de Servicios y Tours que Opera, por proveedor

-- Lista de precios del proveedor (una fila por servicio/precio ofrecido).
-- Cada elemento: {id, tipo_servicio, nombre, moneda, unidad, notas, ...campos según tipo}
ALTER TABLE proveedor ADD COLUMN IF NOT EXISTS tarifario JSONB DEFAULT '[]';

-- IDs de la tabla `tour` que este proveedor puede operar (para filtrar en el futuro Cotizador).
ALTER TABLE proveedor ADD COLUMN IF NOT EXISTS tours_opera INTEGER[] DEFAULT '{}';
