# controllers/itinerario_controller.py

from supabase import Client
import pandas as pd
from datetime import datetime

class ItinerarioController:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def get_catalogo_paquetes(self):
        """Obtiene la lista de paquetes base disponibles."""
        try:
            res = self.client.table('paquete').select('*').execute()
            if res.data:
                return pd.DataFrame(res.data)
            
            res_tour = self.client.table('tour').select('*').execute()
            return pd.DataFrame(res_tour.data or [])
        except Exception as e:
            print(f"Error cargando catálogo: {e}")
            return pd.DataFrame([
                {"id_paquete": 1, "nombre": "Cusco Básico 4D/3N", "costo_base": 450},
                {"id_paquete": 2, "nombre": "Cusco Imperial 5D/4N", "costo_base": 650},
                {"id_paquete": 3, "nombre": "Machu Picchu Full Day", "costo_base": 250}
            ])

    def get_leads_activos(self):
        """Obtiene leads que no han sido convertidos aún."""
        try:
            res = self.client.table('lead').select('id_lead, numero_celular, red_social').neq('estado_lead', 'CONVERTIDO').execute()
            return pd.DataFrame(res.data or [])
        except Exception as e:
            print(f"Error cargando leads: {e}")
            return pd.DataFrame()

    def es_festivo_peru(self, fecha_dt):
        """Verifica si la fecha cae en temporadas de alta demanda (Festivos)."""
        if (fecha_dt.month == 7 and fecha_dt.day in [28, 29]):
            return True
        if (fecha_dt.month == 12 and fecha_dt.day >= 24):
            return True
        return False

    def calcular_presupuesto(self, datos_itinerario):
        """Lógica de 'Gatillos' para calcular el costo total."""
        costo_base = datos_itinerario.get('costo_base_paquete', 0)
        num_adultos = datos_itinerario.get('num_adultos', 1)
        edades_ninos = datos_itinerario.get('edades_ninos_json', [])
        es_nacional = datos_itinerario.get('tipo_turista') == 'Nacional'
        fecha_llegada = datos_itinerario.get('fecha_llegada')
        
        subtotal = costo_base * num_adultos
        for edad in edades_ninos:
            subtotal += (costo_base * 0.5) if edad < 12 else costo_base
        
        sobrecosto_fiestas = 0
        if fecha_llegada and self.es_festivo_peru(fecha_llegada):
            sobrecosto_fiestas = subtotal * 0.15
            subtotal += sobrecosto_fiestas

        if es_nacional:
            subtotal *= 0.9
            
        margen = datos_itinerario.get('margen_ganancia', 20) / 100
        ajuste_manual = datos_itinerario.get('ajuste_manual_fijo', 0)
        total_venta = (subtotal * (1 + margen)) + ajuste_manual
        
        return {
            "subtotal_costo": subtotal,
            "sobrecosto_fiestas": sobrecosto_fiestas,
            "total_venta": total_venta,
            "ganancia_estimada": total_venta - subtotal
        }

    def generar_pdf_itinerario(self, datos, res_cotizacion):
        """Genera un archivo PDF con la cotización del itinerario."""
        from fpdf import FPDF
        import io

        class PDF(FPDF):
            def header(self):
                self.set_font('helvetica', 'B', 15)
                self.cell(0, 10, 'VIAJES CUSCO PERÚ - ITINERARIO DE VIAJE', 0, 1, 'C')
                self.set_font('helvetica', 'I', 10)
                self.cell(0, 5, 'Propuesta Comercial Personalizada', 0, 1, 'C')
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)

        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "1. INFORMACIÓN GENERAL", 1, 1, "L", fill=True)
        pdf.set_font("helvetica", size=11)
        pdf.ln(2)
        pdf.cell(0, 7, f"Lead / Cliente ID: {datos.get('id_lead', 'N/A')}", 0, 1)
        pdf.cell(0, 7, f"Fecha de Inicio: {datos.get('fecha_llegada', 'N/A')}", 0, 1)
        pdf.cell(0, 7, f"Paquete Base: {datos.get('nombre_paquete', 'N/A')}", 0, 1)
        pdf.cell(0, 7, f"Tipo de Turista: {datos.get('tipo_turista', 'N/A')}", 0, 1)
        pdf.ln(5)

        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "2. COMPOSICIÓN DEL GRUPO", 1, 1, "L", fill=True)
        pdf.set_font("helvetica", size=11)
        pdf.ln(2)
        pdf.cell(0, 7, f"Adultos: {datos.get('num_adultos', 1)}", 0, 1)
        edades = datos.get('edades_ninos_json', [])
        pdf.cell(0, 7, f"Niños: {len(edades)} (Edades: {', '.join(map(str, edades)) if edades else 'Ninguno'})", 0, 1)
        pdf.ln(5)

        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "3. SERVICIOS SELECCIONADOS", 1, 1, "L", fill=True)
        pdf.set_font("helvetica", size=11)
        pdf.ln(2)
        pdf.cell(0, 7, f"Alojamiento: {datos.get('alojamiento', 'N/A')}", 0, 1)
        pdf.cell(0, 7, f"Transporte (Tren): {datos.get('tren', 'N/A')}", 0, 1)
        extras = datos.get('servicios_extra', [])
        if extras:
            pdf.cell(0, 7, f"Servicios Adicionales: {', '.join(extras)}", 0, 1)
        pdf.ln(5)

        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "4. PRESUPUESTO FINAL", 1, 1, "L", fill=True)
        pdf.set_font("helvetica", size=11)
        pdf.ln(2)
        pdf.cell(0, 7, f"Costo Base Subtotal: ${res_cotizacion['subtotal_costo']:,.2f}", 0, 1)
        if res_cotizacion.get('sobrecosto_fiestas', 0) > 0:
            pdf.cell(0, 7, f"Recargo Temporada Alta: ${res_cotizacion['sobrecosto_fiestas']:,.2f}", 0, 1)
        
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(0, 102, 204)
        pdf.ln(5)
        pdf.cell(0, 10, f"TOTAL A PAGAR: ${res_cotizacion['total_venta']:,.2f}", 0, 1, "R")

        return bytes(pdf.output())
