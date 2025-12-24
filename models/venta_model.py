# models/base_model.py
import streamlit as st # <--- ¡CRÍTICO! DEBE ESTAR AQUÍ
# importación de credenciales (debería estar importando config)
from config import SUPABASE_URL, SUPABASE_KEY
# importación de la librería Supabase
from supabase import create_client, Client

class BaseModel:
    """Clase base para todos los modelos, maneja la conexión a Supabase."""

    @st.cache_resource
    def _init_supabase_client(self):
        """Inicializa el cliente de Supabase usando el caché de Streamlit."""
        # Se asume que usted tiene sus claves reales en config.py
        try:
            if not SUPABASE_URL or SUPABASE_URL == "TU_URL_DE_SUPABASE":
                st.info("MODO SIMULACIÓN: Credenciales de Supabase no configuradas. Usando datos ficticios.")
                return None
            
            # Intenta crear la conexión
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            # st.error(f"Error de conexión a Supabase: {e}") 
            st.info("MODO SIMULACIÓN: Error al conectar a Supabase. Usando datos ficticios.") 
            return None

    def __init__(self):
        self.supabase = self._init_supabase_client()
        # Asegúrese de que no haya ninguna línea que use 'st.' aquí