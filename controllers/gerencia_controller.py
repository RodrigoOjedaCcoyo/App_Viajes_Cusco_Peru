# controllers/gerencia_controller.py

from supabase import Client
import pandas as pd
from datetime import date

class GerenciaController:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def get_kpis_financieros(self):
        """Calcula Ventas Totales, Recaudado y Pendiente."""
        try:
            # 1. Ventas Totales
            res_ventas = self.client.table('venta').select('precio_total_cierre').execute()
            ventas_data = res_ventas.data or []
            total_ventas = sum([v.get('precio_total_cierre') or 0 for v in ventas_data])

            # 2. Pagos Recaudados
            res_pagos = self.client.table('pago').select('monto_pagado').execute()
            pagos_data = res_pagos.data or []
            total_recaudado = sum([p.get('monto_pagado') or 0 for p in pagos_data])

            # 3. Cálculo de Pendiente
            total_pendiente = total_ventas - total_recaudado

            return {
                'ventas_totales': total_ventas,
                'total_recaudado': total_recaudado,
                'total_pendiente': total_pendiente
            }
        except Exception as e:
            print(f"Error Gerencia Financiero: {e}")
            return {'ventas_totales': 0, 'total_recaudado': 0, 'total_pendiente': 0}

    def get_metricas_comerciales(self):
        """Calcula Leads, Clientes y Tasa de Conversión."""
        try:
            # 1. Leads Totales
            res_leads = self.client.table('lead').select('id_lead, estado, medio_contacto').execute()
            leads_data = res_leads.data or []
            total_leads = len(leads_data)

            # 2. Leads Convertidos (Estado contiene 'Convertido' o 'Venta')
            leads_convertidos = [l for l in leads_data if 'CONVERTIDO' in (l.get('estado') or '').upper()]
            total_convertidos = len(leads_convertidos)

            # 3. Tasa de Conversión
            tasa_conversion = (total_convertidos / total_leads * 100) if total_leads > 0 else 0

            # 4. Distribución por Medio (para pie chart)
            df_leads = pd.DataFrame(leads_data)
            distribucion_medios = {}
            if not df_leads.empty:
                distribucion_medios = df_leads['medio_contacto'].value_counts().to_dict()

            return {
                'total_leads': total_leads,
                'total_convertidos': total_convertidos,
                'tasa_conversion': tasa_conversion,
                'distribucion_medios': distribucion_medios
            }
        except Exception as e:
            print(f"Error Gerencia Comercial: {e}")
            return {'total_leads': 0, 'total_convertidos': 0, 'tasa_conversion': 0, 'distribucion_medios': {}}

    def get_pax_totales(self):
        """Calcula el total de pasajeros programados en tours."""
        try:
            res = self.client.table('venta_tour').select('cantidad_pasajeros').execute()
            pax_data = res.data or []
            return sum([p.get('cantidad_pasajeros') or 0 for p in pax_data])
        except Exception as e:
            print(f"Error Gerencia Pax: {e}")
            return 0

    def get_alertas_gestion(self):
        """Busca ventas con documentación crítica pendiente (basado en Operaciones)."""
        try:
            # Reutilizamos lógica de riesgo: Documentos críticos no validados
            res_docs = (
                self.client.table('documentacion')
                .select('id_pasajero, tipo_documento')
                .eq('es_critico', True)
                .neq('estado_entrega', 'VALIDADO')
                .execute()
            )
            
            # Formateamos para el dashboard
            alertas = []
            if res_docs.data:
                alertas = res_docs.data[:5] # Solo las primeras 5 para no saturar

            return alertas
        except Exception as e:
            print(f"Error Gerencia Alertas: {e}")
            return []

    def get_ventas_mensuales(self):
        """Agrupa ventas por mes para el gráfico de barras."""
        try:
            res_ventas = self.client.table('venta').select('precio_total_cierre, fecha_venta').execute()
            if not res_ventas.data:
                return pd.DataFrame()

            df = pd.DataFrame(res_ventas.data)
            df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])
            df['Mes'] = df['fecha_venta'].dt.strftime('%Y-%m')
            
            resumen = df.groupby('Mes')['precio_total_cierre'].sum().reset_index()
            resumen.columns = ['Mes', 'Ventas']
            return resumen.sort_values('Mes')
        except Exception as e:
            print(f"Error Gerencia Mensual: {e}")
            return pd.DataFrame()
