# vistas/page_gerencia.py
import streamlit as st
import pandas as pd
from controllers.reporte_controller import ReporteController
import plotly.express as px

from models.lead_model import LeadModel # Para métricas de Leads

# Inicializar controladores y modelos
reporte_controller = ReporteController()
lead_model = LeadModel()

def dashboard_ejecutivo():
    """Sub-función para la funcionalidad 'Dashboard Ejecutivo'."""
    st.subheader("📊 Resumen de Indicadores Clave (KPIs)")
    
    # --- 1. Obtener Datos ---
    resumen_ventas = reporte_controller.obtener_resumen_ventas()
    todas_las_ventas = resumen_ventas['detalle_ventas']
    todos_los_leads = lead_model.get_all()
    
    # --- 2. Cálculos Ejecutivos ---
    total_leads = len(todos_los_leads)
    leads_convertidos = sum(1 for lead in todos_los_leads if 'Convertido' in lead['estado'])
    total_ventas = resumen_ventas['total_ventas_registradas']
    
    # Tasa de Conversión (simple)
    tasa_conversion = (leads_convertidos / total_leads * 100) if total_leads > 0 else 0
    
    monto_total_usd = resumen_ventas['monto_total_acumulado']
    
    # --- 3. Presentación de Métricas (KPIs) ---
    st.markdown("### Metas y Conversión")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Total Ingresos (USD)", f"${monto_total_usd:,.2f}")
    col2.metric("Leads Registrados", total_leads)
    col3.metric("Tasa de Conversión", f"{tasa_conversion:.1f}%")

    st.markdown("---")

    # --- 4. Gráfico de Tendencia (Simulado) ---
    st.write("### Ventas por Vendedor (Impacto)")
    
    if todas_las_ventas:
        df_ventas = pd.DataFrame(todas_las_ventas)
        
        # Agrupamos los datos por vendedor y calculamos el monto total
        df_vendedor = df_ventas.groupby('vendedor').agg(
            monto_vendido=('monto_total', 'sum'),
            conteo_ventas=('id', 'count')
        ).reset_index()

        # Gráfico simple de barras de Streamlit
        st.bar_chart(df_vendedor, x='vendedor', y='monto_vendido')
        
    else:
        st.info("No hay datos de ventas para mostrar en el dashboard.")

def auditoria_completa():
    """Sub-función para la funcionalidad 'Auditoría Completa'."""
    st.subheader("🔒 Acceso a Registros Maestros")
    st.warning("Esta sección es para el control de la información y la revisión exhaustiva de todos los movimientos.")
    
    # --- 1. Auditoría de Ventas ---
    st.markdown("#### Detalle Completo de Ventas")
    todas_las_ventas = reporte_controller.obtener_detalle_auditoria()
    if todas_las_ventas:
        df_ventas = pd.DataFrame(todas_las_ventas)
        st.dataframe(df_ventas, use_container_width=True, hide_index=True)
    else:
        st.info("No hay ventas registradas.")
        
    st.markdown("---")

    # --- 2. Auditoría de Leads ---
    st.markdown("#### Detalle Completo de Leads")
    todos_los_leads = lead_model.get_all()
    if todos_los_leads:
        df_leads = pd.DataFrame(todos_los_leads)
        st.dataframe(df_leads, use_container_width=True, hide_index=True)
    else:
        st.info("No hay leads registrados.")


# ----------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE LA VISTA (Llamada por main.py)
# ----------------------------------------------------------------------

def mostrar_pagina(funcionalidad_seleccionada: str):
    """Punto de entrada para el módulo de Gerencia."""
    st.title(f"Módulo de Gerencia / {funcionalidad_seleccionada}")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Dashboard Ejecutivo":
        dashboard_ejecutivo()
    elif funcionalidad_seleccionada == "Auditoría Completa":
        auditoria_completa()
    else:
        st.error("Funcionalidad de Gerencia no encontrada.")