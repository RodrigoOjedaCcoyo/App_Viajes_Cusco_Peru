# controllers/reporte_controller.py
from models.venta_model import VentaModel
from models.lead_model import LeadModel
import pandas as pd

class ReporteController:
    """
    Controlador encargado de obtener datos agregados y reportes
    para las áreas de Gerencia y Contabilidad.
    """
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.venta_model = VentaModel('venta', supabase_client)
        self.lead_model = LeadModel('lead', supabase_client)
        
    def obtener_requerimientos(self):
        """Obtiene la lista de requerimientos (Pagos operativos pendientes en itinerarios)."""
        try:
            # Traer servicios que piden pago operativo
            res = self.client.table('venta_tour').select('*, venta(cliente(nombre))').eq('estado_pago_operativo', 'PENDIENTE').execute()
            data = res.data or []
            # Homogeneizar para la vista
            final = []
            for d in data:
                final.append({
                    "id_venta": d['id_venta'],
                    "n_linea": d['n_linea'],
                    "fecha": d['fecha_servicio'],
                    "cliente": d.get('venta', {}).get('cliente', {}).get('nombre', 'Desconocido'),
                    "concepto": d.get('observacion', 'Servicio'),
                    "monto": d.get('costo_applied', 0),
                    "moneda": d.get('moneda_costo', 'USD'),
                    "datos_pago": d.get('datos_pago_operativo', 'Sin datos'),
                    "estado": d.get('estado_pago_operativo', 'PENDIENTE')
                })
            return final
        except Exception as e:
            print(f"Error obteniendo requerimientos unificados: {e}")
            return []
        
    def obtener_resumen_ventas(self):
        """Devuelve todas las ventas con información clave para reportes."""
        try:
            todas_las_ventas = self.venta_model.get_all()
            total_ventas = len(todas_las_ventas)
            monto_total_usd = sum(v.get('precio_total_cierre', 0) or 0 for v in todas_las_ventas)
            
            return {
                "total_ventas_registradas": total_ventas,
                "monto_total_acumulado": monto_total_usd,
                "detalle_ventas": todas_las_ventas
            }
        except Exception as e:
            print(f"Error obtener_resumen_ventas: {e}")
            return {"total_ventas_registradas": 0, "monto_total_acumulado": 0, "detalle_ventas": []}

    def obtener_detalle_auditoria(self):
        """Devuelve las ventas con nombre de cliente para auditoría."""
        try:
            ventas = self.venta_model.get_all()
            if not ventas: return []
            
            res_c = self.client.table('cliente').select('id_cliente, nombre').execute()
            cli_map = {c['id_cliente']: c['nombre'] for c in res_c.data}
            for v in ventas:
                v['cliente_nombre'] = cli_map.get(v.get('id_cliente'), "Desconocido")
            return ventas
        except Exception as e:
            print(f"Error auditoría: {e}")
            return []

    def get_data_for_dashboard(self):
        """Devuelve dataframes para dashboards financieros."""
        # 1. Ventas
        try:
            ventas = self.venta_model.get_all()
            df_ventas = pd.DataFrame(ventas) if ventas else pd.DataFrame()
            if not df_ventas.empty:
                df_ventas['monto_total'] = df_ventas.get('precio_total_cierre', 0)
                # Mapeos básicos
                res_v = self.client.table('vendedor').select('id_vendedor, nombre').execute()
                vend_map = {v['id_vendedor']: v['nombre'] for v in res_v.data}
                df_ventas['vendedor'] = df_ventas['id_vendedor'].map(vend_map)
                    
                res_c = self.client.table('cliente').select('id_cliente, nombre').execute()
                cli_map = {c['id_cliente']: c['nombre'] for c in res_c.data}
                df_ventas['cliente_nombre'] = df_ventas['id_cliente'].map(cli_map)
        except Exception as e:
            print(f"Error dashboard ventas: {e}")
            df_ventas = pd.DataFrame()

        # 2. Gastos (Requerimientos de Pago del Itinerario)
        try:
            reqs = self.obtener_requerimientos()
            df_reqs = pd.DataFrame(reqs) if reqs else pd.DataFrame()
            if not df_reqs.empty:
                df_reqs['total'] = df_reqs['monto']
        except Exception as e:
            print(f"Error dashboard reqs: {e}")
            df_reqs = pd.DataFrame()
            
        return df_ventas, df_reqs