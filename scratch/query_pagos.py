import os
import toml
from supabase import create_client
import json

secrets = toml.load(os.path.join(".streamlit", "secrets.toml"))
url = secrets["supabase"]["URL"]
key = secrets["supabase"]["ANON_KEY"]

client = create_client(url, key)
data = client.table('pago_operativo').select('id_pago_op, id_proveedor, id_venta, n_linea, metodo_pago, observaciones, observaciones_contables').order('created_at', desc=True).limit(20).execute().data
print(json.dumps(data, indent=2))
