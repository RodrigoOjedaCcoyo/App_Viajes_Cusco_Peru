# controllers/lead_controller.py
from models.lead_model import LeadModel

class LeadController:
    """Controlador para manejar la lógica de negocio de los Leads."""
    
    def __init__(self):
        self.model = LeadModel()
        
    def registrar_nuevo_lead(self, nombre, email, telefono, origen, vendedor):
        """Valida los datos y llama al modelo para guardar el lead."""
        
        # Lógica de Validación (Controlador)
        if not nombre or not email or not telefono:
            return False, "Todos los campos (Nombre, Email, Teléfono) son obligatorios."
            
        # Llamada al Modelo para persistir los datos
        new_id = self.model.create_lead(nombre, email, telefono, origen, vendedor)
        
        if new_id:
            return True, f"Lead registrado con éxito. ID asignado: {new_id}"
        else:
            return False, "Error desconocido al registrar el Lead."

    def obtener_leads_del_vendedor(self, vendedor):
        """Devuelve todos los leads asignados a un vendedor específico."""
        return self.model.get_leads_by_vendedor(vendedor)