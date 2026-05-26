import tomli
from supabase import create_client
import json

with open('.streamlit/secrets.toml', 'rb') as f:
    config = tomli.load(f)

client = create_client(config['SUPABASE_URL'], config['SUPABASE_KEY'])
data = client.table('pago_operativo').select('observaciones, observaciones_contables, n_linea').order('created_at', desc=False).limit(20).execute().data
print(json.dumps(data, indent=2))
