-- 0. REINICIAR (Surgical cleanup compatible con Supabase)
-- Borrar vistas si existen
DROP VIEW IF EXISTS vista_servicios_diarios CASCADE;
DROP VIEW IF EXISTS vista_ventas_completa CASCADE;

-- Borrar tablas si existen (en orden de dependencia)
DROP TABLE IF EXISTS evaluacion_proveedor CASCADE;
DROP TABLE IF EXISTS venta_servicio_proveedor CASCADE;
DROP TABLE IF EXISTS requerimiento CASCADE;
DROP TABLE IF EXISTS documentacion CASCADE; -- Seguridad para versiones viejas
DROP TABLE IF EXISTS pasajero CASCADE;      -- Seguridad para versiones viejas
DROP TABLE IF EXISTS pago CASCADE;
DROP TABLE IF EXISTS venta_tour CASCADE;
DROP TABLE IF EXISTS venta CASCADE;
DROP TABLE IF EXISTS itinerario_digital CASCADE;
DROP TABLE IF EXISTS catalogo_tours_imagenes CASCADE;
DROP TABLE IF EXISTS paquete_tour CASCADE;
DROP TABLE IF EXISTS paquete CASCADE;
DROP TABLE IF EXISTS tour_itinerario_item CASCADE;
DROP TABLE IF EXISTS tour CASCADE;
DROP TABLE IF EXISTS proveedor CASCADE; -- AGREGADO AQUÍ
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
('angel@agencia.com', 'VENTAS'),
('abel@agencia.com', 'VENTAS'),
('maria@agencia.com', 'OPERACIONES'),
('elizabeth@agencia.com', 'OPERACIONES'),
('vanessa@agencia.com', 'GERENCIA'),
('henrry@agencia.com', 'GERENCIA');

INSERT INTO vendedor (nombre, email) VALUES 
('Angel', 'angel@agencia.com'),
('Abel', 'abel@agencia.com'),
('Maria', 'maria@agencia.com'),
('Vanessa', 'vanessa@agencia.com'),
('Henrry', 'henrry@agencia.com');

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
INSERT INTO tour (
  nombre, descripcion, duracion_horas, duracion_dias, precio_adulto_extranjero, precio_adulto_nacional,
  categoria, dificultad, highlights, atractivos, servicios_incluidos, servicios_no_incluidos,
  carpeta_img, hora_inicio, activo
) VALUES 
(
  'CITY TOUR CUSCO PULL',
  'Recorrido guiado por los principales atractivos históricos y culturales de la ciudad del Cusco.',
  4, 1, 41.00, 98.00,
  'CITY TOUR', 'FACIL',
  '{"itinerario": "[Cusco, el Despertar de un Imperio] La Experiencia: \"Descubra el corazón palpitante de los Andes en un viaje a través del tiempo, donde la mampostería inca se funde con la elegancia colonial.\""}'::jsonb,
  '{"Lo que visitarás": ["Catedral del Cusco", "Qoricancha", "Sacsayhuamán", "Qenqo", "Puka Pukara", "Tambomachay"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas a atractivos", "Alimentación", "Gastos personales"]}'::jsonb,
  'city_tour_cusco', '08:00:00', TRUE
),
(
  'CITY TOUR CUSCO + CATEDRAL PULL',
  'Recorrido cultural por el Cusco incluyendo visita guiada al interior de la Catedral.',
  4, 1, 61.00, 163.00,
  'CITY TOUR', 'FACIL',
  '{"itinerario": "[Cusco Profundo y Sagrado] La Experiencia: \"Adéntrese en un museo vivo donde convergen siglos de historia.\""}'::jsonb,
  '{"Lo que visitarás": ["Catedral del Cusco", "Qoricancha", "Sacsayhuamán", "Qenqo", "Puka Pukara", "Tambomachay"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas adicionales", "Alimentación", "Gastos personales"]}'::jsonb,
  'city_tour_cusco_catedral', '08:00:00', TRUE
),
(
  'VALLE SAGRADO VIP PULL',
  'Excursión de día completo por los principales atractivos culturales y paisajísticos del Valle Sagrado.',
  8, 1, 57.00, 150.00,
  'FULL DAY', 'MODERADO',
  '{"itinerario": "[El Valle de los Emperadores] La Experiencia: \"Sumérjase en el fértil valle que alimentó a un imperio, un paisaje impresionante de maizales y montañas infinitas.\""}'::jsonb,
  '{"Lo que visitarás": ["Pisac", "Mercado de Pisac", "Ollantaytambo", "Chinchero"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas a atractivos", "Alimentación", "Gastos personales"]}'::jsonb,
  'valle_sagrado_vip', '08:00:00', TRUE
),
(
  'VALLE SAGRADO VIP (ROSARIO) PULL',
  'Recorrido extendido por el Valle Sagrado con paradas culturales y paisajísticas adicionales.',
  8, 1, 66.00, 182.00,
  'FULL DAY', 'MODERADO',
  '{"itinerario": "[Valle Sagrado: Esencia Andina] La Experiencia: \"Deambule por el Valle Sagrado de los Incas, un lugar de belleza mística y cultura vibrante.\""}'::jsonb,
  '{"Lo que visitarás": ["Mirador Taray", "Pisac", "Ollantaytambo", "Chinchero"]}'::jsonb,
  '{"incluye": ["Guía profesional", "Transporte turístico", "Asistencia permanente"]}'::jsonb,
  '{"no_incluye": ["Entradas a atractivos", "Alimentación", "Gastos personales"]}'::jsonb,
  'valle_sagrado_vip_rosario', '08:00:00', TRUE
),
(
  'MACHU PICCHU FULL DAY PULL',
  'Excursión de día completo al santuario histórico de Machu Picchu desde la ciudad del Cusco.',
  8, 1, 270.00, 730.00,
  'FULL DAY', 'MODERADO',
  '{"itinerario": "[Machu Picchu, La Ciudad Perdida] La Experiencia: \"Embárquese en una peregrinación a la Joya de la Corona de los Andes, una ciudad oculta entre las nubes.\""}'::jsonb,
  '{"Lo que visitarás": ["Aguas Calientes", "Machu Picchu", "Templo del Sol", "Intihuatana"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'machu_picchu_full_day', '08:00:00', TRUE
),
(
  'LAGUNA HUMANTAY PULL',
  'Excursión de día completo a una de las lagunas más impresionantes de la cordillera andina.',
  12, 1, 30.00, 98.00,
  'NATURALEZA', 'MODERADO',
  '{"itinerario": "[Humantay: El Espejo Turquesa] La Experiencia: \"Ascienda a una joya escondida acunada por picos nevados, donde el agua brilla como un espejo turquesa.\""}'::jsonb,
  '{"Lo que visitarás": ["Mollepata", "Soraypampa", "Laguna Humantay", "Nevado Salkantay"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'laguna_humantay', '08:00:00', TRUE
),
(
  'MONTAÑA DE COLORES PULL',
  'Excursión de alta montaña hacia uno de los paisajes más icónicos del Perú.',
  14, 1, 32.00, 104.00,
  'AVENTURA', 'DIFICIL',
  '{"itinerario": "[Vinicunca, El Arcoíris de Piedra] La Experiencia: \"Desafíe su espíritu en una caminata hacia el techo del mundo, donde la tierra se niega a ser de un solo color.\""}'::jsonb,
  '{"Lo que visitarás": ["Cusipata", "Vinicunca", "Valle Rojo", "Nevado Ausangate"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'montana_de_colores', '08:00:00', TRUE
),
(
  'PALCCOYO PULL',
  'Excursión alternativa a la Montaña de Colores con caminatas suaves en zonas poco concurridas.',
  10, 1, 37.00, 124.00,
  'AVENTURA', 'MODERADO',
  '{"itinerario": "[Palccoyo: La Cordillera Pintada] La Experiencia: \"Descubra la hermana serena de la Montaña de Colores, un lugar de majestuosidad tranquila.\""}'::jsonb,
  '{"Lo que visitarás": ["Checacupe", "Palccoyo", "Bosque de Piedras", "Río Rojo"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'palccoyo', '08:00:00', TRUE
),
(
  'PUENTE QESWACHAKA + 4 LAGUNAS PULL',
  'Excursión que combina historia viva inca con paisajes altoandinos.',
  14, 1, 44.00, 146.00,
  'CULTURA', 'MODERADO',
  '{"itinerario": "[Qeswachaka y el Legado Vivo] La Experiencia: \"Sea testigo del increíble legado del último puente inca, una obra maestra tejida a mano.\""}'::jsonb,
  '{"Lo que visitarás": ["Laguna Pomacanchi", "Laguna Asnaqocha", "Puente Qeswachaka", "Río Apurímac"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'puente_qeswachaka_4_lagunas', '08:00:00', TRUE
),
(
  'WAQRAPUKARA PULL',
  'Excursión de aventura hacia un complejo arqueológico rodeado de cañones profundos.',
  13, 1, 39.00, 130.00,
  'AVENTURA', 'MODERADO',
  '{"itinerario": "[Waqrapukara: La Fortaleza de los Cuernos] La Experiencia: \"Aventúrese fuera de los caminos trillados hacia la fortaleza en forma de cuernos de Waqrapukara.\""}'::jsonb,
  '{"Lo que visitarás": ["Comunidad Acomayo", "Waqrapukara", "Cañón del Apurímac", "Pinturas Rupestres"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'waqrapukara', '08:00:00', TRUE
),
(
  'SIETE LAGUNAS AUSANGATE PULL',
  'Ruta de caminata escénica que permite visitar lagunas de colores intensos a los pies del Ausangate.',
  14, 1, 35.00, 117.00,
  'NATURALEZA', 'MODERADO',
  '{"itinerario": "[Ausangate y el Circuito de Cristal] La Experiencia: \"Entre en un paisaje onírico de gran altitud dominado por el poderoso Ausangate.\""}'::jsonb,
  '{"Lo que visitarás": ["Pacchanta", "Laguna Azulcocha", "Laguna Pucacocha", "Nevado Ausangate"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'siete_lagunas_ausangate', '08:00:00', TRUE
),
(
  'VALLE SUR PULL',
  'Recorrido cultural que combina sitios arqueológicos, arquitectura colonial y tradiciones vivas.',
  6, 1, 42.00, 98.00,
  'CULTURA', 'FACIL',
  '{"itinerario": "[Valle Sur: Ingeniería y Fe] La Experiencia: \"Viaje por el camino menos transitado para descubrir la sofisticada ingeniería Wari e Inca.\""}'::jsonb,
  '{"Lo que visitarás": ["Tipón", "Pikillacta", "Andahuaylillas", "Laguna de Huacarpay"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'valle_sur', '08:00:00', TRUE
),
(
  'CHURIN PULL',
  'Excursión a los baños termales de Churín, conocidos por sus propiedades medicinales.',
  12, 1, 30.0, 98.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Churín: Santuario Termal] La Experiencia: \"Entréguese al abrazo curativo de la tierra en los baños termales de Churín.\""}'::jsonb,
  '{"Lo que visitarás": ["Complejo Mamahuarmi", "Baños de Tingo", "Velo de la Novia", "Plaza de Churín"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'churin', '08:00:00', TRUE
),
(
  'CIRCUITO MAGICO + LA CANDELARIA PULL',
  'Espectáculo de luces en el Circuito Mágico del Agua seguido de un show folclórico.',
  4, 1, 137.0, 458.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Lima de Noche: Luces y Tradición] La Experiencia: \"Encienda sus sentidos en un deslumbrante espectáculo de luz, agua y música.\""}'::jsonb,
  '{"Lo que visitarás": ["Parque de la Reserva", "Circuito Mágico", "Show Multimedia", "Cena Show"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'circuito_magico_la_candelaria', '18:00:00', TRUE
),
(
  'MORADA DE LOS DIOSES PULL',
  'Esculturas gigantes modernas talladas en piedra honrando deidades andinas.',
  4, 1, 16.0, 46.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Apukunaq Tianan: Morada Divina] La Experiencia: \"Visite un santuario moderno tallado en la roca viva, donde el arte contemporáneo honra a las deidades antiguas.\""}'::jsonb,
  '{"Lo que visitarás": ["Sencca", "El Puma", "La Pachamama", "Mirador del Cusco"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'morada_de_los_dioses', '09:00:00', TRUE
),
(
  'RUTA DEL SOL CUSCO - PUNO PULL',
  'Traslado turístico de lujo con paradas en los sitios arqueológicos más importantes entre Cusco y Puno.',
  10, 1, 70.0, 231.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[La Ruta del Sol: Altiplano Ancestral] La Experiencia: \"Transforme un simple traslado en una odisea a través del Altiplano.\""}'::jsonb,
  '{"Lo que visitarás": ["Andahuaylillas", "Raqchi", "La Raya", "Pucará"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'ruta_del_sol_cusco_puno', '07:00:00', TRUE
),
(
  'BARRANCO + HUACA PUCLLANA PULL',
  'Visita al barrio bohemio de Barranco y a la pirámide pre-inca de Huaca Pucllana.',
  4, 1, 57.0, 189.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Lima: Contrastes de Tiempo] La Experiencia: \"Experimente el cautivador contraste de Lima, donde una pirámide de adobe pre-inca se alza en medio de la ciudad moderna.\""}'::jsonb,
  '{"Lo que visitarás": ["Huaca Pucllana", "Puente de los Suspiros", "✅ Bajada de Baños", "✅ Malecón"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'barranco_huaca_pucllana', '09:00:00', TRUE
),
(
  'PACHACAMAC + CABALLOS DE PASO PULL',
  'Exploración del santuario de Pachacamac y exhibición del Caballo Peruano de Paso.',
  6, 1, 150.0, 501.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Pachacamac: Oráculo y Tradición] La Experiencia: \"Párese ante el oráculo del Pacífico y sea testigo de la gracia del Caballo Peruano de Paso.\""}'::jsonb,
  '{"Lo que visitarás": ["Templo del Sol", "Museo de Sitio", "Hacienda Mamacona", "Show Ecuestre"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'pachacamac_caballos_de_paso', '09:00:00', TRUE
),
(
  'SOBREVUELO LINEAS DE NAZCA - NAZCA PULL',
  'Vuelo inolvidable sobre las misteriosas líneas y geoglifos de Nazca.',
  1, 1, 141.0, 471.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Nazca: Mensajes del Cielo] La Experiencia: \"Vuele sobre el enigma del desierto donde líneas antiguas dibujan mensajes a los dioses.\""}'::jsonb,
  '{"Lo que visitarás": ["Aeropuerto Nazca", "El Colibrí", "El Mono", "La Araña"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'sobrevuelo_lineas_de_nazca_nazca', '08:00:00', TRUE
),
(
  'LUNAHUANA PULL',
  'Día de aventura con canotaje y cata de vinos en el valle de Cañete.',
  12, 1, 25.0, 82.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Lunahuaná: Aventura y Vino] La Experiencia: \"Disfrute del canotaje en el río Cañete y visite viñedos locales.\""}'::jsonb,
  '{"Lo que visitarás": ["Río Cañete", "Catapalla", "Viñedos", "Apicultura"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'lunahuana', '06:00:00', TRUE
);

INSERT INTO tour (
  nombre, descripcion, duracion_horas, duracion_dias, precio_adulto_extranjero, precio_adulto_nacional,
  categoria, dificultad, highlights, atractivos, servicios_incluidos, servicios_no_incluidos,
  carpeta_img, hora_inicio, activo
) VALUES 
(
  'PARACAS Y HUACACHINA PULL',
  'Full day a la costa y el desierto: Islas Ballestas y Oasis de Huacachina.',
  15, 1, 56.0, 188.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Paracas y Huacachina: Mar y Dunas] La Experiencia: \"Navegue hacia las Islas Ballestas y monte en tubulares en el Oasis de Huacachina.\""}'::jsonb,
  '{"Lo que visitarás": ["Islas Ballestas", "El Candelabro", "Oasis Huacachina", "Dunas"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'paracas_y_huacachina', '04:00:00', TRUE
),
(
  'PLAYA LA MINA PULL',
  'Día de relax en una de las playas más hermosas de la Reserva Nacional de Paracas.',
  12, 1, 34.0, 112.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[La Mina: Paraíso Costero] La Experiencia: \"Relájese en una de las playas más hermosas de la Reserva de Paracas.\""}'::jsonb,
  '{"Lo que visitarás": ["Reserva de Paracas", "Playa La Mina", "Playa Lagunillas", "Miradores"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'playa_la_mina', '04:00:00', TRUE
),
(
  'MARAS, MORAY Y SALINERAS PULL',
  'Descubra el laboratorio agrícola inca de Moray y las milenarias minas de sal de Maras.',
  6, 1, 45.0, 111.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Maras y Moray: Ingenio Inca] La Experiencia: \"Visite los laboratorios agrícolas enigmáticos de Moray y las espectaculares minas de sal de Maras.\""}'::jsonb,
  '{"Lo que visitarás": ["Moray", "Salineras de Maras", "Pueblo de Maras", "Cordillera Vilcanota"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'maras_moray_y_salineras', '08:00:00', TRUE
),
(
  'CORDILLERA PULL',
  'Exploración de paisajes altoandinos y lagunas glaciares en la Cordillera Central.',
  12, 1, 28.0, 94.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Cordillera: Reino del Hielo] La Experiencia: \"Experimente la belleza cruda de los Andes en la Cordillera.\""}'::jsonb,
  '{"Lo que visitarás": ["Lagunas Glaciares", "Nevados", "Valles", "Flora Altoandina"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'cordillera', '05:00:00', TRUE
),
(
  'PLAYA TUQUILLO PULL',
  'Visita a la "Piscina del Pacífico", una de las playas más limpias y tranquilas del Perú.',
  12, 1, 35.0, 116.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Tuquillo: La Piscina del Pacífico] La Experiencia: \"Descubra la Pool of the Pacific en la playa de Tuquillo.\""}'::jsonb,
  '{"Lo que visitarás": ["Playa Tuquillo", "Playa Pocitas", "Huarmey", "Balneario"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'playa_tuquillo', '04:00:00', TRUE
),
(
  'MUSEO LARCO PULL',
  'Inmersión en el arte precolombino en una de las mejores galerías del mundo, en Lima.',
  4, 1, 72.0, 240.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Museo Larco: Tesoros del Pasado] La Experiencia: \"Viaje en el tiempo en el Museo Larco, hogar de una incomparable colección de arte precolombino.\""}'::jsonb,
  '{"Lo que visitarás": ["Galería de Oro", "Sala Erótica", "Depósitos", "Jardines"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'museo_larco', '09:00:00', TRUE
),
(
  'CUATRIMOTO HUAYPO Y SALINERAS PULL',
  'Aventura en cuatrimoto visitando la laguna de Huaypo y las salineras de Maras.',
  5, 1, 43.0, 143.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Cuatrimotos: Aventura sobre Ruedas] La Experiencia: \"Acelere su adrenalina con una aventura en cuatrimotos por Chinchero.\""}'::jsonb,
  '{"Lo que visitarás": ["Laguna Huaypo", "Pampa de Chinchero", "Salineras", "Comunidades"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'cuatrimoto_huaypo_y_salineras', '08:00:00', TRUE
),
(
  'PARACAS Y HUACACHINA SUNSET PULL',
  'Experiencia completa en Paracas e Ica terminando con un atardecer mágico en las dunas.',
  15, 1, 66.0, 221.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Paracas y Atardecer en el Desierto] La Experiencia: \"Experimente la magia del atardecer en el desierto.\""}'::jsonb,
  '{"Lo que visitarás": ["El Candelabro", "Islas Ballestas", "Oasis Huacachina", "Sunset"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'paracas_y_huacachina_sunset', '04:00:00', TRUE
),
(
  'CUATRIMOTO MORAY, MARAS Y SALINERAS PULL',
  'Ruta extrema en cuatrimoto por Cruzpata visitando Moray y Salineras.',
  6, 1, 34.0, 117.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Cuatrimotos: Moray y Salineras] La Experiencia: \"Conduzca cuatrimotos a través de las llanuras de Cruzpata.\""}'::jsonb,
  '{"Lo que visitarás": ["Cruzpata", "Moray", "Salineras", "Vistas del Valle"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'cuatrimoto_moray_maras_y_salineras', '08:00:00', TRUE
),
(
  'CUATRIMOTO MONTAÑA DE COLORES + VALLE ROJO PULL',
  'La forma más rápida y emocionante de llegar a la Montaña de Colores: en cuatrimoto.',
  14, 1, 68.0, 228.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Cuatrimotos a la Montaña de Colores] La Experiencia: \"Combine la emoción de los ATVs con la belleza de la Montaña de Colores.\""}'::jsonb,
  '{"Lo que visitarás": ["Valle del Sur", "Cuatrimotos", "Vinicunca", "Valle Rojo"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'cuatrimoto_montana_de_colores_valle_rojo', '04:00:00', TRUE
);

INSERT INTO tour (
  nombre, descripcion, duracion_horas, duracion_dias, precio_adulto_extranjero, precio_adulto_nacional,
  categoria, dificultad, highlights, atractivos, servicios_incluidos, servicios_no_incluidos,
  carpeta_img, hora_inicio, activo
) VALUES 
(
  'SOBREVUELO LINEAS DE NAZCA - PISCO PULL',
  'Vuelo directo sobre las Líneas de Nazca partiendo desde el aeropuerto de Pisco.',
  4, 1, 362.0, 1211.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Nazca desde Pisco: Vuelo Directo] La Experiencia: \"Desbloquee el misterio de las Líneas de Nazca con la comodidad de una salida costera.\""}'::jsonb,
  '{"Lo que visitarás": ["Aeropuerto Pisco", "Geoglifos", "Desierto de Ica", "Costa Peruana"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'sobrevuelo_lineas_de_nazca_pisco', '08:00:00', TRUE
),
(
  'PALLAY PUNCHU PULL',
  'Caminata a la impresionante montaña con picos afilados y colores vibrantes en Canas.',
  14, 1, 45.0, 150.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Pallay Punchu: La Montaña Filuda] La Experiencia: \"Descubra las crestas afiladas, similares a un poncho, de Pallay Punchu.\""}'::jsonb,
  '{"Lo que visitarás": ["Laguna Langui", "Pallay Punchu", "Canas", "Vistas"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'pallay_punchu', '04:00:00', TRUE
),
(
  'LOMAS DE LACHAY PULL',
  'Visita a la reserva nacional, un ecosistema único de nieblas en el desierto peruano.',
  10, 1, 37.0, 124.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Lomas de Lachay: Oasis de Niebla] La Experiencia: \"Visite el oasis de niebla estacional de Lomas de Lachay.\""}'::jsonb,
  '{"Lo que visitarás": ["Reserva Nacional", "Senderos", "Flora", "Fauna"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'lomas_de_lachay', '07:00:00', TRUE
),
(
  'CHANCAY PULL',
  'Día de playa y visita al pintoresco Castillo de Chancay, una joya arquitectónica frente al mar.',
  10, 1, 31.0, 103.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Castillo de Chancay: Historia y Mar] La Experiencia: \"Adéntrese en un curioso mezcla de historia y fantasía en el Castillo de Chancay.\""}'::jsonb,
  '{"Lo que visitarás": ["Castillo", "Museo", "Mirador", "Plaza de Armas"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'chancay', '08:00:00', TRUE
),
(
  'CIUDADELA SAGRADA DE CARAL PULL',
  'Viaje al pasado visitando la ciudad más antigua de América y centro de la civilización Caral.',
  14, 1, 219.0, 733.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Caral: La Civilización Más Antigua] La Experiencia: \"Camine por las calles de la ciudad más antigua de América.\""}'::jsonb,
  '{"Lo que visitarás": ["Ciudadela", "Pirámides", "Plazas Circulares", "Valle de Supe"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'ciudadela_sagrada_de_caral', '07:00:00', TRUE
),
(
  'ISLAS PALOMINO PULL',
  'Nado con lobos marinos en su hábitat natural frente a las costas del Callao.',
  6, 1, 82.0, 273.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Islas Palomino: Nado con Lobos] La Experiencia: \"Sumérjase en el Pacífico para nadar con los juguetones guardianes de la costa.\""}'::jsonb,
  '{"Lo que visitarás": ["Callao", "Islas Palomino", "El Frontón", "Fauna"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'islas_palomino', '09:00:00', TRUE
),
(
  'ANTIOQUIA PULL',
  'Visita al "pueblo de los cuentos", famoso por sus fachadas pintadas con flores y ángeles.',
  12, 1, 24.0, 78.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Antioquía: El Pueblo de Colores] La Experiencia: \"Entre en un libro de cuentos donde cada pared es un lienzo de flores y ángeles.\""}'::jsonb,
  '{"Lo que visitarás": ["Pueblo Pintado", "Iglesia", "Huertos", "Mirador"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'antioquia', '06:00:00', TRUE
),
(
  'PACHACAMAC + BARRANCO PULL',
  'Combinación de historia ancestral en Pachacamac y cultura moderna en el bohemio Barranco.',
  6, 1, 46.0, 153.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Lima: Pasado y Bohemio] La Experiencia: \"Atraviese el tiempo desde los rituales de barro de Pachacamac hasta el arte callejero de Barranco.\""}'::jsonb,
  '{"Lo que visitarás": ["Pachacamac", "Barranco", "Puente de los Suspiros", "Arte Urbano"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'pachacamac_barranco', '09:00:00', TRUE
),
(
  'CIRCUITO MAGICO DEL AGUA PULL',
  'Recorrido por las fuentes ornamentales más impresionantes de Lima con show de láser.',
  3, 1, 23.0, 75.0,
  'TURISMO', 'FACIL',
  '{"itinerario": "[Circuito Mágico: Fantasía Acuática] La Experiencia: \"Deje que la noche brille en una fantasía de agua y luz.\""}'::jsonb,
  '{"Lo que visitarás": ["Fuente Mágica", "Fuente de la Fantasía", "Túnel de las Sorpresas", "Parque de la Reserva"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'circuito_magico_del_agua', '18:00:00', TRUE
),
(
  'CITY TOUR LIMA COLONIAL Y MODERNA',
  'Recorrido histórico por el centro de Lima y los distritos costeros modernos.',
  4, 1, 30.0, 101.0,
  'CULTURA', 'FACIL',
  '{"itinerario": "[Lima: La Ciudad de los Reyes] La Experiencia: \"Viaje a través de los siglos en la Ciudad de los Reyes.\""}'::jsonb,
  '{"Lo que visitarás": ["Plaza Mayor", "Catedral de Lima", "Catacumbas San Francisco", "Miraflores", "Parque del Amor"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'city_tour_lima_colonial_y_moderna', '09:00:00', TRUE
);

INSERT INTO tour (
  nombre, descripcion, duracion_horas, duracion_dias, precio_adulto_extranjero, precio_adulto_nacional,
  categoria, dificultad, highlights, atractivos, servicios_incluidos, servicios_no_incluidos,
  carpeta_img, hora_inicio, activo
) VALUES 
(
  'TOUR GASTRONOMICO PERUANO',
  'Experiencia culinaria visitando mercados locales y participando en clases de cocina peruana.',
  4, 1, 104.0, 349.0,
  'GASTRONOMÍA', 'FACIL',
  '{"itinerario": "[Sabores del Perú: Aventura Culinaria] La Experiencia: \"Sumerja sus sentidos en la capital gastronómica de América y aprenda los secretos de su sabor.\""}'::jsonb,
  '{"Lo que visitarás": ["Mercado Local", "Clase de Cocina", "Degustación de Pisco", "Almuerzo"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'tour_gastronomico_peruano', '11:00:00', TRUE
),
(
  'CITY TOUR NOCTURNO',
  'Paseo panorámico por Lima iluminada, recorriendo los monumentos y barrios más emblemáticos.',
  3, 1, 78.0, 262.0,
  'CULTURA', 'FACIL',
  '{"itinerario": "[Luces de la Noche: Encanto Urbano] La Experiencia: \"Descubra una cara diferente de la ciudad cuando el sol se pone y las luces se encienden.\""}'::jsonb,
  '{"Lo que visitarás": ["Centro Histórico Iluminado", "Plaza San Martín", "Barranco", "Puente de los Suspiros"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'city_tour_nocturno', '18:00:00', TRUE
),
(
  'TOUR MISTICO',
  'Encuentro espiritual con las tradiciones andinas, lectura de coca y ceremonia de agradecimiento.',
  3, 1, 25.0, 82.0,
  'MÍSTICO', 'FACIL',
  '{"itinerario": "[Conexión Sagrada: Ritual Andino] La Experiencia: \"Conecte con la sabiduría ancestral de los Andes en una ceremonia privada de sanación.\""}'::jsonb,
  '{"Lo que visitarás": ["Altar Sagrado", "Chamán Andino", "Lectura de Coca", "Ofrenda a la Pachamama"]}'::jsonb,
  '{"incluye": ["Transporte", "Guia", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Gastos extras"]}'::jsonb,
  'tour_mistico', '09:00:00', TRUE
),
(
  'DIA LIBRE',
  'Día dedicado al descanso o actividades personales sin itinerario fijo.',
  0, 1, 0.00, 0.00,
  'LIBRE', 'FACIL',
  '{"itinerario": "[Día Libre: Su Propio Ritmo] La Experiencia: \"Disfrute de la libertad de explorar a su propio ritmo sin la presión de un horario.\""}'::jsonb,
  '{"Lo que visitarás": ["Exploración personal", "Gastronomía local", "Descanso", "Compras"]}'::jsonb,
  '{"incluye": ["Asistencia informativa"]}'::jsonb,
  '{"no_incluye": ["Guiado", "Transporte", "Entradas", "Alimentacion"]}'::jsonb,
  'dia_libre', '00:00:00', TRUE
),
(
  'RECEPCION EN EL AEROPUERTO',
  'Servicio de bienvenida y traslado privado desde el aeropuerto al hotel.',
  0, 1, 0.00, 0.00,
  'LOGISTICA', 'FACIL',
  '{"itinerario": "[Bienvenida al Perú: Comience su Aventura] La Experiencia: \"A su llegada, nuestro equipo lo estará esperando con una sonrisa.\""}'::jsonb,
  '{"Lo que visitarás": ["Recepción personalizada", "Traslado privado", "Asistencia de equipaje", "Briefing del viaje"]}'::jsonb,
  '{"incluye": ["Transporte privado", "Asistencia personalizada"]}'::jsonb,
  '{"no_incluye": ["Alimentación", "Propinas"]}'::jsonb,
  'recepcion_aeropuerto', '00:00:00', TRUE
),
(
  'DIA LIBRE Y SALIDA AL AEROPUERTO',
  'Mañana libre para las últimas compras y traslado programado al aeropuerto.',
  0, 1, 0.00, 0.00,
  'LOGISTICA', 'FACIL',
  '{"itinerario": "[Despedida: Memorias y Últimos Tesoros] La Experiencia: \"Aproveche sus últimas horas para comprar recuerdos y prepararse para su vuelo.\""}'::jsonb,
  '{"Lo que visitarás": ["Tiempo libre", "Recojo de hotel", "Traslado al aeropuerto", "Asistencia en embarque"]}'::jsonb,
  '{"incluye": ["Transporte privado", "Asistencia"]}'::jsonb,
  '{"no_incluye": ["Alimentación", "Gastos personales"]}'::jsonb,
  'dia_libre_salida', '00:00:00', TRUE
);




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
        EXECUTE format('DROP POLICY IF EXISTS "Acceso total" ON %I;', tabla_nombre);
        EXECUTE format('CREATE POLICY "Acceso total" ON %I FOR ALL USING (true) WITH CHECK (true);', tabla_nombre);
    END LOOP;
END $$;

-- Permisos storage (Ejecutar en panel SQL)
-- Requiere buckets 'itinerarios' y 'vouchers' creados como Públicos
DROP POLICY IF EXISTS "Acceso Público Itinerarios" ON storage.objects;
DROP POLICY IF EXISTS "Subida Libre Itinerarios" ON storage.objects;
DROP POLICY IF EXISTS "Acceso Público Vouchers" ON storage.objects;
DROP POLICY IF EXISTS "Subida Libre Vouchers" ON storage.objects;

CREATE POLICY "Acceso Público Itinerarios" ON storage.objects FOR SELECT USING (bucket_id = 'itinerarios');
CREATE POLICY "Subida Libre Itinerarios" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'itinerarios');
CREATE POLICY "Acceso Público Vouchers" ON storage.objects FOR SELECT USING (bucket_id = 'vouchers');
CREATE POLICY "Subida Libre Vouchers" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'vouchers');

-- ==============================================================
-- ✅ FIN DEL SCRIPT: INSTALACIÓN EXITOSA
-- ==============================================================
