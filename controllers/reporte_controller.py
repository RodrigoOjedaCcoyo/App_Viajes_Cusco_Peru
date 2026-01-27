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
        self.client = supabase_client
        self.venta_model = VentaModel('venta', supabase_client)
        self.lead_model = LeadModel('lead', supabase_client)
        self.req_model = RequerimientoModel(supabase_client)
        
    def obtener_requerimientos(self):
        """Obtiene la lista de requerimientos (Versión Master Sheet)."""
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
                    "concepto": d['observaciones'],
                    "monto": d['costo_applied'],
                    "moneda": d.get('moneda_costo', 'USD'),
                    "datos_pago": d.get('datos_pago_operativo', 'Sin datos'),
                    "estado": d['estado_pago_operativo']
                })
            return final
        except Exception as e:
            print(f"Error obteniendo requerimientos unificados: {e}")
            return []
        
    def obtener_resumen_ventas(self):
        """Devuelve todas las ventas con información clave para reportes."""
        
        # 1. Obtener los datos sin procesar
        todas_las_ventas = self.venta_model.get_all()
        
        # 2. Calcular métricas clave (Sincronizado: precio_total_cierre)
        total_ventas = len(todas_las_ventas)
        monto_total_usd = sum(v.get('precio_total_cierre', 0) or 0 for v in todas_las_ventas)
        
        # 3. Formatear la salida
        resumen = {
            "total_ventas_registradas": total_ventas,
            "monto_total_acumulado": monto_total_usd,
            "detalle_ventas": todas_las_ventas
        }
        return resumen

    def obtener_detalle_auditoria(self):
        """
        Devuelve una lista combinada de Leads y Ventas para auditoría.
        """
        ventas = self.venta_model.get_all()
        if not ventas: return []
        
        # Mapear Cliente (Nombre) para que el selector sea legible
        try:
            res_c = self.venta_model.client.table('cliente').select('id_cliente, nombre').execute()
            cli_map = {c['id_cliente']: c['nombre'] for c in res_c.data}
            for v in ventas:
                v['cliente_nombre'] = cli_map.get(v.get('id_cliente'), "Desconocido")
        except:
            for v in ventas:
                v['cliente_nombre'] = "Desconocido"
                
        return ventas

    def get_data_for_dashboard(self):
        """Devuelve dataframes listos para pandas con nombres mapeados."""
        import pandas as pd
        
        # 1. Ventas
        ventas = self.venta_model.get_all()
        df_ventas = pd.DataFrame(ventas) if ventas else pd.DataFrame()
        
        if not df_ventas.empty:
            # Sincronizar columna de monto
            df_ventas['monto_total'] = df_ventas['precio_total_cierre']
            
            # Mapear Vendedor (Nombre)
            try:
                # Tabla 'vendedor' en minúsculas según esquema
                res_v = self.venta_model.client.table('vendedor').select('id_vendedor, nombre').execute()
                vend_map = {v['id_vendedor']: v['nombre'] for v in res_v.data}
                df_ventas['vendedor'] = df_ventas['id_vendedor'].map(vend_map)
            except:
                df_ventas['vendedor'] = "Desconocido"
                
            # Mapear Cliente (Nombre)
            try:
                res_c = self.venta_model.client.table('cliente').select('id_cliente, nombre').execute()
                cli_map = {c['id_cliente']: c['nombre'] for c in res_c.data}
                df_ventas['cliente_nombre'] = df_ventas['id_cliente'].map(cli_map)
            except:
                df_ventas['cliente_nombre'] = "Desconocido"
            
        # 2. Gastos (Requerimientos)
        reqs = self.req_model.get_all()
        df_reqs = pd.DataFrame(reqs) if reqs else pd.DataFrame()
        if not df_reqs.empty and 'total' not in df_reqs.columns:
            df_reqs['total'] = 0.0
            
        return df_ventas, df_reqs