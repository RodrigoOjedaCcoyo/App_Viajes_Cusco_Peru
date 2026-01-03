# models/itinerario_model.py
from .base_model import BaseModel
from typing import List, Dict, Any, Optional

class ItinerarioModel(BaseModel):
    """Modelo para la gestión modular de itinerarios y tours."""

    def __init__(self, supabase_client):
        super().__init__('tour', supabase_client)

    def get_catalogo_tours(self) -> List[Dict[str, Any]]:
        """Obtiene el catálogo completo de servicios/tours."""
        try:
            return self.get_all()
        except:
            return []

    def get_paquetes(self) -> List[Dict[str, Any]]:
        """Obtiene las plantillas de paquetes base."""
        try:
            response = self.client.table('paquete').select('*').execute()
            return response.data
        except:
            return []

    def get_tours_por_paquete(self, id_paquete: int) -> List[Dict[str, Any]]:
        """Obtiene los tours asociados a un paquete específico (Rompecabezas)."""
        try:
            # Asumiendo tabla intermedia paquete_tour
            response = (
                self.client.table('paquete_tour')
                .select('orden, tour(*)')
                .eq('id_paquete', id_paquete)
                .order('orden')
                .execute()
            )
            # Aplanamos el resultado para que sea fácil de editar en la tabla
            return [
                {**item['tour'], 'orden': item['orden']} 
                for item in response.data if item.get('tour')
            ]
        except:
            return []

    def registrar_log_cotizacion(self, log_data: Dict[str, Any]) -> bool:
        """Registra una cotización para seguimiento pasivo (Analítica)."""
        try:
            # Asumiendo tabla 'log_cotizacion'
            self.client.table('log_cotizacion').insert(log_data).execute()
            return True
        except Exception as e:
            print(f"Error al registrar log: {e}")
            return False
