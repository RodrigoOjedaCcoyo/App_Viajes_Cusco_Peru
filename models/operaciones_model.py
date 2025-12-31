# models/operaciones_model.py

# Asegúrate de que 'models/base_model.py' está en tu directorio de modelos (si se usa en otros lados)
from datetime import date

# ----------------------------------------------------------------------
# SIMULACIÓN DE DATOS ESTRUCTURADOS (Datos de ejemplo)
# ----------------------------------------------------------------------

# Usaremos un índice inicial más alto para evitar conflictos con IDs ya creados por el módulo Ventas
NEXT_ID_INICIAL = 10 

# Datos de Venta (ID 10 y 11 para evitar conflicto con los primeros creados por page_ventas)
VENTAS_INICIALES = [
    {
        'id': 10, 
        'fecha_salida': date(2026, 1, 10), 
        'vendedor': 'Angel',
        'destino': 'Machu Picchu',
        'estado_pago': 'Pagado',
    },
    {
        'id': 11, 
        'fecha_salida': date(2026, 1, 25), 
        'vendedor': 'Abel',
        'destino': 'Valle Sagrado',
        'estado_pago': 'Pendiente',
    },
    # Venta de prueba que tiene todo VALIDADO para que NO aparezca en Dashboard #1
    {
        'id': 12,
        'fecha_salida': date(2026, 2, 1),
        'vendedor': 'Angel',
        'destino': 'Ausangate',
        'estado_pago': 'Pagado',
    }
]

# Pasajeros:
PASAJEROS_INICIALES = [
    {'id': 10, 'id_venta': 10, 'nombre': 'Juan Perez'},
    {'id': 11, 'id_venta': 10, 'nombre': 'Maria Lopez'},
    {'id': 12, 'id_venta': 11, 'nombre': 'Carla Soto'},
    {'id': 13, 'id_venta': 12, 'nombre': 'Luis Ramos'}, # Pasajero del Viaje 12
]

# Documentación:
DOC_INICIALES = [
    # Viaje 10: Tienen 1 Pasaporte OK, 1 Pendiente (DEBE APARECER en Dashboard #1)
    {'id': 100, 'id_pasajero': 10, 'tipo_documento': 'Pasaporte', 'es_critico': True, 'estado_entrega': 'VALIDADO', 'fecha_entrega': date(2025, 12, 10)},
    {'id': 101, 'id_pasajero': 10, 'tipo_documento': 'Seguro Viaje', 'es_critico': False, 'estado_entrega': 'PENDIENTE', 'fecha_entrega': None},
    {'id': 102, 'id_pasajero': 11, 'tipo_documento': 'Pasaporte', 'es_critico': True, 'estado_entrega': 'PENDIENTE', 'fecha_entrega': None}, # Documento crítico pendiente
    {'id': 103, 'id_pasajero': 11, 'tipo_documento': 'Visa', 'es_critico': False, 'estado_entrega': 'RECIBIDO', 'fecha_entrega': date(2025, 12, 20)},
    
    # Viaje 12: Tienen todos los documentos críticos VALIDADO (NO DEBE APARECER en Dashboard #1)
    {'id': 104, 'id_pasajero': 13, 'tipo_documento': 'Pasaporte', 'es_critico': True, 'estado_entrega': 'VALIDADO', 'fecha_entrega': date(2025, 12, 10)},
]

# Tareas Logísticas:
TAREAS_INICIALES = [
    # Tarea para Venta 10 (Requiere documentación crítica pendiente, DEBE BLOQUEARSE inicialmente)
    {'id': 50, 'id_venta': 10, 'descripcion': 'Comprar Ticket Tren', 'responsable_ejecucion': 'Angel', 'fecha_limite': date(2026, 1, 1), 'estado_cumplimiento': 'PENDIENTE', 'requiere_documentacion': True},
    # Tarea para Venta 10 (NO requiere documentación, DEBE EJECUTARSE)
    {'id': 51, 'id_venta': 10, 'descripcion': 'Reservar Hotel Cusco', 'responsable_ejecucion': 'Abel', 'fecha_limite': date(2026, 1, 5), 'estado_cumplimiento': 'PENDIENTE', 'requiere_documentacion': False},
    # Tarea para Venta 12 (Requiere documentación, pero esta ya está VALIDADO, DEBE EJECUTARSE)
    {'id': 52, 'id_venta': 12, 'descripcion': 'Confirmar Transporte', 'responsable_ejecucion': 'Angel', 'fecha_limite': date(2026, 1, 15), 'estado_cumplimiento': 'PENDIENTE', 'requiere_documentacion': True},
]


# ----------------------------------------------------------------------
# CLASES MODELO ADAPTADAS (MOCK / SESSION STATE)
# ----------------------------------------------------------------------

import streamlit as st 

class OperacionesBaseModel:
    """
    Clase base para modelos operativos (MOCK).
    Gestiona datos en st.session_state en lugar de Supabase.
    """
    def __init__(self, key: str, initial_data: list):
        self.key = key
        
        # Inicializar lista en session_state si no existe
        if self.key not in st.session_state:
            st.session_state[self.key] = []

        # Cargar datos iniciales SOLO si la lista está vacía
        if not st.session_state[self.key]:
            # Establecer el contador de ID un poco más alto para los datos de prueba
            st.session_state[f"{self.key}_next_id"] = NEXT_ID_INICIAL + len(initial_data)
            # Añadir todos los registros iniciales a la lista
            st.session_state[self.key].extend(initial_data)

    def get_all(self):
        """Retorna todos los registros de la lista en memoria."""
        return st.session_state[self.key]

    def get_by_id(self, item_id: int):
        """Busca un ítem por ID."""
        for item in st.session_state[self.key]:
            if item['id'] == item_id:
                return item
        return None

    def update_by_id(self, item_id: int, updates: dict):
        """Actualiza un ítem por ID."""
        for item in st.session_state[self.key]:
            if item['id'] == item_id:
                item.update(updates)
                return True
        return False
        
    def save(self, data: dict):
        """Guarda un nuevo registro (simulado)."""
        new_id = st.session_state.get(f"{self.key}_next_id", 1)
        data['id'] = new_id
        st.session_state[self.key].append(data)
        st.session_state[f"{self.key}_next_id"] = new_id + 1
        return new_id

class VentaModel(OperacionesBaseModel):
    def __init__(self):
        super().__init__('ventas', initial_data=VENTAS_INICIALES)

class PasajeroModel(OperacionesBaseModel):
    def __init__(self):
        super().__init__('pasajeros', initial_data=PASAJEROS_INICIALES)
        
    def get_by_id(self, id):
        """Método de búsqueda adaptado para tu estructura de lista."""
        for item in self.get_all():
            if item['id'] == id:
                return item
        return None

class DocumentacionModel(OperacionesBaseModel):
    def __init__(self):
        super().__init__('documentacion', initial_data=DOC_INICIALES)
        
    def get_documentos_by_venta_id(self, id_venta):
        """Obtiene todos los documentos relacionados a una venta específica."""
        pasajeros = PasajeroModel().get_all()
        doc_list = self.get_all()
        
        # Obtener IDs de pasajeros de la venta
        pasajero_ids = {p['id'] for p in pasajeros if p.get('id_venta') == id_venta}
        
        # Filtrar documentos
        return [doc for doc in doc_list if doc.get('id_pasajero') in pasajero_ids]

class TareaModel(OperacionesBaseModel):
    def __init__(self):
        super().__init__('tareas', initial_data=TAREAS_INICIALES)
        
    def get_tareas_by_responsable(self, responsable):
        """Filtra tareas por el operador responsable."""
        return [t for t in self.get_all() if t.get('responsable_ejecucion') == responsable]