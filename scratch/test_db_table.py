import os
import re
from supabase import create_client

secrets_path = os.path.join(".streamlit", "secrets.toml")
url, key = None, None

if os.path.exists(secrets_path):
    with open(secrets_path, "r") as f:
        content = f.read()
        url_match = re.search(r'URL\s*=\s*"(.*?)"', content)
        key_match = re.search(r'ANON_KEY\s*=\s*"(.*?)"', content)
        if url_match: url = url_match.group(1)
        if key_match: key = key_match.group(1)

if url and key:
    supabase = create_client(url, key)
    print("Conectado a Supabase.")
    try:
        res = supabase.table('meta_mensual').select('*').limit(1).execute()
        print("Consulta exitosa:", res.data)
    except Exception as e:
        print("ERROR AL CONSULTAR TABLA 'meta_mensual':")
        print(e)
else:
    print("No se encontraron secretos.")
