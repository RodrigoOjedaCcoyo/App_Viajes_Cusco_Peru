-- migración para agencias aliadas (B2B)

CREATE TABLE IF NOT EXISTS agencia_aliada (
    id_agencia SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    pais VARCHAR(100),
    celular VARCHAR(50),
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar agencias iniciales
INSERT INTO agencia_aliada (nombre, pais, celular) VALUES 
('Ulise Travel', 'Argentina', '+54 9 3534 2...'),
('Like Travel', 'Argentina', '+54 9 3517 6...'),
('Kuna Travel', 'Mexico', '+52 1 614 27...'),
('Guru Destinos', 'Argentina', '+54 9 11 645...'),
('Hector Mexico', 'Mexico', '+52 1 33 249...'),
('Rogelio', 'Brazil', '+55 48 8424...'),
('Willian', 'Bolivia', '+591 75137...'),
('Cave', 'Peru', '+51 982 167...');

-- Agregar columna a venta para vincular con agencia
ALTER TABLE venta ADD COLUMN IF NOT EXISTS id_agencia_aliada INTEGER REFERENCES agencia_aliada(id_agencia);
