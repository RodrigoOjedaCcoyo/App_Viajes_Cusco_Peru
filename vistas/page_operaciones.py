# vistas/page_operaciones.py

import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import date, timedelta
import urllib.parse
from controllers.operaciones_controller import OperacionesController
from controllers.venta_controller import VentaController

# Renderiza el Botón para el PDF del Itinerario Simple.
def render_itinerary_simple_download(render):
    if not render:
        st.warning("No hay datos de itinerario para descargar.")
        return

    from controllers.pdf_controller import PDFController
    pdf_ctrl = PDFController()
    
    from controllers.excel_controller import ExcelController
    xl_ctrl = ExcelController()
    
    with st.container(border=True):
        st.markdown(f"#### 📄 Resumen de Viaje: {render.get('titulo', 'Sin Título')}")
        st.info("Este documento es una versión simplificada (Ink Saver) ideal para imprimir y para el personal operativo.")
        
        c1, c2 = st.columns(2)
        
        with c1:
            # Generar el PDF en memoria
            pdf_buffer = pdf_ctrl.generar_itinerario_simple_pdf(render)
            if pdf_buffer:
                st.download_button(
                    label="📥 Bajar Resumen (PDF Simple)",
                    data=pdf_buffer,
                    file_name=f"resumen_viaje_{render.get('titulo', 'itinerario')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with c2:
            # Generar el Excel en memoria
            xlsx_buffer = xl_ctrl.generar_resumen_itinerario_xlsx(render)
            if xlsx_buffer:
                st.download_button(
                    label="📊 Bajar Resumen (Excel XLSX)",
                    data=xlsx_buffer,
                    file_name=f"resumen_viaje_{render.get('titulo','itin')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        if not pdf_buffer and not xlsx_buffer:
            st.error("No se pudo generar el documento en este momento.")

# Dashboard 2: Tablero con vistas Duplicadas (Mensual/Semanal).
def dashboard_tablero_diario(controller):
    """Dashboard 2: Tablero con vistas Duplicadas (Mensual/Semanal)."""
    st.subheader("2️⃣ Tablero de Planificación Logística", divider='green')
    
    if 'cal_current_date' not in st.session_state:
        st.session_state['cal_current_date'] = date.today()
    if 'cal_selected_date' not in st.session_state:
        st.session_state['cal_selected_date'] = date.today()
    if 'view_mode' not in st.session_state:
        st.session_state['view_mode'] = "Mensual"

    v_mode = st.radio("Filtro de Vista:", ["Mensual", "Semanal"], 
                      index=0 if st.session_state['view_mode'] == "Mensual" else 1, horizontal=True)
    st.session_state['view_mode'] = v_mode

    current_date = st.session_state['cal_current_date']
    year, month = current_date.year, current_date.month
    nombres_meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    if st.session_state['view_mode'] == "Mensual":
        # --- MES ---
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("◀ Mes Ant"):
                m, y = (12, year-1) if month == 1 else (month-1, year)
                st.session_state['cal_current_date'] = date(y, m, 1)
                st.rerun()
        with c2:
            st.markdown(f"<h3 style='text-align:center;'>{nombres_meses[month]} {year}</h3>", unsafe_allow_html=True)
        with c3:
            if st.button("Mes Sig ▶"):
                m, y = (1, year+1) if month == 12 else (month+1, year)
                st.session_state['cal_current_date'] = date(y, m, 1)
                st.rerun()

        st.markdown("---")
        cal_grid = calendar.monthcalendar(year, month)
        fechas_activas = controller.get_fechas_con_servicios(year, month)
        
        cols = st.columns(7)
        headers = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        for i, h in enumerate(headers): cols[i].markdown(f"<center><b>{h}</b></center>", unsafe_allow_html=True)
            
        for week in cal_grid:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    d_obj = date(year, month, day)
                    sel = (d_obj == st.session_state['cal_selected_date'])
                    act = d_obj in fechas_activas
                    lbl = f"{day}{' 🟢' if act else ''}"
                    if d_obj == date.today(): lbl += "\n(Hoy)"
                    if cols[i].button(lbl, key=f"d_{d_obj}", use_container_width=True, type="primary" if sel else "secondary"):
                        st.session_state['cal_selected_date'] = d_obj
                        st.rerun()

    else:
        # --- SEMANA ---
        d_sel = st.session_state['cal_selected_date']
        lunes = d_sel - timedelta(days=d_sel.weekday())
        domingo = lunes + timedelta(days=6)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("◀ Semana Ant"):
                st.session_state['cal_selected_date'] -= timedelta(days=7)
                st.rerun()
        with c2:
            st.markdown(f"<h3 style='text-align:center;'>Semana de {lunes.day} {nombres_meses[lunes.month]}</h3>", unsafe_allow_html=True)
        with c3:
            if st.button("Semana Sig ▶"):
                st.session_state['cal_selected_date'] += timedelta(days=7)
                st.rerun()
        
        st.markdown("---")
        servicios_w = controller.get_servicios_rango_fechas(lunes, domingo)
        cols_w = st.columns(7)
        headers_w = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        
        for i in range(7):
            f_dia = lunes + timedelta(days=i)
            with cols_w[i]:
                estilo = f"background:{'#1E88E5' if f_dia==date.today() else '#444'}; padding:5px; border-radius:5px; text-align:center; margin-bottom:5px;"
                st.markdown(f"<div style='{estilo}'><small>{headers_w[i]}</small><br><b>{f_dia.day}</b></div>", unsafe_allow_html=True)
                
                s_dia = [s for s in servicios_w if s['Fecha'] == f_dia.isoformat()]
                if not s_dia:
                    st.markdown("<p style='text-align:center; color:gray; font-size:10px;'>Vacío</p>", unsafe_allow_html=True)
                else:
                    for s in s_dia:
                        with st.container(border=True):
                            # Título con indicador de endoso
                            titulo_serv = f"🤝 {s['Servicio']}" if s.get('Endoso?') else s['Servicio']
                            st.markdown(f"<p style='font-size:11px; margin:0;'><b>{titulo_serv}</b></p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='font-size:9px; margin:0; color:#aaa;'>{s['Cliente']} ({s['Pax']} Pax)</p>", unsafe_allow_html=True)
                            
                            # Responsable (Guía o Agencia)
                            responsable = f"🏢 {s['Agencia Endoso']}" if s.get('Endoso?') else f"👮 {s['Guía']}"
                            st.markdown(f"<p style='font-size:9px; margin:0;'>{responsable}</p>", unsafe_allow_html=True)
                
                if st.button("Ver", key=f"v_{f_dia}", use_container_width=True):
                    st.session_state['cal_selected_date'] = f_dia
                    st.rerun()

    # --- DETALLE ---
    st.markdown("---")
    f_p = st.session_state['cal_selected_date']
    st.markdown(f"### 📋 Detalle: {f_p.day} de {nombres_meses[f_p.month]} de {f_p.year}")
    
    servicios = controller.get_servicios_por_fecha(f_p)
    if not servicios:
        st.info("Sin operaciones este día.")
    else:
        pax_val = 0
        try: pax_val = sum(int(s.get('Pax') or 0) for s in servicios)
        except: pass
        st.success(f"Pax totales: {pax_val}")
        df = pd.DataFrame(servicios)
        st.dataframe(
            df,
            column_order=('Log.', 'Hora', 'Día Itin.', 'Servicio', 'Pax', 'Endoso?', 'Proveedor', 'Estado Pago', 'Cliente', 'URL Cloud'),
            column_config={
                "Log.": st.column_config.TextColumn("Log.", width="small"),
                "Día Itin.": st.column_config.NumberColumn("Día", format="%d", width="small"),
                "URL Cloud": st.column_config.LinkColumn("PDF 📄"),
            },
            hide_index=True, use_container_width=True
        )
        st.info("💡 La logística se consulta aquí. Para editarla, usa el Google Sheet Maestro.")

        # --- 🔍 DESGLOSE DETALLADO DE RESPONSABLES ---
        with st.expander("🕵️ Ver Responsables Detallados (Minuto a Minuto)", expanded=False):
            st.markdown("---")
            for idx, s in df.iterrows():
                # Título del servicio
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{s['Hora']} - {s['Servicio']}**")
                    st.caption(f"Cliente: {s['Cliente']} ({s['Pax']} Pax)")
                with c2:
                    st.caption(f"ID: {s.get('ID Servicio', '---')}")
                
                # Lista de proveedores asignados
                detalles = s.get('Detalle Proveedores', [])
                if not detalles:
                    st.warning("⚠️ No hay proveedores detallados asignados en el Master Sheet.")
                else:
                    # Crear una pequeña tabla visual con HTML para que sea bien compacta
                    rows_html = ""
                    for d in detalles:
                        tipo_icon = "👮" if "GUIA" in d['tipo'] else "🚍" if "TRANS" in d['tipo'] else "🍴" if "ALMUERZO" in d['tipo'] else "🎟️"
                        color_estado = "#81C784" if d['estado'] == 'PAGADO' else "#FFB74D"
                        rows_html += f"<tr>" \
                                     f"<td style='padding:5px; font-size:12px;'>{tipo_icon} <b>{d['tipo']}</b></td>" \
                                     f"<td style='padding:5px; font-size:12px;'>{d['nombre']}</td>" \
                                     f"<td style='padding:5px; font-size:10px;'><span style='background:{color_estado}; padding:2px 5px; border-radius:3px; color:black;'>{d['estado']}</span></td>" \
                                     f"</tr>"
                    
                    st.markdown(f"""
                    <table style='width:100%; border-collapse: collapse; margin-bottom:10px;'>
                        <tr style='background: rgba(255,255,255,0.05);'>
                            <th style='text-align:left; padding:5px; font-size:11px;'>ÁREA</th>
                            <th style='text-align:left; padding:5px; font-size:11px;'>PROVEEDOR / RESPONSABLE</th>
                            <th style='text-align:left; padding:5px; font-size:11px;'>ESTADO</th>
                        </tr>
                        {rows_html}
                    </table>
                    """, unsafe_allow_html=True)
                
                st.divider()

        # --- 🔍 DETALLE VISUAL DEL ITINERARIO (ESTILO IMAGEN) ---
        st.markdown("---")
        st.subheader("🏁 Detalle de Inclusiones del Programa")
        
        # Seleccionar una venta para ver su itinerario completo si existe
        ventas_unicas = df[['ID Venta', 'Cliente']].drop_duplicates()
        if not ventas_unicas.empty:
            sel_v = st.selectbox("Seleccione cliente para ver detalle de su programa:", 
                                 ventas_unicas['ID Venta'].tolist(),
                                 format_func=lambda x: f"{ventas_unicas[ventas_unicas['ID Venta']==x]['Cliente'].values[0]} (ID: {x})")
            
            # Obtener el ID del itinerario digital de esta venta
            id_itin_sel = df[df['ID Venta'] == sel_v]['ID Itinerario'].dropna().unique()
            
            if len(id_itin_sel) > 0 and id_itin_sel[0]:
                res_itin = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_sel[0]).single().execute()
                if res_itin.data:
                    render_itinerary_simple_download(res_itin.data['datos_render'])
            else:
                st.warning("Esta venta no tiene un itinerario digital vinculado.")

def generar_mensaje_whatsapp(data):
    """Genera un link de WhatsApp con el mensaje formateado."""
    texto = f"Hola, soy de la Agencia. Aquí el detalle de tu servicio:\n\n"
    texto += f"Servicio: {data['Servicio']}\n"
    texto += f"Cliente: {data['Cliente']}\n"
    texto += f"Fecha: {data['Fecha']}\n"
    texto += f"Guía: {data['Guía']}"
    
    url = f"https://wa.me/?text={urllib.parse.quote(texto)}"
    return url


def registro_ventas_proveedores(supabase_client):
    from controllers.itinerario_digital_controller import ItinerarioDigitalController
    venta_controller = VentaController(supabase_client)
    it_controller = ItinerarioDigitalController(supabase_client)

    st.subheader("🤝 Registro de Venta para Proveedores (B2B)")
    
    # --- 🆔 SELECTOR DE ITINERARIO (FILTRADO SOLO B2B) ---
    itinerarios_raw = it_controller.obtener_todos_recientes(limit=50)
    
    import json
    itinerarios = []
    for it in itinerarios_raw:
        render = it.get('datos_render', {})
        # Robustez: Si viene como string, intentar parsear
        if isinstance(render, str):
            try: render = json.loads(render)
            except: render = {}
        
        # Verificar marca B2B (Checkbox, Canal o palabra clave en títulos)
        meta = render.get('metadata', {})
        tipo = meta.get('tipo_venta', 'B2C')
        canal = str(render.get('canal', '')).upper()
        
        # Juntar todos los títulos posibles para la búsqueda
        full_title = f"{render.get('titulo', '')} {render.get('title_1', '')} {render.get('title_2', '')}".upper()
        
        if tipo == 'B2B' or canal == 'B2B' or "B2B" in full_title:
            itinerarios.append(it)
    
    opciones_it = ["--- Sin Itinerario / Registro Manual ---"]
    mapa_it = {}
    
    for it in itinerarios:
        uuid = it.get('id_itinerario_digital')
        render = it.get('datos_render', {})
        if isinstance(render, str): 
            try: render = json.loads(render)
            except: render = {}
            
        t1, t2 = render.get('title_1', ''), render.get('title_2', '')
        titulo = render.get('titulo') or (f"{t1} {t2}").strip() or "Sin Título"
        pax = it.get('nombre_pasajero_itinerario') or render.get('pasajero', 'Sin Nombre')
        fecha = it.get('fecha_generacion', '')[:10]
        
        # Obtener celular si existe (viene del join extra)
        celular = it.get('lead', {}).get('numero_celular', '') if it.get('lead') else ''
        cel_label = f"📱 {celular} | " if celular else ""
        
        label = f"[{fecha}] {cel_label}{pax} - {titulo}"
        opciones_it.append(label)
        mapa_it[label] = it

    if not itinerarios:
        st.warning("⚠️ No se encontraron itinerarios recientes marcados como B2B. Asegúrese de marcar la casilla '🚩 Venta B2B / Agencia' al crear el itinerario en la sección de Ventas.")

    it_sel = st.selectbox("🎯 Vincular con un Itinerario Digital (B2B CLOUD)", opciones_it, 
                          help="Solo se muestran itinerarios creados específicamente para B2B.")
    
    id_itinerario_dig = None
    def_pax = ""
    def_tour = ""
    def_f_inicio = date.today()
    def_f_fin = date.today() + timedelta(days=1)
    def_cant_pax = 1
    def_precio_pax = 0.0  # Inicialización segura

    if it_sel != "--- Sin Itinerario / Registro Manual ---":
        it_data = mapa_it.get(it_sel)
        id_itinerario_dig = it_data.get('id_itinerario_digital')
        render = it_data.get('datos_render', {})
        if isinstance(render, str):
            try: render = json.loads(render)
            except: render = {}
        
        def_pax = it_data.get('nombre_pasajero_itinerario') or render.get('pasajero', '')
        def_tour = render.get('titulo') or (f"{render.get('title_1', '')} {render.get('title_2', '')}").strip()
        
        # Extraer Fechas (Soporta "fecha_viaje" y "fechas")
        f_inicio_str = render.get('fecha_viaje')
        if f_inicio_str:
            try: def_f_inicio = date.fromisoformat(f_inicio_str)
            except: pass
        else:
            # Intentar parsear desde "fechas" (ej: "DEL 19/01 AL 21/01, 2026")
            f_texto = render.get('fechas', '')
            if "DEL " in f_texto and ", " in f_texto:
                try:
                    partes = f_texto.split(", ")
                    anio = partes[1].strip()
                    dia_mes = partes[0].replace("DEL ", "").split(" AL ")[0]
                    dia, mes = dia_mes.split("/")
                    def_f_inicio = date(int(anio), int(mes), int(dia))
                except: pass
        
        # Calcular fecha fin desde duración
        duracion_raw = render.get('duracion')
        if duracion_raw and isinstance(duracion_raw, str) and 'D' in duracion_raw.upper():
            try:
                num_dias_str = ''.join(filter(str.isdigit, duracion_raw.split('D')[0]))
                if num_dias_str:
                    num_dias = int(num_dias_str)
                    def_f_fin = def_f_inicio + timedelta(days=num_dias - 1)
            except Exception as e:
                print(f"Error parsing duracion in B2B: {e}")
        elif "AL " in render.get('fechas', ''):
            # Intentar extraer fecha fin desde "fechas"
            try:
                f_texto = render.get('fechas', '')
                partes = f_texto.split(", ")
                anio = partes[1].strip()
                dia_mes_fin = partes[0].split(" AL ")[1]
                dia, mes = dia_mes_fin.split("/")
                def_f_fin = date(int(anio), int(mes), int(dia))
            except: pass
        
        # Extraer cantidad de pasajeros
        def_cant_pax = int(render.get('cantidad_pax') or 1)
        
        # Extraer precio desde estructura "precios" (ej: precios.nac.monto)
        def_precio_pax = 0.0
        precios = render.get('precios', {})
        if isinstance(precios, dict):
            # Intentar nacional primero, luego extranjero, luego CAN
            for tipo in ['nac', 'ext', 'can']:
                precio_obj = precios.get(tipo, {})
                if isinstance(precio_obj, dict) and precio_obj.get('monto'):
                    try:
                        def_precio_pax = float(precio_obj['monto'])
                        break
                    except: pass
        
        st.success(f"✅ Datos cargados del itinerario: **{def_tour}**")

    # --- 📝 FORMULARIO DE REGISTRO ---
    with st.form("form_registro_venta_proveedores_ops"):
        col1, col2 = st.columns(2)
        
        # Agencias
        agencias = venta_controller.obtener_agencias_aliadas()
        nombres_agencias = [a['nombre'] for a in agencias]
        mapa_agencias = {a['nombre']: a['id_agencia'] for a in agencias}
        
        proveedor_sel = col1.selectbox("Seleccione la Agencia / Proveedor", ["--- Seleccione ---"] + nombres_agencias)
        nombre_pax_final = col1.text_input("Nombre del Pasajero Principal", value=def_pax)
        
        c1a, c1b = col1.columns(2)
        f_inicio = c1a.date_input("Fecha Inicio", value=def_f_inicio)
        f_fin = c1b.date_input("Fecha Fin", value=def_f_fin)
        
        c1c, c1d = col1.columns(2)
        cant_pax = c1c.number_input("Total Pax", min_value=1, value=def_cant_pax)
        precio_pax = c1d.number_input("Precio Neto/Pax ($)", min_value=0.0, value=def_precio_pax, format="%.2f")

        # Catálogo vs Manual
        catalogo = venta_controller.obtener_catalogo_opciones()
        nombres_cat = ["--- Escribir Manualmente ---"] + [c['nombre'] for c in catalogo]
        mapa_cat = {c['nombre']: c['id'] for c in catalogo}
        
        # Intentar encontrar coincidencia en el catálogo
        idx_default = 0  # "--- Escribir Manualmente ---"
        if def_tour:
            for i, nombre in enumerate(nombres_cat):
                if def_tour.upper() in nombre.upper() or nombre.upper() in def_tour.upper():
                    idx_default = i
                    break
        
        item_sel = col2.selectbox("Clasificar como (Paquete Catálogo)", nombres_cat, index=idx_default)
        
        tour_manual = col2.text_input("Nombre del Tour / Servicio", value=def_tour, placeholder="Ej: Cusco Mágico")
        
        monto_neto_total = cant_pax * precio_pax
        col2.metric("Monto Neto a Cobrar", f"$ {monto_neto_total:,.2f}")
        monto_dep = col2.number_input("Adelanto Recibido ($)", min_value=0.0, value=0.0, format="%.2f")

        st.markdown("---")
        st.write("📂 **Documentación**")
        cf1, cf2 = st.columns(2)
        file_it = cf1.file_uploader("Itinerario (PDF)", type=['pdf'])
        file_pago = cf2.file_uploader("Voucher de Pago (Img/PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        submitted = st.form_submit_button("✅ REGISTRAR VENTA B2B", use_container_width=True)
        
        if submitted:
            if proveedor_sel == "--- Seleccione ---":
                st.error("❌ Seleccione una agencia.")
            elif not nombre_pax_final or (not item_sel and not tour_manual):
                st.error("❌ El nombre del pasajero y el tour son obligatorios.")
            else:
                id_age = mapa_agencias.get(proveedor_sel)
                # Si no seleccionó catálogo, usamos el texto manual
                id_tour_final = mapa_cat.get(item_sel) if item_sel != "--- Escribir Manualmente ---" else tour_manual
                
                exito, msg = venta_controller.registrar_venta_proveedor(
                    nombre_proveedor=proveedor_sel,
                    nombre_cliente=nombre_pax_final,
                    telefono="", 
                    vendedor=None,
                    tour=id_tour_final, 
                    monto_total=monto_neto_total,
                    monto_depositado=monto_dep,
                    id_agencia_aliada=id_age,
                    fecha_inicio=f_inicio,
                    fecha_fin=f_fin,
                    cantidad_pax=cant_pax,
                    id_itinerario_digital=id_itinerario_dig,
                    file_itinerario=file_it,
                    file_pago=file_pago
                )
                
                if exito: 
                    st.success(msg)
                    st.balloons()
                else: 
                    st.error(msg)

def reporte_operativo(controller):
    """Vista global de operaciones (Dashboard + Detalle)."""
    st.subheader("📊 Reporte Operativo Global", divider='blue')
    
    # 1. Dashboard de Analítica (Top)
    from vistas.dashboard_analytics import render_operations_dashboard
    df_ops = controller.get_data_for_analytics()
    render_operations_dashboard(df_ops)
    
    st.divider()
    
    # 2. Detalle de Operaciones (Auditoría)
    st.write("### 📋 Detalle de Servicios Programados")
    # Traer todos los servicios (no solo los de un día)
    range_start = date.today() - timedelta(days=30)
    range_end = date.today() + timedelta(days=60)
    todos_servicios = controller.get_servicios_rango_fechas(range_start, range_end)
    
    if not todos_servicios:
        st.info("No hay servicios registrados en el rango de tiempo seleccionado.")
    else:
        df_all = pd.DataFrame(todos_servicios)
        st.dataframe(
            df_all,
            column_order=("Fecha", "Servicio", "Tipo", "Pax", "Cliente", "Guía", "Estado Pago"),
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha"),
                "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                "Estado Pago": st.column_config.TextColumn("Pago")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 3. Vista Previa de Itinerario (Estilo Imagen)
        st.markdown("---")
        st.subheader("🏁 Verificador de Inclusiones (Itinerario)")
        
        if 'ID Itinerario' in df_all.columns:
            ventas_con_itin = df_all[df_all['ID Itinerario'].notna()]
            if not ventas_con_itin.empty:
                sel_id_v = st.selectbox("Auditar Itinerario de la Venta:", 
                                      ventas_con_itin['ID Venta'].unique(),
                                      format_func=lambda x: f"{ventas_con_itin[ventas_con_itin['ID Venta']==x]['Cliente'].values[0]} ({x})",
                                      key="sb_ops_audit_it")
                
                # Reutilizar lógica de detalle visual
                df_match = df_all[df_all['ID Venta'] == sel_id_v]
                id_itin_audit = df_match['ID Itinerario'].dropna().unique()[0] if not df_match['ID Itinerario'].dropna().empty else None
                
                if id_itin_audit:
                    res = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_audit).single().execute()
                    if res.data:
                        render_itinerary_simple_download(res.data['datos_render'])
            else:
                st.info("Seleccione un servicio con itinerario para ver su detalle.")

def mostrar_pagina(nombre_modulo, rol_actual, user_id, supabase_client):
    """Punto de entrada de Streamlit para el área de Operaciones."""
    controller = OperacionesController(supabase_client)
    
    st.title("⚙️ Gestión de Operaciones")
    st.markdown("---")
    
    if nombre_modulo == "Gestión de Registros":
        tab1, tab2, tab3 = st.tabs([
            "📊 Estructurador de Gastos (Master Sheet)",
            "📋 Rooming List (Pasajeros)",
            "🤝 Ventas B2B (Entrada)"
        ])
        
        with tab1:
            dashboard_simulador_costos(controller)
            
        with tab2:
            dashboard_pasajeros(controller)

        with tab3:
            registro_ventas_proveedores(supabase_client)

    elif nombre_modulo == "Dashboard Diario":
        dashboard_tablero_diario(controller)
    elif nombre_modulo == "Reporte Operativo":
        reporte_operativo(controller)
    else:
        st.info("Seleccione una opción válida del menú lateral.")
            
def dashboard_pasajeros(controller):
    """Gestión de Rooming List / Pasajeros."""
    st.subheader("📋 Lista de Pasajeros (Rooming List)", divider='blue')
    
    # 1. Selector de Venta (Idealmente global, pero por si acaso replicamos lógica local si no hay state)
    ventas_data = controller.obtener_ventas_pendientes() 
    if not ventas_data:
        st.info("No hay ventas activas para gestionar pasajeros.")
        return

    opciones_v = [f"{v['nombre_cliente']} | {v.get('tour_nombre','')} ({v['id_venta']})" for v in ventas_data]
    mapa_v = {opciones_v[i]: v for i, v in enumerate(ventas_data)}
    
    col_sel, _ = st.columns([2,1])
    sel_v = col_sel.selectbox("Seleccionar Grupo / Venta:", ["--- Seleccione ---"] + opciones_v, key="sel_pax_rooming")
    
    if sel_v != "--- Seleccione ---":
        v_act = mapa_v[sel_v]
        id_venta = v_act['id_venta']
        
        # 2. Cargar Pasajeros
        res_pax = controller.client.table('pasajero').select('*').eq('id_venta', id_venta).execute()
        df_pax = pd.DataFrame(res_pax.data)
        
        if df_pax.empty:
            # Crear filas vacías según num_pasajeros de la venta
            num_pax = v_act.get('num_pasajeros', 1)
            df_pax = pd.DataFrame([{
                'nombre_completo': '', 
                'numero_documento': '', 
                'nacionalidad': '', 
                'fecha_nacimiento': None,
                'cuidados_especiales': '',
                'es_principal': False
            } for _ in range(num_pax)])
        
        # 3. Editor
        col_cfg = {
            "nombre_completo": st.column_config.TextColumn("Nombre Completo", required=True, width="medium"),
            "numero_documento": st.column_config.TextColumn("Nro. Documento", width="small"),
            "nacionalidad": st.column_config.TextColumn("Nacionalidad", width="small"),
            "fecha_nacimiento": st.column_config.DateColumn("Fecha Nac.", width="small"),
            "cuidados_especiales": st.column_config.TextColumn("Dietas / Obs.", width="medium"),
            "es_principal": st.column_config.CheckboxColumn("Líder", default=False)
        }
        
        st.info("💡 Edita los datos de los pasajeros directamente en la tabla.")
        
        edited_pax = st.data_editor(
            df_pax,
            column_config=col_cfg,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_pax_{id_venta}",
            column_order=["nombre_completo", "numero_documento", "nacionalidad", "fecha_nacimiento", "cuidados_especiales", "es_principal"]
        )
        
        # 4. Guardar
        if st.button("💾 Guardar Lista de Pasajeros", type="primary"):
            updated = 0
            for i, row in edited_pax.iterrows():
                if row.get('nombre_completo'): # Solo guardar si tiene nombre
                    data_p = {
                        'id_venta': id_venta,
                        'nombre_completo': row['nombre_completo'],
                        'numero_documento': row.get('numero_documento'),
                        'nacionalidad': row.get('nacionalidad'),
                        'fecha_nacimiento': row.get('fecha_nacimiento').isoformat() if row.get('fecha_nacimiento') else None,
                        'cuidados_especiales': row.get('cuidados_especiales'),
                        'es_principal': row.get('es_principal', False)
                    }
                    
                    if 'id_pasajero' in row and pd.notna(row['id_pasajero']):
                        controller.client.table('pasajero').update(data_p).eq('id_pasajero', row['id_pasajero']).execute()
                    else:
                        controller.client.table('pasajero').insert(data_p).execute()
                    updated += 1
            
            if updated > 0:
                st.success(f"✅ Se actualizaron {updated} pasajeros para el grupo de {v_act['nombre_cliente']}.")
                st.rerun()
            
            


def dashboard_simulador_costos(controller):
    """
    Herramienta avanzada para estructurar liquidaciones de grupos/B2B.
    Basado en estructura de Excel (Unitario x Pax = Total).
    """
    st.subheader("📊 Estructurador de Liquidación Profesional", divider='rainbow')

    # Pre-cargar proveedores para evitar errores de scope
    prov_items = []
    try:
        res_prov = controller.client.table('proveedor').select('id_proveedor, nombre_comercial, servicios_ofrecidos').execute()
        prov_items = res_prov.data or []
    except Exception as e:
        print(f"Error cargando proveedores init: {e}")
    
    # Inicializar variables de scope
    ventas_age = []
    mapa_ventas_pax = {}
    pax_sel = "--- Seleccione ---"
    all_edited = pd.DataFrame()

    if 'simulador_data' not in st.session_state:
        st.session_state['simulador_data'] = [
            {"FECHA": date.today(), "SERVICIO": "Servicio Ejemplo", "MONEDA": "USD", "TOTAL": 0.0},
        ]

    st.info("💡 Selecciona el tipo de venta y luego la venta específica para cargar sus datos.")
    
    # Barra de Agencias (Existente)
    from controllers.venta_controller import VentaController
    vc = VentaController(controller.client)
    agencias = vc.obtener_agencias_aliadas()
    nombres_agencias = [a['nombre'] for a in agencias]
    mapa_agencias = {a['nombre']: a['id_agencia'] for a in agencias}
    
    # PASO 1: Seleccionar Tipo de Venta
    c_tipo, c_filtro, c_pax = st.columns([1, 2, 2])
    
    with c_tipo:
        tipo_venta = st.selectbox("1️⃣ Tipo de Venta:", ["--- Seleccione ---", "🏢 B2B (Agencias)", "👤 B2C (Directas)"], key="sel_tipo_venta")
    
    ventas_age = []
    agencia_sel = None
    
    # PASO 2: Filtro según tipo
    if tipo_venta == "🏢 B2B (Agencias)":
        with c_filtro:
            agencia_sel = st.selectbox("2️⃣ Seleccione Agencia:", ["--- Seleccione ---"] + nombres_agencias, key="sel_agencia_b2b")
        
        if agencia_sel != "--- Seleccione ---":
            id_ag = mapa_agencias.get(agencia_sel)
            ventas_age = vc.obtener_ventas_agencia(id_ag)
    
    elif tipo_venta == "👤 B2C (Directas)":
        with c_filtro:
            st.info("📋 Mostrando todas las ventas directas")
        ventas_age = vc.obtener_ventas_directas()
    
    # PASO 3: Seleccionar Venta Específica
    if ventas_age:
        opciones_pax = [f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})" for v in ventas_age]
        mapa_ventas_pax = {f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})": v for v in ventas_age}
        
        with c_pax:
            pax_sel = st.selectbox("3️⃣ Cargar Venta:", ["--- Seleccione ---"] + opciones_pax, key="sel_pax_sim")
        
        if pax_sel != "--- Seleccione ---":
            if st.button(f"📥 Cargar Itinerario de {pax_sel.split('|')[0].strip()}", use_container_width=True):
                v = mapa_ventas_pax.get(pax_sel)
                st.session_state['master_pax_count'] = v.get('num_pasajeros', 1)
                
                # 1. Ajustar Datos Globales (ya no necesarios pero mantenemos compatibilidad)
                
                # 2. Cargar Desglose de Servicios (Venta Tour)
                detalles = vc.obtener_detalles_itinerario_venta(v['id_venta'])
                
                if detalles:
                    nuevos_items = []
                    for d in detalles:
                        nuevos_items.append({
                            "FECHA": date.fromisoformat(d['fecha_servicio']),
                            "SERVICIO": d.get('observaciones') or "Servicio sin nombre",
                            "PROVEEDOR": next((f"{p['nombre_comercial']} ({p.get('servicios_ofrecidos', ['N/A'])[0]})" for p in prov_items if p['id_proveedor'] == d.get('id_proveedor')), "--- Sin Asignar ---"),
                            "MONEDA": d.get('moneda_costo', 'USD'),
                            "CANT": d.get('cantidad_items') or v.get('num_pasajeros', 1),
                            "UNIT": float(d.get('costo_unitario') or 0.0),
                            "TOTAL": float(d.get('costo_applied') or 0.0),
                            "VENTA": float(d.get('precio_applied') or 0.0),
                            "VTA_VENDEDOR": float(d.get('precio_vendedor') or d.get('precio_applied') or 0.0), # Jalamos el precio original del vendedor
                            "💵 Pago Op.": d.get('estado_pago_operativo', 'NO_REQUERIDO'),
                            "📝 Info Pago": d.get('datos_pago_operativo') or '',
                            "📎 Voucher": d.get('url_voucher_operativo', ''),
                            "id_venta": d['id_venta'],
                            "n_linea": d['n_linea'],
                            "ORIGINAL_SERVICE": d.get('observaciones') or "Servicio sin nombre"
                        })
                    st.session_state['simulador_data'] = nuevos_items
                    st.success(f"Itinerario de {len(detalles)} días cargado con éxito.")
                    st.rerun()
                else:
                    st.session_state['simulador_data'] = [
                        {"FECHA": date.fromisoformat(v['fecha_venta']) if v.get('fecha_venta') else date.today(), 
                         "SERVICIO": f"INGRESO B2B: {v['nombre_cliente']}", "MONEDA": "USD", "TOTAL": 0.0}
                    ]
                    st.warning("Venta cargada, pero no tiene itinerario expandido.")
                    st.rerun()

    # Data Editor (El "Excel" por Días)
    if 'simulador_data' not in st.session_state or not st.session_state['simulador_data']:
        st.info("Seleccione una venta para estructurar su liquidación.")
        return

    df_full = pd.DataFrame(st.session_state['simulador_data'])
    
    # Asegurar columnas nuevas y existentes
    required_cols = ["CANT", "UNIT", "VENTA", "VTA_VENDEDOR", "💵 Pago Op.", "📝 Info Pago", "📎 Voucher", "PROVEEDOR", "SERVICIO", "MONEDA", "TOTAL", "id_venta", "n_linea"]
    for col in required_cols:
        if col not in df_full.columns:
            if col == "CANT": df_full[col] = 1
            elif col == "UNIT": df_full[col] = df_full["TOTAL"] if "TOTAL" in df_full.columns else 0.0
            elif col == "VENTA": df_full[col] = 0.0
            elif col == "VTA_VENDEDOR": df_full[col] = df_full["VENTA"] if "VENTA" in df_full.columns else 0.0
            elif col == "TOTAL": df_full[col] = 0.0
            elif col == "MONEDA": df_full[col] = "USD"
            elif col == "PROVEEDOR": df_full[col] = "--- Sin Asignar ---"
            elif col in ["id_venta", "n_linea"]: df_full[col] = None
            else: df_full[col] = ""

    # Ordenar por FECHA
    df_full['FECHA'] = pd.to_datetime(df_full['FECHA']).dt.date
    df_full.sort_values(by=['FECHA'], inplace=True)
    
    # Obtener lista de proveedores (usando la carga inicial)
    lista_proveedores = ["--- Sin Asignar ---"]
    lista_proveedores += [f"{p['nombre_comercial']} ({p.get('servicios_ofrecidos', ['N/A'])[0]})" for p in prov_items]

    col_config = {
        "FECHA": st.column_config.DateColumn("FECHA", disabled=True),
        "SERVICIO": st.column_config.TextColumn("SERVICIO", required=True, width="large"),
        "PROVEEDOR": st.column_config.SelectboxColumn("PROVEEDOR", options=lista_proveedores, width="medium"),
        "UNIT": st.column_config.NumberColumn("COSTO UNITARIO", format="$ %.2f", min_value=0.0, width="small"),
        "CANT": st.column_config.NumberColumn("CANT", min_value=1, default=float(st.session_state.get('master_pax_count', 1)), width="small"),
        "TOTAL": st.column_config.NumberColumn("COSTO TOTAL", format="$ %.2f", disabled=True, width="small"),
        "VENTA": st.column_config.NumberColumn("PRECIO VENTA", format="$ %.2f", min_value=0.0, width="small"),
        "VTA_VENDEDOR": st.column_config.NumberColumn("PRECIO VENDEDOR", format="$ %.2f", min_value=0.0, width="small", disabled=True),
        "MONEDA": st.column_config.SelectboxColumn("MONEDA", options=["USD", "PEN"], default="USD", width="small"),
        "💵 Pago Op.": st.column_config.SelectboxColumn("ESTADO PAGO", options=["NO_REQUERIDO", "PENDIENTE", "PAGADO"], default="NO_REQUERIDO"),
        "📝 Info Pago": st.column_config.TextColumn("INFO PAGO", width="medium"),
        "📎 Voucher": st.column_config.LinkColumn("VOUCHER", width="small")
    }

    # --- VISTA SIMPLIFICADA (SIN NAVEGADOR POR DÍAS) ---
    st.write("### 📋 Resumen de Costos y Servicios (Master)")

    # Inicializar df_master desde la data del simulador
    df_master = pd.DataFrame(st.session_state['simulador_data'])
    all_edited = df_master
    
    # Asegurar que UNIT y CANT sean numéricos para el cálculo de totales
    df_master['UNIT'] = pd.to_numeric(df_master.get('UNIT', 0), errors='coerce').fillna(0.0)
    df_master['CANT'] = pd.to_numeric(df_master.get('CANT', 1), errors='coerce').fillna(1.0)
    df_master['TOTAL'] = df_master['UNIT'] * df_master['CANT']

    st.dataframe(
        df_master,
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
        column_order=["FECHA", "SERVICIO", "PROVEEDOR", "MONEDA", "UNIT", "CANT", "TOTAL", "💵 Pago Op."] 
    )
    
    # Totales Globales
    total_general = df_master['TOTAL'].sum()
    total_pax_venta = pd.to_numeric(df_master['VTA_VENDEDOR'], errors='coerce').fillna(0.0).sum()
    uti_global = total_pax_venta - total_general
    unique_dates = sorted(df_master['FECHA'].unique()) if 'FECHA' in df_master.columns else []

    st.divider()
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("COSTO TOTAL", f"$ {total_general:,.2f}", delta_color="inverse")
    sc2.metric("UTILIDAD GLOBAL", f"$ {uti_global:,.2f}", delta=f"{uti_global:,.2f}")
    sc3.metric("Total Días", len(unique_dates))

    st.info("💡 Esta tabla es de solo consulta. Los cambios de costos y proveedores se realizan en el Google Sheet Maestro y se sincronizan aquí.")

    # --- 📤 ACCIONES DE ENDOSO (UNIFICADO) ---
    if not all_edited.empty:
        st.markdown("---")
        st.subheader("📄 Acciones de Endoso")
        servicios_con_proveedor = all_edited[all_edited['PROVEEDOR'] != "--- Sin Asignar ---"]
        
        if not servicios_con_proveedor.empty:
            opciones_e = [f"{r['SERVICIO']} | {r['PROVEEDOR']} ({r['FECHA']})" for _, r in servicios_con_proveedor.iterrows()]
            sel_e_idx = st.selectbox("🎯 Seleccionar servicio para trámites:", opciones_e)
            
            if sel_e_idx:
                idx_orig = opciones_e.index(sel_e_idx)
                row_e = servicios_con_proveedor.iloc[idx_orig]
                ce1, ce2 = st.columns(2)
                pax_n = pax_sel.split('|')[0].strip() if pax_sel != "--- Seleccione ---" else "Cliente"
                
                data_e = {
                    "nombre_proveedor": row_e['PROVEEDOR'].split(" (")[0],
                    "fecha_servicio": row_e['FECHA'].strftime("%d/%m/%Y") if isinstance(row_e['FECHA'], date) else row_e['FECHA'],
                    "nombre_servicio": row_e['SERVICIO'],
                    "hora_encuentro": "Por confirmar",
                    "nombre_pasajero": pax_n,
                    "cantidad_pax": row_e['CANT'],
                    "id_venta": row_e.get('id_venta', 'N/A'),
                    "observaciones": row_e.get('📝 Info Pago', '')
                }
                
                from controllers.pdf_controller import PDFController
                pdf_ctrl = PDFController()
                with ce1:
                    pdf = pdf_ctrl.generar_voucher_endose_pdf(data_e)
                    if pdf: st.download_button("📄 Bajar Vale PDF", data=pdf, file_name=f"vale_{pax_n}.pdf", use_container_width=True)
                with ce2:
                    msg = f"✅ *ORDEN DE ENDOSE*\n\n👤 *Pax:* {pax_n}\n📅 *Fecha:* {data_e['fecha_servicio']}\n📍 *Servicio:* {data_e['nombre_servicio']}\n👥 *Cant:* {data_e['cantidad_pax']}"
                    st.link_button("📲 Enviar WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}", use_container_width=True)
        else:
            st.info("No hay servicios asignados a proveedores en esta lista.")
