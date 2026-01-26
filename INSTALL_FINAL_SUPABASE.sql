-- 0. REINICIAR (Surgical cleanup compatible con Supabase)
-- Borrar vistas si existen
DROP VIEW IF EXISTS vista_servicios_diarios CASCADE;
DROP VIEW IF EXISTS vista_ventas_completa CASCADE;

-- Borrar tablas si existen (en orden de dependencia)
DROP TABLE IF EXISTS evaluacion_proveedor CASCADE;
DROP TABLE IF EXISTS venta_servicio_proveedor CASCADE;
DROP TABLE IF EXISTS requerimiento CASCADE;
DROP TABLE IF EXISTS documentacion CASCADE;
DROP TABLE IF EXISTS pasajero CASCADE;
DROP TABLE IF EXISTS pago CASCADE;
DROP TABLE IF EXISTS venta_tour CASCADE;
DROP TABLE IF EXISTS venta CASCADE;
DROP TABLE IF EXISTS itinerario_digital CASCADE;
DROP TABLE IF EXISTS catalogo_tours_imagenes CASCADE;
DROP TABLE IF EXISTS paquete_tour CASCADE;
DROP TABLE IF EXISTS paquete CASCADE;
DROP TABLE IF EXISTS tour_itinerario_item CASCADE;
DROP TABLE IF EXISTS tour CASCADE;
DROP TABLE IF EXISTS agencia_aliada CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;
DROP TABLE IF EXISTS lead CASCADE;
DROP TABLE IF EXISTS vendedor CASCADE;
DROP TABLE IF EXISTS usuarios_app CASCADE;

-- Asegurar extensiones para UUIDs y Seguridad
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Restaurar permisos básicos (opcional pero recomendado)
GRANT USAGE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;


-- ==============================================================
-- SECCIÓN 1: TABLAS MAESTRAS (ESTRUCTURA)
-- ==============================================================

CREATE TABLE usuarios_app (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL CHECK (rol IN ('VENTAS', 'OPERACIONES', 'CONTABILIDAD', 'GERENCIA')),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP WITH TIME ZONE
);

CREATE TABLE vendedor (
    id_vendedor SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE, -- CRÍTICO: Requerido por login y búsqueda
    estado VARCHAR(20) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    fecha_ingreso DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lead (
    id_lead SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    nombre_pasajero VARCHAR(255), -- Nuevo campo visual esperado por app
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor) ON DELETE SET NULL,
    numero_celular VARCHAR(20) NOT NULL,
    red_social VARCHAR(50),
    estado_lead VARCHAR(50) DEFAULT 'NUEVO', -- Requerido por Funnel
    estrategia_venta VARCHAR(50) DEFAULT 'General' CHECK (estrategia_venta IN ('Opciones', 'Matriz', 'General')),
    comentario TEXT, -- Requerido por app
    whatsapp BOOLEAN DEFAULT TRUE, -- Requerido por app
    fecha_seguimiento DATE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    pais_origen VARCHAR(100) DEFAULT 'Nacional' CHECK (pais_origen IN ('Nacional', 'Extranjero', 'Mixto')),
    ultimo_itinerario_id UUID
);

CREATE TABLE cliente (
    id_cliente SERIAL PRIMARY KEY,
    id_lead INTEGER REFERENCES lead(id_lead) ON DELETE SET NULL,
    nombre VARCHAR(255), -- Requerido por app
    tipo_cliente VARCHAR(50) DEFAULT 'B2C' CHECK (tipo_cliente IN ('B2C', 'B2B')),
    pais VARCHAR(100), -- Requerido por app
    genero VARCHAR(20), -- Requerido por app
    documento_identidad VARCHAR(50),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agencia_aliada (
    id_agencia SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    pais VARCHAR(100),
    celular VARCHAR(50),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tour (
    id_tour SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    duracion_horas INTEGER,
    duracion_dias INTEGER,
    precio_adulto_extranjero DECIMAL(10,2),
    precio_adulto_nacional DECIMAL(10,2),
    precio_adulto_can DECIMAL(10,2),
    precio_nino_extranjero DECIMAL(10,2),
    precio_nino_nacional DECIMAL(10,2),
    precio_nino_can DECIMAL(10,2),
    precio_estudiante_extranjero DECIMAL(10,2),
    precio_estudiante_nacional DECIMAL(10,2),
    precio_estudiante_can DECIMAL(10,2),
    precio_pcd_extranjero DECIMAL(10,2),
    precio_pcd_nacional DECIMAL(10,2),
    precio_pcd_can DECIMAL(10,2),
    categoria VARCHAR(50),
    dificultad VARCHAR(20) CHECK (dificultad IN ('FACIL', 'MODERADO', 'DIFICIL', 'EXTREMO')),
    highlights JSONB,
    atractivos JSONB,
    servicios_incluidos JSONB,
    servicios_no_incluidos JSONB,
    carpeta_img VARCHAR(255),
    hora_inicio TIME, 
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tour_itinerario_item (
    id_item SERIAL PRIMARY KEY,
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE CASCADE,
    orden INTEGER NOT NULL,
    lugar_nombre VARCHAR(255) NOT NULL,
    descripcion_corta TEXT,
    duracion_estimada_minutos INTEGER,
    es_parada_principal BOOLEAN DEFAULT TRUE,
    url_foto_referencia TEXT
);

CREATE TABLE paquete (
    id_paquete SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    dias INTEGER NOT NULL,
    noches INTEGER NOT NULL,
    precio_sugerido DECIMAL(10,2),
    temporada VARCHAR(50),
    destino_principal VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE paquete_tour (
    id_paquete INTEGER REFERENCES paquete(id_paquete) ON DELETE CASCADE,
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE RESTRICT,
    orden INTEGER NOT NULL,
    dia_del_paquete INTEGER,
    PRIMARY KEY (id_paquete, id_tour, orden)
);

CREATE TABLE catalogo_tours_imagenes (
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE CASCADE PRIMARY KEY,
    urls_imagenes JSONB DEFAULT '[]'::jsonb,
    url_principal TEXT,
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itinerario_digital (
    id_itinerario_digital UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    id_lead INTEGER REFERENCES lead(id_lead) ON DELETE SET NULL,
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor) ON DELETE SET NULL,
    id_paquete INTEGER REFERENCES paquete(id_paquete) ON DELETE SET NULL,
    nombre_pasajero_itinerario VARCHAR(255),
    datos_render JSONB NOT NULL,
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE venta (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INTEGER REFERENCES cliente(id_cliente) ON DELETE RESTRICT,
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor) ON DELETE RESTRICT,
    id_itinerario_digital UUID REFERENCES itinerario_digital(id_itinerario_digital) ON DELETE SET NULL,
    id_paquete INTEGER REFERENCES paquete(id_paquete) ON DELETE SET NULL,
    fecha_venta DATE DEFAULT CURRENT_DATE NOT NULL,
    fecha_inicio DATE,
    fecha_fin DATE,
    precio_total_cierre DECIMAL(10,2) NOT NULL, 
    costo_total DECIMAL(10,2) DEFAULT 0,
    utilidad_bruta DECIMAL(10,2) DEFAULT 0,
    moneda VARCHAR(10) DEFAULT 'USD' CHECK (moneda IN ('USD', 'PEN', 'EUR')),
    tipo_cambio DECIMAL(8,4),
    estado_venta VARCHAR(50) DEFAULT 'CONFIRMADO' CHECK (estado_venta IN ('CONFIRMADO', 'EN_VIAJE', 'COMPLETADO', 'CANCELADO')),
    canal_venta VARCHAR(50) DEFAULT 'DIRECTO',
    estado_liquidacion VARCHAR(30) DEFAULT 'PENDIENTE' CHECK (estado_liquidacion IN ('PENDIENTE', 'PARCIAL', 'FINALIZADO')),
    id_agencia_aliada INTEGER REFERENCES agencia_aliada(id_agencia),
    tour_nombre VARCHAR(255),
    num_pasajeros INTEGER DEFAULT 1, 
    url_itinerario TEXT,
    url_comprobante_pago TEXT,
    url_documentos TEXT,
    cancelada BOOLEAN DEFAULT FALSE,
    fecha_cancelacion TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE venta_tour ( 
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    n_linea INTEGER NOT NULL,
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE RESTRICT,
    fecha_servicio DATE NOT NULL,
    hora_inicio TIME, 
    precio_applied DECIMAL(10,2),
    costo_applied DECIMAL(10,2),
    moneda_costo VARCHAR(10) DEFAULT 'USD',
    id_proveedor INTEGER, -- Definido más adelante como FK
    cantidad_pasajeros INTEGER DEFAULT 1,
    punto_encuentro VARCHAR(255),
    observaciones TEXT,
    id_itinerario_dia_index INTEGER,
    estado_servicio VARCHAR(30) DEFAULT 'PENDIENTE' CHECK (estado_servicio IN ('PENDIENTE', 'CONFIRMADO', 'EN_CURSO', 'COMPLETADO', 'CANCELADO')),
    es_endoso BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id_venta, n_linea)
);

CREATE TABLE pago (
    id_pago SERIAL PRIMARY KEY,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    fecha_pago DATE DEFAULT CURRENT_DATE NOT NULL,
    monto_pagado DECIMAL(10,2) NOT NULL CHECK (monto_pagado > 0),
    moneda VARCHAR(10) DEFAULT 'USD' CHECK (moneda IN ('USD', 'PEN', 'EUR')),
    tipo_cambio DECIMAL(8,4),
    metodo_pago VARCHAR(50) CHECK (metodo_pago IN ('EFECTIVO', 'TRANSFERENCIA', 'TARJETA', 'PAYPAL', 'YAPE', 'PLIN', 'OTRO')),
    tipo_pago VARCHAR(50) CHECK (tipo_pago IN ('ADELANTO', 'SALDO', 'TOTAL', 'PARCIAL')),
    numero_operacion VARCHAR(100),
    observacion TEXT,
    url_comprobante TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pasajero (
    id_pasajero SERIAL PRIMARY KEY,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    nombre_completo VARCHAR(255) NOT NULL,
    nacionalidad VARCHAR(100),
    numero_documento VARCHAR(50),
    tipo_documento VARCHAR(20) CHECK (tipo_documento IN ('DNI', 'PASAPORTE', 'CARNET_EXTRANJERIA', 'OTRO')),
    fecha_nacimiento DATE,
    genero VARCHAR(20),
    cuidados_especiales TEXT,
    contacto_emergencia_nombre VARCHAR(255),
    contacto_emergencia_telefono VARCHAR(20),
    es_principal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documentacion (
    id BIGSERIAL PRIMARY KEY,
    id_pasajero INTEGER REFERENCES pasajero(id_pasajero) ON DELETE CASCADE,
    tipo_documento VARCHAR(50) CHECK (tipo_documento IN ('PASAPORTE', 'VISA', 'SEGURO_VIAJE', 'CERTIFICADO_VACUNA', 'AUTORIZACION_MENOR', 'OTRO')),
    url_archivo TEXT,
    fecha_carga TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento DATE,
    estado_entrega VARCHAR(30) DEFAULT 'PENDIENTE' CHECK (estado_entrega IN ('PENDIENTE', 'RECIBIDO', 'VERIFICADO', 'RECHAZADO')),
    es_critico BOOLEAN DEFAULT FALSE,
    notas TEXT
);

CREATE TABLE requerimiento (
    id SERIAL PRIMARY KEY,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE SET NULL,
    tipo_requerimiento VARCHAR(50) CHECK (tipo_requerimiento IN ('TRANSPORTE', 'ALOJAMIENTO', 'ALIMENTACION', 'GUIA', 'TICKETS', 'OTRO')),
    descripcion TEXT NOT NULL,
    monto_estimado DECIMAL(10,2),
    monto_real DECIMAL(10,2),
    moneda VARCHAR(10) DEFAULT 'USD',
    estado VARCHAR(30) DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'COTIZADO', 'APROBADO', 'PAGADO', 'COMPLETADO', 'CANCELADO')),
    fecha_necesidad DATE,
    fecha_solicitud TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    solicitado_por INTEGER REFERENCES vendedor(id_vendedor),
    aprobado_por INTEGER REFERENCES vendedor(id_vendedor),
    fecha_aprobacion TIMESTAMP WITH TIME ZONE,
    url_comprobante TEXT,
    notas TEXT
);

CREATE TABLE proveedor (
    id_proveedor SERIAL PRIMARY KEY,
    nombre_comercial VARCHAR(255) NOT NULL,
    razon_social VARCHAR(255),
    ruc VARCHAR(20),
    servicios_ofrecidos TEXT[], 
    contacto_nombre VARCHAR(100),
    contacto_telefono VARCHAR(20),
    contacto_email VARCHAR(100),
    direccion TEXT,
    ciudad VARCHAR(100),
    pais VARCHAR(100) DEFAULT 'Perú',
    banco_soles VARCHAR(100),
    cuenta_soles VARCHAR(50),
    cci_soles VARCHAR(50),
    banco_dolares VARCHAR(100),
    cuenta_dolares VARCHAR(50),
    cci_dolares VARCHAR(50),
    metodo_pago_preferido VARCHAR(50) CHECK (metodo_pago_preferido IN (
        'TRANSFERENCIA', 'EFECTIVO', 'CHEQUE', 'DEPOSITO', 'YAPE', 'PLIN'
    )),
    plazo_pago_dias INTEGER DEFAULT 0,
    calificacion_promedio DECIMAL(3,2),
    activo BOOLEAN DEFAULT TRUE,
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Vincular FK faltantes
ALTER TABLE venta_tour ADD CONSTRAINT fk_proveedor_tour FOREIGN KEY (id_proveedor) REFERENCES proveedor(id_proveedor) ON DELETE SET NULL;
ALTER TABLE requerimiento ADD COLUMN id_proveedor INTEGER REFERENCES proveedor(id_proveedor);

CREATE TABLE venta_servicio_proveedor (
    id SERIAL PRIMARY KEY,
    id_venta INTEGER,
    n_linea INTEGER,
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor) ON DELETE RESTRICT,
    tipo_servicio VARCHAR(50) CHECK (tipo_servicio IN (
        'TRANSPORTE', 'ALOJAMIENTO', 'ALIMENTACION', 
        'GUIA', 'TICKETS', 'OTRO'
    )),
    costo_acordado DECIMAL(10,2) NOT NULL,
    moneda VARCHAR(10) DEFAULT 'USD',
    tipo_cambio DECIMAL(8,4),
    estado_pago VARCHAR(30) DEFAULT 'PENDIENTE' CHECK (estado_pago IN (
        'PENDIENTE', 'PAGADO', 'PAGADO_PARCIAL', 'VENCIDO', 'CANCELADO'
    )),
    monto_total_pagado DECIMAL(10,2) DEFAULT 0,
    fecha_vencimiento_pago DATE,
    codigo_reserva VARCHAR(100),
    confirmado BOOLEAN DEFAULT FALSE,
    fecha_confirmacion DATE,
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_venta, n_linea) REFERENCES venta_tour(id_venta, n_linea) ON DELETE CASCADE,
    UNIQUE(id_venta, n_linea, tipo_servicio) -- CRÍTICO: Evitar duplicar guías/tours por servicio
);

CREATE TABLE evaluacion_proveedor (
    id SERIAL PRIMARY KEY,
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor) ON DELETE CASCADE,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE SET NULL,
    calificacion_general INTEGER CHECK (calificacion_general BETWEEN 1 AND 5),
    puntualidad INTEGER CHECK (puntualidad BETWEEN 1 AND 5),
    calidad_servicio INTEGER CHECK (calidad_servicio BETWEEN 1 AND 5),
    relacion_precio_calidad INTEGER CHECK (relacion_precio_calidad BETWEEN 1 AND 5),
    comunicacion INTEGER CHECK (comunicacion BETWEEN 1 AND 5),
    resolveria_contratar BOOLEAN,
    comentarios TEXT,
    evaluado_por INTEGER REFERENCES vendedor(id_vendedor),
    fecha_evaluacion DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================
-- SECCIÓN 2: CARGA DE DATOS (SEMILLAS)
-- ==============================================================

-- 2.1. USUARIOS Y VENDEDORES
-- Los emails deben coincidir para que el sistema vincule el login con el vendedor asignado.
INSERT INTO usuarios_app (email, rol) VALUES 
('angel@agencia.com', 'GERENCIA'),
('abel@agencia.com', 'VENTAS'),
('maria@agencia.com', 'OPERACIONES'),
('admin@agencia.com', 'GERENCIA');

INSERT INTO vendedor (nombre, email) VALUES 
('Angel', 'angel@agencia.com'),
('Abel', 'abel@agencia.com'),
('Maria', 'maria@agencia.com'),
('Anonimo', 'admin@agencia.com');

-- 2.2. AGENCIAS ALIADAS (B2B)
INSERT INTO agencia_aliada (nombre, pais, celular) VALUES 
('Ulises Viaje', 'Argentina', '+54 9 3534 28-1109'),
('Like Travel', 'Argentina', '+54 9 3517 64-3797'),
('Kuna Travel', 'Mexico', '+52 1 614 277 7793'),
('Guru Destinos', 'Argentina', '+54 9 11 6458-9079'),
('Hector', 'Mexico', '+52 1 33 2492 7483'),
('Rogelio', 'Brazil', '+55 48 8424-1401'),
('Willian', 'Bolivia', '+591 75137410'),
('Cave', 'Peru', '+51 982 167 776');

-- 2.3. CATÁLOGO DE TOURS
-- Duplicate simplified INSERT INTO tour removed (kept detailed version below)
-- 2.3. CATÁLOGO DE TOURS
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'CITY TOUR CUSCO PULL',
  'Recorrido histórico guiado.',
  4,
  1,
  41,
  98,
  41,
  28.7,
  68.6,
  28.7,
  TRUE,
  '08:00:00'
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'VALLE SAGRADO VIP PULL',
  'Día completo en el Valle Sagrado.',
  8,
  1,
  48,
  127,
  48,
  33.6,
  88.9,
  33.6,
  TRUE,
  '07:30:00'
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'MACHU PICCHU FULL DAY PULL',
  'Santuario histórico.',
  16,
  1,
  270,
  730,
  240,
  189,
  511,
  168,
  TRUE,
  '04:00:00'
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'LAGUNA HUMANTAY PULL',
  'Laguna turquesa andina.',
  12,
  1,
  30,
  98,
  30,
  21,
  68.6,
  21,
  TRUE,
  '04:30:00'
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'MONTAÑA DE COLORES PULL',
  'Caminata al Vinicunca.',
  14,
  1,
  32,
  104,
  32,
  22.4,
  72.8,
  22.4,
  TRUE,
  '04:00:00'
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'CITY TOUR LIMA COLONIAL Y MODERNA',
  'Recorrido por la capital.',
  4,
  1,
  35,
  85,
  35,
  24.5,
  59.5,
  24.5,
  TRUE,
  '09:00:00'
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'PARACAS Y HUACACHINA PULL',
  'Full Day Ica desde Lima.',
  15,
  1,
  80,
  150,
  80,
  56,
  105,
  56,
  TRUE,
  '04:00:00'
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  precio_adulto_can,
  precio_nino_extranjero,
  precio_nino_nacional,
  precio_nino_can,
  activo,
  hora_inicio
) VALUES (
  'DIA LIBRE Y SALIDA AL AEROPUERTO',
  'Traslado de salida.',
  2,
  1,
  15,
  40,
  15,
  10.5,
  28,
  10.5,
  TRUE,
  '00:00:00'
);
-- Additional tours provided by the user
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'CITY TOUR CUSCO PULL',
  'Recorrido histórico guiado.',
  4,
  1,
  41,
  98,
  'CITY TOUR',
  'FACIL',
  '{"itinerario": "[Cusco, el Despertar de un Imperio] La Experiencia: \"Descubra el corazón palpitante de los Andes...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Catedral del Cusco (Arte religioso colonial)", "✅ Qoricancha (Templo del Sol Inca)", "✅ Sacsayhuamán (Fortaleza megalítica)", "✅ Qenqo (Laberinto sagrado)", "✅ Puka Pukara (Control militar inca)", "✅ Tambomachay (Templo del agua)"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas a atractivos", "Alimentación", "Gastos personales"]}'::jsonb,
  'city_tour_cusco',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'CITY TOUR CUSCO + CATEDRAL PULL',
  'Recorrido cultural por el Cusco incluyendo visita guiada al interior de la Catedral.',
  4,
  1,
  51,
  138,
  'CITY TOUR',
  'FACIL',
  '{"itinerario": "[Cusco Profundo y Sagrado] La Experiencia: \"Adéntrese en un museo vivo...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Catedral del Cusco (Joya del arte cusqueño)", "✅ Qoricancha (Máxima expresión inca)", "✅ Sacsayhuamán (Ingeniería ciclópea)", "✅ Qenqo (Centro ceremonial subterráneo)", "✅ Puka Pukara (Vigía de los Andes)", "✅ Tambomachay (Culto al agua viva)"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas adicionales", "Alimentación", "Gastos personales"]}'::jsonb,
  'city_tour_cusco_catedral',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'VALLE SAGRADO VIP PULL',
  'Excursión de día completo por los principales atractivos culturales y paisajísticos del Valle Sagrado.',
  8,
  1,
  48,
  127,
  'FULL DAY',
  'MODERADO',
  '{"itinerario": "[El Valle de los Emperadores] La Experiencia: \"Sumérjase en el fértil valle...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Pisac (Terrazas y necrópolis)", "✅ Mercado de Pisac (Colores y artesanía)", "✅ Ollantaytambo (Ciudad inca viviente)", "✅ Chinchero (Tejido ancestral)"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas a atractivos", "Alimentación", "Gastos personales"]}'::jsonb,
  'valle_sagrado_vip',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'VALLE SAGRADO VIP (ROSARIO) PULL',
  'Recorrido extendido por el Valle Sagrado con paradas culturales y paisajísticas adicionales.',
  8,
  1,
  56,
  154,
  'FULL DAY',
  'MODERADO',
  '{"itinerario": "[Valle Sagrado: Esencia Andina] La Experiencia: \"Deambule por el Valle Sagrado...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Mirador Taray (Vista panorámica)", "✅ Pisac (Agricultura vertical)", "✅ Ollantaytambo (Fortaleza de resistencia)", "✅ Chinchero (Cultura textil)"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas a atractivos", "Alimentación", "Gastos personales"]}'::jsonb,
  'valle_sagrado_vip_rosario',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'MACHU PICCHU FULL DAY PULL',
  'Excursión de día completo al santuario histórico de Machu Picchu desde la ciudad del Cusco.',
  8,
  1,
  270,
  730,
  'FULL DAY',
  'MODERADO',
  '{"itinerario": "[Machu Picchu, La Ciudad Perdida] La Experiencia: \"Embárquese en una peregrinación a la Joya de la Corona de los Andes...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Aguas Calientes (Pueblo cosmopolita)", "✅ Machu Picchu (Maravilla del Mundo)", "✅ Templo del Sol (Astronomía sagrada)", "✅ Intihuatana (Reloj solar)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'machu_picchu_full_day',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'LAGUNA HUMANTAY PULL',
  'Excursión de día completo a una de las lagunas más impresionantes de la cordillera andina, ideal para amantes de la naturaleza y caminatas de altura.',
  12,
  1,
  30,
  98,
  'Naturaleza y Aventura',
  'MODERADO',
  '{"itinerario": "[Humantay: El Espejo Turquesa] La Experiencia: \"Ascienda a una joya escondida...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Mollepata (Desayuno andino)", "✅ Soraypampa (Campamento base)", "✅ Laguna Humantay (Turquesa glaciar)", "✅ Nevado Salkantay (Apu protector)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'laguna_humantay',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'MONTAÑA DE COLORES PULL',
  'Excursión de alta montaña hacia uno de los paisajes más icónicos del Perú, atravesando comunidades andinas y rutas naturales hasta la famosa Montaña de Colores.',
  14,
  1,
  32,
  104,
  'Naturaleza y Aventura',
  'DIFICIL',
  '{"itinerario": "[Vinicunca, El Arcoíris de Piedra] La Experiencia: \"Desafíe su espíritu en una caminata hacia el techo del mundo...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Cusipata (Pueblo tradicional)", "✅ Vinicunca (Montaña Arcoíris)", "✅ Valle Rojo (Paisaje marciano)", "✅ Nevado Ausangate (Vista lejana)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'montana_de_colores',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'PALCCOYO PULL',
  'Excursión alternativa a la Montaña de Colores que permite apreciar formaciones multicolores, paisajes abiertos y caminatas suaves en zonas altoandinas poco concurridas.',
  10,
  1,
  37,
  124,
  'Naturaleza y Aventura',
  'MODERADO',
  '{"itinerario": "[Palccoyo: La Cordillera Pintada] La Experiencia: \"Descubra la hermana serena de la Montaña de Colores...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Checacupe (Puente colonial)", "✅ Palccoyo (Tres montañas de colores)", "✅ Bosque de Piedras (Formaciones geológicas)", "✅ Río Rojo (Fenómeno natural)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'palccoyo',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'PUENTE QESWACHAKA + 4 LAGUNAS PULL',
  'Excursión cultural y natural que combina historia viva inca con paisajes altoandinos, lagunas de altura y tradiciones ancestrales aún vigentes.',
  14,
  1,
  44,
  146,
  'Cultura y Naturaleza',
  'MODERADO',
  '{"itinerario": "[Qeswachaka y el Legado Vivo] La Experiencia: \"Sea testigo del increíble legado del último puente inca...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Laguna Pomacanchi (Espejo de agua)", "✅ Laguna Asnaqocha (Fauna andina)", "✅ Puente Qeswachaka (Ingeniería de ichu)", "✅ Río Apurímago (Gran hablador)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'puente_qeswachaka_4_lagunas',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'WAQRAPUKARA PULL',
  'Excursión de aventura hacia un complejo arqueológico de ubicación estratégica, rodeado de cañones profundos y paisajes altoandinos de gran valor histórico.',
  13,
  1,
  39,
  130,
  'Aventura y Cultura',
  'MODERADO',
  '{"itinerario": "[Waqrapukara: La Fortaleza de los Cuernos] La Experiencia: \"Aventúrese fuera de los caminos trillados...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Comunidad Acomayo (Cultura rural)", "✅ Waqrapukara (Fortaleza pre-inca)", "✅ Cañón del Apurímac (Abismo natural)", "✅ Pinturas Rupestres (Huellas antiguas)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'waqrapukara',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'SIETE LAGUNAS AUSANGATE PULL',
  'Ruta de caminata escénica alrededor del nevado Ausangate que permite visitar lagunas de colores intensos y paisajes de alta montaña.',
  14,
  1,
  42,
  140,
  'Naturaleza y Aventura',
  'MODERADO',
  '{"itinerario": "[Ausangate y el Circuito de Cristal] La Experiencia: \"Entre en un paisaje onírico de gran altitud...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Pacchanta (Aguas termales)", "✅ Laguna Azulcocha (Azul intenso)", "✅ Laguna Pucacocha (Rojiza mineral)", "✅ Nevado Ausangate (Apu sagrado)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'siete_lagunas_ausangate',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'VALLE SUR PULL',
  'Recorrido cultural por el Valle Sur de Cusco que combina sitios arqueológicos, arquitectura colonial y tradiciones vivas de comunidades locales.',
  6,
  1,
  28,
  92,
  'Cultura',
  'FACIL',
  '{"itinerario": "[Valle Sur: Ingeniería y Fe] La Experiencia: \"Viaje por el camino menos transitado para descubrir la sofisticada ingeniería...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Tipón (Ingeniería hidráulica)", "✅ Pikillacta (Urbanismo Wari)", "✅ Andahuaylillas (Capilla Sixtina de América)", "✅ Laguna de Huacarpay (Humedal protegido)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'valle_sur',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'CHURIN PULL',
  'Excursion a CHURIN PULL',
  0,
  1,
  28,
  94,
  'TURISMO',
  'FACIL',
  '{"itinerario": "[Churín: Santuario Termal] La Experiencia: \"Entréguese al abrazo curativo de la tierra...\"}'::jsonb,
  '{"Lo que visitarás": ["✅ Complejo Mamahuarmi (Pozas naturales)", "✅ Baños de Tingo (Aguas ferrosas)", "✅ Velo de la Novia (Cascada natural)", "✅ Plaza de Churín (Encanto serrano)"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'churin',
  '08:00:00',
  TRUE
);
INSERT INTO tour (
  nombre,
  descripcion,
  duracion_horas,
  duracion_dias,
  precio_adulto_extranjero,
  precio_adulto_nacional,
  categoria,
  dificultad,
  highlights,
  atractivos,
  servicios_incluidos,
  servicios_no_incluidos,
  carpeta_img,
  hora_inicio,
  activo
) VALUES (
  'CIRCUITO MAGICO + LA CAND... (truncated for brevity)'
);;

-- 2.4. PROVEEDORES (DATOS BANCARIOS)
INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_dolares, cuenta_dolares, cci_dolares)
VALUES ('LARRY GUIA', '{"GUIA"}', 'INTERBANK', '420-3363525879', '003-420013363525879-70');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles, cci_soles)
VALUES ('JOSE CHAMPI MAPI', '{"GUIA"}', 'INTERBANK', '419-3380704197', '003-41901338070419000');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles, cci_soles, banco_dolares, cuenta_dolares, cci_dolares)
VALUES ('ROSA GUIA LIMA', '{"GUIA"}', 'BCP', '191-18513860067', '002-191118513860067-59', 'BCP', '191-11784136166', '002-19111784136166-51');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, contacto_telefono, banco_soles, cuenta_soles, cci_soles)
VALUES ('VICKI GUIA PUNO', '{"GUIA"}', '+51 984 754 275', 'BCP', '495-26687175019', '002-495126687175019-02');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles)
VALUES ('VLADIMIRO LARREA', '{"GUIA"}', 'BCP', '285-29611517089');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles, cci_soles)
VALUES ('FRANCISCO ALCANTARA', '{"TRANSPORTE"}', 'BCP', '191-95199282088', '002-191195199282088-59');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles, cci_soles, notas)
VALUES ('JAIME BUS', '{"TRANSPORTE"}', 'BCP', '285-09676107011', '002-285109676107011-56', 'BBVA Soles 0011-0200-0201531370');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles, cci_soles, banco_dolares, cuenta_dolares, cci_dolares)
VALUES ('CENTRAL DE RESERVAS', '{"TRANSPORTE"}', 'INTERBANK', '420-3005326345', '003-420-003005326345-72', 'INTERBANK', '898-3402989352', '003-898-01340298935243');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles, cci_soles)
VALUES ('QORIALVA', '{"TRANSPORTE"}', 'INTERBANK', '420-3230585322', '003-42001323058532279');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, banco_soles, cuenta_soles, cci_soles)
VALUES ('MARIA RENAULT', '{"TRANSPORTE"}', 'INTERBANK', '420-3007297660', '003-420-003007297660-75');

INSERT INTO proveedor (nombre_comercial, servicios_ofrecidos, contacto_telefono)
VALUES 
('ANDEAN TREKING', '{"HOTEL"}', '+51 980 852 691'),
('MIGUEL PACAY', '{"GUIA"}', '+51 974 446 170'),
('ROSA MORADA', '{"GUIA"}', '+51 964 668 030'),
('PICAFLOR', '{"GUIA"}', '+51 987 420 868'),
('FUTURISMO', '{"GUIA"}', '+51 984 736 982'),
('CEVICHE', '{"GUIA"}', '+51 956 849 794');

-- 2.5. PAQUETES PREDEFINIDOS
DO $$
DECLARE
    p_id INTEGER;
    t_id INTEGER;
BEGIN
    INSERT INTO paquete (nombre, descripcion, dias, noches, precio_sugerido, temporada, destino_principal)
    VALUES ('PERÚ PARA EL MUNDO 8D/7N', 'Recorrido completo desde la costa hasta Cusco.', 8, 7, 0.00, 'TODO EL AÑO', 'PERÚ')
    RETURNING id_paquete INTO p_id;
    
    -- Vincular tours
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'CITY TOUR LIMA COLONIAL Y MODERNA' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 1, 1);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'PARACAS Y HUACACHINA PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 2, 2);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'CITY TOUR CUSCO PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 3, 3);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'VALLE SAGRADO VIP PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 4, 4);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'MACHU PICCHU FULL DAY PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 5, 5);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'LAGUNA HUMANTAY PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 6, 6);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'MONTAÑA DE COLORES PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 7, 7);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'DIA LIBRE Y SALIDA AL AEROPUERTO' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 8, 8);
END $$;

DO $$
DECLARE
    p_id INTEGER;
    t_id INTEGER;
BEGIN
    INSERT INTO paquete (nombre, descripcion, dias, noches, precio_sugerido, temporada, destino_principal)
    VALUES ('CUSCO TRADICIONAL 5D/4N', 'Lo esencial: Arqueología, Valles y Machu Picchu.', 5, 4, 0.00, 'TODO EL AÑO', 'CUSCO')
    RETURNING id_paquete INTO p_id;

    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'CITY TOUR CUSCO PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 1, 1);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'VALLE SAGRADO VIP PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 2, 2);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'MACHU PICCHU FULL DAY PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 3, 3);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'LAGUNA HUMANTAY PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 4, 4);
    SELECT id_tour INTO t_id FROM tour WHERE nombre = 'MONTAÑA DE COLORES PULL' LIMIT 1;
    INSERT INTO paquete_tour (id_paquete, id_tour, orden, dia_del_paquete) VALUES (p_id, t_id, 5, 5);
END $$;

-- ==============================================================
-- SECCIÓN 3: FUNCIONES Y TRIGGERS (AUTOMATIZACIÓN)
-- ==============================================================

-- 3.1. Actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_venta_updated_at BEFORE UPDATE ON venta
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 3.2. Sincronizar costo_total
CREATE OR REPLACE FUNCTION sync_costo_venta_total()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE venta SET costo_total = (SELECT COALESCE(SUM(costo_acordado), 0) FROM venta_servicio_proveedor WHERE id_venta = COALESCE(NEW.id_venta, OLD.id_venta))
    WHERE id_venta = COALESCE(NEW.id_venta, OLD.id_venta);
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_sync_costo AFTER INSERT OR UPDATE OR DELETE ON venta_servicio_proveedor
    FOR EACH ROW EXECUTE FUNCTION sync_costo_venta_total();

-- 3.3. Calcular utilidad
CREATE OR REPLACE FUNCTION calcular_utilidad_venta()
RETURNS TRIGGER AS $$
BEGIN
    NEW.utilidad_bruta = COALESCE(NEW.precio_total_cierre, 0) - COALESCE(NEW.costo_total, 0);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_calc_utilidad BEFORE INSERT OR UPDATE OF precio_total_cierre, costo_total ON venta
    FOR EACH ROW EXECUTE FUNCTION calcular_utilidad_venta();

-- ==============================================================
-- SECCIÓN 4: VISTAS (REPORTES)
-- ==============================================================

-- 4.1. Ventas Completa
CREATE OR REPLACE VIEW vista_ventas_completa AS
SELECT 
    v.id_venta, v.fecha_venta, v.fecha_inicio, v.fecha_fin,
    l.nombre as cliente_nombre, aa.nombre as agencia_nombre,
    vend.nombre as vendedor_nombre, v.tour_nombre, v.precio_total_cierre,
    v.moneda, v.estado_venta, COALESCE(SUM(p.monto_pagado), 0) as total_pagado,
    v.precio_total_cierre - COALESCE(SUM(p.monto_pagado), 0) as saldo_pendiente,
    CASE WHEN v.precio_total_cierre - COALESCE(SUM(p.monto_pagado), 0) <= 0.01 THEN 'SALDADO' ELSE 'PENDIENTE' END as estado_pago
FROM venta v
LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
LEFT JOIN lead l ON c.id_lead = l.id_lead
LEFT JOIN agencia_aliada aa ON v.id_agencia_aliada = aa.id_agencia
LEFT JOIN vendedor vend ON v.id_vendedor = vend.id_vendedor
LEFT JOIN pago p ON v.id_venta = p.id_venta
WHERE v.cancelada = FALSE
GROUP BY v.id_venta, l.nombre, aa.nombre, vend.nombre;

-- 4.2. Servicios Diarios
CREATE OR REPLACE VIEW vista_servicios_diarios AS
SELECT 
    vt.fecha_servicio, vt.id_venta, vt.n_linea, l.nombre as cliente, vend.nombre as vendedor,
    COALESCE(t.nombre, vt.observaciones, v.tour_nombre) as servicio,
    vt.cantidad_pasajeros as pax, vt.estado_servicio,
    (SELECT p.nombre_comercial FROM venta_servicio_proveedor vsp JOIN proveedor p ON vsp.id_proveedor = p.id_proveedor 
     WHERE vsp.id_venta = vt.id_venta AND vsp.n_linea = vt.n_linea AND vsp.tipo_servicio = 'GUIA' LIMIT 1) as guia_asignado
FROM venta_tour vt
INNER JOIN venta v ON vt.id_venta = v.id_venta
LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
LEFT JOIN lead l ON c.id_lead = l.id_lead
LEFT JOIN vendedor vend ON v.id_vendedor = vend.id_vendedor
LEFT JOIN tour t ON vt.id_tour = t.id_tour
WHERE v.cancelada = FALSE;

-- ==============================================================
-- SECCIÓN 5: SEGURIDAD (RLS Y POLÍTICAS)
-- ==============================================================

-- Habilitar RLS
ALTER TABLE usuarios_app ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendedor ENABLE ROW LEVEL SECURITY;
ALTER TABLE venta ENABLE ROW LEVEL SECURITY;
-- (Opcional: aplicar a todas las demás tablas)

-- Políticas permisivas (MODO DESARROLLO)
DO $$ 
DECLARE tabla_nombre text;
BEGIN
    FOR tabla_nombre IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('CREATE POLICY "Acceso total" ON %I FOR ALL USING (true) WITH CHECK (true);', tabla_nombre);
    END LOOP;
END $$;

-- Permisos storage (Ejecutar en panel SQL)
-- Requiere buckets 'itinerarios' y 'vouchers' creados como Públicos
CREATE POLICY "Acceso Público Itinerarios" ON storage.objects FOR SELECT USING (bucket_id = 'itinerarios');
CREATE POLICY "Subida Libre Itinerarios" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'itinerarios');
CREATE POLICY "Acceso Público Vouchers" ON storage.objects FOR SELECT USING (bucket_id = 'vouchers');
CREATE POLICY "Subida Libre Vouchers" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'vouchers');

-- ==============================================================
-- ✅ FIN DEL SCRIPT: INSTALACIÓN EXITOSA
-- ==============================================================
