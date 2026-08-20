# controllers/reporte_controller.py
from models.venta_model import VentaModel
from models.lead_model import LeadModel
from models.meta_mensual_model import MetaMensualModel
import pandas as pd

class ReporteController:
    """
    Controlador encargado de obtener datos agregados y reportes
    para las áreas de Gerencia y Contabilidad.
    """
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.venta_model = VentaModel(supabase_client)
        self.lead_model = LeadModel(supabase_client)
        self.meta_model = MetaMensualModel(supabase_client)
        
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
            
            res_c = self.client.table('cliente').select('id_cliente, nombre, lead(numero_celular, pais_origen)').execute()
            cli_map = {}
            tel_map = {}
            for c in res_c.data:
                cli_map[c['id_cliente']] = c['nombre']
                # Extraer celular
                l_info = c.get('lead') or {}
                if isinstance(l_info, list) and len(l_info) > 0:
                    tel_map[c['id_cliente']] = l_info[0].get('numero_celular', '---')
                else:
                    tel_map[c['id_cliente']] = l_info.get('numero_celular', '---')
                    
            for v in ventas:
                v['cliente_nombre'] = cli_map.get(v.get('id_cliente'), "Desconocido")
                v['telefono'] = tel_map.get(v.get('id_cliente'), "---")
            return ventas
        except Exception as e:
            print(f"Error auditoría: {e}")
            return []

    def get_data_for_dashboard(self):
        """Devuelve dataframes para dashboards financieros."""
        # 1. Ventas (excluye canceladas: no deben contarse como ingreso real)
        try:
            res_ventas = self.client.table('venta').select('*').neq('estado_venta', 'CANCELADO').execute()
            ventas = res_ventas.data or []
            df_ventas = pd.DataFrame(ventas) if ventas else pd.DataFrame()
            if not df_ventas.empty:
                df_ventas['monto_total'] = df_ventas.get('precio_total_cierre', 0)
                # Mapeos básicos
                res_v = self.client.table('vendedor').select('id_vendedor, nombre').execute()
                vend_map = {v['id_vendedor']: v['nombre'] for v in res_v.data}
                df_ventas['vendedor'] = df_ventas['id_vendedor'].map(vend_map)
                    
                res_c = self.client.table('cliente').select('id_cliente, nombre, lead(numero_celular, pais_origen)').execute()
                cli_map = {c['id_cliente']: c['nombre'] for c in res_c.data}
                tel_map = {}
                for c in res_c.data:
                    l_info = c.get('lead') or {}
                    if isinstance(l_info, list) and len(l_info) > 0:
                        tel_map[c['id_cliente']] = l_info[0].get('numero_celular', '---')
                    else:
                        tel_map[c['id_cliente']] = l_info.get('numero_celular', '---')
                
                df_ventas['cliente_nombre'] = df_ventas['id_cliente'].map(cli_map)
                df_ventas['telefono'] = df_ventas['id_cliente'].map(tel_map)
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

    def obtener_meta_mensual(self, periodo: str) -> tuple[float, bool]:
        """
        Retorna una tupla: (monto_meta, esta_congelada).
        Si no existe en base de datos, retorna (10000.0, False).
        """
        try:
            meta = self.meta_model.obtener_meta_por_periodo(periodo)
            if meta:
                return float(meta.get('monto_meta', 10000.0)), True
            return 10000.0, False
        except Exception as e:
            print(f"Error al obtener meta mensual para {periodo}: {e}")
            return 10000.0, False

    def guardar_meta_mensual(self, periodo: str, monto: float) -> bool:
        """Guarda y congela la meta para un periodo específico."""
        return self.meta_model.registrar_meta(periodo, monto)