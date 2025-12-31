# controllers/operaciones_controller.py
from models.operaciones_model import VentaModel, PasajeroModel, DocumentacionModel, TareaModel
from datetime import date
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
                # Buscar nombre vendedor (Optimizable con cache o mapeo global)
                nombre_vendedor = "Desconocido"
                if v.get('id_vendedor'):
                    try:
                        res_vend = self.client.table('vendedor').select('nombre').eq('id_vendedor', v['id_vendedor']).single().execute()
                        if res_vend.data: nombre_vendedor = res_vend.data['nombre']
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

                datos_ui.append({
                    'id': v['id_venta'],
                    'destino': destinos,
                    'fecha_salida': v['fecha_venta'], # OJO: Fecha Venta no es Salida. Buscamos fecha_servicio en Venta_Tour
                    'vendedor': nombre_vendedor
                })
                
                # Corrección Fecha Salida: Buscar la min(fecha_servicio) en Venta_Tour
                try:
                    res_fecha = self.client.table('venta_tour').select('fecha_servicio').eq('id_venta', v['id_venta']).order('fecha_servicio').limit(1).execute()
                    if res_fecha.data:
                        datos_ui[-1]['fecha_salida'] = res_fecha.data[0]['fecha_servicio']
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

    # ------------------------------------------------------------------
    # LÓGICA DE EJECUCIÓN (Dashboard #2)
    # ------------------------------------------------------------------

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
                            if res_f.data: fecha_salida = res_f.data[0]['fecha_servicio']
                        except: pass
                        
                    tareas_ejecutables.append({
                        'ID Tarea': tarea['id'],
                        'ID Venta': tarea['id_venta'],
                        'Descripción': tarea['descripcion'],
                        'Destino': destino_str, # Simplificado
                        'Fecha Salida': fecha_salida,
                        'Fecha Límite': tarea['fecha_limite'],
                        'Responsable': tarea['responsable_ejecucion'],
                        'Estado': tarea['estado_cumplimiento']
                    })
                    
        return pd.DataFrame(tareas_ejecutables)

    def completar_tarea(self, id_tarea):
        return self.tarea_model.update_by_id(id_tarea, {'estado_cumplimiento': 'COMPLETADO', 'fecha_completado': date.today().isoformat()}), "Tarea completada."