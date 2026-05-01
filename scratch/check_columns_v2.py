import toml
from supabase import create_client, Client
import os

def check():
    if not os.path.exists(".streamlit/secrets.toml"):
        print("Error: .streamlit/secrets.toml no encontrado")
        return

    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["supabase"]["URL"]
    key = secrets["supabase"]["ANON_KEY"]
    
    supabase: Client = create_client(url, key)
    
    print(f"Conectado a {url}")
    
    try:
        # Intentar seleccionar las nuevas columnas
        res = supabase.table('venta_servicio_proveedor').select('fecha_contratacion, contratado').limit(1).execute()
        print("✅ Las columnas ya existen en la base de datos.")
    except Exception as e:
        print("❌ Las columnas NO existen o hay un problema de permisos.")
        print(f"Detalle: {e}")
        print("\nSugerencia: Ejecuta el siguiente SQL en el panel de Supabase:")
        print("ALTER TABLE venta_servicio_proveedor ADD COLUMN IF NOT EXISTS fecha_contratacion DATE, ADD COLUMN IF NOT EXISTS contratado BOOLEAN DEFAULT FALSE;")

if __name__ == "__main__":
    check()
