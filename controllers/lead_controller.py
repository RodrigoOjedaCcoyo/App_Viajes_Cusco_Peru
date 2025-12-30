# controllers/lead_controller.py

from ..models.lead_model import LeadModel
from supabase import Client
from typing import List, Dict, Any

class LeadController:
    """Controlador para manejar la lógica de negocio de los Leads."""
    def __init__(self, supabase_client:Client):
        self.model = LeadModel(table_name='Leads', supabase_client=supabase_client)
    def registrar_nuevo_lead(self, telefono: str, origen: str, vendedor: str) -> tuple[bool, str]:
        """Valida los datos y llama al modelo para guardar el lead."""
        
        # 1. Validación de Campos (Reintroducida la Lógica de Negocio)
        if not telefono or origen == "---Seleccione---" or vendedor == "---Seleccione---":
            return False, "Los campos Celular, Origen y Vendedor son obligatorios."
        
        # 2. Comprobar si ya existe un lead activo (CRÍTICO)
        lead_existente = self.model.find_by_phone_active(telefono) 
        if lead_existente:
            return False, f"Ya existe un lead activo (estado: {lead_existente.get('estado', 'N/A')}) con ese teléfono."

        # 3. Guardar el lead
        new_id = self.model.create_lead(telefono, origen, vendedor)
        
        if new_id:
            return True, f"Lead registrado con éxito. ID asignado: {new_id}"
        else:
            return False, "Error desconocido al registrar el Lead."

    def obtener_leads_del_vendedor(self, vendedor):
        """Devuelve todos los leads asignados a un vendedor específico."""
        return self.model.get_leads_by_vendedor(vendedor)

    def actualizar_estado_lead(self, lead_id, nuevo_estado): 
        """Busca el lead por ID y actualiza su estado."""
        
        datos_a_actualizar = {'estado': nuevo_estado}

        exito = self.model.update_by_id(lead_id, datos_a_actualizar)
        
        if exito:
            return True, f"Lead ID {lead_id} actualizado a estado: {nuevo_estado}"
        else:
            # 🛑 SINTAXIS CORREGIDA
            return False, f"Error al actualizar o Lead ID {lead_id} no encontrado"