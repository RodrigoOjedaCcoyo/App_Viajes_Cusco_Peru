# vistas/page_operaciones.py

import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import date, timedelta
import urllib.parse
from controllers.operaciones_controller import OperacionesController
from controllers.venta_controller import VentaController

def render_itinerary_details_visual(render):
    """Renderiza el detalle visual del itinerario de forma robusta."""
    # Soportar múltiples estructuras de datos de itinerario
    tours = render.get('itinerario_detalles', []) or render.get('itinerario_detales', []) or render.get('days', [])
    
    with st.container(border=True):
        # Título del Itinerario
        titulo_itin = render.get('titulo') or f"{render.get('title_1', '')} {render.get('title_2', '')}".strip() or "General"
        st.success(f"📍 **ITINERARIO:** {titulo_itin.upper()}")
        
        # --- SECCIÓN GLOBAL (Inclusiones/Exclusiones Generales) ---
        g_inc = render.get('inclusiones_globales') or render.get('servicios_incluidos', []) or render.get('incluye', [])
        g_exc = render.get('exclusiones_globales') or render.get('servicios_no_incluidos', []) or render.get('no_incluye', [])
        
        if g_inc or g_exc:
            with st.expander("✨ Inclusiones y Exclusiones Generales del Paquete", expanded=True):
                if g_inc:
                    st.markdown("<span style='color:#2E7D32; font-weight:bold;'>INCLUYE (Global):</span>", unsafe_allow_html=True)
                    for item in g_inc:
                        txt = item.get('texto') if isinstance(item, dict) else item
                        if txt: st.markdown(f"&nbsp;&nbsp;✔️ {str(txt).upper()}")
                if g_exc:
                    st.markdown("<span style='color:#2E7D32; font-weight:bold;'>NO INCLUYE (Global):</span>", unsafe_allow_html=True)
                    for item in g_exc:
                        txt = item.get('texto') if isinstance(item, dict) else item
                        if txt: st.markdown(f"&nbsp;&nbsp;❌ {str(txt).upper()}")
        st.divider()
        
        # Rendereado Día por Día
        for i, t in enumerate(tours):
            # Obtener Label del Día
            dia_label = f"DIA {i+1}"
            if t.get('fecha'): dia_label = f"DIA: {t['fecha']}"
            elif t.get('numero'): dia_label = f"DIA {t['numero']}"
            
            st.markdown(f"**{dia_label}**")
            
            # Nombre del Servicio y Hora
            t_nom = (t.get('nombre') or t.get('titulo') or "Servicio").upper()
            t_hora = t.get('hora', '')
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✅ **{f'({t_hora}) ' if t_hora else ''}{t_nom}**")
            
            # Inclusiones del Día (Soporta lista de strings o lista de objetos con 'texto')
            inc = t.get('incluye') or t.get('inclusiones', []) or t.get('servicios', [])
            if inc:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#2E7D32; font-weight:bold; font-size:12px;'>INCLUYE:</span>", unsafe_allow_html=True)
                for item in inc:
                    txt = item.get('texto') if isinstance(item, dict) else item
                    if txt: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;✔️ <small>{str(txt).upper()}</small>", unsafe_allow_html=True)
            
            # Exclusiones del Día (Soporta lista de strings o lista de objetos con 'texto')
            exc = t.get('no_incluye') or t.get('exclusiones', []) or t.get('servicios_no', [])
            if exc:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#2E7D32; font-weight:bold; font-size:12px;'>NO INCLUYE:</span>", unsafe_allow_html=True)
                for item in exc:
                    txt = item.get('texto') if isinstance(item, dict) else item
                    if txt: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;❌ <small>{str(txt).upper()}</small>", unsafe_allow_html=True)
            st.write("")


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
                            st.markdown(f"<p style='font-size:11px; margin:0;'><b>{s['Servicio']}</b></p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='font-size:9px; margin:0; color:#aaa;'>{s['Cliente']}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='font-size:9px; margin:0;'>👮 {s['Guía']}</p>", unsafe_allow_html=True)
                
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
            column_order=('Hora', 'Día Itin.', 'Servicio', 'Tipo', 'Pax', 'Cliente', 'Guía', 'Estado Pago', 'ID Itinerario'),
            column_config={
                "Día Itin.": st.column_config.NumberColumn("Día", format="%d", disabled=True),
                "Tipo": st.column_config.TextColumn("Tipo", disabled=True, width="small"),
                "Guía": st.column_config.TextColumn("Asignar Guía ✏️"),
                "Pax": st.column_config.NumberColumn(disabled=True),
                "Servicio": st.column_config.TextColumn(disabled=True),
                "Cliente": st.column_config.TextColumn(disabled=True),
                "Estado Pago": st.column_config.TextColumn(disabled=True),
                "ID Itinerario": st.column_config.TextColumn("Itin. Cloud ☁️", disabled=True, help="UUID del diseño original en la nube"),
            },
            hide_index=True, use_container_width=True, key=f"ed_{f_p}"
        )

        if st.button("💾 Guardar Asignaciones"):
            cc = 0
            for i, r in ed_df.iterrows():
                if r['Guía'] != df.iloc[i]['Guía']:
                    # Nueva firma usando claves compuestas SQL
                    if controller.actualizar_guia_servicio(r['ID Venta'], r['N Linea'], r['Guía'])[0]: 
                        cc += 1
            if cc > 0:
                st.success(f"¡{cc} cambios guardados!")
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
                    render_itinerary_details_visual(res_itin.data['datos_render'])
            else:
                st.warning("Esta venta no tiene un itinerario digital vinculado.")

def generar_mensaje_whatsapp(data):
    """Genera un link de WhatsApp con el mensaje formateado."""
    mensaje = (
        f"*REQUERIMIENTO:*\n"
        f"{data['nombre'].upper()} - {data['motivo'].upper()}\n"
        f"TOTAL: {float(data.get('total') or 0):,.2f} SOLES\n\n"
        f"N° DE CUENTA:\n{data['n_cuenta'].upper()}"
    )
    # Codificar para URL
    mensaje_codificado = urllib.parse.quote(mensaje)
    return f"https://wa.me/?text={mensaje_codificado}"

def dashboard_requerimientos(controller):
    """Módulo para el registro de requerimientos de operaciones."""
    st.subheader("📝 Registro de Requerimientos", divider='orange')

    # Formulario
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        tipo_cliente = col1.selectbox("Tipo de Cliente", ["B2B", "B2C"])
        nombre = col2.text_input("Nombre / Razón Social")
        total = col3.number_input("Total (SOLES)", min_value=0.0, step=1.0, format="%.2f")

        motivo = st.text_area("Motivo del Requerimiento", height=100)
        n_cuenta = st.text_area("N° de Cuenta / Detalles de Pago", height=150)

        if st.button("🔴 Registrar Requerimiento", use_container_width=True):
            if not nombre or not motivo:
                st.error("Por favor completa nombre y motivo.")
            else:
                nuevo_req = {
                    "tipo_cliente": tipo_cliente,
                    "nombre": nombre.upper(),
                    "motivo": motivo.upper(),
                    "total": total,
                    "n_cuenta": n_cuenta.upper() if n_cuenta else ""
                }
                success, msg = controller.registrar_requerimiento(nuevo_req)
                if success:
                    st.success(msg)
                    st.session_state['last_req'] = nuevo_req
                else:
                    st.error(msg)

    # Botón de WhatsApp
    if 'last_req' in st.session_state:
        req = st.session_state['last_req']
        msg_wa = generar_mensaje_whatsapp(req)
        msg_encoded = urllib.parse.quote(msg_wa)
        wa_link = f"https://wa.me/?text={msg_encoded}"
        st.markdown(f"""
            <a href="{wa_link}" target="_blank">
                <button style="width:100%; padding:10px; background-color:#25D366; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">
                    🟢 Enviar a Grupo de WhatsApp
                </button>
            </a>
        """, unsafe_allow_html=True)
        if st.button("Limpiar Registro Actual"):
            del st.session_state['last_req']
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Requerimientos Registrados")
    reqs = controller.get_requerimientos()
    if reqs:
        df_reqs = pd.DataFrame(reqs)
        st.dataframe(df_reqs, hide_index=True, use_container_width=True)
    else:
        st.info("No hay requerimientos registrados.")


def dashboard_registro_ventas_compartido(controller):
    """Vista de Ventas compartida para Operaciones y Contabilidad."""
    st.subheader("💰 Registro de Ventas (Confirmadas)", divider='blue')
    ventas = controller.get_all_ventas()
    
    if not ventas:
        st.info("No hay ventas registradas actualmente.")
    else:
        df_v = pd.DataFrame(ventas)
        st.dataframe(
            df_v,
            column_config={
                "Total": st.column_config.NumberColumn("Monto Cierre", format="$ %.2f"),
                "Fecha": st.column_config.DateColumn("Fecha Venta")
            },
            hide_index=True,
            use_container_width=True
        )


def registro_ventas_proveedores(supabase_client):
    from controllers.itinerario_digital_controller import ItinerarioDigitalController
    venta_controller = VentaController(supabase_client)
    it_controller = ItinerarioDigitalController(supabase_client)

    st.subheader("🤝 Registro de Venta para Proveedores (B2B)")
    
    # --- 🆔 SELECTOR DE ITINERARIO (ESTILO VENDEDORES) ---
    itinerarios = it_controller.obtener_todos_recientes(limit=30)
    opciones_it = ["--- Sin Itinerario / Registro Manual ---"]
    mapa_it = {}
    
    for it in itinerarios:
        uuid = it.get('id_itinerario_digital')
        render = it.get('datos_render', {})
        titulo = render.get('titulo') or render.get('title_1', 'Sin Título')
        pax = it.get('nombre_pasajero_itinerario') or render.get('pasajero', 'Sin Nombre')
        fecha = it.get('fecha_generacion', '')[:10]
        label = f"[{fecha}] {pax} - {titulo} ({uuid[:8]})"
        opciones_it.append(label)
        mapa_it[label] = it

    it_sel = st.selectbox("🎯 Vincular con un Itinerario Digital (CLOUD)", opciones_it, help="Al seleccionar un itinerario se auto-completarán los datos del pasajero, tour y fechas.")
    
    id_itinerario_dig = None
    def_pax = ""
    def_tour = ""
    def_f_inicio = date.today()
    def_f_fin = date.today() + timedelta(days=1)
    def_cant_pax = 1

    if it_sel != "--- Sin Itinerario / Registro Manual ---":
        it_data = mapa_it.get(it_sel)
        id_itinerario_dig = it_data.get('id_itinerario_digital')
        render = it_data.get('datos_render', {})
        
        def_pax = it_data.get('nombre_pasajero_itinerario') or render.get('pasajero', '')
        def_tour = render.get('titulo') or (f"{render.get('title_1', '')} {render.get('title_2', '')}").strip()
        
        # Extraer Fechas
        f_inicio_str = render.get('fecha_viaje')
        if f_inicio_str:
            try: def_f_inicio = date.fromisoformat(f_inicio_str)
            except: pass
        
        duracion = render.get('duracion', '')
        if duracion and 'D' in duracion:
            try:
                num_dias = int(duracion.split('D')[0])
                def_f_fin = def_f_inicio + timedelta(days=num_dias - 1)
            except: pass
        
        def_cant_pax = int(render.get('cantidad_pax') or 1)
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
        precio_pax = c1d.number_input("Precio Neto/Pax ($)", min_value=0.0, value=0.0, format="%.2f")

        # Catálogo vs Manual
        catalogo = venta_controller.obtener_catalogo_opciones()
        nombres_cat = ["--- Escribir Manualmente ---"] + [c['nombre'] for c in catalogo]
        mapa_cat = {c['nombre']: c['id'] for c in catalogo}
        
        item_sel = col2.selectbox("Clasificar como (Paquete Catálogo)", nombres_cat)
        
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
    """
    Vista global de operaciones (Dashboard + Detalle).
    Similar al Reporte de Montos de Contabilidad.
    """
    st.subheader("📊 Reporte Operativo Global", divider='blue')
    
    # 1. Dashboard de Analítica (Top)
    from vistas.dashboard_analytics import render_operations_dashboard
    df_ops = controller.get_data_for_analytics()
    render_operations_dashboard(df_ops)
    
    st.divider()
    
    # 2. Detalle de Operaciones (Auditoría)
    st.write("### 📋 Detalle de Servicios Programados")
    # Traer todos los servicios (no solo los de un día)
    todos_servicios = controller.get_servicios_rango_fechas(date.today() - timedelta(days=30), date.today() + timedelta(days=60))
    
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
        
        ventas_con_itin = df_all[df_all['ID Itinerario'].notna()]
        if not ventas_con_itin.empty:
            sel_id_v = st.selectbox("Auditar Itinerario de la Venta:", 
                                  ventas_con_itin['ID Venta'].unique(),
                                  format_func=lambda x: f"{ventas_con_itin[ventas_con_itin['ID Venta']==x]['Cliente'].values[0]} ({x})",
                                  key="sb_ops_audit_it")
            
            # Reutilizar lógica de detalle visual
            id_it_audit = df_all[df_all['ID Venta'] == sel_id_v]['ID Itinerario'].dropna().unique()[0]
            
            res = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_it_audit).single().execute()
            if res.data:
                render_itinerary_details_visual(res.data['datos_render'])

def mostrar_pagina(nombre_modulo, rol_actual, user_id, supabase_client):
    """Punto de entrada de Streamlit para el área de Operaciones."""
    controller = OperacionesController(supabase_client)
    
    st.title("⚙️ Gestión de Operaciones")
    st.markdown("---")
    
    if nombre_modulo == "Gestión de Registros":
        tab1, tab2, tab3 = st.tabs([
            "📝 Registro de Requerimientos", 
            "📊 Estructurador de Gastos",
            "🤝 Ventas de Proveedores (B2B)"
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
            {"FECHA": date.today(), "SERVICIO": "Servicio Ejemplo", "UNITARIO": 0.0, "TOTAL": 0.0},
        ]
    
    if 'liq_pax_total' not in st.session_state:
        st.session_state['liq_pax_total'] = 1
    if 'liq_precio_pax' not in st.session_state:
        st.session_state['liq_precio_pax'] = 0.0

    # --- PANEL LATERAL DE RESUMEN (INGRESOS vs COSTOS) ---
    col_main, col_summary = st.columns([3, 1])

    with col_summary:
        st.markdown("### 📝 Resumen Liquidación")
        with st.container(border=True):
            pax_total = st.number_input("TOTAL PAXS", min_value=1, value=st.session_state['liq_pax_total'], key="in_pax_total")
            precio_pax = st.number_input("COBRO POR PAX ($)", min_value=0.0, value=st.session_state['liq_precio_pax'], format="%.2f", key="in_precio_pax")
            
            st.session_state['liq_pax_total'] = pax_total
            st.session_state['liq_precio_pax'] = precio_pax
            
            total_ingreso = pax_total * precio_pax
            
            st.metric("TOTAL INGRESO", f"$ {total_ingreso:,.2f}")
            
            # Botones de Acción
            if st.button("🗑️ Limpiar Todo", use_container_width=True, key="btn_clear_ops_sim"):
                st.session_state['simulador_data'] = [{"FECHA": date.today(), "SERVICIO": "", "UNITARIO": 0.0, "TOTAL": 0.0}]
                st.session_state['liq_precio_pax'] = 0.0
                st.rerun()

    with col_main:
        st.info("💡 Consejo: Selecciona una agencia arriba para cargar sus datos y luego ajusta los costos unitarios.")
        
        # Barra de Agencias (Existente)
        from controllers.venta_controller import VentaController
        vc = VentaController(controller.client)
        agencias = vc.obtener_agencias_aliadas()
        nombres_agencias = [a['nombre'] for a in agencias]
        mapa_agencias = {a['nombre']: a['id_agencia'] for a in agencias}
        
        c_age, c_pax = st.columns(2)
        with c_age:
            agencia_sel = st.selectbox("1. Filtrar por Agencia:", ["--- Seleccione ---"] + nombres_agencias, key="sel_agencia_sim")
        
        if agencia_sel != "--- Seleccione ---":
            id_ag = mapa_agencias.get(agencia_sel)
            ventas_age = vc.obtener_ventas_agencia(id_ag)
            
            if ventas_age:
                opciones_pax = [f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})" for v in ventas_age]
                mapa_ventas_pax = {f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})": v for v in ventas_age}
                with c_pax:
                    pax_sel = st.selectbox("2. Cargar Venta específica:", ["--- Seleccione ---"] + opciones_pax, key="sel_pax_sim")
                
                if pax_sel != "--- Seleccione ---":
                    if st.button(f"📥 Cargar Itinerario de {pax_sel.split('|')[0].strip()}", use_container_width=True):
                        v = mapa_ventas_pax.get(pax_sel)
                        
                        # 1. Ajustar Datos Globales
                        st.session_state['liq_pax_total'] = int(v.get('cantidad_pasajeros') or 1)
                        st.session_state['liq_precio_pax'] = float(v.get('precio_total_cierre') or 0)
                        
                        # 2. Cargar Desglose de Servicios (Venta Tour)
                        detalles = vc.obtener_detalles_itinerario_venta(v['id_venta'])
                        
                        if detalles:
                            nuevos_items = []
                            for d in detalles:
                                nuevos_items.append({
                                    "FECHA": date.fromisoformat(d['fecha_servicio']),
                                    "SERVICIO": d.get('observaciones') or "Servicio sin nombre",
                                    "UNITARIO": 0.0,
                                    "TOTAL": 0.0
                                })
                            st.session_state['simulador_data'] = nuevos_items
                            st.success(f"Itinerario de {len(detalles)} días cargado con éxito.")
                            st.rerun()
                        else:
                            st.session_state['simulador_data'] = [
                                {"FECHA": date.fromisoformat(v['fecha_venta']) if v.get('fecha_venta') else date.today(), 
                                 "SERVICIO": f"INGRESO B2B: {v['nombre_cliente']}", "UNITARIO": 0.0, "TOTAL": 0.0}
                            ]
                            st.warning("Venta cargada, pero no tiene itinerario expandido.")
                            st.rerun()

        # Data Editor (El "Excel")
        df = pd.DataFrame(st.session_state['simulador_data'])
        
        # Lógica de cálculo automático: Total = Unitario * Pax_Total
        if not df.empty and 'UNITARIO' in df.columns:
            df['TOTAL'] = df['UNITARIO'] * pax_total

        column_config = {
            "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", required=True),
            "SERVICIO": st.column_config.TextColumn("Servicio / Gasto", required=True, width="large"),
            "UNITARIO": st.column_config.NumberColumn("Costo Unitario ($)", format="%.2f", min_value=0.0, width="medium"),
            "TOTAL": st.column_config.NumberColumn("Costo Total ($)", format="%.2f", min_value=0.0, disabled=True, width="medium")
        }

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
        utilidad = total_ingreso - total_costos
        margen = (utilidad / total_ingreso * 100) if total_ingreso > 0 else 0

        st.divider()
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("COSTO TOTAL GRUPO", f"$ {total_costos:,.2f}", delta_color="inverse")
        sc2.metric("UTILIDAD NETA", f"$ {utilidad:,.2f}")
        sc3.metric("MARGEN %", f"{margen:.1f}%")

        if st.button("📥 Exportar Liquidación (CSV)"):
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", csv, f"liquidacion_{date.today()}.csv", "text/csv")
