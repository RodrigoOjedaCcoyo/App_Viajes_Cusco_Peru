import os
import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta
import random

# Mock Streamlit Secrets for standalone run if needed, 
# but better to rely on `st.secrets` if running via `streamlit run` or just assuming env vars.
# Since we are running via `python populate_mock_data.py`, `st.secrets` might fail if not configured in .streamlit/secrets.toml
# However, the user environment seems to have it. I'll read from main.py's approach.
# If this fails, I'll ask user to ensure secrets are there, but main.py suggests they are.

try:
    # Try loading from secrets.toml by initializing streamlit context essentially, 
    # but `st.secrets` works if the file exists.
    SUPABASE_URL = st.secrets["supabase"]["URL"]
    SUPABASE_ANON_KEY = st.secrets["supabase"]["ANON_KEY"]
except Exception as e:
    print("Error loading secrets:", e)
    print("Please ensure .streamlit/secrets.toml exists.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def populate_data():
    print("Starting data population for January 2026...")

    # 1. Create Dummy Clients
    clientes = ["Juan Perez", "Maria Gomez", "Carlos Smith", "Elena Tour", "Grupo Viajeros"]
    ids_clientes = []
    
    for name in clientes:
        # Check exist
        res = supabase.table('cliente').select('id_cliente').eq('nombre', name).execute()
        if res.data:
            ids_clientes.append(res.data[0]['id_cliente'])
        else:
            data = {"nombre": name, "tipo_cliente": "B2C", "pais": "Peru"}
            res_ins = supabase.table('cliente').insert(data).select('id_cliente').execute()
            if res_ins.data:
                ids_clientes.append(res_ins.data[0]['id_cliente'])
                print(f"Created Cliente: {name}")

    if not ids_clientes:
        print("Failed to create clients.")
        return

    # 2. Get Some Tours (Assuming they exist, or create mock)
    # Just checking first
    res_tours = supabase.table('tour').select('id_tour').limit(5).execute()
    ids_tours = [t['id_tour'] for t in res_tours.data]
    
    if not ids_tours:
        # Create Dummy Tour if none
        res_ins_t = supabase.table('tour').insert({"nombre": "City Tour Cusco Mock", "duracion_dias": 1}).select('id_tour').execute()
        ids_tours.append(res_ins_t.data[0]['id_tour'])

    # 3. Create Sales & Services (Venta_Tour) for Jan 2026
    start_date = date(2026, 1, 1)
    
    # Create ~10 entries spread across first week
    for i in range(10):
        day_offset = random.randint(0, 5) # Jan 1 to Jan 6
        op_date = start_date + timedelta(days=day_offset)
        
        # Select Random Client & Tour
        cli_id = random.choice(ids_clientes)
        tour_id = random.choice(ids_tours)
        pax = random.randint(1, 5)
        
        # INSERT VENTA
        venta_data = {
            "id_cliente": cli_id,
            "id_vendedor": 1, # Assume ID 1 exists
            "fecha_venta": "2025-12-01", # Sold previously
            "estado_venta": "CONFIRMADO",
            "precio_total_cierre": pax * 100,
            "moneda": "USD"
        }
        res_v = supabase.table('venta').insert(venta_data).select('id_venta').execute()
        if not res_v.data: continue
        
        new_venta_id = res_v.data[0]['id_venta']
        
        # INSERT VENTA_TOUR (Service)
        vt_data = {
            "id_venta": new_venta_id,
            "id_tour": tour_id,
            "fecha_servicio": op_date.isoformat(),
            "cantidad_pasajeros": pax, 
            # guia_asignado is handled by our app as update, initially null
        }
        supabase.table('venta_tour').insert(vt_data).execute()
        
        # INSERT PASSENGERS & DOCS (For Risk Dashboard)
        # Add 1 passenger per pax
        for p in range(pax):
            pas_data = {
                "id_venta": new_venta_id,
                "nombre": f"Pax {p+1} of {cli_id}",
                "edad": 30
            }
            res_p = supabase.table('pasajero').insert(pas_data).select('id_pasajero').execute()
            if res_p.data:
                pid = res_p.data[0]['id_pasajero']
                # Add Document Requirement (Passport)
                doc_data = {
                    "id_pasajero": pid,
                    "tipo_documento": "Pasaporte",
                    "es_critico": True,
                    "estado_entrega": "PENDIENTE",
                    "fecha_entrega": None
                }
                supabase.table('documentacion').insert(doc_data).execute()
                
        print(f"Generated Venta {new_venta_id} for Date {op_date} with {pax} pax.")

    print("Data Population Complete.")

if __name__ == "__main__":
    populate_data()
