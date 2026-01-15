from datetime import date, timedelta

# Simulación de 7 Ventas Ricas
MOCK_VENTAS = [
    {
        "id_venta": 101,
        "fecha_venta": "2024-01-05",
        "monto_total": 550.00,
        "vendedor": "Angel",
        "tour": "Machu Picchu Full Day",
        "id_cliente": 1,
        "nombre_cliente": "Juan Perez",
        "estado_venta": "CONFIRMADO",
        "moneda": "USD"
    },
    {
        "id_venta": 102,
        "fecha_venta": "2024-01-06",
        "monto_total": 120.00,
        "vendedor": "Abel",
        "tour": "Montaña 7 Colores",
        "id_cliente": 2,
        "nombre_cliente": "Maria Silva",
        "estado_venta": "PENDIENTE",
        "moneda": "USD"
    },
    {
        "id_venta": 103,
        "fecha_venta": "2024-01-08",
        "monto_total": 1200.00,
        "vendedor": "Angel",
        "tour": "Inca Jungle 4D/3N",
        "id_cliente": 3,
        "nombre_cliente": "Mike & Sarah",
        "estado_venta": "CONFIRMADO",
        "moneda": "USD"
    },
    {
        "id_venta": 104,
        "fecha_venta": "2024-01-10",
        "monto_total": 80.00,
        "vendedor": "Soporte",
        "tour": "City Tour Cusco",
        "id_cliente": 4,
        "nombre_cliente": "Carlos Diaz",
        "estado_venta": "CONFIRMADO",
        "moneda": "USD"
    },
    {
        "id_venta": 105,
        "fecha_venta": "2024-01-12",
        "monto_total": 350.00,
        "vendedor": "Abel",
        "tour": "Valle Sagrado VIP",
        "id_cliente": 5,
        "nombre_cliente": "Familia Wong",
        "estado_venta": "PENDIENTE",
        "moneda": "USD"
    },
    {
        "id_venta": 106,
        "fecha_venta": "2024-01-14",
        "monto_total": 900.00,
        "vendedor": "Angel",
        "tour": "Salkantay Trek",
        "id_cliente": 6,
        "nombre_cliente": "Backpackers Group",
        "estado_venta": "CONFIRMADO",
        "moneda": "USD"
    },
    {
        "id_venta": 107,
        "fecha_venta": "2024-01-14",
        "monto_total": 65.00,
        "vendedor": "Abel",
        "tour": "Laguna Humantay",
        "id_cliente": 7,
        "nombre_cliente": "Luis Gomez",
        "estado_venta": "CONFIRMADO",
        "moneda": "USD"
    }
]

# Simulación de Requerimientos Operativos
MOCK_REQS = [
    {"fecha_registro": "2024-01-06", "nombre": "CONSETTUR", "tipo_cliente": "B2B", "motivo": "BUSES MP JUAN PEREZ", "total": 24.00, "n_cuenta": "BCP 193..."},
    {"fecha_registro": "2024-01-08", "nombre": "PERURAIL", "tipo_cliente": "B2B", "motivo": "TRENES INCA JUNGLE", "total": 150.00, "n_cuenta": "INTERBANK 400..."},
    {"fecha_registro": "2024-01-10", "nombre": "BOLETO TURISTICO", "tipo_cliente": "B2C", "motivo": "CITY TOUR CARLOS", "total": 70.00, "n_cuenta": "CASH"},
    {"fecha_registro": "2024-01-14", "nombre": "ARRIERO JOSE", "tipo_cliente": "B2B", "motivo": "CABALLOS SALKANTAY", "total": 200.00, "n_cuenta": "EFECTIVO"},
]

# Simulación de Servicios Operativos (Para el calendario)
today = date.today()
MOCK_SERVICIOS = [
    {'ID Servicio': 1, 'Fecha': today.isoformat(), 'Hora': '06:00', 'Servicio': 'Recojo Aeropuerto', 'Pax': 2, 'Cliente': 'Juan Perez', 'Guía': 'Jorge', 'Estado Pago': '✅ SALDADO'},
    {'ID Servicio': 2, 'Fecha': today.isoformat(), 'Hora': '08:00', 'Servicio': 'Machu Picchu Full Day', 'Pax': 2, 'Cliente': 'Juan Perez', 'Guía': 'Maria', 'Estado Pago': '✅ SALDADO'},
    {'ID Servicio': 3, 'Fecha': (today + timedelta(days=1)).isoformat(), 'Hora': '04:30', 'Servicio': 'Montaña 7 Colores', 'Pax': 1, 'Cliente': 'Maria Silva', 'Guía': 'Por Asignar', 'Estado Pago': '🔴 PENDIENTE'},
    {'ID Servicio': 4, 'Fecha': (today + timedelta(days=2)).isoformat(), 'Hora': '05:00', 'Servicio': 'Inca Jungle Día 1', 'Pax': 4, 'Cliente': 'Mike & Sarah', 'Guía': 'Pedro', 'Estado Pago': '✅ SALDADO'},
    {'ID Servicio': 5, 'Fecha': (today + timedelta(days=3)).isoformat(), 'Hora': '07:00', 'Servicio': 'Valle Sagrado', 'Pax': 3, 'Cliente': 'Familia Wong', 'Guía': 'Juan', 'Estado Pago': '🔴 PENDIENTE'},
]
