import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_sales_dashboard(df_ventas):
    """Genera el Dashboard Comercial (Objetivos B2C - SOLES)."""
    st.subheader("🎯 Dashboard de Objetivos (B2C)")
    
    # --- META DE VENTAS ---
    if 'meta_ventas' not in st.session_state:
        st.session_state['meta_ventas'] = 10000.0  # Meta por defecto en Soles
        
    c_meta, c_info = st.columns([1, 2])
    with c_meta:
        meta_actual = st.number_input("Establecer Meta Mensual (S/)", min_value=1.0, value=st.session_state['meta_ventas'], step=1000.0)
        st.session_state['meta_ventas'] = meta_actual
        
    if df_ventas.empty:
        st.info("No hay datos de ventas B2C para mostrar el avance aún.")
        total_sales_pen = 0.0
    else:
        # Asumimos que la columna 'monto_total' ya viene convertida a Soles desde page_dashboards
        # o que la vista lo asegura. Por requerimiento: TODO ES SOLES.
        df_ventas['monto_total_pen'] = pd.to_numeric(df_ventas.get('monto_total_pen', df_ventas.get('monto_total', 0)))
        total_sales_pen = df_ventas['monto_total_pen'].sum()
        
    # Cálculos
    porcentaje = (total_sales_pen / meta_actual) * 100 if meta_actual > 0 else 0
    faltante = max(0, meta_actual - total_sales_pen)
    
    # --- MÉTRICAS ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Ventas Acumuladas (S/)", f"S/ {total_sales_pen:,.2f}")
    k2.metric("Meta Establecida (S/)", f"S/ {meta_actual:,.2f}")
    k3.metric("Faltante para Meta (S/)", f"S/ {faltante:,.2f}")
    
    # --- GRÁFICO TIPO GAUGE / VELOCÍMETRO ---
    st.markdown("### 🚀 Progreso de la Meta Ménsual")
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = total_sales_pen,
        number = {'prefix': "S/ ", 'valueformat': ",.2f"},
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Avance: {porcentaje:.1f}%"},
        delta = {'reference': meta_actual, 'position': "top", 'prefix': "Meta: S/ ", 'valueformat': ",.0f"},
        gauge = {
            'axis': {'range': [None, meta_actual], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#00C853" if porcentaje >= 100 else "#2196F3"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, meta_actual * 0.5], 'color': '#FFCDD2'},
                {'range': [meta_actual * 0.5, meta_actual * 0.8], 'color': '#FFF9C4'},
                {'range': [meta_actual * 0.8, meta_actual], 'color': '#DCEDC8'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': meta_actual}
        }
    ))
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # --- MENSAJE MOTIVACIONAL ---
    if not df_ventas.empty:
        st.markdown("---")
        if porcentaje >= 100:
            st.success("🎉 ¡Felicidades equipo! Hemos alcanzado la meta del mes. ¡Sigan así!")
            st.balloons()
        elif porcentaje >= 80:
            st.info("🔥 ¡Estamos muy cerca de la meta! ¡Un último esfuerzo!")
        elif porcentaje >= 50:
            st.warning("💪 ¡Ya pasamos la mitad de la meta! Sigamos empujando.")
        else:
            st.write("✨ ¡Cada venta cuenta! Vamos juntos por esa meta.")

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
    pax_total = df_servicios['cantidad'].sum() if 'cantidad' in df_servicios.columns else len(df_servicios)
    servicios_total = len(df_servicios)
    
    # Simulación de guías asignados (para la métrica)
    asignados = 0 # En un futuro se contaría desde la tabla asignación
    
    k1.metric("Pax en Ruta (Proyectados)", pax_total, delta="Personas")
    k2.metric("Servicios Totales", servicios_total, delta="Logística")
    k3.metric("Complejidad de Operación", f"{max(1, servicios_total//2)} Niv.", delta="Estimado")
    
    # Gráficos de Operación
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
