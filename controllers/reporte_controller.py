# controllers/reporte_controller.py
from models.venta_model import VentaModel
from models.lead_model import LeadModel
from models.operaciones_model import RequerimientoModel

class ReporteController:
    """
    Controlador encargado de obtener datos agregados y reportes
    para las áreas de Gerencia y Contabilidad.
    """
    
    def __init__(self, supabase_client):
        self.venta_model = VentaModel('Venta', supabase_client)
        self.lead_model = LeadModel('lead', supabase_client)
        self.req_model = RequerimientoModel(supabase_client)
        
    def obtener_requerimientos(self):
        """Obtiene la lista de requerimientos desde Operaciones."""
        try:
            return self.req_model.get_all()
        except Exception as e:
            print(f"Error obteniendo requerimientos en ReporteController: {e}")
            return []
        
    def obtener_resumen_ventas(self):
        """Devuelve todas las ventas con información clave para reportes."""
        
        # 1. Obtener los datos sin procesar
        todas_las_ventas = self.venta_model.get_all()
        
        # 2. Calcular métricas clave
        total_ventas = len(todas_las_ventas)
        monto_total_usd = sum(v['monto_total'] for v in todas_las_ventas)
        
        # 3. Formatear la salida
        resumen = {
            "total_ventas_registradas": total_ventas,
            "monto_total_acumulado": monto_total_usd,
            "detalle_ventas": todas_las_ventas
        }
        return resumen

    def obtener_detalle_auditoria(self):
        """
        Devuelve una lista combinada de Leads y Ventas para auditoría 
        (ejemplo simple, en una DB real sería un JOIN).
        """
        ventas = self.venta_model.get_all()
        # En una auditoría real, buscarías el Lead asociado
        return ventas

    def get_data_for_dashboard(self):
        """Devuelve dataframes listos para pandas."""
        import pandas as pd
        
        # --- MODO SIMULACIÓN ACTIVADO ---
        try:
            from controllers.mock_db import MOCK_VENTAS, MOCK_REQS
            df_ventas = pd.DataFrame(MOCK_VENTAS)
            df_reqs = pd.DataFrame(MOCK_REQS)
            return df_ventas, df_reqs
        except ImportError:
            pass
        # -------------------------------
        
        # 1. Ventas
        ventas = self.venta_model.get_all()
        df_ventas = pd.DataFrame(ventas) if ventas else pd.DataFrame()
        if not df_ventas.empty and 'monto_total' not in df_ventas.columns:
            # Fallback seguro si falla modelo
            df_ventas['monto_total'] = 0.0
            
        # 2. Gastos (Requerimientos)
        reqs = self.req_model.get_all()
        df_reqs = pd.DataFrame(reqs) if reqs else pd.DataFrame()
        if not df_reqs.empty and 'total' not in df_reqs.columns:
            df_reqs['total'] = 0.0
            
        return df_ventas, df_reqs