# vistas/page_dashboards.py

import streamlit as st
import pandas as pd
from datetime import date
from controllers.reporte_controller import ReporteController
from controllers.lead_controller import LeadController
from controllers.venta_controller import VentaController

def render_sales_dashboard_visual(supabase_client):
    """Vista puramente visual para el Dashboard Comercial."""
    st.title("📊 Dashboard Comercial")
    
    # KPIs Estáticos
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas Mes", "$2,450", delta="+15%")
    c2.metric("Leads en Proceso", "42", delta="5")
    c3.metric("Conversión", "12%", delta="-2%")
    
    st.divider()
    
    # Integrar lo que antes estaba en page_ventas pero solo visual
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write("📈 **Ranking de Ventas por Vendedor**")
        reporte_ctrl = ReporteController(supabase_client)
        df_ventas, _ = reporte_ctrl.get_data_for_dashboard()
        if not df_ventas.empty:
            sales_by_vendor = df_ventas.groupby('vendedor')['monto_total'].sum().reset_index()
            import plotly.express as px
            fig = px.bar(sales_by_vendor, x='vendedor', y='monto_total', color='monto_total', 
                         color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ventas disponibles.")

    with col_b:
        st.write("🔔 **Agenda Próxima**")
        lead_ctrl = LeadController(supabase_client)
        leads = lead_ctrl.obtener_todos_leads()
        if leads:
            df = pd.DataFrame(leads)
            if 'red_social' in df.columns and 'fecha_seguimiento' in df.columns:
                df_rec = df[df['red_social'].str.contains("REC:", na=False)].copy()
                df_rec['fecha_seguimiento'] = pd.to_datetime(df_rec['fecha_seguimiento']).dt.date
                df_rec = df_rec.sort_values(by='fecha_seguimiento', ascending=True)
                st.dataframe(df_rec[['fecha_seguimiento', 'numero_celular']].head(5), 
                             use_container_width=True, hide_index=True)
            else:
                st.info("No hay recordatorios.")

def render_ops_dashboard_visual(supabase_client):
    """Vista puramente visual para Operaciones."""
    st.title("⚙️ Visión General de Operaciones")
    st.info("Aquí se mostrará el movimiento logístico sin la capacidad de editar servicios.")
    # Implementación futura del dashboard operativo premium
    st.warning("Estructura base del Dashboard Operativo preparada.")

def render_exec_dashboard_visual(supabase_client):
    """Dashboard Ejecutivo para Gerencia."""
    st.title("🏛️ Reporte Ejecutivo")
    st.markdown("---")
    # Llamar a renders de analytics si existen
    from vistas.dashboard_analytics import render_financial_dashboard
    # Placeholder de data
    df_empty = pd.DataFrame()
    render_financial_dashboard(df_empty)

def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None):
    """Enrutador interno del archivo de dashboards."""
    if "Comercial" in funcionalidad_seleccionada:
        render_sales_dashboard_visual(supabase_client)
    elif "Operaciones" in funcionalidad_seleccionada:
        render_ops_dashboard_visual(supabase_client)
    elif "Ejecutivo" in funcionalidad_seleccionada:
        render_exec_dashboard_visual(supabase_client)
    else:
        st.write(f"Dashboard: {funcionalidad_seleccionada} en construcción.")
