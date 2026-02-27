
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

print("--- ACTUALIZANDO ESQUEMA DE BASE DE DATOS ---")
try:
    # Intento 1: Usando la API REST de Supabase (rpc) si existe un helper
    # Pero como es SQL crudo, lo mejor es usar psycopg2 si estuviera instalado, 
    # o pedir al usuario que lo corra. Dado que no puedo interactuar directamente 
    # con el SQL editor de Supabase desde aquí, usaré un truco:
    # A menudo se puede alterar la estructura si se tiene acceso directo, pero a través de REST (Data API) no se permite DDL (ALTER TABLE).
    # Sin embargo, voy a intentar ejecutar un comando RPC (Remote Procedure Call) si está disponible, 
    # o si no, proveeré el comando SQL exacto.
    pass
except Exception as e:
    print(f"Error: {e}")

print("--- VERIFICANDO COLUMNAS EXISTENTES ---")
try:
    # Intentamos leer la tabla pidiendo explícitamente la columna 'cantidad'
    res = supabase.table('venta_servicio_proveedor').select('cantidad').limit(1).execute()
    print("La columna 'cantidad' YA EXISTE.")
except Exception as e:
    print("La columna 'cantidad' NO EXISTE o hubo un error:")
    print(e)
    print("\n[!] IMPORTANTE: Debes ejecutar este SQL en el panel de Supabase:")
    print("ALTER TABLE venta_servicio_proveedor ADD COLUMN cantidad INTEGER DEFAULT 1;")
