# models/venta_model.py
import streamlit as st
from models.base_model import BaseModel

class Venta(BaseModel):
    """Representa la entidad Venta, heredando la funcionalidad simulada."""
    
    def __init__(self):
        super().__init__()
        self.table_name = 'Venta'

    def insert_new(self, data):
        """Simula la inserción de una nueva venta."""
        st.warning(f"Simulación: Insertando nueva Venta. ID de ejemplo: 101...")
        # Simplemente retorna un ID para que el controlador pueda continuar
        return 101 
        
    def update_estado(self, id_venta, nuevo_estado, user_id):
        """Simula la actualización del estado."""
        st.warning(f"Simulación: Actualizando Venta {id_venta} al estado '{nuevo_estado}'...")
        return True