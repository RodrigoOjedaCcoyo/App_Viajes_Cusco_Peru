# models/lead_model.py

from .base_model import BaseModel
from datetime import datetime
from typing import List, Dict, Any
from supabase import Client

class LeadModel(BaseModel):
    """Modelo para la gestión de Leads (Clientes Potenciales)."""

    def __init__(self, table_name: str, supabase_client: Client):
        # Usamos 'leads' como clave para el almacenamiento en sesión
        super().__init__(table_name, supabase_client) 

    # Implementación simplificada para el formulario de 3 campos
    def create_lead(self, telefono: str, origen: str, vendedor: str):
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
        
    def get_leads_by_vendedor(self, vendedor) -> List[Dict[str, Any]]:
        """Obtiene leads filtrados por el nombre del vendedor"""
        try:
            response = self.client.table(self.table_name).select('*').eq('vendedor', vendedor).execute()
            return response.data
        except Exception as e:
            print(f'Error al filtrar leads por vendedor: {e}')
            return []