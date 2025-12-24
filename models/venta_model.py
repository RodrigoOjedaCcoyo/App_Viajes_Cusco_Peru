# models/venta_model.py
import streamlit as st
from .base_model import BaseModel # 🛑 Importación relativa desde el mismo paquete

class Venta(BaseModel):
    """Representa la entidad Venta, sin lógica de BD real."""
    
    def __init__(self):
        super().__init__()
        self.table_name = 'Venta' # Nombre de la tabla simulada

    def insert_new(self, data):
        """Simula la inserción, retornando un ID falso."""
        st.warning("Simulación: Venta insertada.")
        return 101 # ID de ejemplo
        
    def update_estado(self, id_venta, nuevo_estado, user_id):
        """Simula la actualización del estado."""
        st.warning(f"Simulación: Venta {id_venta} actualizada a '{nuevo_estado}'.")
        return True