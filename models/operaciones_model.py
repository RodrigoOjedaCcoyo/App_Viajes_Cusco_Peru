# models/operaciones_model.py
from datetime import date
from typing import List, Dict, Any, Optional
from supabase import Client
from .base_model import BaseModel

# ----------------------------------------------------------------------
# CLASES MODELO CONECTADAS A SUPABASE (REAL)
# ----------------------------------------------------------------------

class VentaModel(BaseModel):
    def __init__(self, supabase_client: Client):
        super().__init__('venta', supabase_client, primary_key='id_venta')

class PasajeroModel(BaseModel):
    def __init__(self, supabase_client: Client):
        super().__init__('pasajero', supabase_client, primary_key='id_pasajero')
        
    def get_by_venta_id(self, venta_id: int) -> List[Dict[str, Any]]:
        """Obtiene todos los pasajeros de una venta."""
        try:
            res = self.client.table(self.table_name).select('*').eq('id_venta', venta_id).execute()
            return res.data
        except Exception as e:
            print(f"Error obteniendo pasajeros venta {venta_id}: {e}")
            return []
