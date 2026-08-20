import toml, os
from supabase import create_client

secrets = toml.load(os.path.join(os.path.dirname(__file__), '..', '.streamlit', 'secrets.toml'))
url = secrets['supabase']['URL']
key = secrets['supabase']['ANON_KEY']

client = create_client(url, key)

res = client.table('pasajero').select('*', count='exact').execute()
print("TOTAL PASAJEROS:", res.count)
print("Muestra de columnas del primer registro:")
if res.data:
    for k, v in res.data[0].items():
        print(f"  {k}: {v!r}")

print("\n--- Sample de 3 registros ---")
for r in res.data[:3]:
    print(r)
