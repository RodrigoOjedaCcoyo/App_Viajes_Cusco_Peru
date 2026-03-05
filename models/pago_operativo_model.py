# models/pago_operativo_model.py
from .base_model import BaseModel
from supabase import Client
from typing import Dict, Any, List

class PagoOperativoModel(BaseModel):
    """Modelo para la gestión de Pagos Operativos (Desembolsos a Proveedores)."""

    def __init__(self, supabase_client: Client):
        super().__init__('pago_operativo', supabase_client, primary_key='id_pago_op')

    def registrar_pago(self, data: Dict[str, Any]) -> Any:
        """Registra un nuevo pago operativo."""
        return self.save(data)

    def obtener_pagos_por_venta(self, id_venta: int) -> List[Dict[str, Any]]:
        """Obtiene todos los pagos operativos vinculados a una venta."""
        try:
            res = self.client.table(self.table_name)\
                .select('*, proveedor(nombre_comercial)')\
                .eq('id_venta', id_venta)\
                .execute()
            return res.data
        except Exception as e:
            print(f"Error obteniendo pagos operativos de venta {id_venta}: {e}")
            return []

    def obtener_pagos_por_proveedor(self, id_proveedor: int) -> List[Dict[str, Any]]:
        """Obtiene todos los pagos realizados a un proveedor específico."""
        try:
            res = self.client.table(self.table_name)\
                .select('*, venta(tour_nombre, fecha_inicio)')\
                .eq('id_proveedor', id_proveedor)\
                .execute()
            return res.data
        except Exception as e:
            print(f"Error obteniendo pagos de proveedor {id_proveedor}: {e}")
            return []
