# models/meta_mensual_model.py
from models.base_model import BaseModel
from supabase import Client as SupabaseClient
from typing import Optional, Dict, Any

class MetaMensualModel(BaseModel):
    """Modelo para gestionar las metas de ventas B2C mensuales en Supabase."""
    
    def __init__(self, supabase_client: SupabaseClient):
        super().__init__(table_name='meta_mensual', supabase_client=supabase_client, primary_key='id_meta')

    def obtener_meta_por_periodo(self, periodo: str) -> Optional[Dict[str, Any]]:
        """Busca una meta mensual por su periodo (Formato AAAA-MM)."""
        try:
            res = self.client.table(self.table_name).select('*').eq('periodo', periodo).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            print(f"Error al obtener meta para el periodo {periodo}: {e}")
            return None

    def registrar_meta(self, periodo: str, monto: float) -> bool:
        """Registra una nueva meta mensual para un periodo."""
        try:
            data = {
                "periodo": periodo,
                "monto_meta": monto
            }
            # Usar upsert para evitar errores de duplicidad si ya existe
            res = self.client.table(self.table_name).upsert(data, on_conflict='periodo').execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"Error al registrar meta para el periodo {periodo}: {e}")
            return False
