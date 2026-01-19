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
    
    kpi1.metric("Ventas Totales (USD)", f"${float(total_sales or 0):,.2f}")
    kpi2.metric("Ticket Promedio", f"${float(avg_ticket or 0):,.2f}")
    kpi3.metric("Cantidad Ventas", int(count_sales or 0))
    
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
    """Genera el Dashboard Operativo Profesional."""
    if df_servicios.empty:
        st.info("No hay servicios operativos registrados para el periodo.")
        return

    # Mapeo defensivo interno para visualización
    fallbacks_fecha = ['fecha_servicio', 'Fecha', 'fecha']
    for fb in fallbacks_fecha:
        if fb in df_servicios.columns:
            if fb != 'fecha_servicio':
                df_servicios.rename(columns={fb: 'fecha_servicio'}, inplace=True)
            break

    # Convertir fecha si es necesario
    if 'fecha_servicio' in df_servicios.columns:
        df_servicios['fecha_servicio'] = pd.to_datetime(df_servicios['fecha_servicio'])

    # KPIs Logísticos
    k1, k2, k3 = st.columns(3)
    pax_total = df_servicios['cantidad_pasajeros'].sum() if 'cantidad_pasajeros' in df_servicios.columns else len(df_servicios)
    servicios_total = len(df_servicios)
    
    # Simulación de guías asignados (para la métrica)
    asignados = 0 # En un futuro se contaría desde la tabla asignación
    
    k1.metric("Pax en Ruta (Proyectados)", pax_total, delta="Personas")
    k2.metric("Servicios Totales", servicios_total, delta="Logística")
    k3.metric("Complejidad de Operación", f"{max(1, servicios_total//2)} Niv.", delta="Estimado")
    
    # Gráficos de Operación
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**📉 Volumen de Pasajeros por Fecha**")
        if 'fecha_servicio' in df_servicios.columns:
            ops_by_date = df_servicios.groupby('fecha_servicio').size().reset_index(name='servicios')
            fig_timeline = px.area(ops_by_date, x='fecha_servicio', y='servicios', 
                                   markers=True, title="Carga de Trabajo Diaria",
                                   color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.warning("⚠️ No se puede mostrar la línea de tiempo: falta columna 'fecha_servicio'")
            if not df_servicios.empty:
                st.write("Columnas disponibles:", df_servicios.columns.tolist())
        
    with c2:
        st.markdown("**📊 Mix de Servicios (Tours)**")
        # Priorizar observaciones o catálogo
        col_servicio = 'observaciones' if 'observaciones' in df_servicios.columns else 'id_tour'
        if col_servicio in df_servicios.columns:
            tour_counts = df_servicios[col_servicio].value_counts().reset_index()
            tour_counts.columns = ['Tour', 'Frecuencia']
            fig_pie = px.pie(tour_counts.head(5), values='Frecuencia', names='Tour', 
                             title="Top 5 Tours Programados",
                             hole=.4)
            st.plotly_chart(fig_pie, use_container_width=True)

def render_financial_dashboard(df_ventas, df_gastos_op=None):
    """Genera el Dashboard Financiero (Liquidación)."""
    st.subheader("Resultados Financieros")
    
    total_ingresos = df_ventas['monto_total'].sum() if not df_ventas.empty else 0
    total_gastos = df_gastos_op['total'].sum() if df_gastos_op is not None and not df_gastos_op.empty else 0
    
    utilidad = total_ingresos - total_gastos
    margen = (utilidad / total_ingresos * 100) if total_ingresos > 0 else 0
    
    # Scorecard
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Total Ingresos (Ventas)", f"${float(total_ingresos or 0):,.2f}", delta="Proyección")
    sc2.metric("Total Gastos Ops (Estimado)", f"${float(total_gastos or 0):,.2f}", delta_color="inverse")
    sc3.metric("Utilidad Operativa", f"${float(utilidad or 0):,.2f}", delta=f"{float(margen or 0):.1f}%")
    
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
