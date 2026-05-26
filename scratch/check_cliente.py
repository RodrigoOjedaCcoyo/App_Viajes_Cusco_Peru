import sys
import os
from supabase import create_client
import toml

secrets = toml.load(os.path.join(".streamlit", "secrets.toml"))
url = secrets["supabase"]["URL"]
key = secrets["supabase"]["ANON_KEY"]

supabase = create_client(url, key)

try:
    res = supabase.table('cliente').select('*').limit(1).execute()
    print("Columnas de 'cliente':", res.data[0].keys() if res.data else "Tabla vacía")
except Exception as e:
    print("Error:", e)
