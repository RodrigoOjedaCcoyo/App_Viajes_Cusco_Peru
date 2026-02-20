# controllers/operaciones_controller.py
from models.operaciones_model import PasajeroModel
from models.venta_model import VentaModel
from datetime import date, timedelta
from supabase import Client
import pandas as pd

class OperacionesController:
    # Inyección de dependencia del Cliente Supabase
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.venta_model = VentaModel('venta', supabase_client)
        self.pasajero_model = PasajeroModel(supabase_client)

    # ------------------------------------------------------------------
    # LÓGICA DE TABLERO DE EJECUCIÓN DIARIA (Dashboard #2)
    # ------------------------------------------------------------------

    def get_fechas_con_servicios(self, year: int, month: int):
        try:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
                
            res = (
                self.client.table('venta_tour')
                .select('fecha_servicio')
                .gte('fecha_servicio', start_date.isoformat())
                .lt('fecha_servicio', end_date.isoformat())
                .execute()
            )
            
            fechas_activas = set()
            if res.data:
                for item in res.data:
                    try:
                        fechas_activas.add(date.fromisoformat(item['fecha_servicio']))
                    except: pass
            return list(fechas_activas)
        except Exception as e:
            print(f"Error en Calendario: {e}")
            return []

    def get_servicios_rango_fechas(self, start_date: date, end_date: date):
        """Obtiene servicios para un rango de fechas con nombres de clientes y ventas."""
        try:
            res_servicios = (
                self.client.table('venta_tour')
                .select('*')
                .gte('fecha_servicio', start_date.isoformat())
                .lte('fecha_servicio', end_date.isoformat())
                .order('fecha_servicio')
                .execute()
            )
            
            if not res_servicios.data:
                return []
                
            servicios_data = res_servicios.data
            ids_ventas = list(set([s['id_venta'] for s in servicios_data]))
            ids_tours = list(set([s['id_tour'] for s in servicios_data if s.get('id_tour')]))
            
            ventas_map = {}
            if ids_ventas:
                res_v = self.client.table('venta').select('*').in_('id_venta', ids_ventas).execute()
                for v in res_v.data:
                    ventas_map[v['id_venta']] = v
                    
            tours_map = {}
            if ids_tours:
                res_t = self.client.table('tour').select('id_tour, nombre').in_('id_tour', ids_tours).execute()
                for t in res_t.data:
                    tours_map[t['id_tour']] = t['nombre']
                    
            ids_clientes = list(set([v['id_cliente'] for v in ventas_map.values() if v.get('id_cliente')]))
            clientes_map = {}
            if ids_clientes:
                res_c = self.client.table('cliente').select('id_cliente, nombre').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    clientes_map[c['id_cliente']] = c['nombre']

            pagos_map = {} 
            if ids_ventas:
                res_p = self.client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute()
                for p in res_p.data:
                    vid = p['id_venta']
                    pagos_map[vid] = pagos_map.get(vid, 0) + (p['monto_pagado'] or 0)

            # Guías y Endosos
            guias_map = {}
            proveedor_endoso_map = {}
            detalles_proveedores_map = {}
            if ids_ventas:
                res_g = (
                    self.client.table('venta_servicio_proveedor')
                    .select('id_venta, n_linea, tipo_servicio, estado_pago, proveedor(nombre_comercial)')
                    .in_('id_venta', ids_ventas)
                    .execute()
                )
                for g in res_g.data:
                    key = f"{g['id_venta']}-{g['n_linea']}"
                    prov_nom = g['proveedor']['nombre_comercial'] if g.get('proveedor') else "Desconocido"
                    if g.get('tipo_servicio') == 'GUIA':
                        guias_map[key] = prov_nom
                    elif g.get('tipo_servicio') in ['PROVEEDOR_ENDOSO', 'AGENCIA_ENDOSO']:
                        proveedor_endoso_map[key] = prov_nom
                    
                    if key not in detalles_proveedores_map:
                        detalles_proveedores_map[key] = []
                    detalles_proveedores_map[key].append({
                        "tipo": g.get('tipo_servicio'),
                        "nombre": prov_nom,
                        "estado": g.get('estado_pago', 'PENDIENTE')
                    })
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                if v.get('id_agencia_aliada') is not None:
                    continue
                
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if float(saldo or 0) <= 0.1 else "🔴 PENDIENTE"
                
                nombre_tour = s.get('observacion') or tours_map.get(s['id_tour']) or v.get('tour_nombre') or "Tour Desconocido"
                
                key_g = f"{s['id_venta']}-{s['n_linea']}"
                nombre_guia = guias_map.get(key_g, "Por Asignar")
                nombre_endoso = proveedor_endoso_map.get(key_g, "---")
                es_endoso = s.get('es_endoso', False)
                
                resultado.append({
                    'ID Venta': s['id_venta'],
                    'N Linea': s['n_linea'],
                    'Fecha': s['fecha_servicio'],
                    'Hora': "08:00 AM",
                    'Servicio': nombre_tour,
                    'Endoso?': es_endoso,
                    'Pax': s.get('cantidad', 1),
                    'Cliente': nombre_cliente,
                    'Guía': nombre_guia,
                    'Agencia Endoso': nombre_endoso,
                    'Proveedor': nombre_endoso if es_endoso else nombre_guia,
                    'Detalle Proveedores': detalles_proveedores_map.get(key_g, []),
                    'Estado Pago': estado_pago,
                    'Tipo': '👤 B2C',
                    'Día Itin.': s.get('id_itinerario_dia_index', 1),
                    'ID Itinerario': v.get('id_itinerario_digital'),
                    'URL Cloud': v.get('url_itinerario') or ""
                })
            return resultado
        except Exception as e:
            print(f"Error en Rango de Fechas: {e}")
            return []

    def get_servicios_por_fecha(self, fecha_filtro: date):
        try:
            start_date = fecha_filtro
            end_date = fecha_filtro + timedelta(days=1)
            
            res_servicios = (
                self.client.table('venta_tour')
                .select('*')
                .gte('fecha_servicio', start_date.isoformat())
                .lt('fecha_servicio', end_date.isoformat())
                .execute()
            )
            
            if not res_servicios.data:
                return []
                
            servicios_data = res_servicios.data
            ids_ventas = list(set([s['id_venta'] for s in servicios_data]))
            ids_tours = list(set([s['id_tour'] for s in servicios_data if s.get('id_tour')]))
            
            ventas_map = {}
            if ids_ventas:
                res_v = self.client.table('venta').select('*').in_('id_venta', ids_ventas).execute()
                for v in res_v.data:
                    ventas_map[v['id_venta']] = v
                    
            tours_map = {}
            if ids_tours:
                res_t = self.client.table('tour').select('id_tour, nombre').in_('id_tour', ids_tours).execute()
                for t in res_t.data:
                    tours_map[t['id_tour']] = t['nombre']
                    
            ids_clientes = list(set([v['id_cliente'] for v in ventas_map.values() if v.get('id_cliente')]))
            clientes_map = {}
            if ids_clientes:
                res_c = self.client.table('cliente').select('id_cliente, nombre').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    clientes_map[c['id_cliente']] = c['nombre']

            pagos_map = {} 
            if ids_ventas:
                res_p = self.client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute()
                for p in res_p.data:
                    vid = p['id_venta']
                    pagos_map[vid] = pagos_map.get(vid, 0) + (p['monto_pagado'] or 0)

            guias_map = {}
            proveedor_endoso_map = {}
            detalles_proveedores_map = {}
            
            if ids_ventas:
                res_g = (
                    self.client.table('venta_servicio_proveedor')
                    .select('id_venta, n_linea, tipo_servicio, estado_pago, proveedor(nombre_comercial)')
                    .in_('id_venta', ids_ventas)
                    .execute()
                )
                for g in res_g.data:
                    key = f"{g['id_venta']}-{g['n_linea']}"
                    prov_nom = g['proveedor']['nombre_comercial'] if g.get('proveedor') else "Desconocido"
                    if g.get('tipo_servicio') == 'GUIA':
                        guias_map[key] = prov_nom
                    elif g.get('tipo_servicio') in ['PROVEEDOR_ENDOSO', 'AGENCIA_ENDOSO']:
                        proveedor_endoso_map[key] = prov_nom
                    if key not in detalles_proveedores_map:
                        detalles_proveedores_map[key] = []
                    detalles_proveedores_map[key].append({
                        "tipo": g.get('tipo_servicio'),
                        "nombre": prov_nom,
                        "estado": g.get('estado_pago', 'PENDIENTE')
                    })
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                if v.get('id_agencia_aliada') is not None:
                    continue
                
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if float(saldo or 0) <= 0.1 else f"🔴 PENDIENTE (${float(saldo or 0):.2f})"
                
                nombre_tour = s.get('observacion') or tours_map.get(s['id_tour']) or v.get('tour_nombre') or "Tour Desconocido"
                
                key_g = f"{s['id_venta']}-{s['n_linea']}"
                nombre_guia = guias_map.get(key_g, "Por Asignar")
                nombre_endoso = proveedor_endoso_map.get(key_g, "---")
                es_endoso = s.get('es_endoso', False)
                status_log = "🟢"
                if es_endoso:
                    if nombre_endoso == "---" or nombre_endoso == "Por Asignar": status_log = "🔴"
                else:
                    if nombre_guia == "Por Asignar": status_log = "🔴"

                resultado.append({
                    'ID Servicio': f"{s['id_venta']}-{s['n_linea']}", 
                    'Hora': "08:00 AM",
                    'Log.': status_log,
                    'Servicio': nombre_tour,
                    'Endoso?': es_endoso,
                    'Pax': s.get('cantidad', 1),
                    'Cliente': nombre_cliente,
                    'Guía': nombre_guia,
                    'Agencia Endoso': nombre_endoso,
                    'Proveedor': nombre_endoso if es_endoso else nombre_guia,
                    'Detalle Proveedores': detalles_proveedores_map.get(key_g, []),
                    'Estado Pago': estado_pago,
                    'Tipo': '👤 B2C',
                    'ID Venta': s['id_venta'],
                    'N Linea': s['n_linea'],
                    'Día Itin.': s.get('id_itinerario_dia_index', 1),
                    'ID Itinerario': v.get('id_itinerario_digital'),
                    'URL Cloud': v.get('url_itinerario') or ""
                })
            return resultado
        except Exception as e:
            print(f"Error en Tablero Diario: {e}")
            return []

    def get_data_for_dashboard(self):
        """Devuelve dataframes para dashboards operativos."""
        try:
            res = self.client.table('venta_tour').select('*').execute()
            data = res.data or []
            df = pd.DataFrame(data)
            
            # Mapeo defensivo de columnas
            columnas_esperadas = {
                'fecha_servicio': ['fecha_servicio', 'Fecha', 'fecha'],
                'cantidad': ['cantidad', 'Pax', 'pax', 'pax_total', 'cantidad_pasajeros']
            }
            
            for col_obj, fallbacks in columnas_esperadas.items():
                if col_obj not in df.columns:
                    for fb in fallbacks:
                        if fb in df.columns:
                            df.rename(columns={fb: col_obj}, inplace=True)
                            break
            return df
        except Exception as e:
            print(f"Error dashboard operaciones: {e}")
            return pd.DataFrame()

    def actualizar_guia_servicio(self, id_venta, n_linea, nombre_guia):
        try:
            if not nombre_guia or nombre_guia == "Por Asignar":
                return False, "Nombre de guía no válido."
            res_g = self.client.table('proveedor').select('id_proveedor').ilike('nombre_comercial', f"%{nombre_guia}%").limit(1).execute()
            if not res_g.data:
                return False, "Guía (proveedor) no encontrado."
            id_guia = res_g.data[0]['id_proveedor']
            
            self.client.table('venta_servicio_proveedor').upsert({
                'id_venta': id_venta,
                'n_linea': n_linea,
                'id_proveedor': id_guia,
                'tipo_servicio': 'GUIA'
            }).execute()
            return True, f"Guía {nombre_guia} asignado correctamente."
        except Exception as e:
            return False, f"Error asignando guía: {e}"