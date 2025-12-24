# controllers/venta_controller.py
from models.venta_model import Venta
import streamlit as st
import pandas as pd
import numpy as np # <--- IMPORTACIÓN DE NUMPY AÑADIDA

class VentaController:
    # 🟢 INICIO DE LA CLASE: TODO LO DEBE ESTAR INDENTADO (CON SANGRÍA)

    def __init__(self):
        self.model = Venta()
        self.ESTADOS = ['COTIZACIÓN', 'CONFIRMADO - PENDIENTE DATA', 'LISTO PARA OPERAR', 'EJECUTADO/PENDIENTE PAGO FINAL', 'CERRADO CONTABLEMENTE']

    # --- Lógica Módulo Comercial (Ventas) ---
    def registrar_venta_inicial(self, cliente_data, venta_data):
        """Registra la venta inicial, establece el estado inicial (CONFIRMADO - PENDIENTE DATA)."""
        venta_data['estado_venta'] = 'CONFIRMADO - PENDIENTE DATA'
        id_venta = self.model.insert_new(venta_data) 
        if id_venta:
            return f"Venta registrada. ID: {id_venta}. Esperando datos operativos."
        return "Error al registrar la venta."

    # --- Lógica Módulo Operativo ---
    def get_ventas_para_operacion(self):
        """Obtiene ventas que están listas para ser ejecutadas u operadas (VISTA)."""
        data = {
            'id_venta': [101, 102, 103, 104, 105],
            'cliente': ['Viajero A', 'Viajero B', 'Agencia C', 'Viajero D', 'Agencia E'],
            'estado_actual': ['CONFIRMADO - PENDIENTE DATA', 'LISTO PARA OPERAR', 'CONFIRMADO - PENDIENTE DATA', 'LISTO PARA OPERAR', 'CONFIRMADO - PENDIENTE DATA'],
            'fecha_viaje': ['2026-03-10', '2026-03-15', '2026-03-11', '2026-03-16', '2026-03-12'],
            'precio_cierre': [1500, 800, 3200, 950, 1800]
        }
        return pd.DataFrame(data)

    def completar_ejecucion(self, id_venta, nuevo_estado):
        """Actualiza la venta al estado 'LISTO PARA OPERAR' o 'EJECUTADO/PENDIENTE PAGO FINAL'."""
        if nuevo_estado in ['LISTO PARA OPERAR', 'EJECUTADO/PENDIENTE PAGO FINAL']:
            st.success(f"Venta ID {id_venta} actualizada exitosamente al estado: **{nuevo_estado}**.")
            return True
        st.error("Error: Estado no permitido para el rol Operaciones.")
        return False

    # 🟢 LÓGICA CORREGIDA: ESTOS MÉTODOS DEBEN ESTAR INDENTADOS DENTRO DE LA CLASE
    # --- Lógica Módulo Contable ---
    def get_ventas_para_cierre(self):
        """Obtiene ventas listas para la auditoría y cierre contable (VISTA)."""
        data = {
            'id_venta': [101, 102, 103, 104, 105, 106],
            'cliente': ['Viajero A', 'Viajero B', 'Agencia C', 'Viajero D', 'Agencia E', 'Cliente F'],
            'estado_actual': ['LISTO PARA OPERAR', 'EJECUTADO/PENDIENTE PAGO FINAL', 'LISTO PARA OPERAR', 'EJECUTADO/PENDIENTE PAGO FINAL', 'CONFIRMADO - PENDIENTE DATA', 'EJECUTADO/PENDIENTE PAGO FINAL'],
            'ingreso_total': [1500.00, 800.00, 3200.00, 950.00, 1800.00, 2500.00],
            'costo_registrado': [750.00, 400.00, 1600.00, 500.00, 900.00, 1250.00],
            'pagos_registrados': [1000.00, 800.00, 3000.00, 950.00, 1800.00, 2500.00]
        }
        df = pd.DataFrame(data)
        df_audit = df[df['estado_actual'].isin(['EJECUTADO/PENDIENTE PAGO FINAL', 'LISTO PARA OPERAR'])]
        return df_audit

    def cerrar_expediente(self, id_venta):
        """Finaliza el flujo de la venta al estado CERRADO CONTABLEMENTE."""
        nuevo_estado = 'CERRADO CONTABLEMENTE'
        st.success(f"Venta ID {id_venta} ha sido marcada como: **{nuevo_estado}**. Expediente cerrado para modificaciones.")
        return True

    # --- Lógica Módulo Gerencial ---
    def get_kpi_dashboard_data(self):
        """Obtiene todos los datos transaccionales para construir los KPIs."""
        data = {
            'id_venta': range(1, 101),
            'estado_venta': np.random.choice(['CONFIRMADO - PENDIENTE DATA', 'LISTO PARA OPERAR', 'CERRADO CONTABLEMENTE', 'EJECUTADO/PENDIENTE PAGO FINAL', 'COTIZACIÓN'], 100, p=[0.1, 0.2, 0.4, 0.1, 0.2]),
            'precio_total_cierre': np.random.randint(1000, 5000, 100),
            'costo_total_cierre': np.random.randint(500, 2500, 100),
            'canal_venta': np.random.choice(['WEB', 'AGENCIA', 'DIRECTO'], 100),
            'id_vendedor': np.random.randint(1, 6, 100) # 5 vendedores
        }
        df = pd.DataFrame(data)
        df['margen_bruto'] = df['precio_total_cierre'] - df['costo_total_cierre']
        return df

    # 🔴 FINAL DE LA CLASE: NO DEBE HABER MÁS CÓDIGO AQUÍ FUERA DE LA INDENTACIÓN