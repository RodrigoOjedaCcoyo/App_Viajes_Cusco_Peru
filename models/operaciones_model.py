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

class DocumentacionModel(BaseModel):
    def __init__(self, supabase_client: Client):
        # Según esquema SQL, usa 'id' como bigint
        super().__init__('documentacion', supabase_client, primary_key='id')
        
    def get_documentos_by_venta_id(self, id_venta: int) -> List[Dict[str, Any]]:
        try:
            # Paso A: Obtener IDs pasajeros (usando id_pasajero PK)
            pasajeros_res = self.client.table('pasajero').select('id_pasajero').eq('id_venta', id_venta).execute()
            if not pasajeros_res.data:
                return []
            
            ids_pasajeros = [p['id_pasajero'] for p in pasajeros_res.data]
            
            # Paso B: Obtener Docs
            res = self.client.table(self.table_name).select('*').in_('id_pasajero', ids_pasajeros).execute()
            return res.data
        except Exception as e:
            print(f"Error doc venta {id_venta}: {e}")
            return []

class TareaModel(BaseModel):
    def __init__(self, supabase_client: Client):
        # Según esquema SQL, usa 'id' como bigint
        super().__init__('tarea', supabase_client, primary_key='id')
        
    def get_tareas_by_responsable(self, responsable: str) -> List[Dict[str, Any]]:
        """Filtra tareas por responsable."""
        try:
            res = self.client.table(self.table_name).select('*').eq('responsable_ejecucion', responsable).execute()
            return res.data
        except Exception as e:
            return []

class RequerimientoModel(BaseModel):
    def __init__(self, supabase_client: Client):
        # Note: 'requerimiento' not in user's SQL snippet, keeping default PK 'id'
        super().__init__('requerimiento', supabase_client, primary_key='id')
