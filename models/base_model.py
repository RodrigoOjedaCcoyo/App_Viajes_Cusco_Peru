# controllers/venta_controller.py
# 🛑 IMPORTACIÓN CRÍTICA: La ruta ABSOLUTA es más confiable en Streamlit Cloud
from models.venta_model import Venta 
import streamlit as st
import pandas as pd
import numpy as np 

class VentaController:
    def __init__(self):
        # Inicializa el modelo de venta simplificado
        self.model = Venta()
        self.ESTADOS = ['COTIZACIÓN', 'CONFIRMADO - PENDIENTE DATA', 'LISTO PARA OPERAR', 'EJECUTADO/PENDIENTE PAGO FINAL', 'CERRADO CONTABLEMENTE']

    # --- SIMULACIÓN DE DATOS (Gerencia) ---
    def get_kpi_dashboard_data(self):
        data = {
            'id_venta': range(1, 101),
            'estado_venta': np.random.choice(self.ESTADOS, 100, p=[0.1, 0.2, 0.4, 0.1, 0.2]),
            'precio_total_cierre': np.random.randint(1000, 5000, 100),
            'margen_bruto': np.random.randint(500, 2500, 100),
            'canal_venta': np.random.choice(['WEB', 'AGENCIA', 'DIRECTO'], 100),
        }
        return pd.DataFrame(data)

    # --- SIMULACIÓN DE ACCIONES ---
    def cerrar_expediente(self, id_venta):
        # Simula la llamada al modelo para actualizar el estado
        return self.model.update_estado(id_venta, 'CERRADO CONTABLEMENTE', 'user_id_placeholder')