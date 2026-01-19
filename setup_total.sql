-- ==============================================================
-- SETUP TOTAL (SIMPLIFICADO): APP VIAJES CUSCO PERÚ
-- ==============================================================
-- Instrucciones: 
-- 1. Borra todas las tablas actuales (DROP SCHEMA public CASCADE; CREATE SCHEMA public;)
-- 2. Pega este código completo en el SQL Editor de Supabase y correlo.
-- ==============================================================

-- --------------------------------------------------------------
-- 1. DEFINICIÓN DE TABLAS
-- --------------------------------------------------------------

-- ACCESO Y ROLES (Basado en Email)
CREATE TABLE usuarios_app (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL -- 'VENTAS', 'OPERACIONES', 'CONTABLE', 'GERENCIA'
);

-- NÚCLEO COMERCIAL
CREATE TABLE vendedor (
    id_vendedor SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100), -- Informativo
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

-- --------------------------------------------------------------
-- 2. DATOS INICIALES (SEMILLAS)
-- --------------------------------------------------------------

-- Configura aquí tu cuenta general/maestra
INSERT INTO usuarios_app (email, rol) VALUES 
('TU_CORREO_MAESTRO@gmail.com', 'GERENCIA'); -- REEMPLAZAR CON TU EMAIL REAL

-- Usuarios de Acceso (Los que inician sesión)
INSERT INTO usuarios_app (email, rol) VALUES 
('ventas@agencia.com', 'VENTAS'),
('operaciones@agencia.com', 'OPERACIONES'),
('contabilidad@agencia.com', 'CONTABILIDAD'),
('gerencia@agencia.com', 'GERENCIA');

-- Vendedores (Nombres para las listas desplegables)
INSERT INTO vendedor (nombre, email) VALUES 
('Angel', 'angel@agencia.com'),
('Abel', 'abel@agencia.com'),
('Admin', 'admin@agencia.com');
('Admin', 'admin@agencia.com');

-- Tours Básicos
INSERT INTO tour (nombre, descripcion, duracion_horas, precio_base_usd) VALUES 
('Machu Picchu Full Day', 'Visita a la ciudadela inca', 15, 250.00),
('City Tour Cusco', 'Catedral, Qoricancha y ruinas aledañas', 5, 20.00),
('Valle Sagrado VIP', 'Pisac, Ollantaytambo y Chinchero', 10, 50.00);

-- Guías
INSERT INTO guia (nombre, idioma, telefono) VALUES 
('Juan Guía', 'Español/Inglés', '987654321'),
('María Guide', 'Inglés/Francés', '912345678');

-- --------------------------------------------------------------
-- 3. SEGURIDAD Y PERMISOS (BÁSICO PARA TEST)
-- --------------------------------------------------------------

-- Habilitar RLS en todas las tablas
DO $$ 
DECLARE 
    t text;
BEGIN
    FOR t IN SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' 
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', t);
        EXECUTE format('CREATE POLICY "Acceso total" ON %I FOR ALL USING (true) WITH CHECK (true);', t);
    END LOOP;
END $$;

-- --------------------------------------------------------------
-- 4. STORAGE RLS (POLITICAS)
-- --------------------------------------------------------------
-- Asegurarse de que los buckets 'itinerarios' y 'vouchers' existan en la UI de Supabase

CREATE POLICY "Acceso Público Itinerarios" ON storage.objects FOR SELECT USING (bucket_id = 'itinerarios');
CREATE POLICY "Subida Libre Itinerarios" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'itinerarios');

CREATE POLICY "Acceso Público Vouchers" ON storage.objects FOR SELECT USING (bucket_id = 'vouchers');
CREATE POLICY "Subida Libre Vouchers" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'vouchers');
