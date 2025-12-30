# controllers/venta_controller.py (Nuevo archivo)

from models.base_model import BaseModel
from supabase import Client
from typing import Optional

class VentaController:
    """Controlador dummy para manejar la lógica de Ventas."""
    def __init__(self, supabase_client:Client):
        # Asumimos que hay una tabla 'Ventas'
        self.model = BaseModel(table_name='Ventas', supabase_client=supabase_client)

    def registrar_venta_directa(self, telefono: str, origen: str, monto: float, tour: str, fecha_tour: str, vendedor: str) -> tuple[bool, str]:
        """Simula el registro de una venta directa en la tabla de Ventas."""
        
        # Aquí iría la lógica de negocio compleja (ej. mover el lead a estado 'Convertido')
        
        venta_data = {
            "telefono_cliente": telefono,
            "origen": origen,
            "monto": monto,
            "tour": tour,
            "fecha_tour": fecha_tour,
            "vendedor": vendedor,
            "fecha_registro": fecha_tour # Usar la misma fecha para simplificar
        }
        
        nuevo_id = self.model.save(venta_data)
        
        if nuevo_id:
            return True, f"Venta registrada con éxito. ID asignado: {nuevo_id}"
        else:
            return False, "Error desconocido al registrar la Venta."