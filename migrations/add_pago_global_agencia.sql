-- migración para "Pago Global por Agencia" (Cuentas por Cobrar B2B)
-- Permite registrar un depósito contra la deuda total de una agencia y repartirlo
-- automáticamente entre sus ventas pendientes (de la más antigua a la más nueva).

-- 1. Registro de cada depósito global recibido
CREATE TABLE IF NOT EXISTS deposito_agencia (
    id_deposito SERIAL PRIMARY KEY,
    id_agencia_aliada INTEGER REFERENCES agencia_aliada(id_agencia) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    moneda VARCHAR(10) NOT NULL CHECK (moneda IN ('USD', 'PEN')),
    tipo_cambio DECIMAL(10,4),
    metodo_pago VARCHAR(50),
    observaciones TEXT,
    monto_aplicado DECIMAL(10,2) DEFAULT 0,
    monto_sobrante DECIMAL(10,2) DEFAULT 0,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Trazabilidad: de qué depósito global viene cada pago individual
ALTER TABLE pago ADD COLUMN IF NOT EXISTS id_deposito_agencia INTEGER REFERENCES deposito_agencia(id_deposito) ON DELETE SET NULL;

-- 3. Saldo a favor de cada agencia, por moneda (lo que sobra de un depósito hasta que se aplique a una venta futura)
ALTER TABLE agencia_aliada ADD COLUMN IF NOT EXISTS credito_pen DECIMAL(10,2) DEFAULT 0;
ALTER TABLE agencia_aliada ADD COLUMN IF NOT EXISTS credito_usd DECIMAL(10,2) DEFAULT 0;
