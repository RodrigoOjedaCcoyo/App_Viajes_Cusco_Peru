# models/base_model.py

# Mantenemos las importaciones de tipos
from supabase import Client as SupabaseClient
from typing import Optional, List, Dict, Any

class BaseModel:
    """Clase base para interactuar directamente con una tabla específica de Supabase.
    Recibe el cliente de Supabase (inyección de dependencia) en la inicialización."""
    
    # 1. Constructor: Corregido el tipo de 'supabase_client'
    def __init__(self, table_name: str, supabase_client: SupabaseClient):
        self.table_name = table_name
        self.client = supabase_client 

    # 2. get_all: Corregido el tipado (Dict) y el acceso al método (client.table)
    def get_all(self) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de la tabla Supabase."""
        try:
            # CORRECCIÓN: self.client.table
            response = self.client.table(self.table_name).select('*').execute()
            return response.data
        except Exception as e:
            print(f'Error al obtener todos los datos de {self.table_name}: {e}')
            return []

    def get_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Busca un ítem en la lista por su ID."""
        try:
            response = self.client.table(self.table_name).select('*').eq('id', item_id).single().execute()
            return response.data
        except Exception:
            return None 

    # 3. save: Corregido el tipado (int) y el acceso al método (self.client)
    def save(self, data: dict) -> Optional[int]:
        """Insertar un nuevo registro en la tabla de Supabase."""
        try:
            # CORRECCIÓN: self.client (en minúsculas)
            response = self.client.table(self.table_name).insert(data).select('id').execute()

            if response.data:
                return response.data[0].get('id')
            return None
        except Exception as e:
            print(f'Error al guardar datos en {self.table_name}: {e}')
            return None 
    
    # Método añadido para facilitar la actualización en el controlador (como LeadController)
    def update_by_id(self, item_id: int, data: dict) -> bool:
        try:
            response = self.client.table(self.table_name).update(data).eq('id', item_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error al actualizar el ID {item_id} en {self.table_name}: {e}")
            return False