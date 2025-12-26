# controllers/lead_controller.py

from ..models.lead_model import LeadModel

class LeadController:
    """Controlador para manejar la lógica de negocio de los Leads."""
    
    def __init__(self):
        self.model = LeadModel()
        
    # Función de Registro (Ajustada a 3 argumentos)
    def registrar_nuevo_lead(self, telefono, origen, vendedor):
        """Valida los datos y llama al modelo para guardar el lead."""
        
        if not telefono or not origen or not vendedor:
            return False, "Todos los campos son obligatorios (Número de Celular, Red Social, Vendedor)."
            
        new_id = self.model.create_lead(telefono, origen, vendedor)
        
        if new_id:
            return True, f"Lead registrado con éxito. ID asignado: {new_id}"
        else:
            return False, "Error desconocido al registrar el Lead."

    # Función de Obtención (Sigue igual)
    def obtener_leads_del_vendedor(self, vendedor):
        """Devuelve todos los leads asignados a un vendedor específico."""
        return self.model.get_leads_by_vendedor(vendedor)

    # Función de Actualización (Añadida y correctamente DENTRO de la clase)
    def actualizar_estado_lead(self, lead_id, nuevo_estado): 
        """Busca el lead por ID y actualiza su estado."""
        
        leads = self.model.get_all()
        
        for lead in leads:
            if lead.get('id') == lead_id:
                lead['estado'] = nuevo_estado
                return True, f"Lead ID {lead_id} actualizado a estado: {nuevo_estado}"
                
        return False, f"Lead ID {lead_id} no encontrado."