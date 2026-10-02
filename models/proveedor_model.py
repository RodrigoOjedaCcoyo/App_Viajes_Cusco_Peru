# models/proveedor_model.py

from .base_model import BaseModel
from supabase import Client as SupabaseClient
from typing import List, Dict, Any, Optional

class ProveedorModel(BaseModel):
    def __init__(self, supabase_client: SupabaseClient):
        super().__init__(table_name='proveedor', supabase_client=supabase_client, primary_key='id_proveedor')

    def obtener_todos(self, incluir_inactivos: bool = False) -> List[Dict[str, Any]]:
        """Obtiene los proveedores activos (o todos, si incluir_inactivos=True)."""
        try:
            q = self.client.table(self.table_name).select('*')
            if not incluir_inactivos:
                q = q.eq('activo', True)
            res = q.order('nombre_comercial').execute()
            return res.data or []
        except Exception as e:
            print(f"Error al obtener proveedores: {e}")
            return []

    def crear_proveedor(self, data: Dict[str, Any]) -> Optional[int]:
        """Crea un nuevo proveedor y retorna su ID."""
        return self.save(data)
