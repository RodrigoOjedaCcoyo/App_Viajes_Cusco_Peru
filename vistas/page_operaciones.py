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
    
    with st.container(border=True):
        st.markdown(f"#### 📄 Resumen de Viaje: {render.get('titulo', 'Sin Título')}")
        st.info("Este documento es una versión simplificada (Ink Saver) ideal para imprimir y para el personal operativo.")
        
        # Generar el PDF en memoria
        pdf_buffer = pdf_ctrl.generar_itinerario_simple_pdf(render)
        
        if pdf_buffer:
            st.download_button(
                label="📥 Descargar Resumen de Viaje (PDF Simple)",
                data=pdf_buffer,
                file_name=f"resumen_viaje_{render.get('titulo', 'itinerario')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("No se pudo generar el PDF en este momento.")

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
        ed_df = st.data_editor(
            df,
            column_order=('Log.', 'Hora', 'Día Itin.', 'Servicio', 'Pax', 'Endoso?', 'Guía', 'Agencia Endoso', 'Estado Pago', 'Cliente', 'URL Cloud'),
            column_config={
                "Log.": st.column_config.TextColumn("Log.", help="Semáforo de Logística (🟢 Todo OK, 🔴 Falta asignar)", disabled=True, width="small"),
                "Día Itin.": st.column_config.NumberColumn("Día", format="%d", disabled=True, width="small"),
                "Endoso?": st.column_config.CheckboxColumn("¿Endoso?", help="Marcar si el servicio se pasa a otra agencia"),
                "Agencia Endoso": st.column_config.TextColumn("Agencia/Proveedor 🏢", help="Nombre de la agencia que recibe el endoso"),
                "URL Cloud": st.column_config.LinkColumn("PDF 📄", help="Abrir Itinerario Premium"),
                "Guía": st.column_config.TextColumn("Guía ✏️", help="Asignar guía (solo si NO es endoso)"),
                "Pax": st.column_config.NumberColumn(disabled=True),
                "Servicio": st.column_config.TextColumn(disabled=True),
                "Cliente": st.column_config.TextColumn(disabled=True),
                "Estado Pago": st.column_config.TextColumn(disabled=True),
            },
            hide_index=True, use_container_width=True, key=f"ed_{f_p}"
        )

        if st.button("💾 Guardar Cambios de Logística"):
            changes_count = 0
            for i, r in ed_df.iterrows():
                old_r = df.iloc[i]
                vid, n_lin = r['ID Venta'], r['N Linea']
                
                # 1. Cambios en Flag Endoso
                if r['Endoso?'] != old_r['Endoso?']:
                    controller.toggle_endoso_servicio(vid, n_lin, r['Endoso?'])
                    changes_count += 1
                
                # 2. Cambios en Guía (Solo si no es endoso)
                if not r['Endoso?'] and r['Guía'] != old_r['Guía']:
                    success, msg = controller.actualizar_guia_servicio(vid, n_lin, r['Guía'])
                    if success: changes_count += 1
                    else: st.error(msg)
                
                # 3. Cambios en Agencia Endoso
                if r['Endoso?'] and r['Agencia Endoso'] != old_r['Agencia Endoso']:
                    success, msg = controller.actualizar_endoso_servicio(vid, n_lin, r['Agencia Endoso'])
                    if success: changes_count += 1
                    else: st.error(msg)

            if changes_count > 0:
                st.success(f"¡{changes_count} cambios de logística aplicados!")
                st.rerun()

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

# Módulo para el registro de requerimientos de operaciones.
def dashboard_requerimientos(controller):
    st.subheader("📝 Registro de Requerimientos de Operaciones", divider='orange')
    with st.form("form_requerimientos"):
        st.info("Formulario simplificado para operaciones.")
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Referencia / Nombre Pax")
        fecha = col1.date_input("Fecha Servicio", value=date.today())
        req = col2.text_area("Descripción del Requerimiento")
        prioridad = col2.selectbox("Prioridad", ["Baja", "Media", "Alta"])
        
        if st.form_submit_button("Guardar Requerimiento"):
            st.success("Requerimiento guardado correctamente.")

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
            "📝 Registro de Requerimientos", 
            "📊 Estructurador de Gastos (Master Sheet)",
            "🤝 Ventas B2B (Entrada)"
        ])
        
        with tab1:
            dashboard_requerimientos(controller)
            
        with tab2:
            dashboard_simulador_costos(controller)
            
        with tab3:
            registro_ventas_proveedores(supabase_client)
            
            
    elif nombre_modulo == "Dashboard Diario":
        dashboard_tablero_diario(controller)
    elif nombre_modulo == "Reporte Operativo":
        reporte_operativo(controller)
    else:
        st.info("Seleccione una opción válida del menú lateral.")


def dashboard_simulador_costos(controller):
    """
    Herramienta avanzada para estructurar liquidaciones de grupos/B2B.
    Basado en estructura de Excel (Unitario x Pax = Total).
    """
    st.subheader("📊 Estructurador de Liquidación Profesional", divider='rainbow')

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
                
                # 1. Ajustar Datos Globales (ya no necesarios pero mantenemos compatibilidad)
                
                # 2. Cargar Desglose de Servicios (Venta Tour)
                detalles = vc.obtener_detalles_itinerario_venta(v['id_venta'])
                
                if detalles:
                    nuevos_items = []
                    for d in detalles:
                        nuevos_items.append({
                            "FECHA": date.fromisoformat(d['fecha_servicio']),
                            "SERVICIO": d.get('observaciones') or "Servicio sin nombre",
                            "PROVEEDOR": next((f"{p['nombre_comercial']} ({p.get('servicios_ofrecidos', ['N/A'])[0]})" for p in res_prov_data if p['id_proveedor'] == d.get('id_proveedor')), "--- Sin Asignar ---"),
                            "MONEDA": d.get('moneda_costo', 'USD'),
                            "TOTAL": float(d.get('costo_applied') or 0.0),
                            "💵 Pago Op.": d.get('estado_pago_operativo', 'NO_REQUERIDO'),
                            "📝 Info Pago": d.get('datos_pago_operativo', ''),
                            "📎 Voucher": d.get('url_voucher_operativo', ''),
                            "id_venta": d['id_venta'],
                            "n_linea": d['n_linea']
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

    # Data Editor (El "Excel")
    df = pd.DataFrame(st.session_state['simulador_data'])
    
    if not df.empty:
        # Asegurar columnas necesarias if empty
        for col in ["💵 Pago Op.", "📝 Info Pago", "📎 Voucher"]:
            if col not in df.columns: df[col] = ""
    else:
        df = pd.DataFrame(columns=["FECHA", "SERVICIO", "PROVEEDOR", "MONEDA", "TOTAL", "💵 Pago Op.", "📝 Info Pago", "📎 Voucher"])

    # Ordenar por FECHA para que al agregar filas con misma fecha queden agrupadas
    if not df.empty and 'FECHA' in df.columns:
        df.sort_values(by='FECHA', inplace=True)
    
    # Obtener lista de proveedores para el selectbox
    lista_proveedores = ["--- Sin Asignar ---"]
    res_prov_data = [] # Variable segura para usar después
    try:
        res_prov = controller.client.table('proveedor').select('id_proveedor, nombre_comercial, servicios_ofrecidos').execute()
        res_prov_data = res_prov.data or []
        lista_proveedores += [f"{p['nombre_comercial']} ({p.get('servicios_ofrecidos', ['N/A'])[0]})" for p in res_prov_data]
    except Exception as e:
        # Si no existe la tabla aún, no romper la app, solo avisar en consola o mostrar vacío
        print(f"Advertencia: No se pudo cargar proveedores (posiblemente falta tabla): {e}")

    column_config = {
        "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", required=True),
        "SERVICIO": st.column_config.TextColumn("Descripción del Servicio", required=True, width="large"),
        "PROVEEDOR": st.column_config.SelectboxColumn("Endosar a (Proveedor)", options=lista_proveedores, width="medium"),
        "MONEDA": st.column_config.SelectboxColumn("💵 Moneda", options=["USD", "PEN"], default="USD", width="small"),
        "TOTAL": st.column_config.NumberColumn("Costo Total", format="%.2f", min_value=0.0, width="medium"),
        "💵 Pago Op.": st.column_config.SelectboxColumn("💵 Pago Op.", options=["NO_REQUERIDO", "PENDIENTE", "PAGADO"], default="NO_REQUERIDO"),
        "📝 Info Pago": st.column_config.TextColumn("📝 Info Pago (Cuentas/Yape)", width="medium"),
        "📎 Voucher": st.column_config.LinkColumn("📎 Voucher", width="small")
    }

    st.info("💡 **Tip:** Para insertar un servicio en un día específico: **1.** Agrégalo al final. **2.** Pon la fecha deseada. **3.** Al Guardar, se ordenará solito.")

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_simulador_ops"
    )

    st.session_state['simulador_data'] = edited_df.to_dict('records')

    # Totales Finales
    total_costos = edited_df['TOTAL'].sum()

    st.divider()
    sc1, sc2 = st.columns(2)
    sc1.metric("COSTO TOTAL GRUPO", f"$ {total_costos:,.2f}", delta_color="inverse")
    sc2.metric("Total Servicios", len(edited_df))

    c_actions_1, c_actions_2 = st.columns(2)
    
    with c_actions_1:
        if st.button("💾 Guardar Borrador", use_container_width=True, type="secondary"):
                # Guardar como borrador (en progreso)
                updated_count = 0
                for index, row in edited_df.iterrows():
                    proveedor_txt = row.get('PROVEEDOR')
                    id_prov = None
                    if proveedor_txt and proveedor_txt != "--- Sin Asignar ---":
                        nombre_prov = proveedor_txt.split(" (")[0]
                        prov_match = next((p for p in res_prov_data if p['nombre'] == nombre_prov), None)
                        if prov_match: id_prov = prov_match['id_proveedor']

                    if pd.notna(row.get('id_venta')) and pd.notna(row.get('n_linea')):
                        # Actualizar existente
                        try:
                            controller.client.table('venta_tour').update({
                                'costo_applied': row['TOTAL'],
                                'moneda_costo': row.get('MONEDA', 'USD'),
                                'id_proveedor': id_prov,
                                'observaciones': row.get('SERVICIO'),
                                'estado_pago_operativo': row.get('💵 Pago Op.', 'NO_REQUERIDO'),
                                'datos_pago_operativo': row.get('📝 Info Pago', ''),
                                'es_endoso': True if id_prov else False # Simplificado: si hay proveedor hay endoso/servicio
                            }).match({'id_venta': row['id_venta'], 'n_linea': row['n_linea']}).execute()
                            updated_count += 1
                        except Exception as e:
                            st.error(f"Error actualizando línea {index}: {e}")
                    else:
                        # Insertar NUEVA línea manual si tenemos contexto de venta cargada
                        if ventas_age and pax_sel != "--- Seleccione ---":
                            v_actual = mapa_ventas_pax.get(pax_sel)
                            try:
                                # Calcular siguiente n_linea
                                last_line = controller.client.table('venta_tour').select('n_linea').eq('id_venta', v_actual['id_venta']).order('n_linea', desc=True).limit(1).execute()
                                next_n = (last_line.data[0]['n_linea'] + 1) if last_line.data else 1
                                
                                controller.client.table('venta_tour').insert({
                                    'id_venta': v_actual['id_venta'],
                                    'n_linea': next_n + index,
                                    'fecha_servicio': row['FECHA'].isoformat(),
                                    'observaciones': row.get('SERVICIO', 'Gasto Adicional'),
                                    'costo_applied': row['TOTAL'],
                                    'moneda_costo': row.get('MONEDA', 'USD'),
                                    'id_proveedor': id_prov,
                                    'cantidad_pasajeros': v_actual.get('num_pasajeros', 1),
                                    'estado_pago_operativo': row.get('💵 Pago Op.', 'NO_REQUERIDO'),
                                    'datos_pago_operativo': row.get('📝 Info Pago', ''),
                                    'es_endoso': True if id_prov else False
                                }).execute()
                                updated_count += 1
                            except Exception as e:
                                st.error(f"Error creando línea nueva {index}: {e}")
                
                if updated_count > 0:
                    st.success(f"💾 Borrador guardado: {updated_count} servicios actualizados. Puedes seguir editando.")
                else:
                    st.warning("No se encontraron líneas para actualizar.")
        
        with c_actions_2:
            if st.button("✅ Guardar y Finalizar", use_container_width=True, type="primary"):
                # Guardar y marcar como finalizado
                updated_count = 0
                for index, row in edited_df.iterrows():
                    proveedor_txt = row.get('PROVEEDOR')
                    id_prov = None
                    if proveedor_txt and proveedor_txt != "--- Sin Asignar ---":
                        nombre_prov = proveedor_txt.split(" (")[0]
                        prov_match = next((p for p in res_prov_data if p['nombre'] == nombre_prov), None)
                        if prov_match: id_prov = prov_match['id_proveedor']

                    if pd.notna(row.get('id_venta')) and pd.notna(row.get('n_linea')):
                        try:
                            controller.client.table('venta_tour').update({
                                'costo_applied': row['TOTAL'],
                                'moneda_costo': row.get('MONEDA', 'USD'),
                                'id_proveedor': id_prov,
                                'observaciones': row.get('SERVICIO'),
                                'estado_pago_operativo': row.get('💵 Pago Op.', 'NO_REQUERIDO'),
                                'datos_pago_operativo': row.get('📝 Info Pago', ''),
                                'es_endoso': True if id_prov else False
                            }).match({'id_venta': row['id_venta'], 'n_linea': row['n_linea']}).execute()
                            updated_count += 1
                        except Exception as e:
                            st.error(f"Error actualizando línea {index}: {e}")
                    else:
                        if ventas_age and pax_sel != "--- Seleccione ---":
                            v_actual = mapa_ventas_pax.get(pax_sel)
                            try:
                                last_line = controller.client.table('venta_tour').select('n_linea').eq('id_venta', v_actual['id_venta']).order('n_linea', desc=True).limit(1).execute()
                                next_n = (last_line.data[0]['n_linea'] + 1) if last_line.data else 1
                                
                                controller.client.table('venta_tour').insert({
                                    'id_venta': v_actual['id_venta'],
                                    'n_linea': next_n + index,
                                    'fecha_servicio': row['FECHA'].isoformat(),
                                    'observaciones': row.get('SERVICIO', 'Gasto Adicional'),
                                    'costo_applied': row['TOTAL'],
                                    'moneda_costo': row.get('MONEDA', 'USD'),
                                    'id_proveedor': id_prov,
                                    'cantidad_pasajeros': v_actual.get('num_pasajeros', 1),
                                    'estado_pago_operativo': row.get('💵 Pago Op.', 'NO_REQUERIDO'),
                                    'datos_pago_operativo': row.get('📝 Info Pago', ''),
                                    'es_endoso': True if id_prov else False
                                }).execute()
                                updated_count += 1
                            except Exception as e:
                                st.error(f"Error creando línea nueva {index}: {e}")
                
                # Marcar la venta como liquidada
                if updated_count > 0 and ventas_age and pax_sel != "--- Seleccione ---":
                    v_actual = mapa_ventas_pax.get(pax_sel)
                    try:
                        controller.client.table('venta').update({
                            'estado_liquidacion': 'FINALIZADO'
                        }).eq('id_venta', v_actual['id_venta']).execute()
                        st.success(f"✅ Liquidación FINALIZADA: {updated_count} servicios guardados. Estado actualizado a COMPLETADO.")
                    except Exception as e:
                        st.warning(f"Servicios guardados pero no se pudo actualizar estado: {e}")
                else:
                    st.warning("No se encontraron líneas para actualizar.")

    # --- 📤 ACCIONES DE ENDOSO (UNIFICADO) ---
    if not edited_df.empty:
        st.markdown("---")
        st.subheader("📄 Acciones Rápidas de Endoso")
        st.info("💡 Selecciona un servicio de la tabla de arriba (haciendo clic en cualquier celda de la fila) para generar su vale de endose.")
        
        # Como data_editor no devuelve la selección de fila fácilmente en esta versión,
        # usamos un selector simple basado en los datos editados para acciones rápidas.
        servicios_con_proveedor = edited_df[edited_df['PROVEEDOR'] != "--- Sin Asignar ---"]
        
        if not servicios_con_proveedor.empty:
            opciones_e = [f"{r['SERVICIO']} | {r['PROVEEDOR']} ({r['FECHA']})" for _, r in servicios_con_proveedor.iterrows()]
            sel_e_idx = st.selectbox("🎯 Generar Vale para:", opciones_e)
            
            if sel_e_idx:
                idx_original = opciones_e.index(sel_e_idx)
                row_e = servicios_con_proveedor.iloc[idx_original]
                
                ce1, ce2 = st.columns(2)
                
                # Datos para el PDF
                pax_nombre = pax_sel.split('|')[0].strip() if pax_sel != "--- Seleccione ---" else "Cliente"
                data_endose = {
                    "nombre_proveedor": row_e['PROVEEDOR'].split(" (")[0],
                    "fecha_servicio": row_e['FECHA'].strftime("%d/%m/%Y"),
                    "nombre_servicio": row_e['SERVICIO'],
                    "hora_encuentro": "Por confirmar",
                    "nombre_pasajero": pax_nombre,
                    "cantidad_pax": 1, # Podría extraerse de la venta si se desea
                    "id_venta": row_e.get('id_venta', 'N/A'),
                    "observaciones": row_e.get('📝 Info Pago', '')
                }
                
                from controllers.pdf_controller import PDFController
                pdf_ctrl = PDFController()
                
                with ce1:
                    pdf_v = pdf_ctrl.generar_voucher_endose_pdf(data_endose)
                    if pdf_v:
                        st.download_button(
                            label="📄 Descargar Vale de Endose (PDF)",
                            data=pdf_v,
                            file_name=f"vale_{pax_nombre.replace(' ','_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                
                with ce2:
                    msg_wa = f"✅ *ORDEN DE ENDOSE - VIAJES CUSCO PERÚ*\n\n"
                    msg_wa += f"👤 *Pax:* {pax_nombre}\n"
                    msg_wa += f"📅 *Fecha:* {data_endose['fecha_servicio']}\n"
                    msg_wa += f"📍 *Servicio:* {data_endose['nombre_servicio']}\n"
                    msg_wa += f"💬 *Info:* {data_endose['observaciones']}"
                    url_wa = f"https://wa.me/?text={urllib.parse.quote(msg_wa)}"
                    st.link_button("📲 Enviar por WhatsApp", url_wa, use_container_width=True)
        else:
            st.write("No hay servicios asignados a proveedores externos en esta liquidación.")
