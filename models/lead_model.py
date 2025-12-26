# models/lead_model.py

from .base_model import BaseModel
from datetime import datetime

class LeadModel(BaseModel):
    """Modelo para la gestión de Leads (Clientes Potenciales)."""

    def __init__(self):
        # Usamos 'leads' como clave para el almacenamiento en sesión
        super().__init__(key="leads") 

    # Implementación simplificada para el formulario de 3 campos
    def create_lead(self, telefono, origen, vendedor):
        """Guarda un nuevo lead en el sistema con información básica."""
        lead_data = {
            # Valores predeterminados ya que no los pedimos en el formulario:
            "nombre": f"Lead Tel: {telefono}",
            "email": "sin_email@app.com",
            
            "telefono": telefono,
            "origen": origen,
            "vendedor": vendedor,
            "estado": "Nuevo", 
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.save(lead_data)
        
    def get_leads_by_vendedor(self, vendedor):
        """Obtiene todos los leads asignados a un vendedor/rol."""
        all_leads = self.get_all()
        # Nota: Aquí se usa el rol del usuario logueado. Puedes cambiar la lógica si necesitas ver todos.
        return [lead for lead in all_leads if lead['vendedor'] == vendedor]