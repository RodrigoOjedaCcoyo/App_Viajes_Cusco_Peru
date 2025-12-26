# vistas/page_ventas.py

import streamlit as st
import pandas as pd
# Importar el controlador
from controllers.venta_controller import VentaController

# Inicializar el controlador (se hace una sola vez)
venta_controller = VentaController()

def registrar_venta_ui(datos_formulario):
    """
    Función que maneja el registro de venta cuando se presiona el botón.
    Recibe los datos del formulario (simulados por ahora).
    """
    try:
        # En el futuro, aquí se manejaría la subida de archivos (el payload del Apps Script)
        archivos_simulados = [] 
        
        # 1. Llamar al controlador con los datos y archivos
        resultado = venta_controller.registrar_nueva_venta(datos_formulario, archivos_simulados)
        
        # 2. Mostrar el resultado de la simulación
        if resultado.get("status") == "success":
            st.success(f"✅ Venta registrada correctamente (Simulación de BD: ID {resultado.get('venta_id')})")
            # Aquí se limpiaría el formulario en una aplicación real
        else:
            st.error("Error al registrar la venta.")
            
    except Exception as e:
        st.error(f"Error interno en el registro: {e}")


def mostrar_pagina():
    """Función principal que dibuja la página de Ventas."""
    st.title("Módulo de Ventas 💸")
    
    # ----------------------------------------------------
    # Aquí debe ir su formulario de ventas (como el Formulario.html)
    # ----------------------------------------------------
    
    # SIMULACIÓN DE FORMULARIO DE REGISTRO
    with st.form(key="form_registro_venta"):
        st.header("Registrar Nueva Venta")
        
        # Campos de ejemplo
        nombre = st.text_input("Nombre del Cliente", key="venta_nombre")
        tour = st.selectbox("Tour", options=["Machu Picchu", "Cusco", "Lima"], key="venta_tour")
        monto_total = st.number_input("Monto Total ($)", min_value=0.0, step=0.01, key="venta_monto_total")
        
        # Botón de registro
        submit_button = st.form_submit_button("Registrar Venta")
        
        if submit_button:
            # 3. Recolectar datos y llamar a la función de registro
            datos = {
                'nombre': nombre, 
                'tour': tour, 
                'monto_total': monto_total,
                # ... añadir más campos aquí ...
            }
            registrar_venta_ui(datos)

# NOTA: Asegúrese que al final del archivo exista la llamada al controlador:
if __name__ == "__main__":
    mostrar_pagina()