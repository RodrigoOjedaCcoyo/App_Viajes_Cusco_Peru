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
            xlsx_b = xl_ctrl.generar_resumen_itinerario_xlsx(render)
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
    
    # Llamar al renderizador de objetivos visuales (Gauge Chart)
    from vistas.dashboard_analytics import render_sales_dashboard
    render_sales_dashboard(df_ventas)

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
        
        # --- 🔍 VERIFICADOR DE INCLUSIONES (ESTILO IMAGEN) ---
        st.markdown("---")
        st.subheader("🏁 Verificador de Inclusiones (Itinerario)")
        
        if not df_servicios.empty:
            # Mapeo defensivo para el itinerario
            col_itin = 'ID Itinerario' if 'ID Itinerario' in df_servicios.columns else 'id_itinerario_digital'
            
            if col_itin in df_servicios.columns:
                # Filtrar solo los que tienen itinerario
                ventas_itin = df_servicios[df_servicios[col_itin].notna()]
                id_itin_audit_ops = None
                if not ventas_itin.empty:
                    # Usar selectbox para elegir cliente/venta
                    # Nota: 'ID Venta' es el nombre en Operaciones
                    col_id_v = 'ID Venta' if 'ID Venta' in df_servicios.columns else 'id_venta'
                    
                    sel_v_id_ops = st.selectbox("Auditar Itinerario de la Venta:", 
                                             ventas_itin[col_id_v].unique(),
                                             format_func=lambda x: f"{ventas_itin[ventas_itin[col_id_v]==x]['Cliente'].values[0]} ({x})",
                                             key="sb_dash_ops_audit")
                    
                    # Obtener el UUID del itinerario
                    id_itin_audit_ops = ventas_itin[ventas_itin[col_id_v] == sel_v_id_ops][col_itin].iloc[0]
                
                if id_itin_audit_ops:
                    res_itin_ops = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_audit_ops).single().execute()
                    if res_itin_ops.data:
                        render_itinerary_details_visual(res_itin_ops.data['datos_render'])
            else:
                st.info("No hay servicios con itinerario digital para auditar en este periodo.")
        else:
            st.info("No hay servicios operativos registrados.")

    with t2:
        # Aquí integramos el calendario (Tablero Diario)
        render_tablero_diario_visual(controller)

def render_tablero_diario_visual(controller):
    """Lógica del calendario adaptada para visualización."""
    if 'cal_current_date' not in st.session_state:
        st.session_state['cal_current_date'] = date.today()
    if 'cal_selected_date' not in st.session_state:
        st.session_state['cal_selected_date'] = date.today()
    if 'view_mode' not in st.session_state:
        st.session_state['view_mode'] = "Mensual"

    v_mode = st.radio("Modo de Vista:", ["Mensual", "Semanal"], horizontal=True, key="dashboard_ops_mode")
    st.session_state['view_mode'] = v_mode

    current_date = st.session_state['cal_current_date']
    year, month = current_date.year, current_date.month
    nombres_meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    if st.session_state['view_mode'] == "Mensual":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("◀ Mes Ant", key="btn_prev_m"):
                m, y = (12, year-1) if month == 1 else (month-1, year)
                st.session_state['cal_current_date'] = date(y, m, 1)
                st.rerun()
        with c2: st.markdown(f"<h3 style='text-align:center;'>{nombres_meses[month]} {year}</h3>", unsafe_allow_html=True)
        with c3:
            if st.button("Mes Sig ▶", key="btn_next_m"):
                m, y = (1, year+1) if month == 12 else (month+1, year)
                st.session_state['cal_current_date'] = date(y, m, 1)
                st.rerun()

        cal_grid = calendar.monthcalendar(year, month)
        fechas_activas = controller.get_fechas_con_servicios(year, month)
        
        cols = st.columns(7)
        for i, h in enumerate(['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']): 
            cols[i].markdown(f"<center><b>{h}</b></center>", unsafe_allow_html=True)
            
        for week in cal_grid:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    d_obj = date(year, month, day)
                    sel = (d_obj == st.session_state['cal_selected_date'])
                    act = d_obj in fechas_activas
                    lbl = f"{day}{' 🟢' if act else ''}"
                    if cols[i].button(lbl, key=f"dash_d_{d_obj}", use_container_width=True, type="primary" if sel else "secondary"):
                        st.session_state['cal_selected_date'] = d_obj
                        st.rerun()
    else:
        # Vista Semanal (Lectura)
        d_sel = st.session_state['cal_selected_date']
        lunes = d_sel - timedelta(days=d_sel.weekday())
        domingo = lunes + timedelta(days=6)
        servicios_w = controller.get_servicios_rango_fechas(lunes, domingo)
        
        cols_w = st.columns(7)
        for i, h in enumerate(['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']):
            f_dia = lunes + timedelta(days=i)
            with cols_w[i]:
                st.markdown(f"<div style='text-align:center;'><b>{h} {f_dia.day}</b></div>", unsafe_allow_html=True)
                s_dia = [s for s in servicios_w if s['Fecha'] == f_dia.isoformat()]
                for s in s_dia:
                    st.caption(f"📍 {s['Servicio']}\n({s['Cliente']})")

    # Detalle Diario (Lectura)
    f_p = st.session_state['cal_selected_date']
    st.write(f"### 📋 Servicios: {f_p}")
    servicios = controller.get_servicios_por_fecha(f_p)
    if servicios:
        st.dataframe(pd.DataFrame(servicios)[['Hora', 'Servicio', 'Pax', 'Cliente', 'Proveedor']], hide_index=True, use_container_width=True)
    else:
        st.info("Sin operaciones para esta fecha.")


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
        
        # Mapeo defensivo para Contabilidad
        col_itin_cont = 'id_itinerario_digital' if 'id_itinerario_digital' in df_ventas.columns else 'id_itinerario'
        
        # --- 🔍 VERIFICADOR DE INCLUSIONES (ESTILO IMAGEN) ---
        st.markdown("---")
        st.subheader("🏁 Verificador de Inclusiones (Itinerario)")
        
        if col_itin_cont in df_ventas.columns:
            ventas_con_itin = df_ventas[df_ventas[col_itin_cont].notna()]
            id_itin_audit = None
            if not ventas_con_itin.empty:
                sel_v_id = st.selectbox("Auditar Itinerario de la Venta:", 
                                      ventas_con_itin['id_venta'].unique(),
                                      format_func=lambda x: f"{ventas_con_itin[ventas_con_itin['id_venta']==x]['cliente_nombre'].values[0]} ({x})",
                                      key="sb_dash_cont_audit")
                
                # Obtener el UUID del itinerario
                id_itin_audit = ventas_con_itin[ventas_con_itin['id_venta'] == sel_v_id][col_itin_cont].iloc[0]
            
            if id_itin_audit:
                res_itin = reporte_ctrl.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_audit).single().execute()
                if res_itin.data:
                    render_itinerary_details_visual(res_itin.data['datos_render'])
        else:
            st.info("No hay ventas con itinerarios registrados para auditar.")

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
