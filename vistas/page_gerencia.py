# vistas/page_gerencia.py
import streamlit as st
import pandas as pd
import plotly.express as px
from controllers.gerencia_controller import GerenciaController
from controllers.operaciones_controller import OperacionesController
from controllers.venta_controller import VentaController
from datetime import date

def _normalizar_genero(val):
    s = str(val or "").strip().upper()
    if not s or s in {"NONE", "NAN", "---"}:
        return "SIN DATO"
    # Normalizaciones comunes
    if s in {"M", "MAS", "MASC", "MASCULINO", "H", "HOMBRE", "MALE"}:
        return "MASCULINO"
    if s in {"F", "FEM", "FEMENINO", "MUJER", "WOMAN", "FEMALE"}:
        return "FEMENINO"
    if s in {"OTRO", "OTRA", "NO BINARIO", "NB", "NON-BINARY"}:
        return "OTRO"
    return s

def _normalizar_pais(val):
    s = str(val or "").strip()
    if not s or s.upper() in {"NONE", "NAN", "---"}:
        return "SIN DATO"
    return s.title()

def _cargar_demografia_clientes(supabase_client):
    """
    Usa tabla `pasajero` como fuente única para:
    - Género (`genero`)
    - País/Nacionalidad (`nacionalidad`)
    - Edad (`edad`)
    """
    try:
        res = (
            supabase_client.table("pasajero")
            .select("genero, nacionalidad, edad")
            .execute()
        )
        df = pd.DataFrame(res.data or [])
        if df.empty:
            return df
        if "genero" in df.columns:
            df["genero_norm"] = df["genero"].apply(_normalizar_genero)
        else:
            df["genero_norm"] = "SIN DATO"
        if "nacionalidad" in df.columns:
            df["pais_norm"] = df["nacionalidad"].apply(_normalizar_pais)
        else:
            df["pais_norm"] = "SIN DATO"
        if "edad" in df.columns:
            df["edad_num"] = pd.to_numeric(df["edad"], errors="coerce")
        else:
            df["edad_num"] = pd.NA
        return df
    except Exception as e:
        print(f"Error cargando demografía (pasajero): {e}")
        return pd.DataFrame()

def dashboard_ejecutivo(controller):
    """Interfaz del Dashboard Principal de Gerencia."""
    # Selector de Moneda elegante
    c_title, c_sel = st.columns([2, 1])
    with c_title:
        st.subheader("📊 Panel de Control Ejecutivo", divider='rainbow')
    with c_sel:
        moneda_sel = st.selectbox("Moneda / Currency:", ["PEN (Soles S/)", "USD (Dólares $)"], index=0, key="gerencia_dashboard_currency")
        
    moneda_dest = 'PEN' if "PEN" in moneda_sel else 'USD'
    symbol = 'S/' if moneda_dest == 'PEN' else '$'

    # --- 1. OBTENER DATOS ---
    with st.spinner("Calculando métricas..."):
        finan = controller.get_kpis_financieros(moneda_destino=moneda_dest)
        comer = controller.get_metricas_comerciales()
        pax_tot = controller.get_pax_totales()
        alertas = controller.get_alertas_gestion()
        ventas_mes = controller.get_ventas_mensuales(moneda_destino=moneda_dest)

    # --- 2. KPIs FINANCIEROS (Fila 1) ---
    st.markdown(f"#### 💰 Resumen Financiero ({moneda_dest})")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Ventas Totales", f"{symbol} {finan['ventas_totales']:,.0f}", delta="Cifra Bruta")
    col2.metric("Recaudado Real", f"{symbol} {finan['total_recaudado']:,.0f}", delta="En Banco", delta_color="normal")
    col3.metric("Saldo Pendiente", f"{symbol} {finan['total_pendiente']:,.0f}", delta="- Deuda Clientes", delta_color="inverse")

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
        # NUEVO: Demografía (Género / País / Edades)
        df_demo = _cargar_demografia_clientes(controller.client)

    # --- 0. DEMOGRAFÍA DE CLIENTES (NUEVO) ---
    st.markdown("#### 🧑‍🤝‍🧑 Demografía de Clientes (Pasajeros)")
    d1, d2, d3 = st.columns(3)
    if df_demo is None or df_demo.empty:
        st.info("Sin datos de pasajeros para graficar demografía.")
    else:
        # A) Diagrama circular de género
        with d1:
            st.markdown("##### Género")
            df_g = df_demo.groupby("genero_norm").size().reset_index(name="Cantidad")
            fig_g = px.pie(
                df_g,
                names="genero_norm",
                values="Cantidad",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_g.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_g, use_container_width=True)

        # B) Barras de países (top 10)
        with d2:
            st.markdown("##### País / Nacionalidad (Top 10)")
            df_p = (
                df_demo.groupby("pais_norm")
                .size()
                .reset_index(name="Cantidad")
                .sort_values("Cantidad", ascending=False)
                .head(10)
            )
            fig_p = px.bar(
                df_p,
                x="pais_norm",
                y="Cantidad",
                text="Cantidad",
                color_discrete_sequence=["#8E24AA"],
            )
            fig_p.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0))
            fig_p.update_xaxes(title=None)
            st.plotly_chart(fig_p, use_container_width=True)

        # C) Histograma de edades
        with d3:
            st.markdown("##### Edades (Histograma)")
            df_e = df_demo.dropna(subset=["edad_num"]).copy()
            # Filtrado defensivo para edades absurdas
            df_e = df_e[(df_e["edad_num"] >= 0) & (df_e["edad_num"] <= 120)]
            if df_e.empty:
                st.info("Sin edades registradas.")
            else:
                fig_e = px.histogram(
                    df_e,
                    x="edad_num",
                    nbins=12,
                    color_discrete_sequence=["#1E88E5"],
                )
                fig_e.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0))
                fig_e.update_xaxes(title="Edad")
                st.plotly_chart(fig_e, use_container_width=True)

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

def panel_revision_gerencia(supabase_client):
    """Panel donde Gerencia revisa y aprueba cada venta/pasajero. Al aprobar, el calendario muestra ⬜."""
    st.subheader("📋 Panel de Revisión de Pasajeros", divider='blue')
    st.caption("Marca como aprobadas las ventas que ya revisaste. El calendario mostrará ⬜ en lugar del color de estado.")

    # --- LEYENDA DE REFERENCIA ---
    st.markdown(
        """
        <div style='display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px;'>
            <span style='background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 12px;font-size:12px;'>🔴 Sin checks (recién registrado)</span>
            <span style='background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 12px;font-size:12px;'>🟡 Confirmación en progreso</span>
            <span style='background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 12px;font-size:12px;'>🟢 Totalmente confirmado</span>
            <span style='background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 12px;font-size:12px;'>🔵 Contratación en progreso</span>
            <span style='background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 12px;font-size:12px;'>🟠 Totalmente contratado</span>
            <span style='background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:4px 12px;font-size:12px;'>⬜ Aprobado por Gerencia (tú)</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    op_ctrl = OperacionesController(supabase_client)

    with st.spinner("Cargando ventas activas..."):
        ventas = op_ctrl.get_ventas_para_revision_gerencia()

    if not ventas:
        st.info("ℹ️ No hay ventas activas para revisar.")
        return

    # Calcular color semáforo de cada venta
    for v in ventas:
        v['Color'] = op_ctrl.get_color_venta(v['id_venta'])
        v['Aprobado ✔'] = v.get('aprobado_gerencia', False)

    df = pd.DataFrame(ventas)

    # Columnas a mostrar
    cols_visible = ['Color', 'Aprobado ✔', 'Cliente', 'Tour', 'Fecha Viaje', 'Fecha Venta', 'Fecha Aprobación']

    edited = st.data_editor(
        df[cols_visible],
        column_config={
            'Color': st.column_config.TextColumn('🚦 Estado', width='small'),
            'Aprobado ✔': st.column_config.CheckboxColumn('Aprobado ✔', help='Marcar como revisado y aprobado por Gerencia'),
            'Cliente': st.column_config.TextColumn('Pasajero', width='medium'),
            'Tour': st.column_config.TextColumn('Tour / Paquete', width='large'),
            'Fecha Viaje': st.column_config.DateColumn('Fecha Viaje', format='DD/MM/YYYY'),
            'Fecha Venta': st.column_config.DateColumn('Fecha Venta', format='DD/MM/YYYY'),
            'Fecha Aprobación': st.column_config.DateColumn('Aprobado el', format='DD/MM/YYYY'),
        },
        disabled=['Color', 'Cliente', 'Tour', 'Fecha Viaje', 'Fecha Venta', 'Fecha Aprobación'],
        hide_index=True,
        use_container_width=True,
        key='editor_revision_gerencia'
    )

    # Procesar cambios en checkboxes
    if 'editor_revision_gerencia' in st.session_state:
        cambios = st.session_state.editor_revision_gerencia.get('edited_rows', {})
        if cambios:
            st.warning(f"⚠️ {len(cambios)} aprobaciones pendientes de guardar.")
            if st.button("💾 Guardar Aprobaciones", type='primary', use_container_width=True):
                exitos = 0
                errores = []
                for row_idx, changes in cambios.items():
                    if 'Aprobado ✔' in changes:
                        id_v = df.iloc[row_idx]['id_venta']
                        aprobado = changes['Aprobado ✔']
                        ok, msg = op_ctrl.set_aprobacion_gerencia(int(id_v), aprobado)
                        if ok:
                            exitos += 1
                        else:
                            errores.append(f"Venta #{id_v}: {msg}")
                if exitos > 0:
                    st.success(f"✅ {exitos} aprobaciones guardadas. El tablero ahora mostrará ⬜ para las ventas aprobadas.")
                    st.rerun()
                for e in errores:
                    st.error(e)

    # --- NUEVO: Sección de Descargas para Auditoría ---
    st.markdown("---")
    st.markdown("### 📥 Descarga de Archivos de Auditoría")
    st.caption("Genera y descarga el Informe Maestro y la Ficha de Control (Grupos) de cualquier pasajero:")
    
    from vistas.page_operaciones import render_operational_master_download
    
    opciones_descarga = [f"{v['Cliente']} | {v['Tour']} (#{v['id_venta']})" for v in ventas]
    mapa_descarga = {f"{v['Cliente']} | {v['Tour']} (#{v['id_venta']})": v for v in ventas}
    
    col_sel_desc, col_btns_desc = st.columns([1, 1])
    
    with col_sel_desc:
        v_descarga_sel = st.selectbox(
            "Seleccione el Pasajero/Venta para generar archivos:", 
            ["--- Seleccione ---"] + opciones_descarga, 
            key="ger_descarga_pax_sel"
        )
        
    with col_btns_desc:
        if v_descarga_sel != "--- Seleccione ---":
            v_selected = mapa_descarga[v_descarga_sel]
            id_venta_sel = v_selected['id_venta']
            render_operational_master_download(op_ctrl, id_venta_sel, label="📊 Generar Informe Maestro", key=f"ger_mast_{id_venta_sel}")
        else:
            st.info("💡 Selecciona un pasajero de la lista de la izquierda para habilitar las descargas.")

    # Resumen rápido
    total = len(ventas)
    aprobados = sum(1 for v in ventas if v.get('aprobado_gerencia'))
    st.markdown(f"---")
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Total Ventas Activas", total)
    col2.metric("✅ Aprobadas por Gerencia", aprobados)
    col3.metric("⏳ Pendientes de Revisión", total - aprobados)


def panel_marketing(supabase_client):
    """Panel específico para Gerencia de Marketing."""
    st.subheader("🎯 Panel de Gerencia de Marketing", divider='orange')
    st.caption("Análisis de intención de compra basado en cotizaciones de Leads.")
    
    from controllers.gerencia_controller import GerenciaController
    controller = GerenciaController(supabase_client)
    
    with st.spinner("Analizando datos de itinerarios de leads..."):
        df_mkt = controller.get_marketing_dashboard_data()
        
    if df_mkt.empty:
        st.info("No hay suficientes datos de itinerarios enviados a leads para generar el análisis.")
        return
        
    # --- KPIs RÁPIDOS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Cotizaciones", len(df_mkt), help="Número de itinerarios creados")
    m2.metric("Intención de Venta (USD)", f"${df_mkt['Precio_USD'].sum():,.0f}", help="Suma del precio de todas las cotizaciones")
    m3.metric("Ticket Promedio (USD)", f"${df_mkt['Precio_USD'].mean():,.0f}", help="Precio promedio por cotización")
    m4.metric("Promedio Pax / Cot", f"{df_mkt['Pax'].mean():.1f}")
    
    st.markdown("---")
    
    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.markdown("##### Origen de Cotizaciones (Leads)")
        df_origen = df_mkt.groupby('Origen').size().reset_index(name='Cantidad')
        fig_origen = px.pie(df_origen, names='Origen', values='Cantidad', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        fig_origen.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_origen, use_container_width=True)
        
    with g2:
        st.markdown("##### Tipología de Viajero")
        df_tipo = df_mkt.groupby('Tipo_Pax').size().reset_index(name='Cantidad')
        fig_tipo = px.bar(df_tipo, x='Tipo_Pax', y='Cantidad', color='Tipo_Pax', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_tipo.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig_tipo, use_container_width=True)
        
    g3, g4 = st.columns(2)
    
    with g3:
        st.markdown("##### Demanda de Días de Viaje")
        df_dias = df_mkt.groupby('Dias').size().reset_index(name='Cantidad')
        # Limpiar datos atípicos para la gráfica de días (ej: 0 días o > 30 días)
        df_dias = df_dias[(df_dias['Dias'] > 0) & (df_dias['Dias'] <= 30)]
        fig_dias = px.bar(df_dias, x='Dias', y='Cantidad', text_auto=True)
        fig_dias.update_xaxes(type='category', title='Cantidad de Días')
        fig_dias.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_dias, use_container_width=True)
        
    with g4:
        st.markdown("##### Top 10 Tours Cotizados")
        # Filtrar tours nulos o vacíos
        df_tours = df_mkt[df_mkt['Tour'].notna() & (df_mkt['Tour'] != '')]
        df_tours = df_tours.groupby('Tour').size().reset_index(name='Cantidad').sort_values('Cantidad', ascending=False).head(10)
        fig_tours = px.bar(df_tours, y='Tour', x='Cantidad', orientation='h', color_discrete_sequence=['#FFCA28'])
        fig_tours.update_yaxes(autorange="reversed", title='')
        fig_tours.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_tours, use_container_width=True)
        
    # --- TABLA DE DATOS ---
    st.markdown("#### 📋 Base de Datos de Cotizaciones MKT")
    st.dataframe(df_mkt, use_container_width=True, hide_index=True)


def mostrar_pagina(funcionalidad_seleccionada, rol_actual, user_id, supabase_client):
    controller = GerenciaController(supabase_client)
    
    st.title("👨‍💼 Gestión Ejecutiva")
    
    # --- 🔔 Centro de Alertas Universal ---
    from controllers.operaciones_controller import OperacionesController
    from vistas.page_operaciones import render_centro_alertas
    ctrl_op = OperacionesController(supabase_client)
    render_centro_alertas(ctrl_op)

    # El selector lateral de Gerencia envía textos como:
    # - "Dashboard Ejecutivo"
    # - "Gerencia de Marketing"
    # - "Auditoría de Gestión"
    # - "Control de Liquidaciones"
    if funcionalidad_seleccionada in ["Dashboard Ejecutivo"]:
        dashboard_ejecutivo(controller)
    elif "Marketing" in funcionalidad_seleccionada:
        panel_marketing(supabase_client)
    elif funcionalidad_seleccionada in ["Auditoría de Gestión", "Gestión de Registros", "Gestión Ejecutiva"]:
        auditoria_maestra(controller)
    elif funcionalidad_seleccionada in ["Control de Liquidaciones"]:
        render_control_financiero_liquidaciones(supabase_client)
    elif funcionalidad_seleccionada in ["Revisión de Pasajeros", "Panel de Revisión", "Revisión Operativa"]:
        panel_revision_gerencia(supabase_client)
    else:
        st.info("Selecciona una opción del menú: `Dashboard Ejecutivo`, `Gerencia de Marketing`, `Auditoría de Gestión`, `Control de Liquidaciones` o `Revisión de Pasajeros`.")

