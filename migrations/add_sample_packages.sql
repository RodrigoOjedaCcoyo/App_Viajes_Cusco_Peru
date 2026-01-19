-- Migración: Paquetes de Prueba para B2B
-- Usamos IDs altos para no chocar con los automáticos si se desea, o simplemente INSERT

INSERT INTO paquete (id_paquete, nombre, descripcion, dias, noches, precio_sugerido) VALUES 
(101, 'Cusco Clásico Mágico', 'Paquete de 4 días incluyendo Machu Picchu y City Tour', 4, 3, 550.00),
(102, 'Aventura Valle Sagrado', 'Paquete de 3 días enfocado en el Valle Sagrado y conexión a MP', 3, 2, 420.00)
ON CONFLICT (id_paquete) DO NOTHING;

-- Relacionar con tours existentes (asegurando que los tours IDs 1, 2, 3 existan según setup_total.sql)
INSERT INTO paquete_tour (id_paquete, id_tour, orden) VALUES 
(101, 2, 1), -- City Tour
(101, 1, 2), -- Machu Picchu
(102, 3, 1), -- Valle Sagrado
(102, 1, 2)  -- Machu Picchu
ON CONFLICT DO NOTHING;
