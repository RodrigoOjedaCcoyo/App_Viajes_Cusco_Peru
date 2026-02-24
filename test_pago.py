import os
import re
from supabase import create_client, Client
from datetime import datetime

def test_pago():
    try:
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        with open(secrets_path, "r") as f:
            content = f.read()
            
        supa_url = re.search(r'URL\s*=\s*"([^"]+)"', content).group(1)
        supa_key = re.search(r'ANON_KEY\s*=\s*"([^"]+)"', content).group(1)
        
        supabase: Client = create_client(supa_url, supa_key)
        
        # Insert raw dict manually in venta to get an ID
        venta_res = supabase.table('venta').insert({
            "id_cliente": 1,
            "id_vendedor": 1,
            "precio_total_cierre": 100,
            "tour_nombre": "Test Tour"
        }).execute()
        
        if not venta_res.data:
            print("Failed to insert dummy venta")
            return
            
        id_venta = venta_res.data[0]['id_venta']
        print(f"Dummy Venta ID: {id_venta}")
        
        pago_data = {
            "id_venta": id_venta,
            "fecha_pago": datetime.now().strftime("%Y-%m-%d"),
            "monto_pagado": 50.0,
            "moneda": "USD",
            "metodo_pago": "EFECTIVO",
            "tipo_pago": "ADELANTO",
            "tipo_comprobante": "RECIBO SIMPLE"
        }
        
        try:
            res = supabase.table('pago').insert(pago_data).execute()
            print("PAGO SUCCESS:", res.data)
        except Exception as e:
            print("PAGO FAIL EXCEPTION:", repr(e))
            
    except Exception as e:
        print("GENERAL ERROR:", repr(e))

if __name__ == "__main__":
    test_pago()
