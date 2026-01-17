# models/catalogo_imagenes_model.py
from .base_model import BaseModel
from typing import Dict, Any, Optional, List
from supabase import Client

class CatalogoImagenesModel(BaseModel):
    """Modelo para vincular tours con sus URLs de imágenes oficiales."""

    def __init__(self, supabase_client: Client):
        # Sincronizado con esquema SQL: tabla 'catalogo_tours_imagenes', PK 'id_tour'
        super().__init__('catalogo_tours_imagenes', supabase_client, primary_key='id_tour')

    def get_imagenes_tour(self, id_tour: int) -> List[str]:
        """Retorna la lista de URLs de imágenes para un tour."""
        try:
            res = self.get_by_id(id_tour)
            if res and 'urls_imagenes' in res:
                return res['urls_imagenes']
            return []
        except Exception as e:
            print(f"Error cargando imágenes del tour {id_tour}: {e}")
            return []
            
    def actualizar_imagenes_tour(self, id_tour: int, urls: List[str]) -> bool:
        """Actualiza o inserta las imágenes de un tour."""
        try:
            data = {"id_tour": id_tour, "urls_imagenes": urls}
            # Usamos upsert de Supabase via client directamente para mayor facilidad con id_tour como PK
            res = self.client.table(self.table_name).upsert(data).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"Error actualizando catálogo de imágenes: {e}")
            return False
