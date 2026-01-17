# controllers/pdf_controller.py
import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from io import BytesIO

class PDFController:
    """Controlador para la generación de documentos PDF a partir de plantillas HTML."""
    
    def __init__(self):
        # Localización de las plantillas
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generar_itinerario_pdf(self, datos_render: dict) -> BytesIO:
        """
        Genera un PDF de itinerario basándose en los datos proporcionados.
        Retorna un objeto BytesIO con el contenido del PDF.
        """
        try:
            # 1. Cargar y Renderizar Plantilla HTML con Jinja2
            template = self.env.get_template('itinerario_template.html')
            
            # Asegurar compatibilidad de nombres de campos entre JSONB y Template
            context = {
                "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
                "fecha_viaje": datos_render.get("fecha_viaje") or "",
                "num_adultos": datos_render.get("num_adultos", 1),
                "num_ninos": datos_render.get("num_ninos", 0),
                "itinerario": datos_render.get("itinerario_detales", []), # Lista de tours
                "total": datos_render.get("precios", {}).get("extranjero", 0) # Por defecto precio extranjero
            }
            
            html_content = template.render(context)
            
            # 2. Convertir HTML a PDF usando xhtml2pdf (ReportLab)
            pdf_output = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_output)
            
            if pisa_status.err:
                print(f"Error en xhtml2pdf: {pisa_status.err}")
                return None
            
            pdf_output.seek(0)
            return pdf_output
            
        except Exception as e:
            print(f"Error generando PDF: {e}")
            return None
