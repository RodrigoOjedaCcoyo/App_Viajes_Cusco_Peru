# models/venta_model.py

from .base_model import BaseModel
from datetime import datetime
from supabase import Client
from typing import Dict, Any

class VentaModel(BaseModel):
    """Modelo para la gestión de Ventas (Conversiones de Leads)."""

    # CORRECCIÓN: El constructor debe recibir table_name y pasarlo a BaseModel.
    def __init__(self, table_name: str, supabase_client: Client): 
        # Llama al constructor de BaseModel, pasando el nombre de la tabla (ej: 'Ventas') y el cliente.
        super().__init__(table_name, supabase_client) 

    def create_venta(self, lead_id: int, monto_total: float, tour_paquete: str, fecha_tour: str, vendedor: str) -> Dict[str, Any]:
        """Guarda un nuevo registro de venta."""
        venta_data = {
            "lead_id": lead_id,
            "monto_total": monto_total,
            "tour_paquete": tour_paquete,
            "fecha_tour": fecha_tour,
            "vendedor": vendedor,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Delega el almacenamiento a BaseModel
        return self.save(venta_data)