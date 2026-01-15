import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_sales_dashboard(df_ventas):
    """Genera el Dashboard Comercial."""
    if df_ventas.empty:
        st.info("No hay datos suficientes para mostrar el Dashboard Comercial.")
        return

    # Convertir fecha
    df_ventas['fecha_venta'] = pd.to_datetime(df_ventas['fecha_venta'])
    
    # KPIs Top
    kpi1, kpi2, kpi3 = st.columns(3)
    total_sales = df_ventas['monto_total'].sum()
    avg_ticket = df_ventas['monto_total'].mean()
    count_sales = len(df_ventas)
    
    kpi1.metric("Ventas Totales (USD)", f"${total_sales:,.2f}")
    kpi2.metric("Ticket Promedio", f"${avg_ticket:,.2f}")
    kpi3.metric("Cantidad Ventas", count_sales)
    
    # Gráficos
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Ventas por Vendedor")
        sales_by_vendor = df_ventas.groupby('vendedor')['monto_total'].sum().reset_index()
        fig_vendor = px.bar(sales_by_vendor, x='vendedor', y='monto_total', text_auto='.2s', title="Ranking Vendedores")
        st.plotly_chart(fig_vendor, use_container_width=True)
        
    with c2:
        st.subheader("Ventas por Paquete/Tour")
        # Asumiendo que la columna es 'tour' o 'id_paquete'
        col_tour = 'tour' if 'tour' in df_ventas.columns else 'id_paquete'
        if col_tour in df_ventas.columns:
            sales_by_tour = df_ventas.groupby(col_tour)['monto_total'].sum().reset_index()
            fig_tour = px.pie(sales_by_tour, values='monto_total', names=col_tour, title="Distribución por Producto")
            st.plotly_chart(fig_tour, use_container_width=True)

def render_operations_dashboard(df_servicios):
    """Genera el Dashboard Operativo."""
    if df_servicios.empty:
        st.info("No hay servicios operativos registrados.")
        return

    # KPIs
    k1, k2 = st.columns(2)
    pax_total = df_servicios['cantidad_pasajeros'].sum() if 'cantidad_pasajeros' in df_servicios.columns else 0
    servicios_p = len(df_servicios)
    
    k1.metric("Total Pasajeros (Proyección)", pax_total)
    k2.metric("Total Servicios Logísticos", servicios_p)
    
    # Timeline
    st.subheader("Densidad Operativa (Timeline)")
    if 'fecha_servicio' in df_servicios.columns:
        df_servicios['fecha_servicio'] = pd.to_datetime(df_servicios['fecha_servicio'])
        ops_by_date = df_servicios.groupby('fecha_servicio').size().reset_index(name='servicios')
        fig_timeline = px.line(ops_by_date, x='fecha_servicio', y='servicios', markers=True, title="Servicios por Día")
        st.plotly_chart(fig_timeline, use_container_width=True)

def render_financial_dashboard(df_ventas, df_gastos_op=None):
    """Genera el Dashboard Financiero (Liquidación)."""
    st.subheader("Resultados Financieros")
    
    total_ingresos = df_ventas['monto_total'].sum() if not df_ventas.empty else 0
    total_gastos = df_gastos_op['total'].sum() if df_gastos_op is not None and not df_gastos_op.empty else 0
    
    utilidad = total_ingresos - total_gastos
    margen = (utilidad / total_ingresos * 100) if total_ingresos > 0 else 0
    
    # Scorecard
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Total Ingresos (Ventas)", f"${total_ingresos:,.2f}", delta="Proyección")
    sc2.metric("Total Gastos Ops (Estimado)", f"${total_gastos:,.2f}", delta_color="inverse")
    sc3.metric("Utilidad Operativa", f"${utilidad:,.2f}", delta=f"{margen:.1f}%")
    
    # Waterfall Chart (Simplificado)
    fig_wf = go.Figure(go.Waterfall(
        name = "Flujo", orientation = "v",
        measure = ["relative", "relative", "total"],
        x = ["Ventas", "Costos Operativos", "Utilidad"],
        textposition = "outside",
        text = [f"${total_ingresos/1000:.1f}k", f"-${total_gastos/1000:.1f}k", f"${utilidad/1000:.1f}k"],
        y = [total_ingresos, -total_gastos, utilidad],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_wf.update_layout(title = "Cascada de Rentabilidad")
    st.plotly_chart(fig_wf, use_container_width=True)
