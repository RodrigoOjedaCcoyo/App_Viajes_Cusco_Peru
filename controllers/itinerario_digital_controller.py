# controllers/itinerario_digital_controller.py
from models.itinerario_digital_model import ItinerarioDigitalModel
from models.lead_model import LeadModel
from models.catalogo_imagenes_model import CatalogoImagenesModel
from supabase import Client
from typing import Dict, Any, Optional

class ItinerarioDigitalController:
    """Controlador que orquesta la persistencia del Itinerario Digital (Cerebro Visual)."""

    def __init__(self, supabase_client: Client):
        self.itinerario_model = ItinerarioDigitalModel(supabase_client)
        self.lead_model = LeadModel('lead', supabase_client)
        self.catalogo_model = CatalogoImagenesModel(supabase_client)

    def registrar_generacion_itinerario(self, 
                                        id_lead: int, 
                                        nombre_pasajero: str, 
                                        id_vendedor: int, 
                                        datos_render: Dict[str, Any]) -> tuple[bool, str]:
        """
        Registra un nuevo diseño en la nube y actualiza el Lead.
        Esta función se llama al presionar 'GENERAR ITINERARIO PDF'.
        """
        try:
            # 1. Preparar datos para itinerario_digital
            datos_itinerario = {
                "id_lead": id_lead,
                "id_vendedor": id_vendedor,
                "nombre_pasajero_itinerario": nombre_pasajero,
                "datos_render": datos_render
            }
            
            # 2. Guardar en itinerario_digital y obtener UUID
            id_itinerario_digital = self.itinerario_model.registrar_itinerario(datos_itinerario)
            
            if not id_itinerario_digital:
                return False, "Error al guardar el itinerario digital en la nube."

            # 3. Actualizar el Lead con el nombre oficial y el link al itinerario
            actualizacion_lead = {
                "nombre_pasajero": nombre_pasajero,
                "ultimo_itinerario_id": id_itinerario_digital,
                "estado_lead": "CALIENTE" # Marcar como caliente al generar itinerario
            }
            
            exito_lead = self.lead_model.update_by_id(id_lead, actualizacion_lead)
            
            if exito_lead:
                return True, f"Itinerario Digital sincronizado. UUID: {id_itinerario_digital}"
            else:
                return True, f"Itinerario guardado ({id_itinerario_digital}), pero no se pudo actualizar el Lead."
                
        except Exception as e:
            print(f"Error en registrar_generacion_itinerario: {e}")
            return False, f"Error crítico: {e}"

    def get_imagenes_para_tour(self, id_tour: int) -> list:
        """Helper para obtener las fotos oficiales del catálogo."""
        return self.catalogo_model.get_imagenes_tour(id_tour)
