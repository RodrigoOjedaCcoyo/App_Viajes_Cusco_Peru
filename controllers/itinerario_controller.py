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
            # Intentamos obtener de la tabla 'paquete' o similar
            res = self.client.table('paquete').select('*').execute()
            if res.data:
                return pd.DataFrame(res.data)
            
            # Si no existe 'paquete', probamos 'tour' como respaldo tentativo
            res_tour = self.client.table('tour').select('*').execute()
            return pd.DataFrame(res_tour.data or [])
        except Exception as e:
            print(f"Error cargando catálogo: {e}")
            # Retornamos datos semilla mínimos si hay error para no bloquear el desarrollo
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
        # Simplificado: 28-29 Julio (Fiestas Patrias), 24-31 Diciembre (Navidad/Año Nuevo)
        dia_mes = (fecha_dt.day, fecha_dt.month)
        if (fecha_dt.month == 7 and fecha_dt.day in [28, 29]):
            return True
        if (fecha_dt.month == 12 and fecha_dt.day >= 24):
            return True
        return False

    def calcular_presupuesto(self, datos_itinerario):
        """
        Lógica de 'Gatillos' para calcular el costo total.
        datos_itinerario: dict con las 9 preguntas.
        """
        costo_base = datos_itinerario.get('costo_base_paquete', 0)
        num_adultos = datos_itinerario.get('num_adultos', 1)
        edades_ninos = datos_itinerario.get('edades_ninos_json', [])
        es_nacional = datos_itinerario.get('tipo_turista') == 'Nacional'
        fecha_llegada = datos_itinerario.get('fecha_llegada')
        
        # 1. Multiplicador por Adultos
        subtotal = costo_base * num_adultos
        
        # 2. Lógica de Niños (Ejm: 50% descuento si < 12 años)
        for edad in edades_ninos:
            if edad < 12:
                subtotal += (costo_base * 0.5)
            else:
                subtotal += costo_base
        
        # 3. Sobrecosto por Fiestas (GATILLO: Fecha)
        sobrecosto_fiestas = 0
        if fecha_llegada and self.es_festivo_peru(fecha_llegada):
            sobrecosto_fiestas = subtotal * 0.15 # 15% de recargo
            subtotal += sobrecosto_fiestas

        # 4. Ajuste por Nacionalidad (Ejm: -10% si es peruano por convenios)
        if es_nacional:
            subtotal *= 0.9
            
        # 5. Ajustes de Complejidad (Margen y Extras)
        margen = datos_itinerario.get('margen_ganancia', 20) / 100
        ajuste_manual = datos_itinerario.get('ajuste_manual_fijo', 0)
        
        total_venta = (subtotal * (1 + margen)) + ajuste_manual
        
        return {
            "subtotal_costo": subtotal,
            "sobrecosto_fiestas": sobrecosto_fiestas,
            "total_venta": total_venta,
            "ganancia_estimada": total_venta - subtotal
        }
