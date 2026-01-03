# controllers/itinerario_controller.py
from supabase import Client
import pandas as pd
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
import io
import os
from models.itinerario_model import ItinerarioModel

class ItinerarioController:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.model = ItinerarioModel(supabase_client)
        # Configuración de Jinja2
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def get_catalogo_paquetes(self):
        """Obtiene la lista de paquetes base disponibles con Cache nativo de la app."""
        data = self.model.get_paquetes()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=['id', 'nombre', 'costo_base'])

    def get_catalogo_tours(self):
        """Obtiene el catálogo de tours individuales."""
        data = self.model.get_catalogo_tours()
        return pd.DataFrame(data) if data else pd.DataFrame()

    def get_tours_de_paquete(self, id_paquete):
        """Carga las 'piezas del rompecabezas' iniciales de un paquete."""
        return self.model.get_tours_por_paquete(id_paquete)

    def registrar_consulta_pasiva(self, tipo, datos):
        """Registra la actividad comercial para analítica."""
        log_entry = {
            "fecha_registro": datetime.now().isoformat(),
            "tipo_consulta": tipo, # 'FLASH' o 'DETALLADA'
            "datos_json": datos,
            "vendedor_id": datos.get('vendedor_id')
        }
        self.model.registrar_log_cotizacion(log_entry)

    def calcular_presupuesto_modular(self, piezas_itinerario, config):
        """
        Motor de Precios Modular corregido.
        piezas_itinerario: Lista de diccionarios {costo_base, costo_nino, ...}
        config: {adultos, ninos, margen, ajuste_fijo}
        """
        subtotal_adultos = 0
        subtotal_ninos = 0
        
        for p in piezas_itinerario:
            costo_a = float(p.get('costo_base', 0))
            costo_n = float(p.get('costo_nino', costo_a * 0.7)) # Fallback 70%
            
            subtotal_adultos += costo_a
            subtotal_ninos += costo_n

        total_costo = (subtotal_adultos * config['adultos']) + (subtotal_ninos * config['ninos'])
        
        # Aplicar Margen
        margen_decimal = config['margen'] / 100
        total_con_margen = total_costo * (1 + margen_decimal)
        
        # Sumar Ajuste Fijo (Negociación/Temporada)
        total_final = total_con_margen + config['ajuste_fijo']
        
        return {
            "costo_total": total_costo,
            "total_venta": total_final,
            "ganancia": total_final - total_costo
        }

    def generar_pdf_premium(self, datos_render):
        """
        Genera un PDF con diseño premium usando HTML + CSS.
        datos_render: Diccionario con cliente, itinerario, total, etc.
        """
        try:
            template = self.jinja_env.get_template('itinerario_template.html')
            html_out = template.render(datos_render)
            
            result = io.BytesIO()
            pisa_status = pisa.CreatePDF(html_out, dest=result)
            
            if pisa_status.err:
                print("Error al generar PDF con xhtml2pdf")
                return None
                
            return result.getvalue()
        except Exception as e:
            print(f"Error crítico en generación de PDF: {e}")
            return None

    # Métodos legacy para mantener compatibilidad si es necesario
    def get_leads_activos(self):
        try:
            res = self.client.table('lead').select('id_lead, numero_celular, red_social').neq('estado_lead', 'CONVERTIDO').execute()
            return pd.DataFrame(res.data or [])
        except: return pd.DataFrame()
