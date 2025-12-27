# controllers/operaciones_controller.py

from models.operaciones_model import VentaModel, PasajeroModel, DocumentacionModel, TareaModel
from datetime import date, timedelta
import pandas as pd

class OperacionesController:
    def __init__(self):
        self.venta_model = VentaModel()
        self.doc_model = DocumentacionModel()
        self.pasajero_model = PasajeroModel()
        self.tarea_model = TareaModel()

    # ------------------------------------------------------------------
    # LÓGICA DE CONTROL DE RIESGO (Dashboard #1)
    # ------------------------------------------------------------------

    def get_ventas_con_documentos_pendientes(self):
        """
        Segmentador Inteligente: Retorna solo las Ventas (y sus datos) 
        que tienen al menos un documento crítico PENDIENTE o RECIBIDO.
        """
        all_ventas = self.venta_model.get_all()
        ventas_pendientes_ids = set()

        for doc in self.doc_model.get_all():
            if doc['es_critico'] and doc['estado_entrega'] in ['PENDIENTE', 'RECIBIDO']:
                # Encontrar a qué venta pertenece este pasajero
                pasajero = self.pasajero_model.get_by_id(doc['id_pasajero'])
                if pasajero:
                    ventas_pendientes_ids.add(pasajero['id_venta'])

        # Filtrar las ventas completas
        return [v for v in all_ventas if v['id'] in ventas_pendientes_ids]
        
    def get_detalle_documentacion_by_venta(self, id_venta):
        """Retorna el detalle de la documentación de todos los pasajeros de una venta."""
        docs_venta = self.doc_model.get_documentos_by_venta_id(id_venta)
        
        # Unir documentos con nombres de pasajeros
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
        return pd.DataFrame(detalle)
    
    def validar_documento(self, id_doc):
        """Actualiza el estado de un documento a VALIDADO."""
        doc = self.doc_model.get_by_id(id_doc)
        if doc:
            self.doc_model.update(id_doc, {'estado_entrega': 'VALIDADO'})
            return True, f"Documento ID {id_doc} validado exitosamente."
        return False, "Documento no encontrado."

    # ------------------------------------------------------------------
    # LÓGICA DE EJECUCIÓN (Dashboard #2)
    # ------------------------------------------------------------------

    def es_viaje_documentalmente_desbloqueado(self, id_venta):
        """
        Verifica si TODOS los documentos críticos de una venta están VALIDADO.
        """
        docs_venta = self.doc_model.get_documentos_by_venta_id(id_venta)
        
        # Si no hay documentos críticos, se considera desbloqueado.
        documentos_criticos = [d for d in docs_venta if d['es_critico']]
        if not documentos_criticos:
            return True
        
        # Verifica que todos los críticos estén VALIDADO
        for doc in documentos_criticos:
            if doc['estado_entrega'] != 'VALIDADO':
                return False # Basta con uno pendiente o recibido
        
        return True

    def get_tareas_ejecutables(self, responsable=None):
        """
        Retorna las tareas PENDIENTES o EN PROCESO que cumplen con la 
        condición de documentación y filtradas por responsable.
        """
        if responsable:
            all_tareas = self.tarea_model.get_tareas_by_responsable(responsable)
        else:
            all_tareas = self.tarea_model.get_all()
            
        tareas_ejecutables = []
        for tarea in all_tareas:
            if tarea['estado_cumplimiento'] in ['PENDIENTE', 'EN PROCESO']:
                
                venta = self.venta_model.get_by_id(tarea['id_venta'])
                
                # Regla de filtro: La tarea solo aparece si cumple el requisito documental
                if not tarea['requiere_documentacion'] or self.es_viaje_documentalmente_desbloqueado(tarea['id_venta']):
                    
                    tareas_ejecutables.append({
                        'ID Tarea': tarea['id'],
                        'ID Venta': tarea['id_venta'],
                        'Descripción': tarea['descripcion'],
                        'Destino': venta['destino'] if venta else 'N/A',
                        'Fecha Salida': venta['fecha_salida'] if venta else date.today(),
                        'Fecha Límite': tarea['fecha_limite'],
                        'Responsable': tarea['responsable_ejecucion'],
                        'Estado': tarea['estado_cumplimiento']
                    })
                    
        return pd.DataFrame(tareas_ejecutables).sort_values(by='Fecha Salida', ascending=True)

    def completar_tarea(self, id_tarea):
        """Actualiza el estado de una tarea a COMPLETADO."""
        tarea = self.tarea_model.get_by_id(id_tarea)
        if tarea:
            self.tarea_model.update(id_tarea, {'estado_cumplimiento': 'COMPLETADO', 'fecha_completado': date.today()})
            return True, f"Tarea ID {id_tarea} marcada como COMPLETADA."
        return False, "Tarea no encontrada."