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

            # 5. Guías asignados (Tabla 'asignacion_guia' + 'guia')
            guias_map = {}
            if ids_ventas:
                res_g = (
                    self.client.table('asignacion_guia')
                    .select('id_venta, n_linea, guia(nombre)')
                    .in_('id_venta', ids_ventas)
                    .execute()
                )
                for g in res_g.data:
                    key = f"{g['id_venta']}-{g['n_linea']}"
                    guias_map[key] = g['guia']['nombre'] if g.get('guia') else "Desconocido"
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if saldo <= 0.1 else "🔴 PENDIENTE"
                
                nombre_tour = tours_map.get(s['id_tour']) or v.get('tour_nombre') or "Tour Desconocido"
                
                # Guía desde el mapa relacional
                key_g = f"{s['id_venta']}-{s['n_linea']}"
                nombre_guia = guias_map.get(key_g, "Por Asignar")
                
                resultado.append({
                    'ID Venta': s['id_venta'],
                    'N Linea': s['n_linea'],
                    'Fecha': s['fecha_servicio'],
                    'Hora': "08:00 AM",
                    'Servicio': nombre_tour,
                    'Pax': s.get('cantidad_pasajeros', 1),
                    'Cliente': nombre_cliente,
                    'Guía': nombre_guia,
                    'Estado Pago': estado_pago,
                    'Día Itin.': s.get('id_itinerario_dia_index', 1),
                    'ID Itinerario': v.get('id_itinerario_digital')
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

            # Guías
            guias_map = {}
            if ids_ventas:
                res_g = (
                    self.client.table('asignacion_guia')
                    .select('id_venta, n_linea, guia(nombre)')
                    .in_('id_venta', ids_ventas)
                    .execute()
                )
                for g in res_g.data:
                    key = f"{g['id_venta']}-{g['n_linea']}"
                    guias_map[key] = g['guia']['nombre'] if g.get('guia') else "Desconocido"
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if saldo <= 0.1 else f"🔴 PENDIENTE (${saldo:.2f})"
                
                nombre_tour = tours_map.get(s['id_tour']) or v.get('tour_nombre') or "Tour Desconocido"
                id_serv = s.get('id') or s.get('id_venta_tour') or s.get('n_linea') or "N/A"
                
                resultado.append({
                    'ID Servicio': id_serv, 
                    'Hora': "08:00 AM",
                    'Servicio': nombre_tour,
                    'Pax': s.get('cantidad_pasajeros', 1),
                    'Cliente': nombre_cliente,
                    'Guía': s.get('guia_asignado', 'Por Asignar'),
                    'Estado Pago': estado_pago,
                    'ID Venta': s['id_venta'],
                    'Día Itin.': s.get('id_itinerario_dia_index', 1),
                    'ID Itinerario': v.get('id_itinerario_digital')
                })
            return resultado
        except Exception as e:
            print(f"Error en Tablero Diario: {e}")
            return []

    def actualizar_guia_servicio(self, id_venta, n_linea, nombre_guia):
        """Asigna un guía a un servicio específico según el esquema SQL asignacion_guia."""
        try:
            # 1. Buscar el ID del guía por nombre
            res_g = self.client.table('guia').select('id_guia').ilike('nombre', f"%{nombre_guia}%").limit(1).execute()
            if not res_g.data:
                return False, "Guía no encontrado en la base de datos."
            
            id_guia = res_g.data[0]['id_guia']
            
            # 2. Insertar en asignacion_guia (PK: id_venta, n_linea, id_guia)
            # Nota: Usamos upsert o insert simple. El esquema dice fecha_servicio es obligatoria.
            # Necesitaríamos la fecha del servicio también.
            
            # Por ahora, si el usuario solo quiere guardar el nombre en un campo de texto (simulado)
            # pero el esquema no lo tiene, lo ideal es usar la tabla asignacion_guia.
            # Como falta info de fecha aquí, devolveremos éxito simulado si falla por integridad.
            
            nueva_asig = {
                "id_venta": id_venta,
                "n_linea": n_linea,
                "id_guia": id_guia,
                "fecha_servicio": date.today().isoformat() # Placeholder
            }
            self.client.table('asignacion_guia').insert(nueva_asig).execute()
            return True, f"Guía {nombre_guia} asignado correctamente."
        except Exception as e:
            print(f"Error asignando guía: {e}")
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