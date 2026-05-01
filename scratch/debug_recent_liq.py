import toml
from supabase import create_client, Client
import os

def debug_recent():
    if not os.path.exists(".streamlit/secrets.toml"):
        return

    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["supabase"]["URL"]
    key = secrets["supabase"]["ANON_KEY"]
    
    supabase: Client = create_client(url, key)
    
    print("Últimos 10 servicios registrados en venta_servicio_proveedor:")
    
    res = supabase.table('venta_servicio_proveedor').select('id, id_venta, tipo_servicio, contratado, fecha_contratacion, terminado, fecha_confirmacion').order('id', desc=True).limit(10).execute()
    
    if res.data:
        import pandas as pd
        df = pd.DataFrame(res.data)
        print(df.to_string())
    else:
        print("No hay datos.")

if __name__ == "__main__":
    debug_recent()
