# vistas/page_gerencia.py
import streamlit as st
import pandas as pd
import plotly.express as px
from controllers.gerencia_controller import GerenciaController
from datetime import date

def dashboard_ejecutivo(controller):
    """Interfaz del Dashboard Principal de Gerencia."""
    st.subheader("📊 Panel de Control Ejecutivo", divider='rainbow')

    # --- 1. OBTENER DATOS ---
    with st.spinner("Calculando métricas..."):
        finan = controller.get_kpis_financieros()
        comer = controller.get_metricas_comerciales()
        pax_tot = controller.get_pax_totales()
        alertas = controller.get_alertas_gestion()
        ventas_mes = controller.get_ventas_mensuales()

    # --- 2. KPIs FINANCIEROS (Fila 1) ---
    st.markdown("#### 💰 Resumen Financiero")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Ventas Totales", f"S/ {finan['ventas_totales']:,.0f}", delta="Cifra Bruta")
    col2.metric("Recaudado Real", f"S/ {finan['total_recaudado']:,.0f}", delta="En Banco", delta_color="normal")
    col3.metric("Saldo Pendiente", f"S/ {finan['total_pendiente']:,.0f}", delta="- Deuda Clientes", delta_color="inverse")

    st.markdown("---")

    # --- 3. KPIs COMERCIALES (Fila 2) ---
    st.markdown("#### 📈 Rendimiento Comercial y Operativo")
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("Leads Totales", comer['total_leads'], help="Personas que consultaron")
    c2.metric("Ratio Conversión", f"{comer['tasa_conversion']:.1f}%", help="Leads que se volvieron Venta")
    c3.metric("Ventas Cerradas", comer['total_convertidos'], delta="Confirmados")
    c4.metric("Pasajeros Totales", pax_tot, help="Total PAX en sistema", delta="Operación")

    st.markdown("---")

    # --- 4. GRÁFICAS (Fila 3) ---
    g1, g2 = st.columns([2, 1])

    with g1:
        st.markdown("##### Ventas por Mes")
        if not ventas_mes.empty:
            fig_bar = px.bar(
                ventas_mes, x="Mes", y="Ventas",
                color_discrete_sequence=["#1E88E5"],
                text_auto='.2s'
            )
            fig_bar.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin histórico de ventas.")

    with g2:
        st.markdown("##### Canales de Venta")
        dist = comer['distribucion_medios']
        if dist:
            df_dist = pd.DataFrame(list(dist.items()), columns=['Canal', 'Cantidad'])
            fig_pie = px.pie(
                df_dist, values='Cantidad', names='Canal',
                hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos de origen.")

    st.markdown("---")

    # --- 5. ALERTAS CRÍTICAS ---
    st.markdown("#### ⚠️ Alertas de Gestión Operativa")
    if alertas:
        st.error(f"Hay {len(alertas)} documentos críticos PENDIENTES que podrían bloquear operaciones.")
        df_al = pd.DataFrame(alertas)
        st.table(df_al)
    else:
        st.success("✅ No hay riesgos críticos detectados por ahora.")

def auditoria_maestra(controller):
    """Vista de auditoría visual avanzada y control de integridad."""
    st.subheader("🕵️ Centro de Control de Auditoría", divider='orange')
    
    with st.spinner("Generando análisis de integridad..."):
        df_v_canal = controller.get_ventas_por_canal()
        df_v_estado = controller.get_ventas_por_estado()
        df_ventas_limpio = controller.get_detalle_ventas_limpio()
        # Reutilizamos los de la auditoría anterior para no perder el funnel
        df_desempeno = controller.get_desempeno_vendedores()
        df_leads_estados = controller.get_distribucion_estados_leads()

    # --- 1. RESUMEN EJECUTIVO DE AUDITORÍA (Métricas Rápidas) ---
    m1, m2, m3 = st.columns(3)
    with m1:
        top_canal = df_v_canal.iloc[0]['Canal'] if not df_v_canal.empty else "N/A"
        st.metric("Canal Líder", top_canal)
    with m2:
        monto_avg = df_ventas_limpio['Monto'].mean() if not df_ventas_limpio.empty else 0
        st.metric("Ticket Promedio", f"S/ {monto_avg:,.2f}")
    with m3:
        pax_total = controller.get_pax_totales()
        st.metric("Operación Actual", f"{pax_total} PAX")

    st.markdown("---")

    # --- 2. GRÁFICAS ANALÍTICAS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.markdown("##### Distribución Económica por Canal")
        if not df_v_canal.empty:
            fig_canal = px.bar(df_v_canal, x='Canal', y='Monto', color='Canal', 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_canal.update_layout(showlegend=False, height=300, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_canal, use_container_width=True)
            
    with g2:
        st.markdown("##### Volumen de Ventas por Estado")
        if not df_v_estado.empty:
            fig_est = px.pie(df_v_estado, values='Cantidad', names='Estado', hole=0.5,
                           color_discrete_sequence=px.colors.sequential.RdBu)
            fig_est.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_est, use_container_width=True)

    st.markdown("---")

    # --- 3. TABLA DE AUDITORÍA ESTILIZADA (El "Libro Diario") ---
    st.markdown("#### 📖 Registro Maestro de Ventas (Auditoría)")
    if not df_ventas_limpio.empty:
        st.dataframe(
            df_ventas_limpio,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn("📆 Fecha", format="DD/MM/YYYY"),
                "Monto": st.column_config.NumberColumn("💰 Monto", format="S/ %.2f"),
                "Divisa": st.column_config.TextColumn("💱"),
                "Estado": st.column_config.TextColumn("📌 Estado"),
                "Cliente": st.column_config.TextColumn("👤 Cliente"),
                "Vendedor": st.column_config.TextColumn("👨‍💼 Vendedor")
            }
        )
    else:
        st.info("No hay ventas para auditar.")

    # --- 4. FUNNEL Y DESEMPEÑO (Se mantiene en expanders para no saturar) ---
    with st.expander("📊 Ver Análisis de Prospección (Leads & Funnel)"):
        c1, c2 = st.columns(2)
        with c1:
            if not df_desempeno.empty:
                st.plotly_chart(px.bar(df_desempeno, x='Vendedor', y='Ventas', title="Cierre por Vendedor"), use_container_width=True)
        with c2:
            if not df_leads_estados.empty:
                st.plotly_chart(px.funnel(df_leads_estados, x='Cantidad', y='Estado', title="Embudo Comercial"), use_container_width=True)

def mostrar_pagina(funcionalidad_seleccionada, rol_actual, user_id, supabase_client):
    controller = GerenciaController(supabase_client)
    
    st.title("👨‍💼 Gestión Ejecutiva")

    if funcionalidad_seleccionada in ["Gestión de Registros", "Gestión Ejecutiva"]:
        auditoria_maestra(controller)
    else:
        st.info("Utilice el Dashboard Ejecutivo para ver métricas de alto nivel.")
