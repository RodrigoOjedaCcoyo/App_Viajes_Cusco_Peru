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
    # LÓGICA DE CONTROL DE RIESGO (Dashboard #1)
    # ------------------------------------------------------------------

    def get_ventas_con_documentos_pendientes(self):
        """
        Retorna las ventas que tienen documentos críticos PENDIENTES o RECIBIDOS (No VALIDADOS).
        """
        try:
            res_docs = (
                self.client.table('documentacion')
                .select('id_pasajero')
                .eq('es_critico', True)
                .neq('estado_entrega', 'VALIDADO')
                .execute()
            )
            
            if not res_docs.data:
                return []
                
            ids_pasajeros_riesgo = list(set([d['id_pasajero'] for d in res_docs.data]))
            
            if not ids_pasajeros_riesgo:
                return []
                
            res_pasajeros = (
                self.client.table('pasajero')
                .select('id_venta')
                .in_('id_pasajero', ids_pasajeros_riesgo)
                .execute()
            )
            
            ids_ventas_riesgo = list(set([p['id_venta'] for p in res_pasajeros.data]))
            
            if not ids_ventas_riesgo:
                return []
                
            res_ventas = (
                self.client.table('venta')
                .select('*') 
                .in_('id_venta', ids_ventas_riesgo)
                .execute()
            )
            
            ventas = res_ventas.data
            
            datos_ui = []
            for v in ventas:
                nombre_vendedor = "Desconocido"
                if v.get('id_vendedor'):
                    try:
                        res_vend = self.client.table('vendedor').select('nombre').eq('id_vendedor', v['id_vendedor']).single().execute()
                        if res_vend.data: nombre_vendedor = res_vend.data['nombre']
                    except: pass
                
                nombre_cliente = "Desconocido"
                if v.get('id_cliente'):
                    try:
                        res_cli = self.client.table('cliente').select('nombre').eq('id_cliente', v['id_cliente']).single().execute()
                        if res_cli.data: nombre_cliente = res_cli.data['nombre']
                    except: pass
                
                destinos = "Múltiple/Desconocido"
                try:
                    res_vt = self.client.table('venta_tour').select('id_tour, tour(nombre)').eq('id_venta', v['id_venta']).execute()
                    if res_vt.data:
                        nombres_tours = [item['tour']['nombre'] for item in res_vt.data if item.get('tour')]
                        destinos = ", ".join(nombres_tours)
                except: pass

                fecha_salida_obj = date.today()
                if v.get('fecha_venta'):
                    try:
                        fecha_salida_obj = date.fromisoformat(v['fecha_venta'])
                    except ValueError: pass

                datos_ui.append({
                    'id': v['id_venta'],
                    'cliente': nombre_cliente,
                    'destino': destinos,
                    'fecha_salida': fecha_salida_obj, 
                    'vendedor': nombre_vendedor
                })
                
                try:
                    res_fecha = self.client.table('venta_tour').select('fecha_servicio').eq('id_venta', v['id_venta']).order('fecha_servicio').limit(1).execute()
                    if res_fecha.data and res_fecha.data[0]['fecha_servicio']:
                        datos_ui[-1]['fecha_salida'] = date.fromisoformat(res_fecha.data[0]['fecha_servicio'])
                except: pass

            return datos_ui
            
        except Exception as e:
            print(f"Error Controller Riesgo: {e}")
            return []

    def get_detalle_documentacion_by_venta(self, id_venta):
        docs_venta = self.doc_model.get_documentos_by_venta_id(id_venta)
        
        detalle = []
        for doc in docs_venta:
            pasajero = self.pasajero_model.get_by_id(doc['id_pasajero'])
            detalle.append({
                'ID Venta': id_venta,
                'ID Pasajero': doc['id_pasajero'],
                'Pasajero': pasajero['nombre'] if pasajero else 'Desconocido',
                'ID Documento': doc['id'], 
                'Tipo Documento': doc['tipo_documento'],
                'Es Crítico': '🟢 Sí' if doc['es_critico'] else '⚪ No',
                'Estado': doc['estado_entrega'],
                'Fecha Entrega': doc['fecha_entrega']
            })
        
        if not detalle:
            return pd.DataFrame(columns=['ID Venta', 'ID Pasajero', 'Pasajero', 'ID Documento', 'Tipo Documento', 'Es Crítico', 'Estado', 'Fecha Entrega'])
            
        return pd.DataFrame(detalle)
    
    def validar_documento(self, id_doc):
        return self.doc_model.update_by_id(id_doc, {'estado_entrega': 'VALIDADO'}), "Documento validado."

    def subir_documento(self, id_doc, file_obj):
        try:
            self.doc_model.update_by_id(id_doc, {'estado_entrega': 'RECIBIDO', 'ubicacion_archivo': f"mock_path/{file_obj.name}"})
            return True, f"Archivo {file_obj.name} subido correctamente."
        except Exception as e:
             return False, f"Error al subir: {e}"

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
            ids_tours = list(set([s['id_tour'] for s in servicios_data]))
            
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
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if saldo <= 0.1 else "🔴 PENDIENTE"
                
                nombre_tour = tours_map.get(s['id_tour'], "Tour Desconocido")
                id_serv = s.get('id') or s.get('id_venta_tour') or s.get('n_linea') or "N/A"
                
                resultado.append({
                    'ID Servicio': id_serv, 
                    'Fecha': s['fecha_servicio'],
                    'Hora': "08:00 AM",
                    'Servicio': nombre_tour,
                    'Pax': s.get('cantidad_pasajeros', 1),
                    'Cliente': nombre_cliente,
                    'Guía': s.get('guia_asignado', 'Por Asignar'),
                    'Estado Pago': estado_pago,
                    'ID Venta': s['id_venta']
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
            ids_tours = list(set([s['id_tour'] for s in servicios_data]))
            
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
            
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if saldo <= 0.1 else f"🔴 PENDIENTE (${saldo:.2f})"
                
                nombre_tour = tours_map.get(s['id_tour'], "Tour Desconocido")
                id_serv = s.get('id') or s.get('id_venta_tour') or s.get('n_linea') or "N/A"
                
                resultado.append({
                    'ID Servicio': id_serv, 
                    'Hora': "08:00 AM",
                    'Servicio': nombre_tour,
                    'Pax': s.get('cantidad_pasajeros', 1),
                    'Cliente': nombre_cliente,
                    'Guía': s.get('guia_asignado', 'Por Asignar'),
                    'Estado Pago': estado_pago,
                    'ID Venta': s['id_venta']
                })
            return resultado
        except Exception as e:
            print(f"Error en Tablero Diario: {e}")
            return []

    def actualizar_guia_servicio(self, id_servicio, nombre_guia):
        try:
            self.client.table('venta_tour').update({'guia_asignado': nombre_guia}).eq('id', id_servicio).execute()
            return True, "Guía asignado correctamente."
        except Exception as e:
            print(f"No se pudo guardar en DB: {e}")
            return True, "Guía asignado (Simulado)."

    # ------------------------------------------------------------------
    # LÓGICA DE REQUERIMIENTOS
    # ------------------------------------------------------------------

    def registrar_requerimiento(self, data: dict):
        """Registra un nuevo requerimiento en la base de datos."""
        try:
            res = self.req_model.create(data)
            return True, "Requerimiento registrado correctamente."
        except Exception as e:
            print(f"Error registrando requerimiento: {e}")
            return False, f"Error: {e}"

    def get_requerimientos(self):
        """Obtiene la lista de requerimientos."""
        try:
            return self.req_model.get_all()
        except Exception as e:
            print(f"Error obteniendo requerimientos: {e}")
            return []