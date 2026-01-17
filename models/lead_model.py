# models/lead_model.py (CÓDIGO FINAL CORREGIDO Y COMPLETO)

from .base_model import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import Client

class LeadModel(BaseModel):
    """Modelo para la gestión de Leads (Clientes Potenciales)."""

    def __init__(self, table_name: str, supabase_client: Client):
        # El constructor de BaseModel guarda table_name y supabase_client (como self.client)
        super().__init__('lead', supabase_client) 

    # Implementación simplificada para el formulario de 3 campos
    def create_lead(self, telefono: str, origen: str, vendedor: str, comentario: str = "", fecha_seguimiento: str = None) -> Optional[int]:
        """Guarda un nuevo lead en el sistema con información básica y seguimiento."""
        lead_data = {
            "numero_celular": telefono,
            "red_social": origen,
            "id_vendedor": vendedor,
            "estado_lead": "NUEVO",
            "comentario": comentario, # Campo común en CRM
            "fecha_seguimiento": fecha_seguimiento, # Campo para el recordatorio
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "whatsapp": True
        }
        return self.save(lead_data)
        
    def get_leads_by_vendedor(self, vendedor: str) -> List[Dict[str, Any]]:
        """Obtiene todos los leads asignados a un vendedor específico."""
        try:
            # Filtra por ID de vendedor (Schema Match)
            response = self.client.table(self.table_name).select('*').eq('id_vendedor', vendedor).execute()
            return response.data
        except Exception as e:
            print(f'Error al filtrar leads por vendedor: {e}')
            return []

    def get_all_leads(self) -> List[Dict[str, Any]]:
        """Obtiene TODOS los leads registrados (Vista General)."""
        try:
            response = self.client.table(self.table_name).select('*').order('fecha_creacion', desc=True).execute()
            return response.data
        except Exception as e:
            print(f'Error al obtener todos los leads: {e}')
            return []
            
    def get_vendedores_mapping(self) -> Dict[int, str]:
        """Retorna un diccionario {id: nombre} de todos los vendedores activos."""
        try:
            # Nota: Tabla 'vendedor' en minúsculas según corrección reciente
            response = self.client.table('vendedor').select('id_vendedor, nombre').execute()
            return {v['id_vendedor']: v['nombre'] for v in response.data}
        except Exception as e:
            print(f"Error obteniendo vendedores: {e}")
            return {}
            
    # --- MÉTODO FALTANTE 1: Búsqueda de Lead Activo (para evitar duplicados) ---
    def find_by_phone_active(self, telefono: str) -> Optional[Dict[str, Any]]:
        """Busca un lead por teléfono que no esté 'Convertido' o 'No Interesado'."""
        try:
            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('numero_celular', telefono)
                .not_.eq('estado_lead', 'CONVERTIDO') # Excluye vendidos
                .not_.eq('estado_lead', 'DESCARTADO')       # Excluye descartados
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
                .eq('id_lead', lead_id)
                .execute()
            )
            return len(response.data) > 0 # Retorna True si al menos una fila fue actualizada
        except Exception as e:
            print(f"Error al actualizar lead ID {lead_id}: {e}")
            return False