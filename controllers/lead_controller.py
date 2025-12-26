# controllers/lead_controller.py
from lead_model import LeadModel

class LeadController:
    def __init__(self):
        self.model = LeadModel()

    def registrar_nuevo_lead(self, datos: dict):
        # Aquí se puede añadir lógica de validación extra si es necesario
        if not datos.get('numero') or not datos.get('vendedor'):
            raise ValueError("Número y vendedor son requeridos.")
        
        # Llama al modelo para la inserción en la "BD"
        return self.model.insert_new_lead(datos)

    def obtener_leads_activos(self, vendedor: str):
        """ Obtiene leads para el seguimiento. """
        return self.model.get_active_leads(vendedor)

    def registrar_seguimiento(self, datos: dict):
        """ Actualiza el estado del lead y registra el historial. """
        numero = datos.get('numero')
        estado = datos.get('estado_lead')
        detalle = datos.get('detalle')
        
        return self.model.update_lead_state(numero, estado, detalle)