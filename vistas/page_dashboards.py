# vistas/page_dashboards.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta
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
    """Vista visual para Operaciones."""
    st.title("⚙️ Visión General de Operaciones")
    # Importar aquí para evitar circularidad si aplica
    from controllers.operaciones_controller import OperacionesController
    controller = OperacionesController(supabase_client)
    
    # KPIs Rápidos
    servicios_hoy = controller.get_servicios_por_fecha(date.today())
    len_hoy = len(servicios_hoy) if servicios_hoy else 0
    st.metric("Servicios para Hoy", len_hoy)
    
    # Gráfico de densidad (Timeline de este mes)
    from vistas.dashboard_analytics import render_operations_dashboard
    start_month = date.today().replace(day=1)
    end_month = (start_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    services_data = controller.get_servicios_rango_fechas(start_month, end_month)
    df_servicios = pd.DataFrame(services_data) if services_data else pd.DataFrame()
    render_operations_dashboard(df_servicios)

def render_contable_dashboard_visual(supabase_client):
    """Vista visual para Contabilidad."""
    st.title("🏦 Dashboard Financiero")
    reporte_ctrl = ReporteController(supabase_client)
    from vistas.dashboard_analytics import render_financial_dashboard
    
    df_ventas, df_reqs = reporte_ctrl.get_data_for_dashboard()
    render_financial_dashboard(df_ventas, df_reqs)
    
    st.divider()
    st.write("### 📋 Últimas Transacciones")
    if not df_ventas.empty:
        st.dataframe(df_ventas[['id', 'monto_total', 'estado_pago', 'vendedor']].head(10), use_container_width=True)

def render_exec_dashboard_visual(supabase_client):
    """Dashboard Ejecutivo para Gerencia."""
    st.title("🏛️ Reporte Ejecutivo 360")
    from controllers.gerencia_controller import GerenciaController
    controller = GerenciaController(supabase_client)
    
    # Resumen Multi-área
    c1, c2, c3 = st.columns(3)
    finan = controller.get_kpis_financieros()
    c1.metric("Ingresos Totales", f"S/ {finan['ventas_totales']:,.0f}")
    
    comer = controller.get_metricas_comerciales()
    c2.metric("Conversión Lead", f"{comer['tasa_conversion']:.1f}%")
    
    pax_tot = controller.get_pax_totales()
    c3.metric("Pax Operados", pax_tot)

    # Gráfico Mix
    st.divider()
    df_v_canal = controller.get_ventas_por_canal()
    if not df_v_canal.empty:
        import plotly.express as px
        fig = px.pie(df_v_canal, values='Monto', names='Canal', title="Ventas por Canal de Captación")
        st.plotly_chart(fig, use_container_width=True)

def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None):
    """Enrutador interno del archivo de dashboards."""
    if "Comercial" in funcionalidad_seleccionada:
        render_sales_dashboard_visual(supabase_client)
    elif "Operaciones" in funcionalidad_seleccionada:
        render_ops_dashboard_visual(supabase_client)
    elif "Contable" in funcionalidad_seleccionada:
        render_contable_dashboard_visual(supabase_client)
    elif "Ejecutivo" in funcionalidad_seleccionada:
        render_exec_dashboard_visual(supabase_client)
    else:
        st.write(f"Dashboard: {funcionalidad_seleccionada} en construcción.")
