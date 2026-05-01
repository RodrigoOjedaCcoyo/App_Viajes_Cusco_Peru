import sys
sys.path.append('c:\\Sistema Viajes Cusco\\App_Viajes_Cusco_Peru')
from models.supabase_client import get_supabase_client
client = get_supabase_client()
res = client.table('venta').select('id_venta, origen, telefono_cliente').order('id_venta', desc=True).limit(1).execute()
print(res.data)
