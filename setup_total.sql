-- ==============================================================
-- SETUP TOTAL: APP VIAJES CUSCO PERÚ (PRODUCCIÓN/TEST)
-- Pegar este código en el SQL Editor de Supabase
-- ==============================================================

-- --------------------------------------------------------------
-- 1. LIMPIEZA DE TABLAS (OPCIONAL - USAR CON CUIDADO)
-- --------------------------------------------------------------
-- DROP TABLE IF EXISTS requerimiento, asignacion_guia, guia, documentacion, pasajero, pago, venta_tour, venta, catalogo_tours_imagenes, itinerario_digital, paquete_tour, paquete, tour, lead, vendedor_mapeo, operador_mapeo, contador_mapeo, gerente_mapeo, vendedor, cliente CASCADE;

-- --------------------------------------------------------------
-- 2. DEFINICIÓN DE TABLAS
-- --------------------------------------------------------------

-- NÚCLEO COMERCIAL
CREATE TABLE vendedor (
    id_vendedor SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    estado VARCHAR(20) DEFAULT 'ACTIVO'
);

CREATE TABLE cliente (
    id_cliente SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo_cliente VARCHAR(50) DEFAULT 'B2C',
    pais VARCHAR(100),
    genero VARCHAR(20),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lead (
    id_lead SERIAL PRIMARY KEY,
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor),
    numero_celular VARCHAR(20) NOT NULL,
    red_social VARCHAR(50),
    estado_lead VARCHAR(50) DEFAULT 'NUEVO',
    comentario TEXT,
    fecha_seguimiento DATE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    whatsapp BOOLEAN DEFAULT TRUE,
    nombre_pasajero VARCHAR(255),
    ultimo_itinerario_id UUID
);

-- CATÁLOGO
CREATE TABLE tour (
    id_tour SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    duracion_horas INTEGER,
    precio_base_usd DECIMAL(10,2)
);

CREATE TABLE paquete (
    id_paquete SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    dias INTEGER,
    noches INTEGER,
    precio_sugerido DECIMAL(10,2)
);

CREATE TABLE paquete_tour (
    id_paquete INTEGER REFERENCES paquete(id_paquete) ON DELETE CASCADE,
    id_tour INTEGER REFERENCES tour(id_tour),
    orden INTEGER NOT NULL,
    PRIMARY KEY (id_paquete, id_tour)
);

-- ITINERARIO DIGITAL
CREATE TABLE itinerario_digital (
    id_itinerario_digital UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    id_lead INTEGER REFERENCES lead(id_lead) ON DELETE SET NULL,
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor),
    nombre_pasajero_itinerario VARCHAR(255),
    datos_render JSONB,
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    url_pdf TEXT
);

CREATE TABLE catalogo_tours_imagenes (
    id_tour INTEGER REFERENCES tour(id_tour) PRIMARY KEY,
    urls_imagenes JSONB
);

-- VENTAS Y PAGOS
CREATE TABLE venta (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INTEGER REFERENCES cliente(id_cliente),
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor),
    id_itinerario_digital UUID REFERENCES itinerario_digital(id_itinerario_digital),
    id_paquete INTEGER REFERENCES paquete(id_paquete),
    fecha_venta DATE DEFAULT CURRENT_DATE,
    canal_venta VARCHAR(50),
    precio_total_cierre DECIMAL(10,2) NOT NULL,
    moneda VARCHAR(10) DEFAULT 'USD',
    estado_venta VARCHAR(50) DEFAULT 'CONFIRMADO',
    url_itinerario TEXT,
    url_comprobante_pago TEXT
);

CREATE TABLE venta_tour (
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    n_linea INTEGER NOT NULL,
    id_tour INTEGER REFERENCES tour(id_tour),
    fecha_servicio DATE NOT NULL,
    precio_applied DECIMAL(10,2),
    costo_applied DECIMAL(10,2),
    cantidad_pasajeros INTEGER DEFAULT 1,
    observaciones TEXT,
    id_itinerario_dia_index INTEGER,
    PRIMARY KEY (id_venta, n_linea)
);

CREATE TABLE pago (
    id_pago SERIAL PRIMARY KEY,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    fecha_pago DATE DEFAULT CURRENT_DATE,
    monto_pagado DECIMAL(10,2) NOT NULL,
    moneda VARCHAR(10) DEFAULT 'USD',
    metodo_pago VARCHAR(50),
    tipo_pago VARCHAR(50),
    observacion TEXT,
    url_comprobante TEXT
);

-- OPERACIONES
CREATE TABLE pasajero (
    id_pasajero SERIAL PRIMARY KEY,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    nombre_completo VARCHAR(255) NOT NULL,
    nacionalidad VARCHAR(100),
    numero_documento VARCHAR(50),
    tipo_documento VARCHAR(20),
    edad INTEGER,
    restricciones_alimentarias TEXT
);

CREATE TABLE documentacion (
    id BIGSERIAL PRIMARY KEY,
    id_pasajero INTEGER REFERENCES pasajero(id_pasajero) ON DELETE CASCADE,
    tipo_documento VARCHAR(50),
    url_archivo TEXT,
    estado_entrega VARCHAR(30) DEFAULT 'PENDIENTE',
    es_critico BOOLEAN DEFAULT FALSE
);

CREATE TABLE guia (
    id_guia SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    idioma VARCHAR(100),
    telefono VARCHAR(20),
    estado VARCHAR(20) DEFAULT 'DISPONIBLE'
);

CREATE TABLE asignacion_guia (
    id_venta INTEGER,
    n_linea INTEGER,
    id_guia INTEGER REFERENCES guia(id_guia),
    fecha_servicio DATE NOT NULL,
    PRIMARY KEY (id_venta, n_linea, id_guia),
    FOREIGN KEY (id_venta, n_linea) REFERENCES venta_tour(id_venta, n_linea)
);

CREATE TABLE requerimiento (
    id SERIAL PRIMARY KEY,
    area_solicitante VARCHAR(50),
    descripcion TEXT,
    monto_estimado DECIMAL(10,2),
    estado VARCHAR(30) DEFAULT 'PENDIENTE',
    fecha_solicitud TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- TABLA DE ACCESO UNIFICADA (Sin UUIDs técnicos)
CREATE TABLE usuarios_app (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL -- 'VENTAS', 'OPERACIONES', 'CONTABLE', 'GERENCIA'
);

-- --------------------------------------------------------------
-- 3. DATOS INICIALES (SEMILLAS DE PRUEBA)
-- --------------------------------------------------------------

-- Usuarios de Acceso
INSERT INTO usuarios_app (email, rol) VALUES 
('angel@agencia.com', 'VENTAS'),
('abel@agencia.com', 'VENTAS');

-- Vendedores
INSERT INTO vendedor (nombre, email) VALUES 
('Angel Vendedor', 'angel@agencia.com'),
('Abel Vendedor', 'abel@agencia.com');

-- Catálogo de Tours
INSERT INTO tour (nombre, descripcion, duracion_horas, precio_base_usd) VALUES 
('Machu Picchu Full Day', 'Visita a la ciudadela inca', 15, 250.00),
('City Tour Cusco', 'Catedral, Qoricancha y ruinas aledañas', 5, 20.00),
('Valle Sagrado VIP', 'Pisac, Ollantaytambo y Chinchero con almuerzo', 10, 50.00),
('Montaña de Colores', 'Trekking a Vinicunca', 12, 40.00),
('Laguna Humantay', 'Trekking a la laguna turquesa', 12, 45.00);

-- Paquetes
INSERT INTO paquete (nombre, descripcion, dias, noches, precio_sugerido) VALUES
('Cusco Clásico 4D/3N', 'Machu Picchu + Valle Sagrado + City Tour', 4, 3, 450.00);

-- Catálogo de Imágenes (URLs de ejemplo)
INSERT INTO catalogo_tours_imagenes (id_tour, urls_imagenes) VALUES 
(1, '["https://images.unsplash.com/photo-1587595431973-160d0d94add1"]'),
(2, '["https://images.unsplash.com/photo-1526392060635-9d6019884377"]');

-- Guías
INSERT INTO guia (nombre, idioma, telefono) VALUES 
('Juan Guía', 'Español/Inglés', '987654321'),
('María Guide', 'Inglés/Francés', '912345678');

-- --------------------------------------------------------------
-- 4. CONFIGURACIÓN DE SEGURIDAD (RLS)
-- --------------------------------------------------------------

-- Habilitar RLS en todas las tablas
ALTER TABLE vendedor ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead ENABLE ROW LEVEL SECURITY;
ALTER TABLE tour ENABLE ROW LEVEL SECURITY;
ALTER TABLE paquete ENABLE ROW LEVEL SECURITY;
ALTER TABLE paquete_tour ENABLE ROW LEVEL SECURITY;
ALTER TABLE itinerario_digital ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalogo_tours_imagenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE venta ENABLE ROW LEVEL SECURITY;
ALTER TABLE venta_tour ENABLE ROW LEVEL SECURITY;
ALTER TABLE pago ENABLE ROW LEVEL SECURITY;
ALTER TABLE pasajero ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE guia ENABLE ROW LEVEL SECURITY;
ALTER TABLE asignacion_guia ENABLE ROW LEVEL SECURITY;
ALTER TABLE requerimiento ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendedor_mapeo ENABLE ROW LEVEL SECURITY;
ALTER TABLE operador_mapeo ENABLE ROW LEVEL SECURITY;
ALTER TABLE contador_mapeo ENABLE ROW LEVEL SECURITY;
ALTER TABLE gerente_mapeo ENABLE ROW LEVEL SECURITY;

-- Crear política de acceso total para pruebas (ANON y AUTHENTICATED)
-- NOTA: En producción real, estas políticas deben ser más restrictivas.
DO $$ 
DECLARE 
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
    LOOP
        EXECUTE format('CREATE POLICY "Acceso total para pruebas" ON %I FOR ALL USING (true) WITH CHECK (true);', t);
    END LOOP;
END $$;

-- --------------------------------------------------------------
-- 5. STORAGE (INSTRUCCIONES)
-- --------------------------------------------------------------
-- Debes crear manualmente estos Buckets en Supabase UI (Storage):
-- 1. "itinerarios" (Público)
-- 2. "vouchers" (Público)
-- 3. "documentos" (Privado)

-- --------------------------------------------------------------
-- 6. PERMISOS DE STORAGE (SQL) - ACCESO TOTAL PARA PRUEBAS
-- --------------------------------------------------------------
-- Nota: En Supabase, las políticas de Storage se aplican a 'storage.objects'

-- 1. Políticas para el bucket 'itinerarios'
CREATE POLICY "Acceso Público Itinerarios" ON storage.objects FOR SELECT USING (bucket_id = 'itinerarios');
CREATE POLICY "Subida Libre Itinerarios" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'itinerarios');

-- 2. Políticas para el bucket 'vouchers'
CREATE POLICY "Acceso Público Vouchers" ON storage.objects FOR SELECT USING (bucket_id = 'vouchers');
CREATE POLICY "Subida Libre Vouchers" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'vouchers');

-- 3. Políticas para el bucket 'documentos'
CREATE POLICY "Acceso Privado Documentos" ON storage.objects FOR SELECT USING (bucket_id = 'documentos');
CREATE POLICY "Subida Libre Documentos" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'documentos');
