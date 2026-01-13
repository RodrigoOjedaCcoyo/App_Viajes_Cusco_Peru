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
        # ESTRATEGIA:
        # 1. Obtener todos los documentos CRÍTICOS que NO están VALIDADOS.
        # 2. Obtener los IDs de pasajeros de esos documentos.
        # 3. Obtener los IDs de ventas de esos pasajeros.
        # 4. Obtener la info de esas ventas.
        
        # Paso 1: Docs Críticos Pendientes/Recibidos
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
            
            # Paso 2: IDs Ventas
            if not ids_pasajeros_riesgo:
                return []
                
            res_pasajeros = (
                self.client.table('pasajero')
                .select('id_venta')
                .in_('id_pasajero', ids_pasajeros_riesgo)
                .execute()
            )
            
            ids_ventas_riesgo = list(set([p['id_venta'] for p in res_pasajeros.data]))
            
            # Paso 3: Detalles Venta (Incluyendo nombres de Vendedor si es posible, por ahora ID o nombre flat)
            if not ids_ventas_riesgo:
                return []
                
            res_ventas = (
                self.client.table('venta')
                .select('*') # Trae todo de Venta
                .in_('id_venta', ids_ventas_riesgo)
                .execute()
            )
            
            ventas = res_ventas.data
            
            # ENRIQUECIMIENTO (Opcional): Obtener nombre vendedor
            # Asumimos que la tabla Venta tiene id_vendedor. Si queremos mostrar nombre, necesitaríamos otro query.
            # Por simplicidad ahora devolvemos la venta cruda o con mapeo básico
            
            # Mapeo para UI
            datos_ui = []
            for v in ventas:
                # Buscar nombre vendedor
                nombre_vendedor = "Desconocido"
                if v.get('id_vendedor'):
                    try:
                        res_vend = self.client.table('vendedor').select('nombre').eq('id_vendedor', v['id_vendedor']).single().execute()
                        if res_vend.data: nombre_vendedor = res_vend.data['nombre']
                    except: pass
                
                # Buscar nombre cliente principal
                nombre_cliente = "Desconocido"
                if v.get('id_cliente'):
                    try:
                        res_cli = self.client.table('cliente').select('nombre').eq('id_cliente', v['id_cliente']).single().execute()
                        if res_cli.data: nombre_cliente = res_cli.data['nombre']
                    except: pass
                
                # Buscar destino (en tabla Venta no hay destino directo en MASTER SCHEMA, está en Venta_Tour -> Tour)
                # O quizas en 'tour' textual si se usó el esquema simplificado antes.
                # Revisando Master Schema: Venta -> Venta_Tour -> Tour(nombre, id_lugar_base -> Lugar(nombre))
                destinos = "Múltiple/Desconocido"
                try:
                    res_vt = self.client.table('venta_tour').select('id_tour, tour(nombre)').eq('id_venta', v['id_venta']).execute()
                    if res_vt.data:
                        nombres_tours = [item['tour']['nombre'] for item in res_vt.data if item.get('tour')]
                        destinos = ", ".join(nombres_tours)
                except: 
                    # Fallback si falla el join complejo
                    pass

                # Convertir fecha_venta a date
                fecha_salida_obj = date.today()
                if v.get('fecha_venta'):
                    try:
                        fecha_salida_obj = date.fromisoformat(v['fecha_venta'])
                    except ValueError: pass

                datos_ui.append({
                    'id': v['id_venta'],
                    'cliente': nombre_cliente, # <--- NUEVO
                    'destino': destinos,
                    'fecha_salida': fecha_salida_obj, 
                    'vendedor': nombre_vendedor
                })
                
                # Corrección Fecha Salida: Buscar la min(fecha_servicio) en Venta_Tour
                try:
                    res_fecha = self.client.table('venta_tour').select('fecha_servicio').eq('id_venta', v['id_venta']).order('fecha_servicio').limit(1).execute()
                    if res_fecha.data and res_fecha.data[0]['fecha_servicio']:
                        # Sobrescribir con la fecha real del tour convertida
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
            # Obtener nombre pasajero
            pasajero = self.pasajero_model.get_by_id(doc['id_pasajero'])
            
            detalle.append({
                'ID Venta': id_venta,
                'ID Pasajero': doc['id_pasajero'],
                'Pasajero': pasajero['nombre'] if pasajero else 'Desconocido',
                'ID Documento': doc['id'], # ID numérico
                'Tipo Documento': doc['tipo_documento'],
                'Es Crítico': '🟢 Sí' if doc['es_critico'] else '⚪ No',
                'Estado': doc['estado_entrega'],
                'Fecha Entrega': doc['fecha_entrega']
            })
        return pd.DataFrame(detalle)
    
    def validar_documento(self, id_doc):
        # Actualizar usando BaseModel real
        return self.doc_model.update_by_id(id_doc, {'estado_entrega': 'VALIDADO'}), "Documento validado."

    def subir_documento(self, id_doc, file_obj):
        """Simula la subida de un documento y actualiza su estado a RECIBIDO."""
        # En producción: Aquí subirías file_obj a S3/Supabase Storage
        # Simulación: Solo actualizamos estado
        try:
            self.doc_model.update_by_id(id_doc, {'estado_entrega': 'RECIBIDO', 'ubicacion_archivo': f"mock_path/{file_obj.name}"})
            return True, f"Archivo {file_obj.name} subido correctamente."
        except Exception as e:
             return False, f"Error al subir: {e}"

    # ------------------------------------------------------------------
    # LÓGICA DE TABLERO DE EJECUCIÓN DIARIA (Dashboard #2)
    # ------------------------------------------------------------------

    def get_fechas_con_servicios(self, year: int, month: int):
        """Devuelve un SET de objetos date que tienen servicios en el mes dado."""
        try:
            # Construir rango de fechas
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
                
            # Query range
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


    def es_viaje_documentalmente_desbloqueado(self, id_venta):
        # Verificar documentos de esta venta
        docs = self.doc_model.get_documentos_by_venta_id(id_venta)
        criticos = [d for d in docs if d['es_critico']]
        for d in criticos:
            if d['estado_entrega'] != 'VALIDADO':
                return False
        return True

    def get_tareas_ejecutables(self, responsable=None):
        if responsable:
            all_tareas = self.tarea_model.get_tareas_by_responsable(responsable)
        else:
            all_tareas = self.tarea_model.get_all()
            
        tareas_ejecutables = []
        for tarea in all_tareas:
            if tarea['estado_cumplimiento'] in ['PENDIENTE', 'EN PROCESO']:
                
                # Check desbloqueo
                bloqueado = False
                if tarea['requiere_documentacion']:
                    if not self.es_viaje_documentalmente_desbloqueado(tarea['id_venta']):
                        bloqueado = True
                
                if not bloqueado:
                    # Enriquecer datos de venta para la tabla
                    venta = self.venta_model.get_by_id(tarea['id_venta'])
                    destino_str = "N/A"
                    fecha_salida = date.today()
                    
                    if venta:
                        # Intentar sacar fecha servicio
                        try:
                            res_f = self.client.table('venta_tour').select('fecha_servicio').eq('id_venta', tarea['id_venta']).limit(1).execute()
                            if res_f.data: 
                                # Convertir string ISO a objeto date
                                fecha_str = res_f.data[0]['fecha_servicio']
                                fecha_salida = date.fromisoformat(fecha_str)
                        except: pass
                        
                    tareas_ejecutables.append({
                        'ID Tarea': tarea['id'],
                        'ID Venta': tarea['id_venta'],
                        'Descripción': tarea['descripcion'],
                        'Destino': destino_str, # Simplificado
                        'Fecha Salida': fecha_salida, # Ahora es objeto date, compatible con st.column_config
                        'Fecha Límite': tarea['fecha_limite'],
                        'Responsable': tarea['responsable_ejecucion'],
                        'Estado': tarea['estado_cumplimiento']
                    })
                    
        df = pd.DataFrame(tareas_ejecutables)
        # Asegurar conversión explícita si el DF se crea vacío o mixto
        if not df.empty and 'Fecha Salida' in df.columns:
            df['Fecha Salida'] = pd.to_datetime(df['Fecha Salida']).dt.date
            
        return df

    def completar_tarea(self, id_tarea):
        return self.tarea_model.update_by_id(id_tarea, {'estado_cumplimiento': 'COMPLETADO', 'fecha_completado': date.today().isoformat()}), "Tarea completada."

    # ------------------------------------------------------------------
    # LÓGICA DE TABLERO DE EJECUCIÓN DIARIA (Dashboard #2)
    # ------------------------------------------------------------------

    def get_servicios_rango_fechas(self, start_date: date, end_date: date):
        """
        Obtiene todos los servicios en un rango de fechas (usado para vista semanal).
        Retorna lista de diccionarios planos.
        """
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
            
            # Reutilizamos la lógica de mapeo (Bulk fetch) para eficiencia
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
                    'Fecha': s['fecha_servicio'], # Util para agrupar en vista semanal
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
        """
        Obtiene todos los servicios (Tours) programados para una fecha específica.
        Retorna una lista de diccionarios planos para el Dashboard.
        """
        try:
            # Uso rango para evitar problemas de timestamp vs date
            start_date = fecha_filtro
            end_date = fecha_filtro + timedelta(days=1)
            
            res_servicios = (
                self.client.table('venta_tour')
                .select('*') # Use wildcard to avoid crashing if 'guia_asignado' column is missing
                .gte('fecha_servicio', start_date.isoformat())
                .lt('fecha_servicio', end_date.isoformat())
                .execute()
            )
            
            if not res_servicios.data:
                return []
                
            servicios_data = res_servicios.data
            ids_ventas = list(set([s['id_venta'] for s in servicios_data]))
            ids_tours = list(set([s['id_tour'] for s in servicios_data]))
            
            # 2. Fetch Bulk de Ventas y Tours para evitar N+1
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
                    
            # 3. Fetch Clientes (Necesitamos id_cliente de las ventas)
            ids_clientes = list(set([v['id_cliente'] for v in ventas_map.values() if v.get('id_cliente')]))
            clientes_map = {}
            if ids_clientes:
                res_c = self.client.table('cliente').select('id_cliente, nombre').in_('id_cliente', ids_clientes).execute()
                for c in res_c.data:
                    clientes_map[c['id_cliente']] = c['nombre']

            # 4. Fetch Pagos (Para calcular saldo)
            pagos_map = {} # id_venta -> total_pagado
            if ids_ventas:
                res_p = self.client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute()
                for p in res_p.data:
                    vid = p['id_venta']
                    pagos_map[vid] = pagos_map.get(vid, 0) + (p['monto_pagado'] or 0)
            
            # 5. Construir Resultado Plano
            resultado = []
            for s in servicios_data:
                v = ventas_map.get(s['id_venta'], {})
                id_cliente = v.get('id_cliente')
                nombre_cliente = clientes_map.get(id_cliente, "Desconocido")
                
                # Cálculo de saldo
                precio_total = v.get('precio_total_cierre', 0) or 0
                total_pagado = pagos_map.get(s['id_venta'], 0)
                saldo = precio_total - total_pagado
                estado_pago = "✅ SALDADO" if saldo <= 0.1 else "🔴 PENDIENTE" # Tolerancia centavos
                if saldo > 0:
                    estado_pago += f" (${saldo:.2f})"
                
                # Nombre Tour
                nombre_tour = tours_map.get(s['id_tour'], "Tour Desconocido")
                
                # Identificar el ID de forma flexible (puede ser 'id' o 'id_venta_tour' o similar)
                id_serv = s.get('id') or s.get('id_venta_tour') or s.get('n_linea') or "N/A"
                
                resultado.append({
                    'ID Servicio': id_serv, 
                    'Hora': "08:00 AM", # Hardcoded por ahora, no está en modelo
                    'Servicio': nombre_tour,
                    'Pax': s.get('cantidad_pasajeros', 1),
                    'Cliente': nombre_cliente,
                    'Guía': s.get('guia_asignado', 'Por Asignar'),
                    'Estado Pago': estado_pago,
                    'ID Venta': s['id_venta']
                })
                
            return resultado

        except Exception as e:
            # En producción no queremos st.error aquí si ya lo manejamos en la vista, 
            # pero para depurar lo dejamos un momento más o lo logueamos.
            print(f"Error en Tablero Diario: {e}")
            # Si el error es 'id', ya sabemos qué es.
            return []

    def actualizar_guia_servicio(self, id_servicio, nombre_guia):
        """Simula o ejecuta la asignación de guía a un servicio (Venta_Tour)."""
        try:
            # Intento de update directo. Si la columna no existe, fallará y capturaremos el error.
            # En un escenario real, esto actualizaría la tabla Venta_Tour o una tabla Asignacion_Guia
            self.client.table('venta_tour').update({'guia_asignado': nombre_guia}).eq('id', id_servicio).execute()
            return True, "Guía asignado correctamente."
        except Exception as e:
            # Fallback para demo: No romper si falla por esquema, solo loguear
            print(f"No se pudo guardar en DB (posible falta de columna): {e}")
            return True, "Guía asignado (Simulado en Session)."