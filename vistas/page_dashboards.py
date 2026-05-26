import streamlit as st
import pandas as pd
from datetime import date, timedelta
from controllers.reporte_controller import ReporteController
from controllers.lead_controller import LeadController
from controllers.venta_controller import VentaController
import calendar

def render_itinerary_details_visual(render):
    """Renderiza únicamente los botones de descarga del itinerario."""
    if not render:
        st.warning("No hay datos de itinerario disponibles.")
        return

    with st.container(border=True):
        # Título del Itinerario
        titulo_itin = render.get('titulo') or f"{render.get('title_1', '')} {render.get('title_2', '')}".strip() or "General"
        st.markdown(f"#### 📄 Centro de Descargas: {titulo_itin.upper()}")
        st.info("Utilice los botones para obtener el resumen del itinerario en formato profesional.")
        
        # --- BOTONES DE DESCARGA ---
        c_pdf, c_xlsx = st.columns(2)
        
        from controllers.pdf_controller import PDFController
        pdf_ctrl = PDFController()
        
        from controllers.excel_controller import ExcelController
        xl_ctrl = ExcelController()

        with c_pdf:
            pdf_b = pdf_ctrl.generar_itinerario_simple_pdf(render)
            if pdf_b:
                st.download_button(
                    label="📥 Bajar Resumen (PDF)",
                    data=pdf_b,
                    file_name=f"resumen_{render.get('titulo','itin')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with c_xlsx:
            # Extraer parámetros de enriquecimiento
            nombre_pax = render.get('nombre_pasajero')
            total_pax = render.get('num_pasajeros')
            
            # Generar el Excel en memoria con parámetros forzados
            xlsx_b = xl_ctrl.generar_resumen_itinerario_xlsx(render, nombre_cliente=nombre_pax, num_pax=total_pax)
            if xlsx_b:
                st.download_button(
                    label="📊 Bajar Resumen (Excel XLSX)",
                    data=xlsx_b,
                    file_name=f"resumen_{render.get('titulo','itin')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

def render_sales_dashboard_visual(supabase_client):
    """Vista puramente visual para el Dashboard Comercial (Objetivos B2C - Soles)."""
    
    st.markdown("### 🗓️ Periodo Comercial")
    col_mes, col_anio, _ = st.columns([1, 1, 3])
    
    meses_opciones = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    with col_mes:
        mes_sel_nombre = st.selectbox("Mes", list(meses_opciones.values()), index=date.today().month - 1)
        mes_sel = [k for k, v in meses_opciones.items() if v == mes_sel_nombre][0]
    
    with col_anio:
        anio_actual = date.today().year
        anios_opciones = list(range(anio_actual - 2, anio_actual + 3))
        anio_sel = st.selectbox("Año", anios_opciones, index=anios_opciones.index(anio_actual))
    
    st.divider()

    # KPIs Reales pero solo B2C directos
    venta_ctrl = VentaController(supabase_client)
    ventas_b2c_raw = venta_ctrl.obtener_ventas_directas() or []
    
    # --- APLICAR FILTRO TEMPORAL ---
    ventas_b2c = []
    for v in ventas_b2c_raw:
        fecha_str = v.get('fecha_venta')
        if fecha_str:
            try:
                # Convertir a objeto date para extraer mes/año sin error
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha_str.split('T')[0], '%Y-%m-%d').date()
                if fecha_obj.year == anio_sel and fecha_obj.month == mes_sel:
                    ventas_b2c.append(v)
            except Exception as e:
                # Si falla el parseo, se descarta para ser seguros
                pass
    
    lead_ctrl = LeadController(supabase_client)
    # Ideally leads should also be filtered, but for now we filter sales.
    total_leads = len(lead_ctrl.obtener_todos_leads())
    
    # Procesar ventas B2C para estandarizar en Soles (PEN)
    df_ventas = pd.DataFrame()
    total_b2c_pen = 0.0
    
    if ventas_b2c:
        for v in ventas_b2c:
            monto_orig = float(v.get('precio_total_cierre') or 0.0)
            tipo_c = float(v.get('tipo_cambio') or 3.80)
            moneda = str(v.get('moneda', 'USD')).upper()
            
            if moneda == 'USD':
                monto_pen = monto_orig * tipo_c
            elif moneda == 'EUR':
                monto_pen = monto_orig * (tipo_c * 1.05) # Asumiendo ratio simplificado
            else:
                monto_pen = monto_orig
                
            v['monto_total_pen'] = monto_pen
            total_b2c_pen += monto_pen

        df_ventas = pd.DataFrame(ventas_b2c)
        df_ventas.rename(columns={'fecha_venta': 'fecha_venta'}, inplace=True) # Ensure column exists
        
    # Las métricas superiores (S/, Leads, Conversión) han sido ocultadas a petición del usuario.
    # Mostrar directamente sólo la gráfica de la "culebrita".
    
    # --- CREACIÓN DE PESTAÑAS (TABS) ---
    tab_metricas, tab_calendario, tab_ventas = st.tabs(["📊 Métricas Clave", "🗓️ Calendario Operativo", "📋 Historial de Ventas"])
    
    with tab_metricas:
        # Llamar al renderizador de objetivos visuales (Gauge Chart)
        from vistas.dashboard_analytics import render_sales_dashboard
        render_sales_dashboard(df_ventas)

    with tab_calendario:
        # Agregar Calendario de Operaciones al Dashboard Comercial
        from vistas.page_operaciones import dashboard_tablero_diario
        from controllers.operaciones_controller import OperacionesController
        
        ctrl_ops = OperacionesController(supabase_client)
        dashboard_tablero_diario(ctrl_ops)

    with tab_ventas:
        st.write("### 📜 Registro Consolidado de Ventas")
        st.caption("Visualización de las ventas más recientes (B2C y B2B).")
        
        col_excel, _ = st.columns([1, 2])
        from controllers.excel_controller import ExcelController
        xl_ctrl = ExcelController()
        excel_buffer = xl_ctrl.generar_reporte_ventas_consolidado_xlsx(supabase_client)
        
        col_excel.download_button(
            label="📥 Descargar Reporte Maestro de Ventas (Excel)",
            data=excel_buffer.getvalue(),
            file_name=f"reporte_maestro_ventas_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
        
        # 1. Obtener Ventas B2C
        ventas_b2c = venta_ctrl.obtener_ventas_directas() or []
        # 2. Obtener Ventas B2B
        ventas_b2b = venta_ctrl.obtener_todas_ventas_b2b() or []
        
        # 3. Consolidar
        all_ventas = []
        for v in ventas_b2c:
            v['tipo'] = '🏠 DIRECTA (B2C)'
            v['entidad'] = v.get('nombre_cliente', 'Desconocido')
            all_ventas.append(v)
            
        for v in ventas_b2b:
            v['tipo'] = '🤝 AGENCIA (B2B)'
            v['entidad'] = f"{v.get('nombre_agencia', '---')} / Pax: {v.get('nombre_cliente', '---')}"
            all_ventas.append(v)
            
        if not all_ventas:
            st.info("No hay ventas registradas para mostrar.")
        else:
            df_all = pd.DataFrame(all_ventas)
            # Ordenar por fecha_venta descendente
            if 'fecha_venta' in df_all.columns:
                df_all['fecha_venta'] = pd.to_datetime(df_all['fecha_venta'])
                df_all = df_all.sort_values(by='fecha_venta', ascending=False)
            
            # Limpieza de columnas para visualización
            cols_show = ['fecha_venta', 'tipo', 'entidad', 'tour_nombre', 'precio_total_cierre', 'moneda', 'estado_pago']
            
            # --- NUEVO: TABLA CON TACHITO (ELIMINAR) ---

            # Encabezado de la tabla manual
            h1, h2, h3, h4, h5, h6 = st.columns([1.2, 1.2, 2.5, 3.0, 1.0, 0.5])
            h1.markdown("**🗓️ Fecha**")
            h2.markdown("**🏷️ Tipo**")
            h3.markdown("**👤 Cliente / Agencia**")
            h4.markdown("**🚙 Tour / Paquete**")
            h5.markdown("**💰 Total**")
            h6.markdown("**🗑️**")
            st.divider()

            for idx, row in df_all.head(15).iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 2.5, 3.0, 1.0, 0.5])
                
                f_v = row['fecha_venta'].strftime('%Y-%m-%d') if hasattr(row['fecha_venta'], 'strftime') else str(row['fecha_venta'])
                
                entidad_str = row['entidad']
                tour_str = row['tour_nombre']
                if row.get('estado_venta') == 'CANCELADO':
                    entidad_str = f"❌ <s>{entidad_str}</s> <span style='color:#ff4b4b; font-weight:bold;'>(CANCELADO)</span>"
                    tour_str = f"<s>{tour_str}</s>"
                
                c1.markdown(f"<small>{f_v}</small>", unsafe_allow_html=True)
                c2.markdown(f"<small>{row['tipo']}</small>", unsafe_allow_html=True)
                c3.markdown(f"<small>{entidad_str}</small>", unsafe_allow_html=True)
                c4.markdown(f"<small>{tour_str}</small>", unsafe_allow_html=True)
                c5.markdown(f"<small>{row['moneda']} {row['precio_total_cierre']:,.2f}</small>", unsafe_allow_html=True)
                
                # Botón de eliminar con confirmación simple
                if c6.button("🗑️", key=f"btn_del_{row['id_venta']}", help=f"Eliminar venta {row['id_venta']}"):
                    st.session_state[f"confirm_del_{row['id_venta']}"] = True

                if st.session_state.get(f"confirm_del_{row['id_venta']}"):
                    st.warning(f"¿Eliminar venta de {row['entidad']}?")
                    col_si, col_no = st.columns(2)
                    if col_si.button("SÍ, ELIMINAR", key=f"si_{row['id_venta']}"):
                        exito, msg = venta_ctrl.eliminar_venta(row['id_venta'])
                        if exito:
                            st.success(msg)
                            st.session_state[f"confirm_del_{row['id_venta']}"] = False
                            st.rerun()
                        else:
                            st.error(msg)
                    if col_no.button("CANCELAR", key=f"no_{row['id_venta']}"):
                        st.session_state[f"confirm_del_{row['id_venta']}"] = False
                        st.rerun()
                st.divider()

            if len(all_ventas) > 15:
                st.info("💡 Se muestran las 15 ventas más recientes. Para ver el historial completo, use el módulo de Reportes.")

def render_ops_dashboard_visual(supabase_client):
    """Vista visual para Operaciones con Tablero Diario."""
    st.title("⚙️ Visión General de Operaciones")
    
    # Modo En Vivo (Auto-refresh manual)
    c_live, _ = st.columns([1, 4])
    live_mode = c_live.toggle("🛰️ Modo en Vivo", help="Refresca los datos automáticamente cada 60 segundos", key="ops_live")
    if live_mode:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=60 * 1000, key="ops_refresh_counter")

    from controllers.operaciones_controller import OperacionesController
    controller = OperacionesController(supabase_client)
    
    t1, t2 = st.tabs(["📉 Resumen Operativo", "📅 Tablero de Planificación"])
    
    with t1:
        servicios_hoy = controller.get_servicios_por_fecha(date.today())
        len_hoy = len(servicios_hoy) if servicios_hoy else 0
        st.metric("Servicios para Hoy", len_hoy)
        
        from vistas.dashboard_analytics import render_operations_dashboard
        data_ops = controller.get_data_for_analytics()
        df_servicios = pd.DataFrame(data_ops) if data_ops else pd.DataFrame()
        render_operations_dashboard(df_servicios)
        


    with t2:
        # Aquí integramos el calendario (Tablero Diario)
        render_tablero_diario_visual(controller)

def render_tablero_diario_visual(controller):
    """Lógica del calendario centralizada - consume de page_operaciones."""
    from vistas.page_operaciones import dashboard_tablero_diario
    dashboard_tablero_diario(controller)


def render_contable_dashboard_visual(supabase_client):
    """Vista visual para Contabilidad."""
    st.title("🏦 Dashboard Financiero")
    
    # Modo En Vivo (Auto-refresh manual)
    c_live, _ = st.columns([1, 4])
    live_mode = c_live.toggle("🛰️ Modo en Vivo", help="Refresca los datos automáticamente cada 60 segundos", key="fin_live")
    if live_mode:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=60 * 1000, key="fin_refresh_counter")

    reporte_ctrl = ReporteController(supabase_client)
    from vistas.dashboard_analytics import render_financial_dashboard
    
    df_ventas, df_reqs = reporte_ctrl.get_data_for_dashboard()
    render_financial_dashboard(df_ventas, df_reqs)
    
    st.divider()
    st.write("### 📋 Últimas Transacciones")
    if not df_ventas.empty:
        # Usar nombres de columnas correctos según esquema SQL
        cols_to_show = ['id_venta', 'monto_total', 'estado_venta', 'vendedor']
        # Verificar que las columnas existan antes de filtrar (robusto)
        available_cols = [c for c in cols_to_show if c in df_ventas.columns]
        st.dataframe(df_ventas[available_cols].head(10), use_container_width=True, hide_index=True)
        


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
    from controllers.operaciones_controller import OperacionesController
    from vistas.page_operaciones import render_centro_alertas
    ctrl_op = OperacionesController(supabase_client)
    render_centro_alertas(ctrl_op)
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
        
    # --- OPTIMIZACIÓN: Cargar datos una sola vez para evitar errores de conexión (ConnectionTerminated) ---
    try:
        res_ventas = supabase_client.table('venta').select('*, cliente(*), pasajero(nacionalidad, es_principal)').order('fecha_venta', desc=True).execute()
        ventas_data = res_ventas.data or []
        res_pagos = supabase_client.table('pago').select('*').order('fecha_pago', desc=False).execute()
        pagos_data = res_pagos.data or []
    except Exception as e:
        st.error(f"Error cargando datos globales: {e}")
        ventas_data, pagos_data = [], []

    # Render Master Sales Table B2C for all roles
    render_master_sales_table_visual(ventas_data, pagos_data)

    # Render B2B list ONLY for Operaciones, Contabilidad, Ejecutivo
    permitidos_b2b = ["Operaciones", "Contable", "Ejecutivo"]
    if any(p in funcionalidad_seleccionada for p in permitidos_b2b):
        render_b2b_sales_table_visual(ventas_data, pagos_data)

def procesar_datos_tabla(ventas_data, pagos_data, anio_sel=None, mes_sel=None, filtro_tipo=None):
    """Función unificada para formatear las ventas en el DataFrame de los reportes."""
    pagos_por_venta = {}
    for p in pagos_data:
        id_v = p.get('id_venta')
        if id_v not in pagos_por_venta:
            pagos_por_venta[id_v] = []
        pagos_por_venta[id_v].append(p)

    data_rows = []
    from datetime import datetime
    for v in ventas_data:
        # Filtrar B2C o B2B
        es_b2b = bool(v.get('id_agencia_aliada'))
        tipo = "B2B" if es_b2b else "B2C"
        
        if filtro_tipo and tipo != filtro_tipo:
            continue

        f_venta_str = v.get('fecha_venta')
        if not f_venta_str: continue
        
        if anio_sel and mes_sel:
            try:
                f_obj = datetime.strptime(f_venta_str.split('T')[0], '%Y-%m-%d').date()
                if f_obj.year != anio_sel or f_obj.month != mes_sel:
                    continue
            except:
                continue
            
        cliente_info = v.get('cliente') or {}
        nombre_pax = v.get('nombre_cliente') or cliente_info.get('nombre', 'Desconocido')
        
        # Para B2B mostramos también el nombre de la agencia
        if es_b2b:
            agencia = v.get('nombre_agencia') or 'Agencia'
            pax = f"{agencia} / {nombre_pax} x {v.get('num_pasajeros', 1)}"
        else:
            pax = f"{nombre_pax} x {v.get('num_pasajeros', 1)}"
        
        moneda_venta = v.get('moneda', 'USD')
        monto_orig = float(v.get('precio_total_cierre') or 0.0)
        tc = float(v.get('tipo_cambio') or 3.80)
        
        if moneda_venta == 'USD':
            monto_total_usd = monto_orig
            monto_total_pen = monto_orig * tc
        else:
            monto_total_pen = monto_orig
            monto_total_usd = monto_orig / tc if tc > 0 else 0.0

        lista_pagos = pagos_por_venta.get(v.get('id_venta'), [])
        lista_pagos = [p for p in lista_pagos if p.get('tipo_pago') != 'REEMBOLSO']
        
        total_pagado_pen, total_pagado_usd = 0.0, 0.0
        for p in lista_pagos:
            p_moneda = p.get('moneda', moneda_venta)
            p_monto = float(p.get('monto_pagado') or 0.0)
            if p_moneda == 'USD':
                total_pagado_usd += p_monto
                total_pagado_pen += p_monto * tc
            else:
                total_pagado_pen += p_monto
                total_pagado_usd += p_monto / tc if tc > 0 else 0.0
        
        dif_pen = monto_total_pen - total_pagado_pen
        dif_usd = monto_total_usd - total_pagado_usd
        
        estado = str(v.get('estado_venta', 'CONFIRMADO')).upper()
        
        # Extraer nacionalidad desde PASAJEROS (tabla pasajero), no del lead
        nacionalidad = ""
        pax_info = v.get('pasajero', [])
        if pax_info and isinstance(pax_info, list):
            # Prioridad: pasajero marcado como principal, si no el primero
            principal = next((p for p in pax_info if p.get('es_principal')), pax_info[0])
            nacionalidad = str(principal.get('nacionalidad') or '').upper()
                
        data_rows.append({
            "FECHA": f_venta_str,
            "PAX": pax,
            "NACIONALIDAD": nacionalidad,
            "TOUR": v.get('fecha_inicio', ''),
            "TOTAL S/": round(monto_total_pen, 2),
            "TOTAL $": round(monto_total_usd, 2),
            "PAGADO S/": round(total_pagado_pen, 2),
            "PAGADO $": round(total_pagado_usd, 2),
            "SALDO S/": round(dif_pen, 2),
            "SALDO $": round(dif_usd, 2),
            "ESTADO": estado,
            "TIPO": tipo
        })
    return data_rows

def render_master_sales_table_visual(ventas_data, pagos_data):
    """Renderiza una tabla visual con el Reporte Maestro de Ventas DIRECTAS (B2C), filtrable por mes."""
    st.divider()
    st.markdown("### 📊 Reporte Maestro de Ventas (Directas - B2C)")
    st.caption("Visión detallada de las ventas directas del mes. Disponible para todas las áreas.")
    
    col_mes, col_anio, _ = st.columns([1, 1, 3])
    
    meses_opciones = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    with col_mes:
        mes_sel_nombre = st.selectbox("Mes Reporte", list(meses_opciones.values()), index=date.today().month - 1, key="master_mes_b2c")
        mes_sel = [k for k, v in meses_opciones.items() if v == mes_sel_nombre][0]
    
    with col_anio:
        anio_actual = date.today().year
        anios_opciones = list(range(anio_actual - 2, anio_actual + 3))
        anio_sel = st.selectbox("Año Reporte", anios_opciones, index=anios_opciones.index(anio_actual), key="master_anio_b2c")

    data_rows = procesar_datos_tabla(ventas_data, pagos_data, anio_sel=anio_sel, mes_sel=mes_sel, filtro_tipo="B2C")

    if data_rows:
        df = pd.DataFrame(data_rows)
        def highlight_cancelled(row):
            if row['ESTADO'] == 'CANCELADO':
                return ['background-color: #FEE2E2; color: #991B1B'] * len(row)
            return [''] * len(row)
        
        styled_df = df.style.apply(highlight_cancelled, axis=1).format({
            "TOTAL S/": "{:,.2f}", "TOTAL $": "{:,.2f}", 
            "PAGADO S/": "{:,.2f}", "PAGADO $": "{:,.2f}", 
            "SALDO S/": "{:,.2f}", "SALDO $": "{:,.2f}"
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay ventas B2C registradas para este periodo.")

def render_b2b_sales_table_visual(ventas_data, pagos_data):
    """Renderiza una tabla visual con el Reporte Maestro de Ventas de AGENCIAS (B2B), sin selector de fecha."""
    st.divider()
    st.markdown("### 🤝 Registro Consolidado de Agencias (B2B)")
    st.caption("Visión global e histórica de todas las ventas B2B. Acceso restringido.")

    # No pasamos anio_sel ni mes_sel, para mostrar TODAS.
    data_rows = procesar_datos_tabla(ventas_data, pagos_data, anio_sel=None, mes_sel=None, filtro_tipo="B2B")

    if data_rows:
        df = pd.DataFrame(data_rows)
        def highlight_cancelled(row):
            if row['ESTADO'] == 'CANCELADO':
                return ['background-color: #FEE2E2; color: #991B1B'] * len(row)
            return [''] * len(row)
        
        styled_df = df.style.apply(highlight_cancelled, axis=1).format({
            "TOTAL S/": "{:,.2f}", "TOTAL $": "{:,.2f}", 
            "PAGADO S/": "{:,.2f}", "PAGADO $": "{:,.2f}", 
            "SALDO S/": "{:,.2f}", "SALDO $": "{:,.2f}"
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay ventas B2B registradas en el sistema.")
