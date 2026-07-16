# vistas/page_gerencia.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from controllers.gerencia_controller import GerenciaController
from controllers.operaciones_controller import OperacionesController
from controllers.venta_controller import VentaController
from datetime import date, timedelta

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

def _filas_pasajero_por_fecha_venta(res_data, fecha_inicio=None, fecha_fin=None, segmento=None):
    """
    Toma filas de `pasajero` con `venta(fecha_venta, id_agencia_aliada)` embebido y las
    filtra por la FECHA DE VENTA (no por created_at) y por segmento (B2C/Corporativo),
    para ser consistente con el resto de métricas del panel (que usan fecha_venta).
    """
    filas = []
    for p in (res_data or []):
        v = p.get('venta') or {}
        if isinstance(v, list):
            v = v[0] if v else {}
        f_venta = v.get('fecha_venta')
        if not f_venta:
            continue
        try:
            f_obj = pd.to_datetime(f_venta).date()
        except Exception:
            continue
        if fecha_inicio and fecha_fin and not (fecha_inicio <= f_obj <= fecha_fin):
            continue

        tipo = 'Corporativo' if v.get('id_agencia_aliada') else 'B2C'
        if segmento and tipo != segmento:
            continue

        fila = dict(p)
        fila.pop('venta', None)
        fila['fecha_venta'] = f_obj
        filas.append(fila)
    return filas


def _cargar_demografia_clientes(supabase_client, fecha_inicio=None, fecha_fin=None, segmento=None):
    """
    Usa tabla `pasajero` para demografía (Género, Nacionalidad, Edad), filtrando por la
    fecha de la venta asociada (venta.fecha_venta) y por segmento B2C/Corporativo.
    """
    try:
        res = (
            supabase_client.table("pasajero")
            .select("genero, nacionalidad, edad, venta(fecha_venta, id_agencia_aliada)")
            .execute()
        )
        filas = _filas_pasajero_por_fecha_venta(res.data, fecha_inicio, fecha_fin, segmento)
        df = pd.DataFrame(filas)
        if df.empty:
            return df
        df["genero_norm"] = df["genero"].apply(_normalizar_genero) if "genero" in df.columns else "SIN DATO"
        df["pais_norm"]   = df["nacionalidad"].apply(_normalizar_pais) if "nacionalidad" in df.columns else "SIN DATO"
        df["edad_num"]    = pd.to_numeric(df["edad"], errors="coerce") if "edad" in df.columns else pd.NA
        return df
    except Exception as e:
        print(f"Error cargando demografía (pasajero): {e}")
        return pd.DataFrame()


def _cargar_top_clientes(supabase_client, fecha_inicio=None, fecha_fin=None, segmento=None, top_n=15):
    """
    Obtiene los pasajeros marcados como es_principal=True (quien compró el viaje),
    filtrando por la fecha de la venta asociada y por segmento, igual que `_cargar_demografia_clientes`.
    """
    try:
        res = (
            supabase_client.table("pasajero")
            .select("genero, nacionalidad, edad, nombre_completo, venta(fecha_venta, id_agencia_aliada)")
            .eq("es_principal", True)
            .execute()
        )
        filas = _filas_pasajero_por_fecha_venta(res.data, fecha_inicio, fecha_fin, segmento)
        df = pd.DataFrame(filas)
        if df.empty:
            return df
        df["genero_norm"] = df["genero"].apply(_normalizar_genero) if "genero" in df.columns else "SIN DATO"
        df["pais_norm"]   = df["nacionalidad"].apply(_normalizar_pais) if "nacionalidad" in df.columns else "SIN DATO"
        df["edad_num"]    = pd.to_numeric(df["edad"], errors="coerce") if "edad" in df.columns else pd.NA
        return df
    except Exception as e:
        print(f"Error cargando clientes principales: {e}")
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
    
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        f_inicio = st.date_input("Fecha Inicio", date.today().replace(day=1), key="auditoria_finicio")
    with col_d2:
        f_fin = st.date_input("Fecha Fin", date.today(), key="auditoria_ffin")
    with col_d3:
        segmento = st.selectbox("Segmento", ["Todos", "B2C", "Corporativo"], key="auditoria_seg")
        
    seg_val = None if segmento == "Todos" else segmento
    
    with st.spinner("Generando análisis de integridad..."):
        df_v_canal     = controller.get_ventas_por_canal(fecha_inicio=f_inicio, fecha_fin=f_fin, segmento=seg_val)
        df_v_estado    = controller.get_ventas_por_estado(fecha_inicio=f_inicio, fecha_fin=f_fin, segmento=seg_val)
        df_ventas_limpio = controller.get_detalle_ventas_limpio(fecha_inicio=f_inicio, fecha_fin=f_fin, segmento=seg_val)
        df_desempeno   = controller.get_desempeno_vendedores(fecha_inicio=f_inicio, fecha_fin=f_fin, segmento=seg_val)
        df_leads_origen = controller.get_distribucion_origen_leads(fecha_inicio=f_inicio, fecha_fin=f_fin)
        # Demografía de PASAJEROS
        df_demo        = _cargar_demografia_clientes(controller.client, fecha_inicio=f_inicio, fecha_fin=f_fin, segmento=seg_val)
        # TOP CLIENTES (por ventas realizadas)
        df_top_clientes = _cargar_top_clientes(controller.client, fecha_inicio=f_inicio, fecha_fin=f_fin, segmento=seg_val)

    # ─────────────────────────────────────────────────────────────────────────
    # 0. KPIs RÁPIDOS
    # ─────────────────────────────────────────────────────────────────────────
    total_pax = len(df_demo) if df_demo is not None and not df_demo.empty else 0
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        top_canal = df_v_canal.iloc[0]['Canal'] if not df_v_canal.empty else "N/A"
        st.metric("Canal Líder", top_canal)
    with m2:
        monto_avg = df_ventas_limpio['Monto'].mean() if not df_ventas_limpio.empty else 0
        st.metric("Ticket Promedio", f"S/ {float(monto_avg or 0):,.2f}")
    with m3:
        pax_total = controller.get_pax_totales()
        st.metric("PAX en Operación", f"{pax_total}")
    with m4:
        n_clientes = len(df_top_clientes) if df_top_clientes is not None and not df_top_clientes.empty else 0
        st.metric("Clientes con Ventas", f"{n_clientes}")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────
    # 1. DEMOGRAFÍA DE PASAJEROS
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("#### 🧑‍🤝‍🧑 Demografía de Pasajeros")
    if df_demo is None or df_demo.empty:
        st.info("Sin datos de pasajeros en el rango seleccionado.")
    else:
        da1, da2, da3 = st.columns(3)

        # A) Diagrama circular de género
        with da1:
            st.markdown("##### Género")
            df_g = df_demo.groupby("genero_norm").size().reset_index(name="Cantidad")
            fig_g = px.pie(
                df_g, names="genero_norm", values="Cantidad", hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_g.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0), showlegend=True)
            st.plotly_chart(fig_g, use_container_width=True)

        # B) Barras de nacionalidad (top 10)
        with da2:
            st.markdown("##### Nacionalidad / País (Top 10)")
            df_p = (
                df_demo.groupby("pais_norm")
                .size()
                .reset_index(name="Cantidad")
                .sort_values("Cantidad", ascending=False)
                .head(10)
            )
            fig_p = px.bar(
                df_p, x="pais_norm", y="Cantidad", text="Cantidad",
                color="Cantidad",
                color_continuous_scale="Purples",
            )
            fig_p.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
            fig_p.update_xaxes(title=None)
            st.plotly_chart(fig_p, use_container_width=True)

        # C) Canal de captación (red_social)
        with da3:
            st.markdown("##### Edades de Pasajeros (Histograma)")
            df_e = df_demo.dropna(subset=["edad_num"]).copy()
            df_e = df_e[(df_e["edad_num"] >= 0) & (df_e["edad_num"] <= 120)]
            if df_e.empty:
                st.info("Sin edades registradas.")
            else:
                fig_e = px.histogram(
                    df_e, x="edad_num", nbins=12,
                    color_discrete_sequence=["#1E88E5"],
                )
                fig_e.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0))
                fig_e.update_xaxes(title="Edad")
                st.plotly_chart(fig_e, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 1B. CLIENTES PRINCIPALES (pasajero es_principal=True)
    # ─────────────────────────────────────────────────────────────────────────
    n_principales = len(df_top_clientes) if df_top_clientes is not None and not df_top_clientes.empty else 0
    st.markdown(f"#### 🏆 Demografía de Clientes Principales ({n_principales} registros — `es_principal = true`)")
    if df_top_clientes is None or df_top_clientes.empty:
        st.info("Sin datos de clientes principales en el rango seleccionado.")
    else:
        cp1, cp2, cp3 = st.columns(3)

        # A) Género
        with cp1:
            st.markdown("##### Género")
            df_cg = df_top_clientes.groupby("genero_norm").size().reset_index(name="Cantidad")
            fig_cg = px.pie(
                df_cg, names="genero_norm", values="Cantidad", hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_cg.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0), showlegend=True)
            st.plotly_chart(fig_cg, use_container_width=True)

        # B) Nacionalidad (top 10)
        with cp2:
            st.markdown("##### Nacionalidad / País (Top 10)")
            df_cp = (
                df_top_clientes.groupby("pais_norm")
                .size()
                .reset_index(name="Cantidad")
                .sort_values("Cantidad", ascending=False)
                .head(10)
            )
            fig_cp = px.bar(
                df_cp, x="pais_norm", y="Cantidad", text="Cantidad",
                color="Cantidad",
                color_continuous_scale="Teal",
            )
            fig_cp.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
            fig_cp.update_xaxes(title=None)
            st.plotly_chart(fig_cp, use_container_width=True)

        # C) Edades (histograma)
        with cp3:
            st.markdown("##### Edades (Histograma)")
            df_ce = df_top_clientes.dropna(subset=["edad_num"]).copy()
            df_ce = df_ce[(df_ce["edad_num"] >= 0) & (df_ce["edad_num"] <= 120)]
            if df_ce.empty:
                st.info("Sin edades registradas.")
            else:
                fig_ce = px.histogram(
                    df_ce, x="edad_num", nbins=12,
                    color_discrete_sequence=["#FF7043"],
                )
                fig_ce.update_layout(height=320, margin=dict(l=0, r=0, t=30, b=0))
                fig_ce.update_xaxes(title="Edad")
                st.plotly_chart(fig_ce, use_container_width=True)


    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. DESEMPEÑO DE VENDEDORES
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("#### 👨‍💼 Desempeño de Vendedores")
    if df_desempeno is None or df_desempeno.empty:
        st.info("Sin datos de vendedores para el rango seleccionado.")
    else:
        vv1, vv2 = st.columns(2)
        with vv1:
            st.markdown("##### Ventas Cerradas por Vendedor")
            df_v_ord = df_desempeno.sort_values("Ventas", ascending=True)
            fig_v_vend = px.bar(
                df_v_ord, x="Ventas", y="Vendedor", orientation="h",
                text="Ventas",
                color="Ventas",
                color_continuous_scale="Greens",
            )
            fig_v_vend.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
            fig_v_vend.update_yaxes(title=None)
            st.plotly_chart(fig_v_vend, use_container_width=True)

        with vv2:
            st.markdown("##### Leads Asignados vs Ventas Cerradas")
            df_comp = df_desempeno.melt(id_vars="Vendedor", value_vars=["Leads", "Ventas"],
                                        var_name="Tipo", value_name="Cantidad")
            fig_comp = px.bar(
                df_comp, x="Vendedor", y="Cantidad", color="Tipo",
                barmode="group",
                color_discrete_sequence=["#42A5F5", "#66BB6A"],
                text="Cantidad",
            )
            fig_comp.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), legend_title="")
            st.plotly_chart(fig_comp, use_container_width=True)

        # Tasa de conversión por vendedor
        st.markdown("##### Tasa de Conversión (Leads → Ventas) por Vendedor")
        df_conv = df_desempeno.copy()
        df_conv["Conversión %"] = df_conv.apply(
            lambda r: round(r["Ventas"] / r["Leads"] * 100, 1) if r["Leads"] > 0 else 0, axis=1
        )
        df_conv = df_conv.sort_values("Conversión %", ascending=False)
        fig_conv = px.bar(
            df_conv, x="Vendedor", y="Conversión %",
            text=df_conv["Conversión %"].apply(lambda v: f"{v}%"),
            color="Conversión %",
            color_continuous_scale="RdYlGn",
        )
        fig_conv.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig_conv, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. DISTRIBUCIÓN POR CANAL Y ESTADO
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("#### 📊 Análisis de Ventas")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("##### Distribución Económica por Canal")
        if not df_v_canal.empty:
            fig_canal = px.bar(df_v_canal, x='Canal', y='Monto', color='Canal',
                               color_discrete_sequence=px.colors.qualitative.Pastel,
                               text_auto=True)
            fig_canal.update_layout(showlegend=False, height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_canal, use_container_width=True)
        else:
            st.info("Sin datos de canales.")

    with g2:
        st.markdown("##### Volumen de Ventas por Estado")
        if not df_v_estado.empty:
            fig_est = px.pie(df_v_estado, values='Cantidad', names='Estado', hole=0.5,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            fig_est.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_est, use_container_width=True)
        else:
            st.info("Sin datos de estados.")

    # Leads por canal social
    if not df_leads_origen.empty:
        st.markdown("##### Leads por Canal Social")
        fig_leads = px.bar(df_leads_origen, x='Origen', y='Cantidad',
                           color='Cantidad', color_continuous_scale='Blues',
                           text='Cantidad')
        fig_leads.update_layout(height=280, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig_leads, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. REGISTRO MAESTRO DE VENTAS
    # ─────────────────────────────────────────────────────────────────────────
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


def panel_desempeno_operaciones(supabase_client):
    """Panel exclusivo de Gerencia: desempeño operativo del área de Operaciones, con selector de fechas y B2B/B2C."""
    st.subheader("⚙️ Desempeño de Operaciones", divider='violet')
    st.caption("Vista de Gerencia sobre el desempeño del área de Operaciones (servicios ejecutados, cumplimiento y proveedores).")

    op_ctrl = OperacionesController(supabase_client)

    # --- FILTROS: Rango de fechas (por defecto, mes anterior completo) y Segmento B2B/B2C ---
    hoy = date.today()
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)

    c1, c2 = st.columns([2, 1])
    with c1:
        fechas = st.date_input(
            "Rango de Fechas (Fecha de Servicio)",
            [primer_dia_mes_anterior, ultimo_dia_mes_anterior],
            key="ger_ops_fechas"
        )
    with c2:
        segmento = st.selectbox("Segmento", ["Todos", "B2B", "B2C"], key="ger_ops_segmento")

    f_ini = f_fin = None
    if isinstance(fechas, (tuple, list)):
        if len(fechas) == 2:
            f_ini, f_fin = fechas
        elif len(fechas) == 1:
            f_ini = f_fin = fechas[0]

    if not f_ini or not f_fin:
        st.info("Selecciona un rango de fechas válido para continuar.")
        return

    seg_val = None if segmento == "Todos" else segmento

    with st.spinner("Calculando desempeño operativo..."):
        df_actual = op_ctrl.get_servicios_desempeno(f_ini, f_fin, segmento=seg_val)
        df_top_prov = op_ctrl.get_top_proveedores_periodo(f_ini, f_fin, segmento=seg_val)
        df_costo_tipo = op_ctrl.get_costos_por_tipo_servicio_periodo(f_ini, f_fin, segmento=seg_val)
        df_lead_time = op_ctrl.get_lead_time_confirmacion_periodo(f_ini, f_fin, segmento=seg_val)

    if df_actual.empty:
        st.info("No hay servicios operativos registrados para el rango y segmento seleccionados.")
        return

    ids_venta_periodo = df_actual['id_venta'].unique().tolist()
    with st.spinner("Cargando demografía de pasajeros..."):
        df_nacionalidades = op_ctrl.get_nacionalidades_periodo(ids_venta_periodo)

    # ─────────────────────────────────────────────────────────────────
    # 1. KPIs DEL PERIODO
    # ─────────────────────────────────────────────────────────────────
    servicios_totales = len(df_actual)
    pax_atendidos = int(df_actual['pax'].sum())
    terminados = int((df_actual['estado'] == 'TERMINADO').sum())
    pct_cumplidos = (terminados / servicios_totales * 100) if servicios_totales else 0
    costo_total = float(df_actual['costo_usd'].sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🛎️ Servicios Ejecutados", f"{servicios_totales:,}")
    k2.metric("🧑‍🤝‍🧑 Pax Atendidos", f"{pax_atendidos:,}")
    k3.metric("✅ % Cumplidos a Tiempo", f"{pct_cumplidos:.1f}%")
    k4.metric("💵 Costo Operativo (USD)", f"${costo_total:,.0f}")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 2. CARGA OPERATIVA DIARIA (B2B vs B2C)
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 📅 Carga Operativa Diaria")
    df_carga = df_actual.copy()
    df_carga['fecha_servicio'] = pd.to_datetime(df_carga['fecha_servicio']).dt.date
    df_carga_agg = df_carga.groupby(['fecha_servicio', 'tipo_venta']).size().reset_index(name='Servicios')
    fig_carga = px.bar(
        df_carga_agg, x='fecha_servicio', y='Servicios', color='tipo_venta',
        barmode='stack',
        color_discrete_map={'B2B': '#7E57C2', 'B2C': '#26A69A'},
        labels={'fecha_servicio': 'Fecha', 'tipo_venta': 'Tipo'}
    )
    fig_carga.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), legend_title='')
    st.plotly_chart(fig_carga, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 3. ESTADO DE CUMPLIMIENTO Y MIX B2B/B2C
    # ─────────────────────────────────────────────────────────────────
    e1, e2 = st.columns(2)
    with e1:
        st.markdown("#### 🚦 Estado de Cumplimiento")
        df_estado = df_actual.groupby('estado').size().reset_index(name='Cantidad')
        colores_estado = {'TERMINADO': '#66BB6A', 'PENDIENTE': '#FFA726', 'CANCELADO': '#EF5350'}
        fig_estado = px.pie(
            df_estado, names='estado', values='Cantidad', hole=0.5,
            color='estado', color_discrete_map=colores_estado
        )
        fig_estado.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_estado, use_container_width=True)

    with e2:
        st.markdown("#### 🏢 Mix B2B / B2C")
        df_mix = df_actual.groupby('tipo_venta').size().reset_index(name='Cantidad')
        fig_mix = px.pie(
            df_mix, names='tipo_venta', values='Cantidad', hole=0.5,
            color='tipo_venta', color_discrete_map={'B2B': '#7E57C2', 'B2C': '#26A69A'}
        )
        fig_mix.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_mix, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 4. TOP PROVEEDORES DEL PERIODO
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🏆 Top Proveedores del Periodo")
    if df_top_prov.empty:
        st.info("No hay proveedores asignados en el rango seleccionado.")
    else:
        p1, p2 = st.columns(2)
        with p1:
            df_p_serv = df_top_prov.sort_values('Servicios', ascending=True)
            fig_p_serv = px.bar(
                df_p_serv, x='Servicios', y='Proveedor', orientation='h',
                text='Servicios', color='Servicios', color_continuous_scale='Purples',
                title='Por Cantidad de Servicios'
            )
            fig_p_serv.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0), coloraxis_showscale=False)
            fig_p_serv.update_yaxes(title=None)
            st.plotly_chart(fig_p_serv, use_container_width=True)
        with p2:
            df_p_costo = df_top_prov.sort_values('Costo_USD', ascending=True)
            fig_p_costo = px.bar(
                df_p_costo, x='Costo_USD', y='Proveedor', orientation='h',
                text=df_p_costo['Costo_USD'].apply(lambda v: f"${v:,.0f}"),
                color='Costo_USD', color_continuous_scale='Oranges',
                title='Por Costo Operativo (USD)'
            )
            fig_p_costo.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0), coloraxis_showscale=False)
            fig_p_costo.update_yaxes(title=None)
            st.plotly_chart(fig_p_costo, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 5. COSTO OPERATIVO POR TIPO DE SERVICIO
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🧾 Costo Operativo por Tipo de Servicio")
    if df_costo_tipo.empty:
        st.info("No hay costos operativos registrados en el rango seleccionado.")
    else:
        fig_costo_tipo = px.bar(
            df_costo_tipo, x='Tipo de Servicio', y='Costo_USD',
            text=df_costo_tipo['Costo_USD'].apply(lambda v: f"${v:,.0f}"),
            color='Costo_USD', color_continuous_scale='Tealgrn',
        )
        fig_costo_tipo.update_layout(
            height=350, margin=dict(l=0, r=0, t=20, b=0),
            coloraxis_showscale=False, yaxis_title='Costo (USD)'
        )
        st.plotly_chart(fig_costo_tipo, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 6. NACIONALIDAD DE PASAJEROS ATENDIDOS
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🌍 Nacionalidad de Pasajeros Atendidos")
    if df_nacionalidades.empty:
        st.info("No hay pasajeros registrados para las ventas del periodo seleccionado.")
    else:
        df_nac_top = df_nacionalidades.head(10)
        fig_nac = px.bar(
            df_nac_top, x='nacionalidad', y='Cantidad', text='Cantidad',
            color='Cantidad', color_continuous_scale='Blues',
        )
        fig_nac.update_layout(
            height=350, margin=dict(l=0, r=0, t=20, b=0),
            coloraxis_showscale=False, xaxis_title=None
        )
        st.plotly_chart(fig_nac, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 7. ANTICIPACIÓN DE CONFIRMACIÓN DE SERVICIOS
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### ⏱️ Anticipación de Confirmación de Servicios")
    st.caption("Días entre la fecha en que se confirmó cada servicio y la fecha en que se ejecutó. Valores bajos indican contrataciones de última hora.")
    if df_lead_time.empty:
        st.info("No hay servicios con fecha de confirmación registrada en el rango seleccionado.")
    else:
        fig_lead = px.histogram(
            df_lead_time, x='dias_anticipacion', nbins=15,
            color_discrete_sequence=['#AB47BC'],
        )
        fig_lead.update_layout(
            height=320, margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title='Días de anticipación', yaxis_title='Cantidad de servicios'
        )
        st.plotly_chart(fig_lead, use_container_width=True)


def panel_desempeno_contabilidad(supabase_client):
    """Panel exclusivo de Gerencia: desempeño financiero/contable, con selector de fechas, B2B/B2C y moneda."""
    st.subheader("🏦 Desempeño de Contabilidad", divider='green')
    st.caption("Vista de Gerencia sobre el desempeño financiero: ingresos cobrados, gastos operativos y cuentas por cobrar.")

    controller = GerenciaController(supabase_client)

    # --- FILTROS: Rango de fechas (por defecto, mes anterior completo), Segmento B2B/B2C y Moneda ---
    hoy = date.today()
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        fechas = st.date_input(
            "Rango de Fechas (Fecha de Pago)",
            [primer_dia_mes_anterior, ultimo_dia_mes_anterior],
            key="ger_cont_fechas"
        )
    with c2:
        segmento = st.selectbox("Segmento", ["Todos", "B2B", "B2C"], key="ger_cont_segmento")
    with c3:
        moneda_sel = st.selectbox("Moneda", ["PEN (Soles S/)", "USD (Dólares $)"], key="ger_cont_moneda")

    moneda_dest = 'PEN' if "PEN" in moneda_sel else 'USD'
    symbol = 'S/' if moneda_dest == 'PEN' else '$'

    f_ini = f_fin = None
    if isinstance(fechas, (tuple, list)):
        if len(fechas) == 2:
            f_ini, f_fin = fechas
        elif len(fechas) == 1:
            f_ini = f_fin = fechas[0]

    if not f_ini or not f_fin:
        st.info("Selecciona un rango de fechas válido para continuar.")
        return

    seg_val = None if segmento == "Todos" else segmento

    with st.spinner("Calculando desempeño contable..."):
        df_ingresos = controller.get_ingresos_detalle_periodo(f_ini, f_fin, segmento=seg_val, moneda_destino=moneda_dest)
        df_gastos = controller.get_gastos_detalle_periodo(f_ini, f_fin, segmento=seg_val, moneda_destino=moneda_dest)
        df_cxc = controller.get_cuentas_por_cobrar_periodo(f_ini, f_fin, segmento=seg_val, moneda_destino=moneda_dest)
        df_top_prov_gasto = controller.get_top_proveedores_gasto_periodo(f_ini, f_fin, segmento=seg_val, moneda_destino=moneda_dest)

    if df_ingresos.empty and df_gastos.empty:
        st.info("No hay movimientos de ingresos ni gastos registrados para el rango y segmento seleccionados.")
        return

    # ─────────────────────────────────────────────────────────────────
    # 1. KPIs DEL PERIODO
    # ─────────────────────────────────────────────────────────────────
    ingresos_total = float(df_ingresos['monto'].sum()) if not df_ingresos.empty else 0.0
    gastos_total = float(df_gastos['monto'].sum()) if not df_gastos.empty else 0.0
    utilidad = ingresos_total - gastos_total
    margen = (utilidad / ingresos_total * 100) if ingresos_total > 0 else 0.0
    cuentas_cobrar_total = float(df_cxc['Saldo Pendiente'].sum()) if not df_cxc.empty else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("💰 Ingresos Cobrados", f"{symbol} {ingresos_total:,.0f}")
    k2.metric("💸 Gastos Operativos", f"{symbol} {gastos_total:,.0f}")
    k3.metric("📈 Utilidad", f"{symbol} {utilidad:,.0f}", delta=f"{margen:.1f}% margen")
    k4.metric("📋 Cuentas por Cobrar", f"{symbol} {cuentas_cobrar_total:,.0f}")
    k5.metric("🧾 Transacciones", f"{len(df_ingresos) + len(df_gastos):,}")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 2. FLUJO DIARIO: INGRESOS VS. GASTOS
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 📅 Flujo Diario: Ingresos vs. Gastos")
    df_ing_dia = (
        df_ingresos.groupby('fecha')['monto'].sum().reset_index().rename(columns={'monto': 'Ingresos'})
        if not df_ingresos.empty else pd.DataFrame(columns=['fecha', 'Ingresos'])
    )
    df_gas_dia = (
        df_gastos.groupby('fecha')['monto'].sum().reset_index().rename(columns={'monto': 'Gastos'})
        if not df_gastos.empty else pd.DataFrame(columns=['fecha', 'Gastos'])
    )
    df_flujo = pd.merge(df_ing_dia, df_gas_dia, on='fecha', how='outer').fillna(0).sort_values('fecha')
    if not df_flujo.empty:
        df_flujo['fecha'] = pd.to_datetime(df_flujo['fecha'])
        fig_flujo = px.line(
            df_flujo, x='fecha', y=['Ingresos', 'Gastos'], markers=True,
            color_discrete_sequence=['#42A5F5', '#EF5350'],
            labels={'value': f'Monto ({moneda_dest})', 'fecha': 'Fecha', 'variable': 'Tipo'}
        )
        fig_flujo.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0), legend_title='', hovermode='x unified')
        st.plotly_chart(fig_flujo, use_container_width=True)
    else:
        st.info("Sin movimientos diarios para graficar.")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 3. CASCADA DE RENTABILIDAD DEL PERIODO
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🌊 Cascada de Rentabilidad del Periodo")
    fig_wf = go.Figure(go.Waterfall(
        orientation='v',
        measure=['relative', 'relative', 'total'],
        x=['Ingresos', 'Gastos', 'Utilidad'],
        text=[f"{symbol}{ingresos_total:,.0f}", f"-{symbol}{gastos_total:,.0f}", f"{symbol}{utilidad:,.0f}"],
        y=[ingresos_total, -gastos_total, utilidad],
        connector={'line': {'color': 'rgb(120,120,120)'}},
        decreasing={'marker': {'color': '#EF5350'}},
        increasing={'marker': {'color': '#66BB6A'}},
        totals={'marker': {'color': '#42A5F5'}}
    ))
    fig_wf.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0), showlegend=False)
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 4. MÉTODOS DE PAGO (INGRESOS Y GASTOS)
    # ─────────────────────────────────────────────────────────────────
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("#### 💳 Ingresos por Método de Pago")
        if df_ingresos.empty:
            st.info("Sin ingresos registrados.")
        else:
            df_met_ing = df_ingresos.groupby('metodo_pago')['monto'].sum().reset_index().rename(
                columns={'metodo_pago': 'Método', 'monto': 'Monto'}
            )
            fig_met_ing = px.pie(
                df_met_ing, names='Método', values='Monto', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_met_ing.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_met_ing, use_container_width=True)

    with m2:
        st.markdown("#### 💳 Gastos por Método de Pago")
        if df_gastos.empty:
            st.info("Sin gastos registrados.")
        else:
            df_met_gas = df_gastos.groupby('metodo_pago')['monto'].sum().reset_index().rename(
                columns={'metodo_pago': 'Método', 'monto': 'Monto'}
            )
            fig_met_gas = px.pie(
                df_met_gas, names='Método', values='Monto', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_met_gas.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_met_gas, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 5. MIX DE INGRESOS B2B / B2C
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🏢 Mix de Ingresos B2B / B2C")
    if df_ingresos.empty:
        st.info("Sin ingresos registrados.")
    else:
        df_mix = df_ingresos.groupby('tipo_venta')['monto'].sum().reset_index().rename(
            columns={'tipo_venta': 'Tipo', 'monto': 'Monto'}
        )
        fig_mix = px.pie(
            df_mix, names='Tipo', values='Monto', hole=0.5,
            color='Tipo', color_discrete_map={'B2B': '#7E57C2', 'B2C': '#26A69A'}
        )
        fig_mix.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_mix, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 6. TOP PROVEEDORES POR GASTO PAGADO
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🏆 Top Proveedores por Gasto Pagado")
    if df_top_prov_gasto.empty:
        st.info("No hay pagos a proveedores en el rango seleccionado.")
    else:
        df_p = df_top_prov_gasto.sort_values('Monto', ascending=True)
        fig_p = px.bar(
            df_p, x='Monto', y='Proveedor', orientation='h',
            text=df_p['Monto'].apply(lambda v: f"{symbol}{v:,.0f}"),
            color='Monto', color_continuous_scale='Oranges'
        )
        fig_p.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0), coloraxis_showscale=False)
        fig_p.update_yaxes(title=None)
        st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 7. TOP CLIENTES CON SALDO PENDIENTE (CUENTAS POR COBRAR)
    # ─────────────────────────────────────────────────────────────────
    st.markdown("#### 📋 Top Clientes con Saldo Pendiente (Cuentas por Cobrar)")
    if df_cxc.empty:
        st.success("✅ No hay saldos pendientes en el rango seleccionado.")
    else:
        df_c = df_cxc.sort_values('Saldo Pendiente', ascending=True)
        fig_c = px.bar(
            df_c, x='Saldo Pendiente', y='Cliente', orientation='h',
            text=df_c['Saldo Pendiente'].apply(lambda v: f"{symbol}{v:,.0f}"),
            color='Saldo Pendiente', color_continuous_scale='Reds'
        )
        fig_c.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0), coloraxis_showscale=False)
        fig_c.update_yaxes(title=None)
        st.plotly_chart(fig_c, use_container_width=True)


def panel_marketing(supabase_client):
    """Panel específico para Gerencia de Marketing."""
    from datetime import date
    st.subheader("🎯 Panel de Gerencia de Marketing", divider='orange')
    st.caption("Análisis de intención de compra basado en cotizaciones enviadas a Leads (1 itinerario por lead, el más reciente).")
    
    import importlib
    import controllers.gerencia_controller as gc_mod
    importlib.reload(gc_mod)
    from controllers.gerencia_controller import GerenciaController
    controller = GerenciaController(supabase_client)
    
    # --- FILTROS ---
    c1, c2, _ = st.columns([2, 1, 3])
    with c1:
        hoy = date.today()
        # Por defecto desde hace un año hasta hoy, o todo
        fechas = st.date_input("Filtrar por Rango de Fechas (Generación)", [], key="mkt_fechas")
    with c2:
        segmento = st.selectbox("Segmento", ["Todos", "B2C", "Corporativo"], key="mkt_seg")
        
    f_ini = f_fin = None
    if isinstance(fechas, tuple) or isinstance(fechas, list):
        if len(fechas) == 2:
            f_ini, f_fin = fechas
        elif len(fechas) == 1:
            f_ini = f_fin = fechas[0]
            
    seg_val = None if segmento == "Todos" else segmento
    
    with st.spinner("Analizando datos de itinerarios de leads..."):
        resultado = controller.get_marketing_dashboard_data(fecha_inicio=f_ini, fecha_fin=f_fin, segmento=seg_val)
        # Manejar las distintas versiones del retorno
        if isinstance(resultado, tuple):
            if len(resultado) == 4:
                total_leads, total_itinerarios, df_paquetes, df_tours = resultado
            elif len(resultado) == 3:
                total_leads, df_paquetes, df_tours = resultado
                total_itinerarios = len(df_paquetes)
            else:
                total_leads, total_itinerarios = 0, 0
                df_paquetes, df_tours = resultado
        else:
            total_leads, total_itinerarios = 0, 0
            df_paquetes = resultado
            df_tours = pd.DataFrame()
        
    if df_paquetes.empty:
        st.info("No hay suficientes datos de itinerarios para este filtro.")
        return
    
    # --- DIAGNÓSTICO ---
    with st.expander("🔍 Diagnóstico de Datos", expanded=False):
        st.write(f"- **Leads totales en el sistema:** {total_leads}")
        st.write(f"- **Itinerarios totales en la DB:** {total_itinerarios}")
        st.write(f"- **Itinerarios filtrados (1 por lead):** {len(df_paquetes)}")
        st.write(f"- **Tours individuales extraídos:** {len(df_tours)}")
        
    # --- KPIs RÁPIDOS ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📨 Leads Cotizados", f"{len(df_paquetes):,}", help="Leads que recibieron al menos 1 itinerario en este periodo/segmento (solo se cuenta el último).")
    k2.metric("💰 Intención de Venta", f"${df_paquetes['Precio_Total_USD'].sum():,.0f}", help="Suma total de precios de las cotizaciones enviadas en este filtro.")
    k3.metric("🎫 Ticket Promedio", f"${df_paquetes['Precio_Total_USD'].mean():,.0f}", help="Precio promedio por cotización = Intención de Venta ÷ Leads Cotizados.")
    k4.metric("🗺️ Tours Incluidos", f"{len(df_tours):,}", help="Cantidad total de tours individuales incluidos en estas cotizaciones.")
    
    st.markdown("---")
    
    # --- GRÁFICOS DE TENDENCIA (LÍNEAS) ---
    st.markdown("##### 📈 Tendencia de Cotizaciones en el Tiempo")
    if 'Fecha_Cotizacion' in df_paquetes.columns and not df_paquetes['Fecha_Cotizacion'].isnull().all():
        df_temp = df_paquetes.copy()
        df_temp['Fecha_Cotizacion'] = pd.to_datetime(df_temp['Fecha_Cotizacion'], errors='coerce')
        df_tendencia = df_temp.dropna(subset=['Fecha_Cotizacion']).copy()
        df_tendencia['Mes'] = df_tendencia['Fecha_Cotizacion'].dt.to_period('M').astype(str)
        
        df_agrupado = df_tendencia.groupby('Mes').agg(
            Intencion_Venta_USD=('Precio_Total_USD', 'sum'),
            Cantidad_Cotizaciones=('Paquete', 'count'),
            Ticket_Promedio=('Precio_Total_USD', 'mean')
        ).reset_index()
        
        t1, t2 = st.columns(2)
        with t1:
            fig_tend_venta = px.line(df_agrupado, x='Mes', y='Intencion_Venta_USD', markers=True, 
                                    title='Intención de Venta por Mes (USD)',
                                    color_discrete_sequence=['#FF7043'])
            fig_tend_venta.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10), 
                                         yaxis_title='USD', xaxis_title='')
            st.plotly_chart(fig_tend_venta, use_container_width=True)
            
        with t2:
            fig_tend_cant = px.line(df_agrupado, x='Mes', y='Cantidad_Cotizaciones', markers=True,
                                    title='Cantidad de Cotizaciones por Mes',
                                    color_discrete_sequence=['#42A5F5'])
            fig_tend_cant.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10),
                                        yaxis_title='Cotizaciones', xaxis_title='')
            st.plotly_chart(fig_tend_cant, use_container_width=True)
        
        # Línea de Ticket Promedio
        fig_ticket = px.area(df_agrupado, x='Mes', y='Ticket_Promedio', markers=True,
                             title='Evolución del Ticket Promedio por Mes (USD)',
                             color_discrete_sequence=['#AB47BC'])
        fig_ticket.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10),
                                  yaxis_title='USD', xaxis_title='')
        st.plotly_chart(fig_ticket, use_container_width=True)
    else:
        st.info("No hay suficientes fechas válidas para trazar la línea de tendencia.")
        
    st.markdown("---")
    
    # --- GRÁFICOS SECUNDARIOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.markdown("##### 🌍 Origen del Pasajero (Nacionalidad)")
        df_origen = df_paquetes.groupby('Origen_Nacionalidad').size().reset_index(name='Cantidad')
        fig_origen = px.pie(df_origen, names='Origen_Nacionalidad', values='Cantidad', hole=0.4, 
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_origen.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_origen, use_container_width=True)
        
    with g2:
        st.markdown("##### 💵 Distribución de Precios Cotizados (USD)")
        fig_precios = px.histogram(df_paquetes, x="Precio_Total_USD", nbins=15, 
                                   color_discrete_sequence=['#43A047'])
        fig_precios.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), 
                                   yaxis_title="Cantidad", xaxis_title="Precio Total (USD)")
        st.plotly_chart(fig_precios, use_container_width=True)
        
    st.markdown("---")
    
    # --- TOP TOURS ---
    st.markdown("##### 🏆 Top 15 Tours Individuales Más Cotizados")
    if not df_tours.empty:
        df_tours_validos = df_tours[df_tours['Tour'].notna() & (df_tours['Tour'] != '')]
        df_t_count = df_tours_validos.groupby('Tour').size().reset_index(name='Cantidad').sort_values('Cantidad', ascending=False).head(15)
        
        fig_tours = px.bar(df_t_count, y='Tour', x='Cantidad', orientation='h', 
                           color='Cantidad', color_continuous_scale='YlOrRd')
        fig_tours.update_yaxes(autorange="reversed", title='')
        fig_tours.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig_tours, use_container_width=True)
    else:
        st.info("No hay información de tours detallados disponibles en los itinerarios.")
        
    st.markdown("---")
    
    # --- TABLA DE DATOS DETALLADA ---
    st.markdown("#### 📋 Detalle de Cotizaciones (1 por Lead)")
    st.dataframe(df_paquetes, use_container_width=True, hide_index=True, 
                 column_config={
                     "Pasajero": st.column_config.TextColumn("👤 Pasajero", width="medium"),
                     "Vendedor": st.column_config.TextColumn("🧑‍💼 Vendedor", width="small"),
                     "Paquete": st.column_config.TextColumn("📦 Paquete", width="medium"),
                     "Duración": st.column_config.TextColumn("📅 Duración", width="small"),
                     "Fechas_Viaje": st.column_config.TextColumn("✈️ Fechas Viaje", width="medium"),
                     "Origen_Nacionalidad": st.column_config.TextColumn("🌍 Origen", width="small"),
                     "Precio_Total_USD": st.column_config.NumberColumn("💰 Precio USD", format="$%,.0f"),
                     "Fecha_Cotizacion": st.column_config.TextColumn("📆 Fecha Cot.", width="small"),
                 })



def panel_comunicados_gerencia(supabase_client):
    """Panel de administración y auditoría de comunicados de todas las áreas."""
    st.subheader("📢 Administración de Comunicados del Sistema", divider='blue')
    st.caption("Como Gerente, puedes auditar, crear, archivar o reactivar cualquier comunicado de cualquier área.")

    # ── FORMULARIO DE PUBLICACIÓN DESDE GERENCIA ──
    with st.container(border=True):
        st.markdown("#### ➕ Publicar Comunicado (Como Gerencia)")
        c1, c2 = st.columns([2, 1])
        titulo_nuevo = c1.text_input("📝 Título del comunicado", placeholder="Ej: Mantenimiento del sistema", key="com_titulo")
        
        areas_map = {
            "Todos": "TODOS",
            "Ventas": "VENTAS",
            "Operaciones": "OPERACIONES",
            "Contabilidad": "CONTABILIDAD",
            "Gerencia": "GERENCIA"
        }
        dest_nombre = c2.selectbox("🎯 Dirigido a (Área)", list(areas_map.keys()), key="com_dest")
        dest_code = areas_map[dest_nombre]
        
        c_n, c_u = st.columns([1, 1])
        nivel_nuevo = c_n.selectbox("🔴 Nivel de Urgencia", ["💡 INFO", "⚠️ AVISO", "🚨 URGENTE"], key="com_nivel")
        
        con_expiracion = c_u.checkbox("Establecer fecha de expiración", key="com_exp_check")
        fecha_exp = None
        if con_expiracion:
            from datetime import date as _date, timedelta
            fecha_exp = st.date_input("Expira el", value=_date.today() + timedelta(days=7), key="com_fecha_exp")
            
        mensaje_nuevo = st.text_area("💬 Mensaje", placeholder="Escribe aquí el detalle...", height=100, key="com_mensaje")

        if st.button("🚀 Publicar Comunicado", type="primary", use_container_width=True, key="btn_publicar_com"):
            if not titulo_nuevo.strip() or not mensaje_nuevo.strip():
                st.warning("⚠️ El Título y el Mensaje son obligatorios.")
            else:
                nivel_code = nivel_nuevo.split(" ")[-1]
                payload = {
                    'titulo': titulo_nuevo.strip(),
                    'mensaje': mensaje_nuevo.strip(),
                    'nivel': nivel_code,
                    'autor_area': 'GERENCIA',
                    'area_destino': dest_code,
                    'activo': True,
                    'fecha_expiracion': fecha_exp.isoformat() if fecha_exp else None
                }
                try:
                    supabase_client.table('comunicado').insert(payload).execute()
                    st.success("✅ Comunicado publicado exitosamente.")
                    st.rerun()
                except Exception as e_ins:
                    st.error(f"❌ Error al publicar: {e_ins}")

    st.divider()

    # ── LISTA DE COMUNICADOS ACTIVOS ──
    st.markdown("#### 📄 Historial de Comunicados de todas las áreas")
    try:
        res = supabase_client.table('comunicado').select('*').order('fecha_creacion', desc=True).execute()
        comunicados = res.data or []
    except Exception as e_sel:
        st.error(f"No se pudo cargar la lista: {e_sel}")
        comunicados = []

    if not comunicados:
        st.info("No hay comunicados publicados en el sistema.")
    else:
        _nivel_badge = {'URGENTE': '🚨 URGENTE', 'AVISO': '⚠️ AVISO', 'INFO': '💡 INFO'}
        for c in comunicados:
            estado_label = "✅ Activo" if c.get('activo') else "📂 Archivado"
            nivel_label = _nivel_badge.get(str(c.get('nivel', 'INFO')).upper(), 'INFO')
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**{c.get('titulo')}** &nbsp; `{nivel_label}` &nbsp; `{estado_label}`")
                    st.caption(c.get('mensaje', ''))
                    fecha_raw = str(c.get('fecha_creacion', ''))[:10]
                    exp_raw = c.get('fecha_expiracion') or 'Sin expiración'
                    st.caption(f"De: **{c.get('autor_area')}** ➔ Para: **{c.get('area_destino')}** &nbsp;|&nbsp; 📅 Publicado: {fecha_raw} &nbsp;|&nbsp; ⏰ Expira: {exp_raw}")
                with col_btn:
                    if c.get('activo'):
                        if st.button("📂 Archivar", key=f"arch_com_{c['id']}", use_container_width=True):
                            supabase_client.table('comunicado').update({'activo': False}).eq('id', c['id']).execute()
                            st.success("Comunicado archivado.")
                            st.rerun()
                    else:
                        if st.button("♻️ Reactivar", key=f"react_com_{c['id']}", use_container_width=True):
                            supabase_client.table('comunicado').update({'activo': True}).eq('id', c['id']).execute()
                            st.success("Comunicado reactivado.")
                            st.rerun()


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
    elif funcionalidad_seleccionada in ["Comunicados", "Tablero de Comunicados"]:
        panel_comunicados_gerencia(supabase_client)
    elif funcionalidad_seleccionada in ["Auditoría de Gestión", "Gestión de Registros", "Gestión Ejecutiva"]:
        auditoria_maestra(controller)
    elif funcionalidad_seleccionada in ["Control de Liquidaciones"]:
        render_control_financiero_liquidaciones(supabase_client)
    elif funcionalidad_seleccionada in ["Revisión de Pasajeros", "Panel de Revisión", "Revisión Operativa"]:
        panel_revision_gerencia(supabase_client)
    elif funcionalidad_seleccionada in ["Desempeño de Operaciones", "Desempeño Operativo"]:
        panel_desempeno_operaciones(supabase_client)
    elif funcionalidad_seleccionada in ["Desempeño de Contabilidad", "Desempeño Contable"]:
        panel_desempeno_contabilidad(supabase_client)
    else:
        st.info("Selecciona una opción del menú: `Dashboard Ejecutivo`, `Gerencia de Marketing`, `Auditoría de Gestión`, `Desempeño de Operaciones`, `Desempeño de Contabilidad`, `Control de Liquidaciones`, `Comunicados` o `Revisión de Pasajeros`.")

