
# check_db_direct.py
import os
import re
from supabase import create_client

# Cargar secretos de Streamlit manualmente para evitar dependencias
secrets_path = os.path.join(".streamlit", "secrets.toml")
url = None
key = None

if os.path.exists(secrets_path):
    with open(secrets_path, "r") as f:
        content = f.read()
        url_match = re.search(r'URL\s*=\s*"(.*?)"', content)
        key_match = re.search(r'ANON_KEY\s*=\s*"(.*?)"', content)
        if url_match: url = url_match.group(1)
        if key_match: key = key_match.group(1)
else:
    print("No se encontró .streamlit/secrets.toml")
    exit(1)

if not url or not key:
    print("No se pudieron extraer las credenciales del secrets.toml")
    exit(1)

supabase = create_client(url, key)

print("--- REPORTE DE VENTAS EN DB ---")
res = supabase.table('venta').select('id_venta, fecha_venta, id_agencia_aliada, estado_liquidacion, monto_total').execute()
if res.data:
    febrero_b2c = 0
    total_sales = 0
    for v in res.data:
        total_sales += 1
        print(v)
        fecha = v.get('fecha_venta', '')
        es_b2c = v.get('id_agencia_aliada') is None
        es_finalizado = v.get('estado_liquidacion') == 'FINALIZADO'
        if '2026-02' in fecha and es_b2c:
            febrero_b2c += 1
    print(f"\nTotal Ventas: {total_sales}")
    print(f"Ventas B2C Febrero 2026: {febrero_b2c}")
else:
    print("No hay ventas en la tabla 'venta'.")

print("\n--- REPORTE DE ITINERARIOS EN DB ---")
res_it = supabase.table('itinerario_digital').select('id_itinerario_digital, nombre_pasajero, fecha_generacion').limit(5).execute()
if res_it.data:
    for it in res_it.data:
        print(it)
else:
    print("No hay itinerarios digitales.")
