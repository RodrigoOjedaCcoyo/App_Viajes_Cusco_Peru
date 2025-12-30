# models/lead_model.py (CÓDIGO FINAL CORREGIDO Y COMPLETO)

from .base_model import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import Client

class LeadModel(BaseModel):
    """Modelo para la gestión de Leads (Clientes Potenciales)."""

    def __init__(self, table_name: str, supabase_client: Client):
        # El constructor de BaseModel guarda table_name y supabase_client (como self.client)
        super().__init__(table_name, supabase_client) 

    # Implementación simplificada para el formulario de 3 campos
    def create_lead(self, telefono: str, origen: str, vendedor: str) -> Optional[int]:
        """Guarda un nuevo lead en el sistema con información básica."""
        lead_data = {
            # Valores predeterminados para campos no solicitados:
            "nombre": f"Lead Tel: {telefono}",
            "email": "sin_email@app.com",
            
            "telefono": telefono,
            "origen": origen,
            "vendedor": vendedor,
            "estado": "Nuevo", 
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Delega el guardado a BaseModel
        return self.save(lead_data)
        
    def get_leads_by_vendedor(self, vendedor: str) -> List[Dict[str, Any]]:
        """Obtiene todos los leads asignados a un vendedor específico."""
        try:
            # Filtra por vendedor
            response = self.client.table(self.table_name).select('*').eq('vendedor', vendedor).execute()
            return response.data
        except Exception as e:
            print(f'Error al filtrar leads por vendedor: {e}')
            return []
            
    # --- MÉTODO FALTANTE 1: Búsqueda de Lead Activo (para evitar duplicados) ---
    def find_by_phone_active(self, telefono: str) -> Optional[Dict[str, Any]]:
        """Busca un lead por teléfono que no esté 'Convertido' o 'No Interesado'."""
        try:
            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('telefono', telefono)
                .not_.eq('estado', 'Convertido (Vendido)') # Excluye vendidos
                .not_.eq('estado', 'No Interesado')       # Excluye descartados
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al buscar lead activo por teléfono: {e}")
            return None

    # --- MÉTODO FALTANTE 2: Actualización por ID ---
    def update_by_id(self, lead_id: int, datos_a_actualizar: Dict[str, Any]) -> bool:
        """Actualiza un lead por su ID."""
        try:
            # Llama al método update de BaseModel (asumiendo que está implementado)
            # Si el update de BaseModel no está implementado, esta llamada delegará la actualización.
            # Aquí lo implementamos explícitamente si BaseModel es solo un wrapper de 'save'
            
            response = (
                self.client.table(self.table_name)
                .update(datos_a_actualizar)
                .eq('id', lead_id)
                .execute()
            )
            return len(response.data) > 0 # Retorna True si al menos una fila fue actualizada
        except Exception as e:
            print(f"Error al actualizar lead ID {lead_id}: {e}")
            return False