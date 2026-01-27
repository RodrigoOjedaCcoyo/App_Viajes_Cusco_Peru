# controllers/operaciones_controller.py
from models.operaciones_model import VentaModel, PasajeroModel, DocumentacionModel, TareaModel, RequerimientoModel
from datetime import date, timedelta
from supabase import Client
import pandas as pd

class OperacionesController:
    # Inyección de dependencia del Cliente Supabase
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.venta_model = VentaModel(supabase_client)
        self.doc_model = DocumentacionModel(supabase_client)
        self.pasajero_model = PasajeroModel(supabase_client)
        self.tarea_model = TareaModel(supabase_client)
        self.req_model = RequerimientoModel(supabase_client)

    # ------------------------------------------------------------------
    # LÓGICA DE TABLERO DE EJECUCIÓN DIARIA (Dashboard #2)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # LÓGICA DE TABLERO DE EJECUCIÓN DIARIA (Dashboard #2)
    # ------------------------------------------------------------------

    def get_fechas_con_servicios(self, year: int, month: int):
        # Limpieza completa de simulación
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
            return fechas_activas
        except Exception as e:
            print(f"Error fetching fechas activas: {e}")
            return set()

    def get_servicios_rango_fechas(self, start_date: date, end_date: date):
        try:
            res_servicios = (
                self.client.table('venta_tour')
                .select('*')
                .gte('fecha_servicio', start_date.isoformat())
                .lte('fecha_servicio', end_date.isoformat())
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

            # 4. Pagos acumulados
            pagos_map = {}
            if ids_ventas:
                res_p = self.client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute()
                for p in res_p.data:
                    vid = p['id_venta']
                    pagos_map[vid] = pagos_map.get(vid, 0) + (p['monto_pagado'] or 0)

            # Guías y Endosos (Tabla 'venta_servicio_proveedor' + 'proveedor')
            guias_map = {}
            proveedor_endoso_map = {}
            if ids_ventas:
                res_g = (
                    self.client.table('venta_servicio_proveedor')
                    .select('id_venta, n_linea, tipo_servicio, proveedor(nombre_comercial)')
                    .in_('id_venta', ids_ventas)
                    .execute()
                )
                for g in res_g.data:
                    key = f"{g['id_venta']}-{g['n_linea']}"
                    if g.get('tipo_servicio') == 'GUIA':
                        guias_map[key] = g['proveedor']['nombre_comercial'] if g.get('proveedor') else "Desconocido"
                    elif g.get('tipo_servicio') == 'PROVEEDOR_ENDOSO' or g.get('tipo_servicio') == 'AGENCIA_ENDOSO':
                        proveedor_endoso_map[key] = g['proveedor']['nombre_comercial'] if g.get('proveedor') else "Desconocido"
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                
                # FILTRO: Excluir ventas B2B del tablero diario (solo mostrar ventas directas)
                if v.get('id_agencia_aliada') is not None:
                    continue
                
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if float(saldo or 0) <= 0.1 else "🔴 PENDIENTE"
                
                # Prioridad: 1. Observaciones del día, 2. Catálogo de tours, 3. Nombre general de la venta
                nombre_tour = s.get('observaciones') or tours_map.get(s['id_tour']) or v.get('tour_nombre') or "Tour Desconocido"
                
                # Guía y Endoso desde el mapa relacional
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
                    'Pax': s.get('cantidad_pasajeros', 1),
                    'Cliente': nombre_cliente,
                    'Guía': nombre_guia,
                    'Agencia Endoso': nombre_endoso,
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
            clientes_map = {}
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

            # Guías y Endosos (Tabla 'venta_servicio_proveedor' + 'proveedor')
            guias_map = {}
            proveedor_endoso_map = {}
            if ids_ventas:
                res_g = (
                    self.client.table('venta_servicio_proveedor')
                    .select('id_venta, n_linea, tipo_servicio, proveedor(nombre_comercial)')
                    .in_('id_venta', ids_ventas)
                    .execute()
                )
                for g in res_g.data:
                    key = f"{g['id_venta']}-{g['n_linea']}"
                    if g.get('tipo_servicio') == 'GUIA':
                        guias_map[key] = g['proveedor']['nombre_comercial'] if g.get('proveedor') else "Desconocido"
                    elif g.get('tipo_servicio') == 'PROVEEDOR_ENDOSO' or g.get('tipo_servicio') == 'AGENCIA_ENDOSO':
                        proveedor_endoso_map[key] = g['proveedor']['nombre_comercial'] if g.get('proveedor') else "Desconocido"
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                
                # FILTRO: Excluir ventas B2B del tablero diario (solo mostrar ventas directas)
                if v.get('id_agencia_aliada') is not None:
                    continue
                
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if float(saldo or 0) <= 0.1 else f"🔴 PENDIENTE (${float(saldo or 0):.2f})"
                
                # Prioridad: 1. Observaciones del día, 2. Catálogo de tours, 3. Nombre general de la venta
                nombre_tour = s.get('observaciones') or tours_map.get(s['id_tour']) or v.get('tour_nombre') or "Tour Desconocido"
                
                # Guía y Endoso desde el mapa relacional
                key_g = f"{s['id_venta']}-{s['n_linea']}"
                nombre_guia = guias_map.get(key_g, "Por Asignar")
                nombre_endoso = proveedor_endoso_map.get(key_g, "---")
                
                # Semáforo de Logística
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
                    'Pax': s.get('cantidad_pasajeros', 1),
                    'Cliente': nombre_cliente,
                    'Guía': nombre_guia,
                    'Agencia Endoso': nombre_endoso,
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

    def actualizar_guia_servicio(self, id_venta, n_linea, nombre_guia):
        """Asigna un guía a un servicio específico según el esquema SQL venta_servicio_proveedor."""
        try:
            if not nombre_guia or nombre_guia == "Por Asignar":
                return False, "Nombre de guía no válido."
                
            # 1. Buscar el ID del guía (en tabla proveedor)
            res_g = self.client.table('proveedor').select('id_proveedor').ilike('nombre_comercial', f"%{nombre_guia}%").limit(1).execute()
            if not res_g.data:
                return False, "Guía (proveedor) no encontrado."
            
            id_guia = res_g.data[0]['id_proveedor']
            
            # 2. Upsert en venta_servicio_proveedor (vincular como GUIA)
            datos = {
                "id_venta": id_venta,
                "n_linea": n_linea,
                "id_proveedor": id_guia,
                "tipo_servicio": 'GUIA',
                "estado_pago": 'PENDIENTE'
            }
            self.client.table('venta_servicio_proveedor').upsert(datos, on_conflict='id_venta, n_linea, tipo_servicio').execute()
            return True, f"Guía {nombre_guia} asignado correctamente."
        except Exception as e:
            print(f"Error asignando guía: {e}")
            return False, f"Error: {e}"

    def actualizar_endoso_servicio(self, id_venta, n_linea, nombre_agencia):
        """Asigna una agencia proveedora para un servicio de endoso."""
        try:
            if not nombre_agencia or nombre_agencia == "---":
                return False, "Nombre de agencia no válido."

            # 1. Buscar el ID de la agencia (en tabla proveedor)
            res_p = self.client.table('proveedor').select('id_proveedor').ilike('nombre_comercial', f"%{nombre_agencia}%").limit(1).execute()
            if not res_p.data:
                # Si no existe, podríamos intentar buscar en agencia_aliada si es un B2B puro
                return False, "Agencia/Proveedor no encontrado."
            
            id_prov = res_p.data[0]['id_proveedor']
            
            # 2. Upsert en venta_servicio_proveedor (vincular como PROVEEDOR_ENDOSO)
            datos = {
                "id_venta": id_venta,
                "n_linea": n_linea,
                "id_proveedor": id_prov,
                "tipo_servicio": 'PROVEEDOR_ENDOSO',
                "estado_pago": 'PENDIENTE'
            }
            self.client.table('venta_servicio_proveedor').upsert(datos, on_conflict='id_venta, n_linea, tipo_servicio').execute()
            
            # Además actualizar la tabla venta_tour para marcar es_endoso = True
            self.client.table('venta_tour').update({"es_endoso": True}).match({"id_venta": id_venta, "n_linea": n_linea}).execute()
            
            return True, f"Endoso a {nombre_agencia} registrado."
        except Exception as e:
            print(f"Error registrando endoso: {e}")
            return False, f"Error: {e}"

    def toggle_endoso_servicio(self, id_venta, n_linea, es_endoso):
        """Activa o desactiva el flag de endoso para un servicio."""
        try:
            self.client.table('venta_tour').update({"es_endoso": es_endoso}).match({"id_venta": id_venta, "n_linea": n_linea}).execute()
            return True, "Estado de endoso actualizado."
        except Exception as e:
            print(f"Error haciendo toggle de endoso: {e}")
            return False, f"Error: {e}"

    # ------------------------------------------------------------------
    # LÓGICA DE REQUERIMIENTOS
    # ------------------------------------------------------------------

    def registrar_requerimiento(self, data: dict):
        """Registra un nuevo requerimiento en la base de datos."""
        try:
            res = self.req_model.save(data)
            return True, "Requerimiento registrado correctamente."
        except Exception as e:
            print(f"Error registrando requerimiento: {e}")
            return False, f"Error: {e}"

    def get_requerimientos(self):
        """Obtiene la lista de requerimientos directamente desde la base de datos."""
        try:
            return self.req_model.get_all()
        except Exception as e:
            print(f"Error obteniendo requerimientos: {e}")
            return []

    def get_all_ventas(self):
        """Obtiene todas las ventas registradas para vista compartida."""
        try:
            # Sincronizado: tabla 'venta', columna 'precio_total_cierre'
            res = self.client.table('venta').select('*').order('fecha_venta', desc=True).execute()
            ventas = res.data
            
            resultado = []
            for v in ventas:
                # Buscar cliente (tabla 'cliente')
                res_c = self.client.table('cliente').select('nombre').eq('id_cliente', v['id_cliente']).single().execute()
                nombre_cliente = res_c.data['nombre'] if res_c.data else "Desconocido"
                
                # Buscar vendedor (tabla 'vendedor')
                res_v = self.client.table('vendedor').select('nombre').eq('id_vendedor', v['id_vendedor']).single().execute()
                nombre_vendedor = res_v.data['nombre'] if res_v.data else "Desconocido"

                resultado.append({
                    'ID': v['id_venta'],
                    'Fecha': v['fecha_venta'],
                    'Cliente': nombre_cliente,
                    'Vendedor': nombre_vendedor,
                    'Total': v['precio_total_cierre'],
                    'Estado': v['estado_venta']
                })
            return resultado
        except Exception as e:
            print(f"Error get_all_ventas: {e}")
            return []

    def get_data_for_analytics(self):
        """Obtiene datos de servicios operativos para dashboards de analítica de logística."""
        try:
            # Traemos los servicios con información básica de la venta
            res = self.client.table('venta_tour').select('*').execute()
            if not res.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(res.data)
            
            # Mapeo defensivo de columnas (por si acaso el esquema varía)
            columnas_esperadas = {
                'fecha_servicio': ['fecha_servicio', 'Fecha', 'fecha'],
                'cantidad_pasajeros': ['cantidad_pasajeros', 'Pax', 'pax', 'pax_total']
            }
            
            for col_obj, fallbacks in columnas_esperadas.items():
                if col_obj not in df.columns:
                    for fb in fallbacks:
                        if fb in df.columns:
                            df.rename(columns={fb: col_obj}, inplace=True)
                            break
            
            # Asegurar conversión de fecha
            if 'fecha_servicio' in df.columns:
                df['fecha_servicio'] = pd.to_datetime(df['fecha_servicio'])
            
            return df
        except Exception as e:
            print(f"Error en get_data_for_analytics: {e}")
            return pd.DataFrame()

    def obtener_ventas_pendientes(self):
        """Obtiene ventas confirmadas que requieren atención operativa (Rooming List, etc)."""
        try:
            # Traer ventas confirmadas
            res = self.client.table('venta').select('*').in_('estado_venta', ['CONFIRMADO', 'EN_VIAJE']).order('fecha_venta', desc=True).execute()
            ventas = res.data or []
            
            # Enriquecer con nombre de cliente (como en get_all_ventas)
            ids_clientes = list(set([v['id_cliente'] for v in ventas]))
            clientes_map = {}
            if ids_clientes:
                res_c = self.client.table('cliente').select('id_cliente, nombre').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    clientes_map[c['id_cliente']] = c['nombre']
            
            resultado = []
            for v in ventas:
                nombre_cliente = clientes_map.get(v['id_cliente'], "Cliente Desconocido")
                resultado.append({
                    'id_venta': v['id_venta'],
                    'nombre_cliente': nombre_cliente,
                    'tour_nombre': v.get('tour_nombre'),
                    'fecha_venta': v['fecha_venta'],
                    'num_pasajeros': v.get('num_pasajeros', 1)
                })
            return resultado
        except Exception as e:
            print(f"Error obtener_ventas_pendientes: {e}")
            return []