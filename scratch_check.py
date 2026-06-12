import os
import sys
from supabase import create_client

URL = "https://stdclpseaxjiyjhuqopi.supabase.co"
ANON_KEY = "sb_publishable_XoMIYpI1w3GF_UvFqcVTqQ_xJkTU2Mh"

client = create_client(URL, ANON_KEY)

# Let's find sales that are active and have a currency of USD
res = client.table('venta').select('*, cliente(nombre)').eq('moneda', 'USD').order('fecha_creacion', desc=True).limit(5).execute()

for v in res.data:
    print(f"ID Venta: {v['id_venta']}, Cliente: {v.get('cliente', {}).get('nombre')}, Precio Total Cierre: {v['precio_total_cierre']}, TC: {v['tipo_cambio']}")
    
    # Get services
    res_s = client.table('venta_servicio_proveedor').select('*').eq('id_venta', v['id_venta']).execute()
    for s in res_s.data:
        print(f"  Servicio: {s.get('tipo_servicio')}, Costo: {s.get('costo_unitario')}, Moneda: {s.get('moneda')}, TC: {s.get('tipo_cambio')}, Pax: {s.get('cantidad_pax')}")
