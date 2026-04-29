# vistas/page_gerencia.py
import streamlit as st
import pandas as pd
import plotly.express as px
from controllers.gerencia_controller import GerenciaController
from controllers.operaciones_controller import OperacionesController
from controllers.venta_controller import VentaController
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
        df_desempeno = controller.get_desempeno_vendedores()
        df_leads_origen = controller.get_distribucion_origen_leads()

    # --- 1. RESUMEN EJECUTIVO DE AUDITORÍA (Métricas Rápidas) ---
    m1, m2, m3 = st.columns(3)
    with m1:
        top_canal = df_v_canal.iloc[0]['Canal'] if not df_v_canal.empty else "N/A"
        st.metric("Canal Líder", top_canal)
    with m2:
        monto_avg = df_ventas_limpio['Monto'].mean() if not df_ventas_limpio.empty else 0
        st.metric("Ticket Promedio", f"S/ {float(monto_avg or 0):,.2f}")
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
            if not df_leads_origen.empty:
                st.plotly_chart(px.bar(df_leads_origen, x='Origen', y='Cantidad', title="Leads por Origen (Canal Social)"), use_container_width=True)

def render_control_financiero_liquidaciones(supabase_client):
    """Interfaz para que Gerencia complete costos y monedas de las liquidaciones."""
    st.subheader("💰 Control Financiero de Liquidaciones", divider='green')
    
    op_ctrl = OperacionesController(supabase_client)
    vc = VentaController(supabase_client)
    
    # --- 1. SELECTOR DE VENTA (ESTILO OPERACIONES) ---
    c_tipo, c_filtro, c_pax = st.columns([1, 2, 2])
    
    with c_tipo:
        tipo_venta = st.selectbox("1️⃣ Tipo de Venta:", ["--- Seleccione ---", "🏢 B2B (Agencias)", "👤 B2C (Directas)"], key="ger_sel_tipo_v")
    
    ventas_filtradas = []
    
    if tipo_venta == "🏢 B2B (Agencias)":
        agencias = vc.obtener_agencias_aliadas()
        nombres_agencias = [a['nombre'] for a in agencias]
        mapa_agencias = {a['nombre']: a['id_agencia'] for a in agencias}
        with c_filtro:
            ag_sel = st.selectbox("2️⃣ Seleccione Agencia:", ["--- Seleccione ---"] + nombres_agencias, key="ger_sel_ag_b2b")
        if ag_sel != "--- Seleccione ---":
            ventas_filtradas = vc.obtener_ventas_agencia(mapa_agencias[ag_sel])
    
    elif tipo_venta == "👤 B2C (Directas)":
        with c_filtro:
            st.info("📋 Mostrando todas las ventas directas")
        ventas_filtradas = vc.obtener_ventas_directas()
    
    id_venta = None
    if ventas_filtradas:
        opciones_v = [f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})" for v in ventas_filtradas]
        mapa_v = {f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})": v for v in ventas_filtradas}
        with c_pax:
            v_sel = st.selectbox("3️⃣ Cargar Venta:", ["--- Seleccione ---"] + opciones_v, key="ger_sel_v_act")
        if v_sel != "--- Seleccione ---":
            id_venta = mapa_v[v_sel]['id_venta']

    if id_venta:
        st.markdown(f"#### 📋 Panel de Liquidación: Venta #{id_venta}")
        
        try:
            # Reutilizamos componentes de descarga (los mismos que Operaciones)
            from vistas.page_operaciones import render_operational_master_download, render_itinerary_simple_download
            
            # --- SECCIÓN DE DESCARGAS ---
            with st.expander("📥 Descargas y Reportes (Informe Maestro, Ficha, Itinerarios)", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    render_operational_master_download(op_ctrl, id_venta, label="📊 Informe Maestro & Ficha de Control")
                
                # Recuperar render_data para los itinerarios
                res_v_full = supabase_client.table('venta').select('*, itinerario_digital(datos_render)').eq('id_venta', id_venta).single().execute()
                v_full = res_v_full.data or {}
                it_dig = v_full.get('itinerario_digital')
                render_data = None
                
                if it_dig:
                    if isinstance(it_dig, list) and it_dig: it_dig = it_dig[0] # Handle join list
                    render_data = it_dig.get('datos_render')
                    if isinstance(render_data, str):
                        import json
                        render_data = json.loads(render_data)
                
                with c2:
                    if render_data:
                        render_itinerary_simple_download(render_data)
                        # El PDF detallado (Cloud) suele guardarse dentro de datos_render o como metadato
                        url_cloud = render_data.get('url_pdf') or (it_dig.get('url_pdf') if isinstance(it_dig, dict) else None)
                        if url_cloud:
                            st.link_button("🌐 Ver Itinerario Cloud (Detallado)", url_cloud, use_container_width=True, type="secondary")
                    else:
                        st.info("No hay itinerario digital vinculado para esta venta.")

            st.markdown("---")
            
            # --- TABLA DE LIQUIDACIÓN (EDITABLE) ---
            res_v_meta = supabase_client.table('venta').select('moneda, tipo_cambio').eq('id_venta', id_venta).single().execute()
            v_meta = res_v_meta.data or {"moneda": "USD", "tipo_cambio": 3.8}
            tc_v = float(v_meta.get('tipo_cambio') or 3.8)
            
            liq_data = op_ctrl.get_liquidaciones_venta(id_venta)
            
            if liq_data:
                display_data = []
                for l in liq_data:
                    l['Dia'] = l.get('n_linea')
                    l['Hora'] = l.get('hora_servicio') or "---"
                    l['Tipo de Servicio'] = l.get('tipo_servicio', '---')
                    l['Proveedor'] = l.get('proveedor', {}).get('nombre_comercial') if l.get('proveedor') else "---"
                    l['Guía'] = l.get('nombre_guia', '---')
                    l['F. Confirmación'] = l.get('fecha_confirmacion', '---')
                    l['Observacion'] = l.get('observacion', '---')
                    
                    c_u = float(l.get('costo_unitario', 0))
                    p = float(l.get('cantidad_pax') or 1)
                    l['moneda'] = l.get('moneda', 'USD')
                    l['costo_unitario'] = c_u
                    l['PAX'] = int(p)
                    l['TOTAL (PEN)'] = (c_u * p) * tc_v if l['moneda'] == 'USD' else (c_u * p)
                    l['Estado'] = "🟢 OK" if l.get('terminado') else "🔴 PENDIENTE"
                    display_data.append(l)

                df_edit = pd.DataFrame(display_data)
                cols_visible = ['Estado', 'terminado', 'Dia', 'Hora', 'Tipo de Servicio', 'Proveedor', 'Guía', 'F. Confirmación', 'Observacion', 'moneda', 'costo_unitario', 'PAX', 'TOTAL (PEN)']
                
                edited_result = st.data_editor(
                    df_edit[cols_visible],
                    column_config={
                        "Estado": st.column_config.TextColumn("Status", width="small"),
                        "terminado": st.column_config.CheckboxColumn("OK", help="Cerrar Servicio"),
                        "Guía": st.column_config.TextColumn("Guía"),
                        "moneda": st.column_config.SelectboxColumn("Moneda", options=["USD", "PEN", "EUR"]),
                        "costo_unitario": st.column_config.NumberColumn("Costo Unit.", format="%.2f"),
                        "PAX": st.column_config.NumberColumn("Pax"),
                        "TOTAL (PEN)": st.column_config.NumberColumn("Total (S/.)", format="S/. %.2f")
                    },
                    disabled=['Estado', 'Dia', 'Hora', 'Tipo de Servicio', 'Proveedor', 'Guía', 'F. Confirmación', 'Observacion', 'TOTAL (PEN)'],
                    hide_index=True,
                    use_container_width=True,
                    key="editor_liq_gerencia"
                )

                if "editor_liq_gerencia" in st.session_state:
                    state = st.session_state.editor_liq_gerencia
                    cambios = state.get("edited_rows", {})
                    if cambios:
                        st.warning(f"⚠️ {len(cambios)} cambios pendientes.")
                        if st.button("💾 Guardar Cambios Financieros", type="primary"):
                            exitos = 0
                            for row_idx, changes in cambios.items():
                                reg_id = df_edit.iloc[row_idx]['id']
                                mapping = {"moneda": "moneda", "costo_unitario": "costo_unitario", "PAX": "cantidad_pax", "terminado": "terminado"}
                                db_changes = {mapping[k]: v for k, v in changes.items() if k in mapping}
                                
                                # NUEVO: Automatización de Fecha de Confirmación
                                if changes.get('terminado') is True:
                                    from datetime import date
                                    db_changes['fecha_confirmacion'] = date.today().isoformat()
                                elif changes.get('terminado') is False:
                                    db_changes['fecha_confirmacion'] = None

                                if db_changes:
                                    res_up, _ = op_ctrl.actualizar_campos_liquidacion(reg_id, db_changes)
                                    if res_up: exitos += 1
                            if exitos > 0:
                                st.success(f"✅ Se actualizaron {exitos} registros.")
                                st.rerun()
            else:
                st.info("No hay servicios cargados para liquidar en esta venta. Operaciones debe subir el Excel primero.")
        except Exception as e:
            st.error(f"Error en panel financiero: {e}")

def mostrar_pagina(funcionalidad_seleccionada, rol_actual, user_id, supabase_client):
    controller = GerenciaController(supabase_client)
    
    st.title("👨‍💼 Gestión Ejecutiva")
    
    # --- 🔔 Centro de Alertas Universal ---
    from controllers.operaciones_controller import OperacionesController
    from vistas.page_operaciones import render_centro_alertas
    ctrl_op = OperacionesController(supabase_client)
    render_centro_alertas(ctrl_op)

    if funcionalidad_seleccionada in ["Control de Liquidaciones"]:
        render_control_financiero_liquidaciones(supabase_client)
    elif funcionalidad_seleccionada in ["Gestión de Registros", "Gestión Ejecutiva"]:
        auditoria_maestra(controller)
    else:
        st.info("Utilice el Dashboard Ejecutivo para ver métricas de alto nivel.")
