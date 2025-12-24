# models/base_model.py
import streamlit as st
# from supabase import create_client, Client # 🛑 Estas líneas se activarán más tarde

class BaseModel:
    """
    Clase base para todos los modelos de datos (Venta, Operaciones, etc.).
    Actualmente simula la conexión a la base de datos (Supabase).
    """
    
    def __init__(self):
        # En el futuro, aquí se leerán las claves de Supabase y se creará el cliente.
        self.db = "Simulación de Conexión a Supabase"
        self.table_name = None # Se define en cada modelo hijo

    def get_all(self):
        """Simula la obtención de todos los registros."""
        st.info(f"Simulación: Obteniendo todos los datos de la tabla {self.table_name}")
        # En el futuro:
        # return self.db.from_(self.table_name).select('*').execute()
        return []

    def get_by_id(self, id_registro):
        """Simula la obtención de un registro por ID."""
        st.info(f"Simulación: Obteniendo {self.table_name} con ID {id_registro}")
        return None