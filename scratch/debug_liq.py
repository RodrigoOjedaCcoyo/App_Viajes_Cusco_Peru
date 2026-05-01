import toml
from supabase import create_client, Client
import os
import sys

def debug_sale(id_venta):
    if not os.path.exists(".streamlit/secrets.toml"):
        print("Error: .streamlit/secrets.toml no encontrado")
        return

    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["supabase"]["URL"]
    key = secrets["supabase"]["ANON_KEY"]
    
    supabase: Client = create_client(url, key)
    
    print(f"Debug de la venta ID: {id_venta}")
    
    res = supabase.table('venta_servicio_proveedor').select('*').eq('id_venta', id_venta).execute()
    
    if res.data:
        for i, row in enumerate(res.data):
            print(f"\n--- Fila {i+1} ---")
            print(f"ID: {row.get('id')}")
            print(f"Tipo: {row.get('tipo_servicio')}")
            print(f"Contratado: {row.get('contratado')}")
            print(f"F. Contratacion: {row.get('fecha_contratacion')}")
            print(f"Confirmado: {row.get('terminado')}")
            print(f"F. Confirmacion: {row.get('fecha_confirmacion')}")
    else:
        print("No se encontraron liquidaciones para esta venta.")

if __name__ == "__main__":
    # El ID de la venta parece ser un entero según el código
    # Pero vamos a intentar obtener el último ID cargado si es posible o pedirlo.
    # En el screenshot no se ve el ID, pero puedo intentar buscar las más recientes.
    debug_sale(id_venta=104) # Un ID de ejemplo si supiera, pero mejor busco los recientes
