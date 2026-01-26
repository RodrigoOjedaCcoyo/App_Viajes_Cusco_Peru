# controllers/pdf_controller.py
import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from io import BytesIO

import datetime

class PDFController:
    """Controlador para la generación de documentos PDF a partir de plantillas HTML."""
    
    def __init__(self):
        # Localización de las plantillas
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def _render_pdf(self, template_name: str, context: dict) -> BytesIO:
        """Helper centralizado para renderizar HTML y convertir a PDF."""
        try:
            template = self.env.get_template(template_name)
            html_content = template.render(context)
            
            pdf_output = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_output)
            
            if pisa_status.err:
                print(f"Error en xhtml2pdf ({template_name}): {pisa_status.err}")
                return None
            
            pdf_output.seek(0)
            return pdf_output
        except Exception as e:
            print(f"Error renderizando PDF {template_name}: {e}")
            return None

    def generar_itinerario_pdf(self, datos_render: dict) -> BytesIO:
        """Genera un PDF de itinerario PREMIUM."""
        context = {
            "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
            "fecha_viaje": datos_render.get("fecha_viaje") or "",
            "num_adultos": datos_render.get("num_adultos", 1),
            "num_ninos": datos_render.get("num_ninos", 0),
            "itinerario": (datos_render.get("itinerario_detalles") or 
                           datos_render.get("itinerario_detales") or 
                           datos_render.get("days") or 
                           datos_render.get("servicios") or 
                           datos_render.get("itinerario") or []),
            "total": datos_render.get("precios", {}).get("extranjero", 0)
        }
        return self._render_pdf('itinerario_template.html', context)

    def generar_itinerario_simple_pdf(self, datos_render: dict) -> BytesIO:
        """Genera un PDF de itinerario SIMPLE (Ink Saver)."""
        context = {
            "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
            "fecha_viaje": datos_render.get("fecha_viaje") or "Pendiente",
            "num_adultos": datos_render.get("num_adultos", 1),
            "num_ninos": datos_render.get("num_ninos", 0),
            "itinerario": (datos_render.get("itinerario_detalles") or 
                           datos_render.get("itinerario_detales") or 
                           datos_render.get("days") or 
                           datos_render.get("servicios") or 
                           datos_render.get("itinerario") or []),
            "total": datos_render.get("precios", {}).get("extranjero", 0),
            "hoy": datetime.date.today().strftime("%d/%m/%Y")
        }
        return self._render_pdf('itinerario_simple_template.html', context)
