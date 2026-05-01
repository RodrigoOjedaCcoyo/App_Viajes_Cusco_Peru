import sys
import os

# Añadir el path del proyecto para importar los módulos
sys.path.append('c:\\Sistema Viajes Cusco\\App_Viajes_Cusco_Peru')

from models.supabase_client import get_supabase_client

def migrate():
    client = get_supabase_client()
    
    # Supabase Python client doesn't support raw SQL easily via the API 
    # unless using a postgres-py connection or an RPC.
    # However, I can try to use a simple RPC if one exists, 
    # but usually, I can't run ALTER TABLE directly through PostgREST.
    
    # I will try to check if the columns exist by trying to fetch them.
    try:
        res = client.table('venta_servicio_proveedor').select('fecha_contratacion, contratado').limit(1).execute()
        print("Las columnas ya existen.")
        return
    except Exception as e:
        print("Las columnas no existen o hay un error:", e)
        print("Intentando sugerir SQL al usuario si el script no puede ejecutarlas.")

if __name__ == "__main__":
    migrate()
