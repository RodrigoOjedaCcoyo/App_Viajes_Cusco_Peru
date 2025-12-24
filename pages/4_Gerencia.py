# pages/4_Gerencia.py

import streamlit as st
import pandas as pd
import numpy as np
from controllers.venta_controller import VentaController

# Inicializar el controlador (Capa de negocio)
# La instancia se crea fuera de la función para usar el caché de Streamlit
venta_ctrl = VentaController()

def mostrar_pagina():
    """Contenido del Módulo Gerencial (Dashboards) - VISTA"""
    st.title("📊 Módulo Gerencial: Dashboards de KPIs")
    
    st.header("Análisis Estratégico del Sistema SGVO")
    st.info("Esta vista consolida datos de Ventas, Operaciones y Contabilidad para la toma de decisiones. (Vista de solo lectura).")

    # 1. Obtener los datos del controlador
    df_ventas = venta_ctrl.get_kpi_dashboard_data()
    
    if df_ventas.empty:
        st.warning("No hay datos para generar los KPIs.")
        return

    # --- KPI 1: MADUREZ OPERATIVA (Seguimiento al Flujo Condicional) ---
    st.header("1. Madurez Operativa: Estado del Flujo")
    
    df_estados = df_ventas.groupby('estado_venta').size().reset_index(name='Total')
    df_estados['Porcentaje'] = (df_estados['Total'] / df_ventas.shape[0]) * 100
    
    col1, col2, col3 = st.columns(3)
    
    total_ventas = df_ventas.shape[0]
    total_cerradas = df_estados[df_estados['estado_venta'] == 'CERRADO CONTABLEMENTE']['Total'].sum()
    
    col1.metric("Ventas Totales Registradas", total_ventas)
    col2.metric("Ventas Cerradas Contablemente", total_cerradas)
    
    # KPI: Porcentaje de Madurez Operativa (Cerradas / Totales)
    pct_madurez = (total_cerradas / total_ventas) * 100 if total_ventas > 0 else 0
    col3.metric("KPI Madurez Operativa", f"{pct_madurez:.1f}%")

    st.subheader("Distribución por Estado de Venta")
    st.bar_chart(df_estados.set_index('estado_venta')['Total'])

    # --- KPI 2: RENTABILIDAD (Margen de Contribución por Canal) ---
    st.header("2. Rentabilidad y Margen Bruto")
    
    total_margen = df_ventas['margen_bruto'].sum()
    total_ingreso = df_ventas['precio_total_cierre'].sum()
    
    col4, col5 = st.columns(2)
    col4.metric("Margen Bruto Total", f"${total_margen:,.0f}")
    col5.metric("Ingreso Total (Precio de Cierre)", f"${total_ingreso:,.0f}")
    
    df_margen_canal = df_ventas.groupby('canal_venta')['margen_bruto'].sum().sort_values(ascending=False)
    st.subheader("Margen por Canal de Venta")
    
    st.bar_chart(df_margen_canal)

    # --- KPI 3: DESEMPEÑO COMERCIAL ---
    st.header("3. Desempeño Comercial")
    
    # Venta y Margen por Vendedor
    df_desempeno = df_ventas.groupby('id_vendedor').agg(
        Venta_Total=('precio_total_cierre', 'sum'),
        Margen_Total=('margen_bruto', 'sum'),
        Total_Ventas=('id_venta', 'count')
    ).reset_index()
    
    df_desempeno['Margen_Promedio'] = df_desempeno['Margen_Total'] / df_desempeno['Total_Ventas']
    
    st.subheader("Ranking de Vendedores (Por Venta Total)")
    st.dataframe(df_desempeno.sort_values(by='Venta_Total', ascending=False), use_container_width=True)


# CRÍTICO: Este bloque asegura que la función se ejecute al cargar la página.
if __name__ == '__main__':
    mostrar_pagina()