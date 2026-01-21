-- Migración para Proveedores (Operadores/Endosos)

CREATE TABLE IF NOT EXISTS proveedor (
    id_proveedor SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    tipo_servicio VARCHAR(100), -- 'HOTEL', 'TRANSPORTE', 'GUIA', 'RESTAURANTE'
    celular VARCHAR(50),
    email VARCHAR(100),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar proveedores de ejemplo
INSERT INTO proveedor (nombre, tipo_servicio) VALUES 
('Hotel Cusco Plaza', 'HOTEL'),
('Transportes El Inka', 'TRANSPORTE'),
('Restaurante Tunupa', 'RESTAURANTE'),
('Guía Juan Perez', 'GUIA');

-- Agregar columna a venta_tour para asignar proveedor
ALTER TABLE venta_tour ADD COLUMN IF NOT EXISTS id_proveedor INTEGER REFERENCES proveedor(id_proveedor);
