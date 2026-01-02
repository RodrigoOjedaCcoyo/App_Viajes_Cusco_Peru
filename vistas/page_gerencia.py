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
    """Vista de auditoría para ver tablas crudas."""
    st.subheader("🔒 Auditoría de Datos del Sistema")
    
    with st.expander("Ver todas las Ventas (Tabla Cruda)"):
        res = controller.client.table('venta').select('*').execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
            
    with st.expander("Ver todos los Leads"):
        res = controller.client.table('lead').select('*').execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)

def mostrar_pagina(funcionalidad_seleccionada, rol_actual, user_id, supabase_client):
    """Punto de entrada para el módulo de Gerencia."""
    # st.title se llama en main.py usualmente, pero aquí lo personalizamos
    
    controller = GerenciaController(supabase_client)
    
    if funcionalidad_seleccionada == "Dashboard Ejecutivo":
        dashboard_ejecutivo(controller)
    elif funcionalidad_seleccionada == "Auditoría Completa":
        auditoria_maestra(controller)
    else:
        st.info("Seleccione una opción del menú lateral.")