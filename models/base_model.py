# models/base_model.py

import streamlit as st
import pandas as pd

class BaseModel:
    """Clase base para manejar la conexión a Supabase (simulada con st.session_state)."""
    
    # CORRECCIÓN CLAVE: DEBE ACEPTAR EL PARÁMETRO 'key: str'
    def __init__(self, key: str):
        self.key = key 
        if self.key not in st.session_state:
            st.session_state[self.key] = [] 
            st.session_state[f"{self.key}_next_id"] = 1 

    def get_all(self):
        return st.session_state[self.key]

    def save(self, data: dict):
        new_id = st.session_state[f"{self.key}_next_id"]
        data['id'] = new_id
        
        if self.key == "ventas" and 'estado_pago' not in data: 
            data['estado_pago'] = "Pendiente" 
            
        st.session_state[self.key].append(data)
        st.session_state[f"{self.key}_next_id"] += 1
        return new_id 
    
    # Método añadido para facilitar la actualización en el controlador (como LeadController)
    def update_by_id(self, item_id: int, data: dict):
        for item in st.session_state[self.key]:
            if item['id'] == item_id:
                item.update(data)
                return True
        return False