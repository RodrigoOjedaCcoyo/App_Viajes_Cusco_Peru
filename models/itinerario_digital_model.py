# models/itinerario_digital_model.py
from .base_model import BaseModel
from typing import Dict, Any, Optional
from supabase import Client

class ItinerarioDigitalModel(BaseModel):
    """Modelo para la gestión de itinerarios visuales/digitales (Cerebro Visual)."""

    def __init__(self, supabase_client: Client):
        # Sincronizado con esquema SQL: tabla 'itinerario_digital', PK 'id_itinerario_digital' (UUID)
        super().__init__('itinerario_digital', supabase_client, primary_key='id_itinerario_digital')

    def registrar_itinerario(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Guarda el diseño visual (datos_render) y retorna el UUID generado.
        """
        # El UUID se genera en Supabase por defecto, save() de BaseModel lo recuperará.
        return self.save(data)

    def obtener_por_lead(self, id_lead: int) -> Optional[Dict[str, Any]]:
        """Obtiene el último itinerario generado para un lead específico."""
        try:
            res = (
                self.client.table(self.table_name)
                .select('*')
                .eq('id_lead', id_lead)
                .order('fecha_generacion', desc=True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"Error obteniendo itinerario digital: {e}")
            return None
