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

    def _extraer_fecha_viaje_robusta(self, datos_render: dict) -> str:
        f_inicio = datos_render.get('fecha_viaje') or datos_render.get('fecha_inicio') or datos_render.get('fechaViaje') or datos_render.get('fecha')
        ci = datos_render.get('control_interno', {})
        if not f_inicio and ci:
            f_inicio = ci.get('fecha_inicio') or ci.get('fecha_llegada') or ci.get('fecha_viaje')
        if not f_inicio:
            dias_itin = datos_render.get('itinerario') or datos_render.get('days') or datos_render.get('itinerario_detalles')
            if dias_itin and isinstance(dias_itin, list) and len(dias_itin) > 0 and isinstance(dias_itin[0], dict):
                f_inicio = dias_itin[0].get('fecha')
        return str(f_inicio).strip() if f_inicio else ""

    def generar_itinerario_pdf(self, datos_render: dict) -> BytesIO:
        """Genera un PDF de itinerario PREMIUM."""
        fecha_robusta = self._extraer_fecha_viaje_robusta(datos_render)
        precios = datos_render.get("precios", {})
        total_val = precios.get("extranjero", 0)
        moneda_val = precios.get("moneda_extranjero", "USD")
        
        context = {
            "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
            "fecha_viaje": fecha_robusta,
            "num_adultos": datos_render.get("num_adultos", 1),
            "num_ninos": datos_render.get("num_ninos", 0),
            "itinerario": (datos_render.get("itinerario_detalles") or 
                           datos_render.get("itinerario_detales") or 
                           datos_render.get("days") or 
                           datos_render.get("servicios") or 
                           datos_render.get("itinerario") or []),
            "total": total_val,
            "moneda_total": moneda_val
        }
        return self._render_pdf('itinerario_template.html', context)

    def generar_itinerario_simple_pdf(self, datos_render: dict) -> BytesIO:
        """Genera un PDF de itinerario SIMPLE (Ink Saver)."""
        fecha_robusta = self._extraer_fecha_viaje_robusta(datos_render)
        precios = datos_render.get("precios", {})
        total_val = precios.get("extranjero", 0)
        moneda_val = precios.get("moneda_extranjero", "USD")

        context = {
            "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
            "fecha_viaje": fecha_robusta if fecha_robusta else "Pendiente",
            "num_adultos": datos_render.get("num_adultos", 1),
            "num_ninos": datos_render.get("num_ninos", 0),
        itinerario_raw = (datos_render.get("itinerario_detalles") or 
                          datos_render.get("itinerario_detales") or 
                          datos_render.get("days") or 
                          datos_render.get("servicios") or 
                          datos_render.get("itinerario") or [])
        
        # Procesar negritas (*** -> <b>)
        itinerario_procesado = []
        for item in itinerario_raw:
            it_copy = item.copy()
            desc = it_copy.get('descripcion', '')
            if desc:
                # Reemplazo simple de pares de *** por <b> y </b>
                # Buscamos el primero y lo cambiamos por <b>, el segundo por </b>, etc.
                parts = desc.split('***')
                new_desc = ""
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        new_desc += part
                    else:
                        new_desc += f"<b>{part}</b>"
                it_copy['descripcion'] = new_desc
            itinerario_procesado.append(it_copy)

        context = {
            "cliente_nombre": datos_render.get("nombre_pasajero") or "Pasajero",
            "fecha_viaje": fecha_robusta if fecha_robusta else "Pendiente",
            "num_adultos": datos_render.get("num_adultos", 1),
            "num_ninos": datos_render.get("num_ninos", 0),
            "itinerario": itinerario_procesado,
            "total": total_val,
            "moneda_total": moneda_val,
            "hoy": datetime.date.today().strftime("%d/%m/%Y")
        }
        return self._render_pdf('itinerario_simple_template.html', context)

    def generar_voucher_endose_pdf(self, data: dict) -> BytesIO:
        """Genera un Vale de Endose para un proveedor específico."""
        data['hoy'] = datetime.date.today().strftime("%d/%m/%Y")
        return self._render_pdf('voucher_endose_template.html', data)
