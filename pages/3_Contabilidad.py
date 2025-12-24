# pages/3_Contabilidad.py

import streamlit as st
import pandas as pd
from controllers.venta_controller import VentaController

# Inicializar el controlador
venta_ctrl = VentaController()

def mostrar_pagina():
    """Contenido del Módulo Contable - VISTA"""
    st.title("💰 Módulo Contable: Cierre de Expedientes")
    
    st.header("Auditoría y Cierre Contable")
    st.info("Esta vista muestra las ventas listas para el cierre contable (Pago Final o Ejecución Logística completada).")

    # 1. Obtener los datos del controlador
    df_cierre = venta_ctrl.get_ventas_para_cierre()
    
    if df_cierre.empty:
        st.success("🎉 ¡No hay expedientes pendientes de cierre contable! Buen trabajo.")
        return

    st.subheader(f"Expedientes Pendientes de Auditoría ({df_cierre.shape[0]} casos)")
    
    # 2. Mostrar tabla interactiva
    df_display = df_cierre[['id_venta', 'cliente', 'estado_actual', 'ingreso_total', 'costo_registrado', 'pagos_registrados']]
    df_display['Margen Bruto'] = df_display['ingreso_total'] - df_display['costo_registrado']
    
    st.dataframe(df_display, use_container_width=True)

    # 3. Formulario para el cierre (Funcionalidad de acción)
    st.markdown("---")
    st.subheader("Acción de Cierre")
    
    # Se genera una lista de IDs para el selectbox
    id_a_cerrar = st.selectbox(
        "Seleccione el ID de la Venta a cerrar contablemente:",
        df_cierre['id_venta'].tolist()
    )
    
    if st.button(f"Cerrar Expediente ID {id_a_cerrar}"):
        # Llama al método del controlador para actualizar el estado a CERRADO CONTABLEMENTE
        venta_ctrl.cerrar_expediente(id_a_cerrar)
        st.experimental_rerun() # Recarga la página para reflejar el cambio


# Para que Streamlit ejecute esta función
if __name__ == '__main__':
    mostrar_pagina()