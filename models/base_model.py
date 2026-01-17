# models/base_model.py

# Mantenemos las importaciones de tipos
from supabase import Client as SupabaseClient
from typing import Optional, List, Dict, Any

class BaseModel:
    """Clase base para interactuar directamente con una tabla específica de Supabase.
    Recibe el cliente de Supabase (inyección de dependencia) en la inicialización."""
    
    # 1. Constructor: Añadido primary_key param
    def __init__(self, table_name: str, supabase_client: SupabaseClient, primary_key: str = 'id'):
        self.table_name = table_name
        self.client = supabase_client 
        self.primary_key = primary_key

    # 2. get_all: Corregido el tipado (Dict) y el acceso al método (client.table)
    def get_all(self) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de la tabla Supabase."""
        try:
            response = self.client.table(self.table_name).select('*').execute()
            return response.data
        except Exception as e:
            print(f'Error al obtener todos los datos de {self.table_name}: {e}')
            return []

    def get_by_id(self, item_id: Any) -> Optional[Dict[str, Any]]:
        """Busca un ítem en la tabla por su PK."""
        try:
            response = self.client.table(self.table_name).select('*').eq(self.primary_key, item_id).single().execute()
            return response.data
        except Exception:
            return None 

    def save(self, data: dict) -> Optional[Any]:
        """Insertar un nuevo registro y devolver el valor de la PK."""
        try:
            response = self.client.table(self.table_name).insert(data).select(self.primary_key).execute()

            if response.data:
                return response.data[0].get(self.primary_key)
            return None
        except Exception as e:
            print(f'Error al guardar datos en {self.table_name}: {e}')
            return None 
    
    def update_by_id(self, item_id: Any, data: dict) -> bool:
        """Actualiza un registro filtrando por su PK."""
        try:
            response = self.client.table(self.table_name).update(data).eq(self.primary_key, item_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error al actualizar PK {item_id} en {self.table_name}: {e}")
            return False
