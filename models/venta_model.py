# models/venta_model.py

from .base_model import BaseModel
from datetime import datetime

class VentaModel(BaseModel):
    """Modelo para la gestión de Ventas (Conversiones de Leads)."""

    def __init__(self):
        super().__init__(key="ventas") 

    def create_venta(self, lead_id, monto_total, tour_paquete, fecha_tour, vendedor):
        """Guarda un nuevo registro de venta."""
        venta_data = {
            "lead_id": lead_id,
            "monto_total": monto_total,
            "tour_paquete": tour_paquete,
            "fecha_tour": fecha_tour,
            "vendedor": vendedor,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.save(venta_data)