# models/base_model.py
import streamlit as st # <--- CRÍTICO: Necesario para st.cache_resource y para que los modelos usen st.warning
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client

class BaseModel:
    """Clase base para todos los modelos, maneja la conexión a Supabase."""

    @st.cache_resource
    def _init_supabase_client(self):
        """Inicializa el cliente de Supabase usando el caché de Streamlit."""
        try:
            # Si no hay credenciales reales, forzamos el modo simulación
            if not SUPABASE_URL or SUPABASE_URL == "TU_URL_DE_SUPABASE":
                st.info("MODO SIMULACIÓN: Credenciales de Supabase no configuradas. Usando datos ficticios.")
                return None
            
            # Intenta crear la conexión
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            # En caso de fallo de conexión (ej. firewall, URL incorrecta)
            st.info(f"MODO SIMULACIÓN: Error al conectar a Supabase ({e}). Usando datos ficticios.") 
            return None

    def __init__(self):
        # Inicializa el cliente Supabase (si es posible) y lo guarda en self.supabase
        self.supabase = self._init_supabase_client()
        self.table_name = None # Se define en la clase heredada (ej. 'Venta')

    def select_all(self):
        # Función base para seleccionar todos (simulación)
        st.error("Método select_all no implementado para simulación. Implementar la consulta a Supabase aquí.")
        return None

# Fin de la clase BaseModel