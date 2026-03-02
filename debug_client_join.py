
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

print("--- DEBUG VENTA + CLIENTE ---")
try:
    res = supabase.table('venta').select('*, cliente(nombre)').order('created_at', desc=True).limit(1).execute()
    if res.data:
        v = res.data[0]
        print(f"ID VENTA: {v.get('id_venta')}")
        print(f"PAX: {v.get('num_pasajeros')}")
        print(f"CLIENTE OBJ: {v.get('cliente')}")
        if v.get('cliente'):
            print(f"CLIENTE NOMBRE: {v['cliente'].get('nombre')}")
    else:
        print("No se encontraron ventas.")
except Exception as e:
    print(f"Error: {e}")
