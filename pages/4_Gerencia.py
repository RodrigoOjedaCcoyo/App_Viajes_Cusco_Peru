# pages/4_Gerencia.py
import streamlit as st
import pandas as pd
from controllers.venta_controller import VentaController 

# Inicializar el controlador 
@st.cache_resource
def get_controller():
    return VentaController()

venta_ctrl = get_controller()

def mostrar_pagina():
    st.title("📊 Dashboard Gerencial: Indicadores Clave")
    st.markdown("---")
    
    df = venta_ctrl.get_kpi_dashboard_data()
    
    if df.empty:
        st.warning("No hay datos simulados disponibles para el dashboard.")
        return

    st.subheader("Resumen de Margen y Ventas")
    col1, col2, col3 = st.columns(3)
    
    total_ventas = df.shape[0]
    ingreso_total = df['precio_total_cierre'].sum()
    margen_bruto = df['margen_bruto'].sum()
    
    col1.metric("Total de Ventas (Simulación)", f"{total_ventas}")
    col2.metric("Ingreso Total (Simulación)", f"S/ {ingreso_total:,.2f}")
    col3.metric("Margen Bruto Total", f"S/ {margen_bruto:,.2f}")

    st.markdown("---")
    
    st.subheader("Distribución de Ventas por Estado")
    df_estados = df['estado_venta'].value_counts().reset_index()
    df_estados.columns = ['Estado', 'Conteo']
    st.bar_chart(df_estados, x='Estado', y='Conteo')
    
    st.markdown("---")
    st.subheader("Datos Simulado Detallado")
    st.dataframe(df, use_container_width=True)