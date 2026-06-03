"""Script de debug para ver los datos que extrae el panel de marketing."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["supabase"]["URL"]
SUPABASE_ANON_KEY = st.secrets["supabase"]["ANON_KEY"]
client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# 1. Total Leads
res_leads = client.table('lead').select('id_lead', count='exact').limit(1).execute()
total_leads = res_leads.count if res_leads.count is not None else 0
print(f"=== TOTAL LEADS EN SISTEMA: {total_leads} ===\n")

# 2. Total itinerarios
res = client.table('itinerario_digital').select('id_lead, fecha_generacion, datos_render').order('fecha_generacion', desc=True).execute()
data = res.data or []
print(f"=== TOTAL ITINERARIOS EN DB: {len(data)} ===\n")

# 3. Dedup por lead
leads_vistos = set()
data_unica = []
for d in data:
    id_lead = d.get('id_lead')
    if id_lead and id_lead not in leads_vistos:
        leads_vistos.add(id_lead)
        data_unica.append(d)
    elif not id_lead:
        data_unica.append(d)

print(f"=== ITINERARIOS ÚNICOS (1 por lead): {len(data_unica)} ===\n")

# 4. Mostrar primeros 5 como ejemplo
for i, d in enumerate(data_unica[:5]):
    raw = d.get('datos_render')
    if isinstance(raw, str):
        try: render = json.loads(raw)
        except: render = {}
    elif isinstance(raw, dict):
        render = raw
    else:
        render = {}
    
    precio = float(render.get('total_final_calculado') or render.get('precio_total') or render.get('total') or 0)
    origen = render.get('origen') or 'NO ESPECIFICADO'
    t1 = render.get('title_1') or ''
    t2 = render.get('title_2') or ''
    paquete = f"{t1} {t2}".strip() or 'Personalizado'
    
    itinerario_lista = render.get('itinerario') or render.get('days') or []
    tours = []
    if isinstance(itinerario_lista, list):
        for dia in itinerario_lista:
            if isinstance(dia, dict) and dia.get('titulo'):
                tours.append(dia['titulo'])
    
    print(f"--- Cotización #{i+1} ---")
    print(f"  Lead ID: {d.get('id_lead')}")
    print(f"  Fecha: {d.get('fecha_generacion')}")
    print(f"  Paquete: {paquete}")
    print(f"  Precio Total: ${precio:,.2f}")
    print(f"  Origen Nacionalidad: {origen}")
    print(f"  Tours ({len(tours)}):")
    for t in tours:
        print(f"    - {t}")
    print()
