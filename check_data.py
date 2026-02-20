from supabase import create_client, Client

URL = "https://stdclpseaxjiyjhuqopi.supabase.co"
ANON_KEY = "sb_publishable_XoMIYpI1w3GF_UvFqcVTqQ_xJkTU2Mh"

try:
    supabase: Client = create_client(URL, ANON_KEY)

    # 1. Check venta_tour
    res = supabase.table('venta_tour').select('*', count='exact').execute()
    print(f"--- VENTA_TOUR table ---")
    print(f"Total count: {res.count}")
    if res.data:
        print("First 10 records:")
        for r in res.data[:10]:
            print(f"ID Venta: {r['id_venta']}, Fecha: {r['fecha_servicio']}, Servicio: {r.get('observacion')}")
    else:
        print("No records found in venta_tour.")

    # 2. Check venta
    res_v = supabase.table('venta').select('id_venta, fecha_inicio, fecha_fin', count='exact').limit(5).execute()
    print(f"\n--- VENTA table (sample) ---")
    for v in res_v.data:
        print(f"ID Venta: {v['id_venta']}, Inicio: {v.get('fecha_inicio')}, Fin: {v.get('fecha_fin')}")

except Exception as e:
    print("Error:", e)
