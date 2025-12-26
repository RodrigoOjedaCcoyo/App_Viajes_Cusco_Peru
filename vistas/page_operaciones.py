# vistas/page_operaciones.py
import streamlit as st
import pandas as pd
from controllers.operacion_controller import OperacionController

operacion_controller = OperacionController()

def seguimiento_de_tours():
    """Sub-función para la funcionalidad 'Seguimiento de Tours'."""
    st.subheader("📋 Tours Pendientes de Operación")
    st.markdown("Lista de todas las ventas para planificar logística.")

    tours_pendientes = operacion_controller.obtener_tours_pendientes()

    if tours_pendientes:
        df_tours = pd.DataFrame(tours_pendientes)
        
        # Columnas importantes para Operaciones
        columnas_op = ['id', 'tour_paquete', 'fecha_tour', 'monto_total', 'estado_pago', 'vendedor']
        
        st.dataframe(
            df_tours[columnas_op], 
            use_container_width=True, 
            hide_index=True
        )
        st.markdown(f"**Total de Ventas / Tours Activos:** `{len(tours_pendientes)}`")
    else:
        st.info("No hay tours pendientes de operar. ¡Sistema limpio!")

def actualizacion_de_ventas():
    """Sub-función para la funcionalidad 'Actualización de Ventas' (Estado de Pago/Operación)."""
    st.subheader("🔄 Actualizar Estado de Venta/Tour")
    
    tours_pendientes = operacion_controller.obtener_tours_pendientes()
    
    if not tours_pendientes:
        st.warning("No hay ventas para actualizar.")
        return

    # Creamos opciones para el selector de Ventas
    opciones_ventas = [f"ID {v['id']} | {v['tour_paquete']} | Monto: ${v['monto_total']}" for v in tours_pendientes]
    
    with st.form("form_actualizar_venta"):
        venta_seleccionada_str = st.selectbox(
            "Seleccione la Venta a Actualizar",
            opciones_ventas
        )
        
        # Extraemos el ID
        venta_id = int(venta_seleccionada_str.split(' ')[1])
        
        # Campos de actualización (usando 'estado_pago' temporalmente como estado de operación)
        nuevo_estado = st.selectbox(
            "Nuevo Estado (Pago/Operación)",
            ["Pendiente", "Pagado (OK)", "Operado", "Cancelado/Reembolso"]
        )
        
        submitted = st.form_submit_button("Actualizar Estado")
        
        if submitted:
            exito, mensaje = operacion_controller.actualizar_estado_tour(venta_id, nuevo_estado)
            if exito:
                st.success(mensaje)
                st.rerun()
            else:
                st.error(mensaje)


# ----------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE LA VISTA (Llamada por main.py)
# ----------------------------------------------------------------------

def mostrar_pagina(funcionalidad_seleccionada: str):
    """Punto de entrada para el módulo de Operaciones."""
    st.title(f"Módulo de Operaciones / {funcionalidad_seleccionada}")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Seguimiento de Tours":
        seguimiento_de_tours()
    elif funcionalidad_seleccionada == "Actualización de Ventas":
        actualizacion_de_ventas()
    else:
        st.error("Funcionalidad de Operaciones no encontrada.")