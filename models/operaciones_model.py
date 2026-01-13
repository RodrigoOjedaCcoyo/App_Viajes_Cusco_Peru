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
        super().__init__('venta', supabase_client)

class PasajeroModel(BaseModel):
    def __init__(self, supabase_client: Client):
        super().__init__('pasajero', supabase_client)
        
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
        super().__init__('documentacion', supabase_client)
        
    def get_documentos_by_venta_id(self, id_venta: int) -> List[Dict[str, Any]]:
        """
        Obtiene documentos filtrando por los pasajeros de la venta.
        Utiliza Join (select relacional) para eficiencia si es posible, 
        o dos pasos. Aquí usamos select relacional si la FK está bien definida.
        """
        try:
            # Opción 1: Query Directo con Join a Pasajero
            # Supabase permite: select('*, pasajero!inner(*)') para filtrar
            # Pero dado el esquema, haremos query en dos pasos para seguridad inicial o un join simple
            
            # Paso A: Obtener IDs pasajeros
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
        super().__init__('tarea', supabase_client)
        
    def get_tareas_by_responsable(self, responsable: str) -> List[Dict[str, Any]]:
        """Filtra tareas por responsable."""
        try:
            res = self.client.table(self.table_name).select('*').eq('responsable_ejecucion', responsable).execute()
            return res.data
        except Exception as e:
            return []

class RequerimientoModel(BaseModel):
    def __init__(self, supabase_client: Client):
        super().__init__('requerimiento', supabase_client)