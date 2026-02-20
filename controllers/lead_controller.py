# controllers/lead_controller.py

from models.lead_model import LeadModel
from supabase import Client
from typing import List, Dict, Any

class LeadController:
    """Controlador para manejar la lógica de negocio de los Leads."""
    def __init__(self, supabase_client:Client):
        self.model = LeadModel(supabase_client)
    def registrar_nuevo_lead(self, telefono: str, origen: str, vendedor: str, nombre_pasajero: str = "") -> tuple[bool, str]:
        """Valida los datos y llama al modelo para guardar el lead."""
        
        # 1. Validación de Campos
        if not telefono or origen == "---Seleccione---":
            return False, "El campo Celular y Origen son obligatorios."
        
        # 2. Comprobar si ya existe un lead (Búsqueda simple por teléfono para el MMM)
        lead_existente = self.model.find_by_phone(telefono) 
        if lead_existente:
            return False, "Ya existe un lead con ese teléfono en la base de datos."

        # 3. Guardar el lead
        new_id = self.model.create_lead(telefono, origen, vendedor, nombre_pasajero)
        
        if new_id:
            return True, f"Registro exitoso. ID: {new_id}"
        else:
            return False, "Error al registrar en la base de datos."

    def obtener_leads_del_vendedor(self, vendedor):
        """Devuelve todos los leads asignados a un vendedor específico."""
        return self.model.get_leads_by_vendedor(vendedor)

    def obtener_todos_leads(self):
        """Devuelve TODOS los leads del sistema (Vista General)."""
        return self.model.get_all_leads()

    def obtener_mapeo_vendedores(self):
        """Devuelve diccionario {id: nombre} de vendedores."""
        return self.model.get_vendedores_mapping()

    def actualizar_estado_lead(self, lead_id, nuevo_estado): 
        """Operación no soportada en el esquema resumido."""
        return False, "La tabla Lead ya no tiene columna de Estado."
