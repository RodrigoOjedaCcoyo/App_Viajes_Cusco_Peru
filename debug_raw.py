from supabase import create_client
import os
import streamlit as st

try:
    SUPABASE_URL = st.secrets["supabase"]["URL"]
    SUPABASE_ANON_KEY = st.secrets["supabase"]["ANON_KEY"]
except:
    print("Secrets not found in environment, make sure to run properly.")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def inspect_data():
    print("--- RAW DATA INSPECTION ---")
    
    # 1. Fetch simplified list of dates
    res = supabase.table('venta_tour').select('id, fecha_servicio').limit(10).execute()
    print("Sample Rows (id, fecha_servicio):")
    for row in res.data:
        print(row)

    # 2. Try the specific problematic query
    print("\n--- TEST QUERY ---")
    start = "2026-01-03" # Try simple format first
    # If the DB column is DATE, 'gte' with timestamp ISO might fail or behave oddly if not casted.
    # Let's try explicit range.
    
    q_start = "2026-01-03"
    q_end = "2026-01-04" 
    
    print(f"Querying: fecha_servicio >= {q_start} AND < {q_end}")
    
    res_query = (
        supabase.table('venta_tour')
        .select('*')
        .gte('fecha_servicio', q_start)
        .lt('fecha_servicio', q_end)
        .execute()
    )
    print(f"Found {len(res_query.data)} rows.")
    if res_query.data:
        print(res_query.data[0])

if __name__ == "__main__":
    inspect_data()
