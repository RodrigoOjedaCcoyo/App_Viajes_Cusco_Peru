-- ==============================================================
-- SECCIÓN 1: TABLAS DE AUTENTICACIÓN Y ROLES
-- ==============================================================

CREATE TABLE usuarios_app (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL CHECK (rol IN ('VENTAS', 'OPERACIONES', 'CONTABILIDAD', 'GERENCIA')),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE usuarios_app IS 'Usuarios con acceso al sistema por email y rol';
COMMENT ON COLUMN usuarios_app.rol IS 'Rol del usuario: VENTAS, OPERACIONES, CONTABILIDAD o GERENCIA';

-- ==============================================================
-- SECCIÓN 2: NÚCLEO COMERCIAL
-- ==============================================================

CREATE TABLE vendedor (
    id_vendedor SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE, -- Agregado para vinculación con usuarios_app
    url_empresa VARCHAR(255),  -- Agregado para firmas/logos en PDFs
    estado VARCHAR(20) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    fecha_ingreso DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE vendedor IS 'Vendedores de la agencia (solo nombre para asignaciones)';

CREATE TABLE lead (
    id_lead SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor) ON DELETE SET NULL,
    numero_celular VARCHAR(20) NOT NULL,
    red_social VARCHAR(50),
    estrategia_venta VARCHAR(50) DEFAULT 'General' CHECK (estrategia_venta IN ('Opciones', 'Matriz', 'General')),
    fecha_seguimiento DATE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    pais_origen VARCHAR(100) DEFAULT 'Nacional' CHECK (pais_origen IN ('Nacional', 'Extranjero', 'Mixto')),
    ultimo_itinerario_id UUID
);

COMMENT ON TABLE lead IS 'Clientes potenciales en proceso de conversión';
COMMENT ON COLUMN lead.fecha_seguimiento IS 'Fecha para recordatorio de contacto o última vez contactado';
COMMENT ON COLUMN lead.pais_origen IS 'País detectado automáticamente por código de teléfono (+51=Perú, +54=Argentina, etc)';
COMMENT ON COLUMN lead.ultimo_itinerario_id IS 'UUID del último itinerario generado para este lead';

CREATE TABLE cliente (
    id_cliente SERIAL PRIMARY KEY,
    id_lead INTEGER REFERENCES lead(id_lead) ON DELETE SET NULL,
    tipo_cliente VARCHAR(50) DEFAULT 'B2C' CHECK (tipo_cliente IN ('B2C', 'B2B')),
    documento_identidad VARCHAR(50),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
);

COMMENT ON TABLE cliente IS 'Clientes de la agencia (leads convertidos que ya compraron)';
COMMENT ON COLUMN cliente.id_lead IS 'Referencia al lead original (para obtener nombre, teléfono, email, país)';
COMMENT ON COLUMN cliente.tipo_cliente IS 'B2C=Individual, B2B=Otra agencia de viajes';
COMMENT ON COLUMN cliente.documento_identidad IS 'DNI/RUC/Pasaporte para facturación (se llena después si es necesario)';


-- ==============================================================
-- SECCIÓN 3: CATÁLOGO DE PRODUCTOS
-- ==============================================================

CREATE TABLE tour ( --> Falta a los lugares que va a visitar tu que piensas
    id_tour SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    duracion_horas INTEGER,
    duracion_dias INTEGER,
    precio_base_usd DECIMAL(10,2),
    precio_nacional DECIMAL(10,2),
    categoria VARCHAR(50),
    dificultad VARCHAR(20) CHECK (dificultad IN ('FACIL', 'MODERADO', 'DIFICIL', 'EXTREMO')),
    highlights JSONB,
    atractivos JSONB,
    servicios_incluidos JSONB,
    servicios_no_incluidos JSONB,
    carpeta_img VARCHAR(255),
    hora_inicio TIMESTAMP WITH TIME ZONE,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tour IS 'Catálogo de tours individuales ofrecidos por la agencia';
COMMENT ON COLUMN tour.highlights IS 'Puntos clave del tour en formato JSON para PDFs premium';
COMMENT ON COLUMN tour.servicios_incluidos IS 'Servicios incluidos con íconos SVG para diseño visual';
COMMENT ON COLUMN tour.servicios_no_incluidos IS 'Servicios NO incluidos para PDFs';

CREATE TABLE paquete (
    id_paquete SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    dias INTEGER NOT NULL,
    noches INTEGER NOT NULL,
    precio_sugerido DECIMAL(10,2),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE paquete IS 'Paquetes prediseñados (combinaciones de tours)';
COMMENT ON COLUMN paquete.precio_sugerido IS 'Precio de referencia del paquete (puede estar vacío y calcularse después)';

CREATE TABLE paquete_tour (
    id_paquete INTEGER REFERENCES paquete(id_paquete) ON DELETE CASCADE,
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE RESTRICT,
    orden INTEGER NOT NULL,
    dia_del_paquete INTEGER,
    PRIMARY KEY (id_paquete, id_tour, orden)
);

COMMENT ON TABLE paquete_tour IS 'Relación entre paquetes y tours (composición)';
COMMENT ON COLUMN paquete_tour.dia_del_paquete IS 'En qué día del paquete se realiza este tour';

CREATE TABLE catalogo_tours_imagenes (
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE CASCADE PRIMARY KEY,
    urls_imagenes JSONB DEFAULT '[]'::jsonb,
    url_principal TEXT,
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE catalogo_tours_imagenes IS 'Galería de imágenes para cada tour del catálogo';

-- ==============================================================
-- SECCIÓN 4: ITINERARIOS DIGITALES
-- ==============================================================

CREATE TABLE itinerario_digital (
    id_itinerario_digital UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    id_lead INTEGER REFERENCES lead(id_lead) ON DELETE SET NULL,
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor) ON DELETE SET NULL,
    id_paquete INTEGER REFERENCES paquete(id_paquete) ON DELETE SET NULL,
    nombre_pasajero_itinerario VARCHAR(255),
    datos_render JSONB NOT NULL,
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE itinerario_digital IS 'Itinerarios digitales generados con el Constructor Premium (guardados como JSON y PDF)';
COMMENT ON COLUMN itinerario_digital.datos_render IS 'JSON completo del itinerario para regenerar PDF o editar después';
COMMENT ON COLUMN itinerario_digital.fecha_envio IS 'Cuándo se envió el itinerario al cliente (NULL si aún no se envió)';

-- ==============================================================
-- SECCIÓN 5: VENTAS Y PAGOS (CORRECCIÓN CRÍTICA APLICADA)
-- ==============================================================

CREATE TABLE venta (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INTEGER REFERENCES cliente(id_cliente) ON DELETE RESTRICT,
    id_vendedor INTEGER REFERENCES vendedor(id_vendedor) ON DELETE RESTRICT,
    id_itinerario_digital UUID REFERENCES itinerario_digital(id_itinerario_digital) ON DELETE SET NULL,
    id_paquete INTEGER REFERENCES paquete(id_paquete) ON DELETE SET NULL,
    fecha_venta DATE DEFAULT CURRENT_DATE NOT NULL,
    fecha_inicio DATE, -- Auto-llenado desde itinerario
    fecha_fin DATE,    -- Auto-llenado desde itinerario
    precio_total_cierre DECIMAL(10,2) NOT NULL, 
    costo_total DECIMAL(10,2) DEFAULT 0,
    utilidad_bruta DECIMAL(10,2) DEFAULT 0,
    moneda VARCHAR(10) DEFAULT 'USD' CHECK (moneda IN ('USD', 'PEN', 'EUR')),
    tipo_cambio DECIMAL(8,4),
    estado_venta VARCHAR(50) DEFAULT 'CONFIRMADO' CHECK (estado_venta IN ('CONFIRMADO', 'EN_VIAJE', 'COMPLETADO', 'CANCELADO')),
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

COMMENT ON TABLE venta IS 'Ventas confirmadas de la agencia (convertidas desde leads o directas)';
COMMENT ON COLUMN venta.fecha_inicio IS 'Fecha de inicio del viaje (para calendario de operaciones)';
COMMENT ON COLUMN venta.fecha_fin IS 'Fecha de finalización del viaje';
COMMENT ON COLUMN venta.tour_nombre IS 'Nombre del tour cuando no está en catálogo (tours externos/personalizados)';

CREATE TABLE venta_tour ( 
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    n_linea INTEGER NOT NULL,
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE RESTRICT,
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor) ON DELETE SET NULL, -- Agregado para liquidación rápida
    fecha_servicio DATE NOT NULL,
    hora_inicio TIME, 
    precio_applied DECIMAL(10,2),
    costo_applied DECIMAL(10,2),
    moneda_costo VARCHAR(10) DEFAULT 'USD', -- Agregado para liquidación multimoneda
    cantidad_pasajeros INTEGER DEFAULT 1,
    punto_encuentro VARCHAR(255),
    observaciones TEXT,                   -- ✅ Usado para nombres de tours diarios específicos
    id_itinerario_dia_index INTEGER,
    estado_servicio VARCHAR(30) DEFAULT 'PENDIENTE' CHECK (estado_servicio IN ('PENDIENTE', 'CONFIRMADO', 'EN_CURSO', 'COMPLETADO', 'CANCELADO')),
    es_endoso BOOLEAN DEFAULT FALSE,      -- Movido desde ALTER TABLE para definición limpia
    PRIMARY KEY (id_venta, n_linea)
);

COMMENT ON TABLE venta_tour IS 'Detalles de servicios/tours por venta (permite múltiples días)';
COMMENT ON COLUMN venta_tour.observaciones IS 'Nombre específico del tour del día (ej: "CITY TOUR CUSCO IMPERIAL")';
COMMENT ON COLUMN venta_tour.n_linea IS 'Número de línea secuencial (permite expandir 1 venta en N días de viaje)';

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

COMMENT ON TABLE pago IS 'Registro de pagos realizados por clientes';

-- ==============================================================
-- SECCIÓN 6: OPERACIONES Y LOGÍSTICA
-- ==============================================================

CREATE TABLE pasajero (
    id_pasajero SERIAL PRIMARY KEY,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE CASCADE,
    nombre_completo VARCHAR(255) NOT NULL,
    nacionalidad VARCHAR(100),
    numero_documento VARCHAR(50),
    tipo_documento VARCHAR(20) CHECK (tipo_documento IN ('DNI', 'PASAPORTE', 'CARNET_EXTRANJERIA', 'OTRO')),
    fecha_nacimiento DATE,
    genero VARCHAR(20),
    cuidados_especiales TEXT, -- Antes 'alergias', incluye restricciones o cuidados específicos
    contacto_emergencia_nombre VARCHAR(255),
    contacto_emergencia_telefono VARCHAR(20),
    es_principal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pasajero IS 'Datos de pasajeros asociados a una venta (puede haber múltiples por venta)';

CREATE TABLE documentacion (  --> Esta demas esta carpeta o tu que piensas
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

COMMENT ON TABLE documentacion IS 'Documentos de pasajeros (pasaportes, visas, seguros, etc)';

-- NOTA: Los guías ahora están UNIFICADOS en la tabla PROVEEDOR
-- tipo_proveedor = 'GUIA_FREELANCE' para guías
-- Asignación mediante venta_servicio_proveedor con tipo_servicio = 'GUIA'

CREATE TABLE requerimiento (
    id SERIAL PRIMARY KEY,
    id_venta INTEGER REFERENCES venta(id_venta) ON DELETE SET NULL,
    tipo_requerimiento VARCHAR(50) CHECK (tipo_requerimiento IN ('TRANSPORTE', 'ALOJAMIENTO', 'ALIMENTACION', 'GUIA', 'TICKETS', 'OTRO')),
    proveedor VARCHAR(255),
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

COMMENT ON TABLE requerimiento IS 'Requerimientos operativos (transporte, guías, tickets, etc)';

-- ==============================================================
-- SECCIÓN 6.5: GESTIÓN DE PROVEEDORES Y ENDOSOS
-- ==============================================================

-- Catálogo maestro de proveedores externos
CREATE TABLE proveedor (
    id_proveedor SERIAL PRIMARY KEY,
    nombre_comercial VARCHAR(255) NOT NULL,
    razon_social VARCHAR(255),
    ruc VARCHAR(20),
    servicios_ofrecidos TEXT[], -- Array: {'TRANSPORTE', 'GUIA', 'HOTEL'}
    contacto_nombre VARCHAR(100),
    contacto_telefono VARCHAR(20),
    contacto_email VARCHAR(100),
    direccion TEXT,
    ciudad VARCHAR(100),
    pais VARCHAR(100) DEFAULT 'Perú',
    banco VARCHAR(100),
    cuenta_bancaria VARCHAR(50),
    cuenta_interbancaria VARCHAR(50),
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

COMMENT ON TABLE proveedor IS 'Catálogo de empresas proveedoras (una empresa puede brindar varios servicios como transporte, hotel, etc)';
COMMENT ON COLUMN proveedor.servicios_ofrecidos IS 'Lista de servicios que la empresa es capaz de brindar (Array)';
COMMENT ON COLUMN proveedor.plazo_pago_dias IS 'Días de crédito otorgado por la empresa (0 = pago inmediato)';

-- Proveedores predefinidos por tour (plantilla)
CREATE TABLE tour_proveedor_predefinido (
    id SERIAL PRIMARY KEY,
    id_tour INTEGER REFERENCES tour(id_tour) ON DELETE CASCADE,
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor) ON DELETE RESTRICT,
    tipo_servicio VARCHAR(50) CHECK (tipo_servicio IN (
        'TRANSPORTE', 'ALOJAMIENTO', 'ALIMENTACION', 
        'GUIA', 'TICKETS', 'OTRO'
    )),
    costo_estimado DECIMAL(10,2),
    moneda VARCHAR(10) DEFAULT 'USD',
    dias_anticipo_reserva INTEGER,
    es_obligatorio BOOLEAN DEFAULT TRUE,
    notas TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(id_tour, id_proveedor, tipo_servicio)
);

COMMENT ON TABLE tour_proveedor_predefinido IS 'Configuración de proveedores típicos por tour (plantilla para nuevas ventas)';
COMMENT ON COLUMN tour_proveedor_predefinido.dias_anticipo_reserva IS 'Días de anticipación requeridos para reservar con este proveedor';

-- Proveedores reales asignados a cada servicio de una venta
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
    FOREIGN KEY (id_venta, n_linea) REFERENCES venta_tour(id_venta, n_linea) ON DELETE CASCADE
);

COMMENT ON TABLE venta_servicio_proveedor IS 'Proveedores reales asignados a cada servicio de una venta (costos operativos reales)';
COMMENT ON COLUMN venta_servicio_proveedor.confirmado IS 'TRUE cuando el proveedor confirmó la reserva';

-- Historial de pagos realizados a proveedores (permite pagos en cuotas)
CREATE TABLE pago_proveedor (
    id_pago_proveedor SERIAL PRIMARY KEY,
    id_venta_servicio_proveedor INTEGER REFERENCES venta_servicio_proveedor(id) ON DELETE CASCADE,
    fecha_pago DATE NOT NULL DEFAULT CURRENT_DATE,
    monto DECIMAL(10,2) NOT NULL CHECK (monto > 0),
    moneda VARCHAR(10) DEFAULT 'USD',
    tipo_cambio DECIMAL(8,4),
    metodo_pago VARCHAR(50) CHECK (metodo_pago IN (
        'TRANSFERENCIA', 'EFECTIVO', 'CHEQUE', 'DEPOSITO', 'YAPE', 'PLIN', 'OTRO'
    )),
    numero_operacion VARCHAR(100),
    banco VARCHAR(100),
    url_comprobante TEXT,
    pagado_por INTEGER REFERENCES vendedor(id_vendedor),
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pago_proveedor IS 'Historial de pagos realizados a proveedores (permite pagos parciales/cuotas)';

-- Endosos: Tercerización completa de servicios a otras agencias operadoras
CREATE TABLE endoso (
    id_endoso SERIAL PRIMARY KEY,
    id_venta INTEGER,
    n_linea INTEGER,
    id_proveedor_operador INTEGER REFERENCES proveedor(id_proveedor) ON DELETE RESTRICT,
    precio_venta_cliente DECIMAL(10,2) NOT NULL,
    costo_endoso DECIMAL(10,2) NOT NULL,
    comision_agencia DECIMAL(10,2) GENERATED ALWAYS AS (precio_venta_cliente - costo_endoso) STORED,
    porcentaje_comision DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN precio_venta_cliente > 0 
            THEN ((precio_venta_cliente - costo_endoso) / precio_venta_cliente * 100)
            ELSE 0 
        END
    ) STORED,
    fecha_confirmacion DATE,
    codigo_reserva_operador VARCHAR(100),
    nombre_contacto_operador VARCHAR(100),
    telefono_contacto VARCHAR(20),
    estado VARCHAR(30) DEFAULT 'PENDIENTE' CHECK (estado IN (
        'PENDIENTE', 'CONFIRMADO', 'EN_CURSO', 'COMPLETADO', 'CANCELADO'
    )),
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_venta, n_linea) REFERENCES venta_tour(id_venta, n_linea) ON DELETE CASCADE,
    UNIQUE(id_venta, n_linea)
);

COMMENT ON TABLE endoso IS 'Endosos: servicios tercerizados completamente a otras agencias operadoras';
COMMENT ON COLUMN endoso.comision_agencia IS 'Calculado automáticamente como diferencia entre precio venta y costo endoso';
COMMENT ON COLUMN endoso.porcentaje_comision IS 'Porcentaje de comisión sobre el precio de venta';

-- Tarifarios de proveedores (tarifas variables según temporada/volumen)
CREATE TABLE tarifario_proveedor (
    id SERIAL PRIMARY KEY,
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor) ON DELETE CASCADE,
    tipo_servicio VARCHAR(50),
    descripcion VARCHAR(255),
    temporada VARCHAR(50) CHECK (temporada IN ('ALTA', 'MEDIA', 'BAJA', 'ESPECIAL')),
    tarifa DECIMAL(10,2) NOT NULL,
    moneda VARCHAR(10) DEFAULT 'USD',
    vigencia_desde DATE NOT NULL,
    vigencia_hasta DATE,
    minimo_pax INTEGER,
    maximo_pax INTEGER,
    incluye TEXT,
    no_incluye TEXT,
    condiciones TEXT,
    activo BOOLEAN DEFAULT TRUE,
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tarifario_proveedor IS 'Tarifas de proveedores según temporada, fechas y número de pasajeros';
COMMENT ON COLUMN tarifario_proveedor.temporada IS 'Temporada turística: ALTA (junio-agosto), MEDIA, BAJA (diciembre-febrero)';

-- Evaluaciones de desempeño de proveedores
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
    aspectos_positivos TEXT,
    aspectos_mejorar TEXT,
    evaluado_por INTEGER REFERENCES vendedor(id_vendedor),
    fecha_evaluacion DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE evaluacion_proveedor IS 'Evaluaciones de desempeño de proveedores post-servicio';
COMMENT ON COLUMN evaluacion_proveedor.resolveria_contratar IS 'Si volvería a contratar al proveedor';

-- Documentación de proveedores (contratos, licencias, certificados)
CREATE TABLE documentacion_proveedor (
    id SERIAL PRIMARY KEY,
    id_proveedor INTEGER REFERENCES proveedor(id_proveedor) ON DELETE CASCADE,
    tipo_documento VARCHAR(50) CHECK (tipo_documento IN (
        'CONTRATO', 'RUC', 'LICENCIA_OPERACION', 'SEGURO_RESPONSABILIDAD',
        'CERTIFICADO_CALIDAD', 'ACREDITACION', 'OTRO'
    )),
    nombre_documento VARCHAR(255),
    url_archivo TEXT,
    fecha_emision DATE,
    fecha_vencimiento DATE,
    estado VARCHAR(30) DEFAULT 'VIGENTE' CHECK (estado IN ('VIGENTE', 'VENCIDO', 'POR_RENOVAR', 'CANCELADO')),
    alerta_dias_previos INTEGER DEFAULT 30,
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE documentacion_proveedor IS 'Documentos legales y operativos de proveedores (contratos, licencias, seguros)';
COMMENT ON COLUMN documentacion_proveedor.alerta_dias_previos IS 'Días de anticipación para alertar sobre vencimiento';

-- Modificación de tabla existente: requerimiento
ALTER TABLE requerimiento
ADD COLUMN id_proveedor INTEGER REFERENCES proveedor(id_proveedor) ON DELETE SET NULL,
ADD COLUMN id_venta_servicio_proveedor INTEGER REFERENCES venta_servicio_proveedor(id) ON DELETE SET NULL;

COMMENT ON COLUMN requerimiento.id_proveedor IS 'Proveedor asignado al requerimiento (reemplaza campo proveedor texto libre)';
COMMENT ON COLUMN requerimiento.id_venta_servicio_proveedor IS 'Vincula el requerimiento con el servicio de proveedor específico';

-- (Secciones de ALTER TABLE eliminadas porque se integraron en la definición original de venta_tour)

-- ==============================================================
-- SECCIÓN 7: ÍNDICES DE RENDIMIENTO
-- ==============================================================

-- Índices para búsquedas frecuentes
CREATE INDEX idx_lead_celular ON lead(numero_celular);
CREATE INDEX idx_lead_vendedor ON lead(id_vendedor);

CREATE INDEX idx_cliente_lead ON cliente(id_lead);
CREATE INDEX idx_cliente_tipo ON cliente(tipo_cliente);

CREATE INDEX idx_venta_cliente ON venta(id_cliente);
CREATE INDEX idx_venta_vendedor ON venta(id_vendedor);
CREATE INDEX idx_venta_fecha ON venta(fecha_venta);
CREATE INDEX idx_venta_fechas_viaje ON venta(fecha_inicio, fecha_fin);  -- ✅ Nuevo para calendario
CREATE INDEX idx_venta_estado ON venta(estado_venta) WHERE cancelada = FALSE;

CREATE INDEX idx_venta_tour_fecha ON venta_tour(fecha_servicio);  -- ✅ Crítico para dashboard operaciones
CREATE INDEX idx_venta_tour_servicio ON venta_tour(id_venta, n_linea);

CREATE INDEX idx_pago_venta ON pago(id_venta);
CREATE INDEX idx_pago_fecha ON pago(fecha_pago);

CREATE INDEX idx_itinerario_lead ON itinerario_digital(id_lead);
CREATE INDEX idx_itinerario_vendedor ON itinerario_digital(id_vendedor);
CREATE INDEX idx_itinerario_pasajero ON itinerario_digital(nombre_pasajero_itinerario);

-- Índices para módulo de proveedores
CREATE INDEX idx_proveedor_servicios ON proveedor USING GIN (servicios_ofrecidos); -- Índice para búsqueda en Array
CREATE INDEX idx_proveedor_nombre ON proveedor(nombre_comercial);
CREATE INDEX idx_proveedor_ruc ON proveedor(ruc);

CREATE INDEX idx_tour_prov_tour ON tour_proveedor_predefinido(id_tour) WHERE activo = TRUE;
CREATE INDEX idx_tour_prov_proveedor ON tour_proveedor_predefinido(id_proveedor);

CREATE INDEX idx_venta_serv_prov_venta ON venta_servicio_proveedor(id_venta, n_linea);
CREATE INDEX idx_venta_serv_prov_proveedor ON venta_servicio_proveedor(id_proveedor);
CREATE INDEX idx_venta_serv_prov_estado ON venta_servicio_proveedor(estado_pago) WHERE estado_pago IN ('PENDIENTE', 'VENCIDO', 'PAGADO_PARCIAL');
CREATE INDEX idx_venta_serv_prov_vencimiento ON venta_servicio_proveedor(fecha_vencimiento_pago) WHERE estado_pago != 'PAGADO';

CREATE INDEX idx_pago_prov_servicio ON pago_proveedor(id_venta_servicio_proveedor);
CREATE INDEX idx_pago_prov_fecha ON pago_proveedor(fecha_pago);

CREATE INDEX idx_endoso_venta ON endoso(id_venta, n_linea);
CREATE INDEX idx_endoso_operador ON endoso(id_proveedor_operador);
CREATE INDEX idx_endoso_estado ON endoso(estado) WHERE estado IN ('PENDIENTE', 'CONFIRMADO');

CREATE INDEX idx_tarifario_proveedor ON tarifario_proveedor(id_proveedor) WHERE activo = TRUE;
CREATE INDEX idx_tarifario_vigencia ON tarifario_proveedor(vigencia_desde, vigencia_hasta);

CREATE INDEX idx_eval_prov_proveedor ON evaluacion_proveedor(id_proveedor);
CREATE INDEX idx_eval_prov_fecha ON evaluacion_proveedor(fecha_evaluacion);

CREATE INDEX idx_doc_prov_proveedor ON documentacion_proveedor(id_proveedor);
CREATE INDEX idx_doc_prov_vencimiento ON documentacion_proveedor(fecha_vencimiento) WHERE estado IN ('VIGENTE', 'POR_RENOVAR');

-- ==============================================================
-- SECCIÓN 8: DATOS INICIALES (SEMILLAS)
-- ==============================================================

-- IMPORTANTE: Reemplazar TU_CORREO_MAESTRO@gmail.com con tu email real
INSERT INTO usuarios_app (email, rol) VALUES 
('gerencia@agencia.com', 'GERENCIA'),
('ventas@agencia.com', 'VENTAS'),
('operaciones@agencia.com', 'OPERACIONES'),
('contabilidad@agencia.com', 'CONTABILIDAD');

-- Vendedores iniciales
INSERT INTO vendedor (nombre) VALUES 
('Angel'),
('Abel');

-- ==============================================================
-- SECCIÓN 9: TRIGGERS Y FUNCIONES (AUTOMATIZACIÓN)
-- ==============================================================

-- Trigger para actualizar updated_at en tabla venta
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_venta_updated_at BEFORE UPDATE ON venta
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Función para sincronizar costo_total en venta desde servicios de proveedores
CREATE OR REPLACE FUNCTION sync_costo_venta_total()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE venta 
    SET costo_total = (
        SELECT COALESCE(SUM(costo_acordado), 0) 
        FROM venta_servicio_proveedor 
        WHERE id_venta = COALESCE(NEW.id_venta, OLD.id_venta)
    )
    WHERE id_venta = COALESCE(NEW.id_venta, OLD.id_venta);
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_sync_costo AFTER INSERT OR UPDATE OR DELETE ON venta_servicio_proveedor
    FOR EACH ROW EXECUTE FUNCTION sync_costo_venta_total();

-- Función para calcular utilidad bruta automáticamente al cambiar precio o costo
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
-- SECCIÓN 10: ROW LEVEL SECURITY (RLS)
-- ==============================================================

-- Habilitar RLS en todas las tablas principales
ALTER TABLE usuarios_app ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendedor ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead ENABLE ROW LEVEL SECURITY;
ALTER TABLE tour ENABLE ROW LEVEL SECURITY;
ALTER TABLE paquete ENABLE ROW LEVEL SECURITY;
ALTER TABLE itinerario_digital ENABLE ROW LEVEL SECURITY;
ALTER TABLE venta ENABLE ROW LEVEL SECURITY;
ALTER TABLE venta_tour ENABLE ROW LEVEL SECURITY;
ALTER TABLE pago ENABLE ROW LEVEL SECURITY;
ALTER TABLE pasajero ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE requerimiento ENABLE ROW LEVEL SECURITY;

-- Políticas permisivas para desarrollo (ajustar en producción según roles)
DO $$ 
DECLARE 
    tabla_nombre text;
BEGIN
    FOR tabla_nombre IN 
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS "Acceso total" ON %I;', tabla_nombre);
        EXECUTE format('CREATE POLICY "Acceso total" ON %I FOR ALL USING (true) WITH CHECK (true);', tabla_nombre);
    END LOOP;
END $$;

COMMENT ON POLICY "Acceso total" ON venta IS 'DESARROLLO: Política permisiva. AJUSTAR EN PRODUCCIÓN según roles de usuarios_app';

-- ==============================================================
-- SECCIÓN 11: POLÍTICAS DE STORAGE
-- ==============================================================

-- NOTA: Ejecutar DESPUÉS de crear los buckets en la UI de Supabase
-- Buckets requeridos: 'itinerarios' (público) y 'vouchers' (público)

DROP POLICY IF EXISTS "Acceso Público Itinerarios" ON storage.objects;
DROP POLICY IF EXISTS "Subida Libre Itinerarios" ON storage.objects;
DROP POLICY IF EXISTS "Acceso Público Vouchers" ON storage.objects;
DROP POLICY IF EXISTS "Subida Libre Vouchers" ON storage.objects;

CREATE POLICY "Acceso Público Itinerarios" ON storage.objects 
    FOR SELECT USING (bucket_id = 'itinerarios');
    
CREATE POLICY "Subida Libre Itinerarios" ON storage.objects 
    FOR INSERT WITH CHECK (bucket_id = 'itinerarios');

CREATE POLICY "Acceso P úblico Vouchers" ON storage.objects 
    FOR SELECT USING (bucket_id = 'vouchers');
    
CREATE POLICY "Subida Libre Vouchers" ON storage.objects 
    FOR INSERT WITH CHECK (bucket_id = 'vouchers');

-- ==============================================================
-- SECCIÓN 12: VISTAS ÚTILES PARA REPORTES
-- ==============================================================

-- Vista consolidada de ventas con información completa
CREATE OR REPLACE VIEW vista_ventas_completa AS
SELECT 
    v.id_venta,
    v.fecha_venta,
    v.fecha_inicio,
    v.fecha_fin,
    l.nombre as cliente_nombre,
    l.numero_celular as cliente_telefono,
    vend.nombre as vendedor_nombre,
    v.tour_nombre,
    v.precio_total_cierre,
    v.moneda,
    v.estado_venta,
    COALESCE(SUM(p.monto_pagado), 0) as total_pagado,
    v.precio_total_cierre - COALESCE(SUM(p.monto_pagado), 0) as saldo_pendiente,
    CASE 
        WHEN v.precio_total_cierre - COALESCE(SUM(p.monto_pagado), 0) <= 0.01 THEN 'SALDADO'
        ELSE 'PENDIENTE'
    END as estado_pago,
    v.num_pasajeros
FROM venta v
LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
LEFT JOIN lead l ON c.id_lead = l.id_lead
LEFT JOIN vendedor vend ON v.id_vendedor = vend.id_vendedor
LEFT JOIN pago p ON v.id_venta = p.id_venta
WHERE v.cancelada = FALSE
GROUP BY v.id_venta, l.nombre, l.numero_celular, vend.nombre;

COMMENT ON VIEW vista_ventas_completa IS 'Vista consolidada de ventas con estado de pago calculado';

-- Vista para dashboard de operaciones (servicios del día)
CREATE OR REPLACE VIEW vista_servicios_diarios AS
SELECT 
    vt.fecha_servicio,
    vt.id_venta,
    vt.n_linea,
    l.nombre as cliente,
    vend.nombre as vendedor,
    COALESCE(t.nombre, vt.observaciones, v.tour_nombre) as servicio,
    vt.cantidad_pasajeros as pax,
    vt.estado_servicio,
    (SELECT p.nombre_comercial 
     FROM venta_servicio_proveedor vsp 
     JOIN proveedor p ON vsp.id_proveedor = p.id_proveedor 
     WHERE vsp.id_venta = vt.id_venta 
       AND vsp.n_linea = vt.n_linea 
       AND vsp.tipo_servicio = 'GUIA' 
     LIMIT 1) as guia_asignado,
    v.id_itinerario_digital
FROM venta_tour vt
INNER JOIN venta v ON vt.id_venta = v.id_venta
LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
LEFT JOIN lead l ON c.id_lead = l.id_lead
LEFT JOIN vendedor vend ON v.id_vendedor = vend.id_vendedor
LEFT JOIN tour t ON vt.id_tour = t.id_tour
WHERE v.cancelada = FALSE
ORDER BY vt.fecha_servicio, vt.id_venta, vt.n_linea;

COMMENT ON VIEW vista_servicios_diarios IS 'Vista optimizada para el dashboard de operaciones (calendario)';

-- ==============================================================
-- SECCIÓN 12.1: VISTAS PARA GESTIÓN DE PROVEEDORES
-- ==============================================================

-- Vista: Servicios Pendientes de Pago a Proveedores
CREATE OR REPLACE VIEW vista_pagos_proveedores_pendientes AS
SELECT 
    vsp.id,
    vsp.id_venta,
    vsp.n_linea,
    vt.fecha_servicio,
    p.nombre_comercial as proveedor,
    vsp.tipo_servicio,
    vsp.costo_acordado,
    vsp.monto_total_pagado,
    vsp.costo_acordado - COALESCE(vsp.monto_total_pagado, 0) as saldo_pendiente,
    vsp.fecha_vencimiento_pago,
    CASE 
        WHEN vsp.fecha_vencimiento_pago < CURRENT_DATE THEN 'VENCIDO'
        WHEN vsp.fecha_vencimiento_pago <= CURRENT_DATE + INTERVAL '7 days' THEN 'POR_VENCER'
        ELSE vsp.estado_pago
    END as estado_pago_real,
    vsp.codigo_reserva,
    l.nombre_pasajero as cliente,
    v.tour_nombre,
    p.metodo_pago_preferido,
    p.cuenta_bancaria,
    p.contacto_telefono
FROM venta_servicio_proveedor vsp
INNER JOIN proveedor p ON vsp.id_proveedor = p.id_proveedor
INNER JOIN venta_tour vt ON vsp.id_venta = vt.id_venta AND vsp.n_linea = vt.n_linea
INNER JOIN venta v ON vt.id_venta = v.id_venta
INNER JOIN cliente c ON v.id_cliente = c.id_cliente
LEFT JOIN lead l ON c.id_lead = l.id_lead
WHERE vsp.estado_pago IN ('PENDIENTE', 'PAGADO_PARCIAL', 'VENCIDO')
  AND v.cancelada = FALSE
ORDER BY 
    CASE WHEN vsp.fecha_vencimiento_pago < CURRENT_DATE THEN 0 ELSE 1 END,
    vsp.fecha_vencimiento_pago, 
    vsp.costo_acordado DESC;

COMMENT ON VIEW vista_pagos_proveedores_pendientes IS 'Pagos pendientes a proveedores con alertas de vencimiento';

-- Vista: Utilidad Real por Venta (considerando costos de proveedores)
CREATE OR REPLACE VIEW vista_utilidad_real_ventas AS
SELECT 
    v.id_venta,
    v.fecha_venta,
    v.fecha_inicio,
    v.fecha_fin,
    l.nombre as cliente,
    vend.nombre as vendedor,
    v.tour_nombre,
    v.precio_total_cierre as ingreso_total,
    v.moneda,
    COALESCE(SUM(vsp.costo_acordado), 0) as total_costo_proveedores,
    v.precio_total_cierre - COALESCE(SUM(vsp.costo_acordado), 0) as utilidad_bruta,
    CASE 
        WHEN v.precio_total_cierre > 0 
        THEN ROUND(((v.precio_total_cierre - COALESCE(SUM(vsp.costo_acordado), 0)) / v.precio_total_cierre * 100)::numeric, 2)
        ELSE 0 
    END as margen_porcentaje,
    COUNT(DISTINCT vsp.id_proveedor) as num_proveedores,
    v.estado_venta
FROM venta v
LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
LEFT JOIN lead l ON c.id_lead = l.id_lead
LEFT JOIN vendedor vend ON v.id_vendedor = vend.id_vendedor
LEFT JOIN venta_tour vt ON v.id_venta = vt.id_venta
LEFT JOIN venta_servicio_proveedor vsp ON vt.id_venta = vsp.id_venta AND vt.n_linea = vsp.n_linea
WHERE v.cancelada = FALSE
GROUP BY v.id_venta, l.nombre, vend.nombre
ORDER BY v.fecha_venta DESC;

COMMENT ON VIEW vista_utilidad_real_ventas IS 'Utilidad real por venta considerando costos de proveedores';

-- Vista: Calificaciones Promedio de Proveedores
CREATE OR REPLACE VIEW vista_evaluacion_proveedores AS
SELECT 
    p.id_proveedor,
    p.nombre_comercial,
    p.servicios_ofrecidos,
    COUNT(ep.id) as total_evaluaciones,
    ROUND(AVG(ep.calificacion_general)::numeric, 2) as calificacion_promedio,
    ROUND(AVG(ep.puntualidad)::numeric, 2) as puntualidad_promedio,
    ROUND(AVG(ep.calidad_servicio)::numeric, 2) as calidad_promedio,
    ROUND(AVG(ep.relacion_precio_calidad)::numeric, 2) as relacion_precio_promedio,
    ROUND(AVG(ep.comunicacion)::numeric, 2) as comunicacion_promedio,
    SUM(CASE WHEN ep.resolveria_contratar = TRUE THEN 1 ELSE 0 END) as total_si_recontrataria,
    ROUND((SUM(CASE WHEN ep.resolveria_contratar = TRUE THEN 1 ELSE 0 END)::numeric / 
           NULLIF(COUNT(ep.id), 0) * 100), 2) as porcentaje_recomendacion,
    MAX(ep.fecha_evaluacion) as ultima_evaluacion,
    p.activo,
    p.contacto_telefono,
    p.contacto_email
FROM proveedor p
LEFT JOIN evaluacion_proveedor ep ON p.id_proveedor = ep.id_proveedor
GROUP BY p.id_proveedor
ORDER BY calificacion_promedio DESC NULLS LAST, total_evaluaciones DESC;

COMMENT ON VIEW vista_evaluacion_proveedores IS 'Calificaciones y estadísticas de desempeño de proveedores';

-- ==============================================================
-- FINALIZACIÓN Y PERMISOS
-- ==============================================================

-- Restaurar permisos del esquema public
GRANT USAGE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;

GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- ==============================================================
-- ✅ INSTALACIÓN COMPLETADA
-- ==============================================================
-- Próximos pasos:
-- 1. Verificar en Table Editor que todas las tablas se crearon correctamente
-- 2. Crear buckets 'itinerarios' y 'vouchers' en Storage (Públicos)
-- 3. Actualizar TU_CORREO_MAESTRO@gmail.com en la tabla usuarios_app
-- 4. Ejecutar git push para sincronizar código Python con nueva estructura
-- 5. Probar registro de venta con itinerario digital
-- ==============================================================
