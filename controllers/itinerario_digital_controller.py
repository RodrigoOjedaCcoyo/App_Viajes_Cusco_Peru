from models.itinerario_digital_model import ItinerarioDigitalModel
from models.lead_model import LeadModel
from models.catalogo_imagenes_model import CatalogoImagenesModel
from .pdf_controller import PDFController
from supabase import Client
from typing import Dict, Any, Optional
from io import BytesIO
import datetime

class ItinerarioDigitalController:
    """Controlador que orquesta la persistencia del Itinerario Digital (Cerebro Visual)."""

    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.itinerario_model = ItinerarioDigitalModel(supabase_client)
        self.lead_model = LeadModel('lead', supabase_client)
        self.catalogo_model = CatalogoImagenesModel(supabase_client)
        self.pdf_engine = PDFController()

    def registrar_generacion_itinerario(self, 
                                        id_lead: int, 
                                        nombre_pasajero: str, 
                                        id_vendedor: int, 
                                        datos_render: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """
        Registra un nuevo diseño en la nube, genera el PDF, lo sube y actualiza el Lead.
        Retorna (Exito, Mensaje, URL_PDF).
        """
        try:
            # 0. Generar PDF Localmente (en memoria)
            # Pasamos el nombre del pasajero al diccionario de datos para el renderizado
            datos_render["nombre_pasajero"] = nombre_pasajero
            pdf_buffer = self.pdf_engine.generar_itinerario_pdf(datos_render)
            
            if not pdf_buffer:
                return False, "Error al generar el documento PDF.", None

            # 1. Subir PDF al Storage de Supabase
            nombre_archivo = f"itinerario_{id_lead}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            try:
                self.client.storage.from_("itinerarios").upload(
                    path=nombre_archivo,
                    file=pdf_buffer.getvalue(),
                    file_options={"content-type": "application/pdf"}
                )
                url_pdf = self.client.storage.from_("itinerarios").get_public_url(nombre_archivo)
            except Exception as e:
                print(f"Error subiendo PDF: {e}")
                url_pdf = None

            # 2. Preparar datos para itinerario_digital
            datos_itinerario = {
                "id_lead": id_lead,
                "id_vendedor": id_vendedor,
                "nombre_pasajero_itinerario": nombre_pasajero,
                "datos_render": datos_render,
                "url_pdf": url_pdf # Guardar el link generado
            }
            
            # 3. Guardar en itinerario_digital y obtener UUID
            id_itinerario_digital = self.itinerario_model.registrar_itinerario(datos_itinerario)
            
            if not id_itinerario_digital:
                return False, "Error al guardar el itinerario digital en la nube.", None

            # 4. Actualizar el Lead
            actualizacion_lead = {
                "nombre_pasajero": nombre_pasajero,
                "ultimo_itinerario_id": id_itinerario_digital,
                "estado_lead": "CALIENTE"
            }
            
            self.lead_model.update_by_id(id_lead, actualizacion_lead)
            
            return True, f"¡Éxito! Itinerario generado y guardado en la nube.", url_pdf
                
        except Exception as e:
            print(f"Error en registrar_generacion_itinerario: {e}")
            return False, f"Error crítico: {e}", None

    def get_imagenes_para_tour(self, id_tour: int) -> list:
        """Helper para obtener las fotos oficiales del catálogo."""
        return self.catalogo_model.get_imagenes_tour(id_tour)
