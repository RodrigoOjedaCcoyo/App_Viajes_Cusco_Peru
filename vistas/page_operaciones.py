# vistas/page_operaciones.py

import streamlit as st
import pandas as pd
import io
import plotly.express as px
import calendar
from datetime import date, timedelta
import urllib.parse
from controllers.operaciones_controller import OperacionesController
from controllers.venta_controller import VentaController
from controllers.excel_controller import ExcelController

# NUEVO: Renderiza el Botón para el Excel Maestro Operativo.
def render_operational_master_download(controller, id_venta, label="📊 Generar Informe Maestro", key=None):
    """
    Recopila toda la información de la operación y ofrece la descarga del Excel Maestro.
    """
    try:
        xl_ctrl = ExcelController()
        
        # fallback: Obtener toda la data necesaria aquí mismo para evitar problemas de cache del controller
        # 1. Obtener Datos de la Venta
        vc = VentaController(controller.client)
        # Buscar la venta específica en la base de datos para tener datos frescos
        res_v = controller.client.table('venta').select('*, cliente(nombre, lead(numero_celular))').eq('id_venta', id_venta).single().execute()
        if not res_v.data:
            return
            
        v_raw = res_v.data
        cliente_nest = v_raw.get('cliente', {})
        lead_nest = cliente_nest.get('lead', {}) if isinstance(cliente_nest, dict) else {}
        
        v_data = {
            "id_venta": v_raw['id_venta'],
            "nombre_cliente": cliente_nest.get('nombre', 'Desconocido') if isinstance(cliente_nest, dict) else 'Desconocido',
            "telefono": lead_nest.get('numero_celular', '---') if isinstance(lead_nest, dict) else '---',
            "tour_nombre": v_raw.get('tour_nombre', 'Sin Tour'),
            "fecha_inicio": v_raw.get('fecha_inicio'),
            "fecha_fin": v_raw.get('fecha_fin'),
            "num_pasajeros": v_raw.get('num_pasajeros', 1),
            "vendedor": "---", 
            "moneda": v_raw.get('moneda', 'USD'),
            "monto_total": v_raw.get('precio_total_cierre', 0),
            "monto_pagado": 0,
            "drive_url": v_raw.get('drive_url')
        }

        # 2. Calcular Pagos
        res_p = controller.client.table('pago').select('monto_pagado').eq('id_venta', id_venta).execute()
        v_data['monto_pagado'] = sum(float(p['monto_pagado'] or 0) for p in res_p.data)

        # 3. Obtener Itinerario Logístico (Con proveedores asignados)
        itinerario = controller.get_servicios_rango_fechas(date(2000,1,1), date(2100,1,1))
        it_venta = [s for s in itinerario if s['ID Venta'] == id_venta]

        # 4. Obtener Pasajeros
        pasajeros = controller.pasajero_model.get_by_venta_id(id_venta)

        # 5. Obtener Liquidación Detallada (Costos)
        liquidaciones = controller.get_liquidaciones_venta(id_venta)

        # 6. Empaquetar
        data_hoja = {
            "venta": v_data,
            "itinerario": it_venta,
            "pasajeros": pasajeros,
            "liquidaciones": liquidaciones
        }
        
        # Generar Excel
        master_buffer = xl_ctrl.generar_hoja_servicio_maestra_xlsx(data_hoja)
        
        if master_buffer:
            st.download_button(
                label=label,
                data=master_buffer,
                file_name=f"informe_maestro_{id_venta}_{data_hoja['venta']['nombre_cliente'].replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Expediente completo: Resumen Financiero, Logística, Costos Detallados y Pasajeros.",
                key=key or f"dl_mast_{id_venta}",
                use_container_width=True,
                type="primary"
            )
            
    except Exception as e:
        st.error(f"Error generando Hoja de Servicio: {e}")

# Renderiza el Botón para el PDF del Itinerario Simple.
def render_itinerary_simple_download(render):
    if not render:
        st.warning("No hay datos de itinerario para descargar.")
        return

    from controllers.pdf_controller import PDFController
    pdf_ctrl = PDFController()
    
    from controllers.excel_controller import ExcelController
    xl_ctrl = ExcelController()
    
    # Extraer parámetros de enriquecimiento si existen
    nombre_pax = render.get('nombre_pasajero')
    total_pax = render.get('num_pasajeros')
    
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
            # Generar el Excel en memoria con parámetros forzados
            xlsx_buffer = xl_ctrl.generar_resumen_itinerario_xlsx(render, nombre_cliente=nombre_pax, num_pax=total_pax)
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

def render_centro_alertas(controller):
    """
    Componente visual que muestra alertas operativas divididas por urgencia (colores).
    Reglas: 1-2 días Rojo, 3-5 Amarillo, 6-10 Verde.
    Pestaña especial: Machu Picchu (Tickets MINISTERIO).
    """
    with st.expander("🔔 CENTRO DE ALERTAS OPERATIVAS (Urgente)", expanded=True):
        alertas = controller.get_alertas_operativas()
        
        if "error" in alertas and alertas["error"]:
            st.error(f"Error Técnico en Base de Datos: {alertas['error']}")
            with st.expander("Ver Detalle Técnico"):
                st.code(alertas.get('trace', ''))
            return
            
        # Pestañas para el semáforo
        # Formatear etiquetas con conteo
        t_mp = f"🏛️ MP Tickets ({len(alertas['machupicchu'])})"
        t_r = f"🔴 Crítico ({len(alertas['rojo'])})"
        t_sa = f"⚠️ Sin Asignar ({len(alertas['sin_asignar'])})"
        t_a = f"🟡 Atención ({len(alertas['amarillo'])})"
        t_v = f"🟢 Preventivo ({len(alertas['verde'])})"
        
        tabs = st.tabs([t_mp, t_r, t_sa, t_a, t_v])
        
        def mostrar_tabla_alertas(lista_alertas, empty_msg, show_proveedor=True):
            if not lista_alertas:
                st.info(empty_msg)
                return
            
            df = pd.DataFrame(lista_alertas)
            # Ordenar por días
            df = df.sort_values(by="dias")
            
            cols = ["fecha", "servicio", "cliente", "proveedor", "dias"]
            if not show_proveedor:
                cols.remove("proveedor")

            st.dataframe(
                df,
                column_order=cols,
                column_config={
                    "fecha": "📅 Fecha",
                    "servicio": "🚙 Servicio / Tour",
                    "cliente": "👤 Cliente",
                    "proveedor": "🤝 Proveedor",
                    "dias": st.column_config.NumberColumn("⏰ Días Falta", format="%d d")
                },
                use_container_width=True,
                hide_index=True
            )

        with tabs[0]: 
            st.markdown("### 🏛️ Tickets Machu Picchu (MINISTERIO)")
            st.caption("Todos los ingresos pendientes asignados al proveedor del estado.")
            mostrar_tabla_alertas(alertas['machupicchu'], "No hay tickets de MP pendientes.")
            
        with tabs[1]:
            st.markdown("### 🔴 Alertas Críticas (0 a 2 días)")
            st.caption("Servicios inminentes que no han sido marcados como 'Terminado'.")
            mostrar_tabla_alertas(alertas['rojo'], "No hay alertas críticas pendientes.")

        with tabs[2]:
            st.markdown("### ⚠️ Servicios Sin Asignar (Riesgo Alto)")
            st.error("Estos servicios están en el itinerario pero NO tienen costos ni proveedores registrados. Las alertas de colores NO funcionarán para estos casos si no se completan.")
            mostrar_tabla_alertas(alertas['sin_asignar'], "Todos los servicios dentro de los próximos 10 días tienen asignaciones.")
            
        with tabs[3]:
            st.markdown("### 🟡 Alertas de Atención (3 a 5 días)")
            st.caption("Servicios próximos que requieren verificación operativa.")
            mostrar_tabla_alertas(alertas['amarillo'], "No hay alertas de atención pendientes.")
            
        with tabs[4]:
            st.markdown("### 🟢 Alertas Preventivas (6 a 10 días)")
            st.caption("Servicios programados para la próxima semana.")
            mostrar_tabla_alertas(alertas['verde'], "No hay alertas preventivas pendientes.")

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
        # --- TABLAR INTERACTIVA DE SERVICIOS (REDISEÑO) ---
        c_head = st.columns([0.8, 2.5, 0.6, 2, 1.2])
        c_head[0].markdown("**Hora**")
        c_head[1].markdown("**Servicio**")
        c_head[2].markdown("**Pax**")
        c_head[3].markdown("**Cliente**")
        c_head[4].markdown("**📄 Info**")
        st.markdown("<hr style='margin:0; border:0.5px solid #555;'>", unsafe_allow_html=True)

        for i, s in enumerate(servicios):
            with st.container():
                c_row = st.columns([0.8, 2.5, 0.6, 2, 1.2])
                c_row[0].write(s.get('Hora', '---'))
                
                # Nombre del servicio con indicador de endoso
                serv_name = f"🤝 {s['Servicio']}" if s.get('Endoso?') else s['Servicio']
                c_row[1].write(f"**{serv_name}**")
                
                c_row[2].write(f"**{s.get('Pax', 1)}**")
                c_row[3].write(s.get('Cliente', '---'))
                
                with c_row[4]:
                    id_v = s.get('ID Venta')
                    if id_v:
                        render_operational_master_download(controller, id_v, label="📁 Maestro", key=f"dl_cal_{id_v}_{i}")
                    else:
                        st.caption("Sin Venta")
                st.markdown("<hr style='margin:0; border:0.1px solid #333;'>", unsafe_allow_html=True)

        st.info("💡 Haz clic en '📁 Maestro' para descargar el expediente completo del pasajero.")

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
    from controllers.lead_controller import LeadController
    import json

    venta_controller = VentaController(supabase_client)
    it_controller = ItinerarioDigitalController(supabase_client)
    lead_controller = LeadController(supabase_client)

    st.subheader("🤝 Registro de Venta B2B (Agencias & Partners)")

    # ═══════════════════════════════════════════════════════════════
    # 1️⃣ SELECTOR DE ITINERARIO (Diseño Cloud)
    # ═══════════════════════════════════════════════════════════════
    # Mostrar itinerarios recientes de forma global para B2B
    itinerarios_recuperados = it_controller.obtener_todos_recientes(limit=50)
    
    opciones_itinerario = ["--- Sin Itinerario ---"]
    mapa_itinerarios = {}
    
    if itinerarios_recuperados:
        # 1. Ordenar por antigüedad (fecha_generacion ascendente)
        itinerarios_recuperados.sort(key=lambda x: x.get('fecha_generacion', ''))
        
        # 2. Contador para versiones
        conteos = {}

        for it in itinerarios_recuperados:
            render_data = it.get('datos_render') # Supabase py suele devolverlo como dict si es jsonb
            if isinstance(render_data, str):
                try: render_data = json.loads(render_data)
                except: render_data = {}
            
            # Asegurar que sea un dict
            if not isinstance(render_data, dict):
                render_data = {}

            # --- FILTRO B2B: Solo mostrar itinerarios generados como B2B ---
            # Robustez: Si no hay metadata, por defecto es B2C
            metadata = render_data.get('metadata')
            if not isinstance(metadata, dict):
                metadata = {}
            
            tipo_v = metadata.get('tipo_venta', 'B2C')
            if tipo_v != 'B2B':
                continue

            titulo = render_data.get('titulo', '')
            if not titulo:
                t1, t2 = render_data.get('title_1', ''), render_data.get('title_2', '')
                titulo = f"{t1} {t2}".strip() or 'Sin título'
            
            pax_itin = it.get('nombre_pasajero_itinerario') or render_data.get('pasajero', 'Sin Nombre')
            fecha = it.get('fecha_generacion', '')[:10] if it.get('fecha_generacion') else 'Sin fecha'
            
            # Label descriptivo base
            base_label = f"[{fecha}] {pax_itin} - {titulo}"
            
            # Manejo de Versiones (V1, V2...)
            conteos[base_label] = conteos.get(base_label, 0) + 1
            ver = conteos[base_label]
            
            label_final = f"{base_label} - V{ver}"
            opciones_itinerario.append(label_final)
            mapa_itinerarios[label_final] = it
    
    def_cant_pax = 1

    if len(opciones_itinerario) == 1:
        st.warning("⚠️ No se encontraron itinerarios marcados como **B2B**. ¿Olvidaste marcar la casilla 'Venta B2B' al diseñarlo?")
        if st.checkbox("🔍 Buscar también en itinerarios B2C (Solo para vincular errores)"):
            # Re-procesar itinerarios sin el filtro B2B
            for it in itinerarios_recuperados:
                r_d = it.get('datos_render')
                if isinstance(r_d, str):
                    try: r_d = json.loads(r_d)
                    except: r_d = {}
                
                # Obtener título y pax igual que arriba
                tit = r_d.get('titulo') or f"{r_d.get('title_1','')} {r_d.get('title_2','')}".strip() or 'Sin Título'
                pax_i = it.get('nombre_pasajero_itinerario') or (r_d.get('pasajero') if isinstance(r_d, dict) else 'Sin Nombre')
                f_i = it.get('fecha_generacion', '')[:10] if it.get('fecha_generacion') else 'Sin fecha'
                
                lab = f"📦 [B2C] {f_i} - {pax_i} - {tit}"
                if lab not in opciones_itinerario:
                    opciones_itinerario.append(lab)
                    mapa_itinerarios[lab] = it

    itinerario_seleccionado = st.selectbox(
        "✨ Seleccionar Itinerario Visual (Diseño Cloud)", 
        opciones_itinerario,
        help="Seleccione el diseño que corresponde a esta venta B2B"
    )

    # ═══════════════════════════════════════════════════════════════
    # 2️⃣ AUTO-COMPLETADO Y DATOS SUGERIDOS
    # ═══════════════════════════════════════════════════════════════
    id_itinerario_dig = None
    def_pax = ""
    def_tour = ""
    def_cel = ""
    def_precio_total = 0.0
    def_moneda = 'USD'
    def_f_inicio = date.today()
    def_f_fin = date.today()
    def_cant_pax = 1

    if itinerario_seleccionado != "--- Sin Itinerario ---":
        it_data = mapa_itinerarios.get(itinerario_seleccionado)
        if it_data:
            id_itinerario_dig = it_data.get('id_itinerario_digital')
            id_lead_from_itinerario = it_data.get('id_lead')
            render = it_data.get('datos_render', {})
            if isinstance(render, str):
                import json
                try: render = json.loads(render)
                except: render = {}

            def_pax = it_data.get('nombre_pasajero_itinerario', '') or render.get('pasajero', '') or def_pax
            def_tour = render.get('titulo', '') or f"{render.get('title_1', '')} {render.get('title_2', '')}".strip()
            
            # Fechas y Pax
            f_viaje = render.get('fecha_viaje')
            if f_viaje:
                try: 
                    f_clean = f_viaje.replace(" ", "")
                    if '/' in f_clean:
                        from datetime import datetime
                        def_f_inicio = datetime.strptime(f_clean, "%d/%m/%Y").date()
                    else:
                        def_f_inicio = date.fromisoformat(f_clean)
                except: pass
            
            def_f_fin = def_f_inicio
            duracion_raw = render.get('duracion')
            if duracion_raw and isinstance(duracion_raw, str) and 'D' in duracion_raw.upper():
                try:
                    num_dias_str = ''.join(filter(str.isdigit, duracion_raw.split('D')[0]))
                    if num_dias_str: def_f_fin = def_f_inicio + timedelta(days=int(num_dias_str) - 1)
                except: pass
            
            def_cant_pax = int(render.get('cantidad_pax') or 1)

            # --- INICIALIZACIÓN DE VARIABLES PARA AUTO-COMPLETADO ---
            items_extraidos = []
            tipos_vistos = set()
            ci = render.get('control_interno', {})
            tc_itin = ci.get('tipo_cambio_aplicado', 3.8)
            try: tc_itin = float(tc_itin or 3.8)
            except: tc_itin = 3.8

            # 1. PRIORIDAD: Precios Cierre (Itinerario Automático)
            precios_cierre = render.get('precios_cierre', [])
            if precios_cierre and isinstance(precios_cierre, list):
                for pc in precios_cierre:
                    label = pc.get('label', '').upper()
                    m_raw = pc.get('monto_total', 0) or 0
                    try: monto_total = float(str(m_raw).replace(',', ''))
                    except: monto_total = 0.0
                    simbolo = pc.get('simbolo', '$')
                    
                    t_code = 'NACIONAL' if 'NACIONAL' in label else ('EXTRANJERO' if 'EXTRANJERO' in label else 'CAN')
                    es_usd = (simbolo == '$')
                    
                    # Conteo de pax desde desglose_pasajeros
                    pax_info = ci.get('desglose_pasajeros', {}).get(t_code.lower(), {})
                    c_f = sum(int(v or 0) for v in pax_info.values()) if isinstance(pax_info, dict) else 0
                    if not c_f: c_f = 1 # Fallback a 1 pax para no romper división
                    
                    p_f_soles = monto_total * tc_itin if es_usd else monto_total
                    items_extraidos.append({
                        "descripcion": f"Pax {t_code.capitalize()} (Auto-Total)", 
                        "cantidad": int(c_f), 
                        "precio_unitario": p_f_soles / int(c_f), 
                        "tipo": t_code, 
                        "p_raw": monto_total / int(c_f),
                        "moneda": "USD" if es_usd else "PEN"
                    })
                    tipos_vistos.add(t_code)

            # 2. SEGUNDA OPCIÓN: Precios Estructurados (Manual Nuevo o Auto-Compacto)
            precios_meta = render.get('precios', {})
            if not items_extraidos and precios_meta:
                # Mapeo de claves posibles
                mapeo_p = [('NACIONAL', ['nacional', 'nac']), ('EXTRANJERO', ['extranjero', 'ext']), ('CAN', ['can'])]
                for t_code, keys in mapeo_p:
                    p_data = None
                    for k in keys:
                        p_data = precios_meta.get(k)
                        if p_data is not None: break
                    
                    if p_data is not None:
                        # Extraer monto
                        try:
                            if isinstance(p_data, dict): 
                                m_raw = p_data.get('total') or p_data.get('monto') or 0
                                p_raw = float(str(m_raw).replace(',', ''))
                            else: 
                                p_raw = float(str(p_data).replace(',', ''))
                        except:
                            p_raw = 0.0
                        
                        if p_raw > 0:
                            # Moneda
                            moneda_key = f"moneda_{t_code.lower()}"
                            moneda_fix = precios_meta.get(moneda_key)
                            es_usd = (moneda_fix == "USD") if moneda_fix else (t_code in ['EXTRANJERO', 'CAN'])
                            
                            # Conteo
                            c_f = int(render.get(f'num_pax_{t_code.lower()[0:3]}', 1) or 1)
                            
                            p_f_soles = p_raw * tc_itin if es_usd else p_raw
                            items_extraidos.append({
                                "descripcion": f"Pax {t_code.capitalize()} (Precio)", 
                                "cantidad": c_f, "precio_unitario": p_f_soles, "tipo": t_code, "p_raw": p_raw,
                                "moneda": "USD" if es_usd else "PEN"
                            })
                            tipos_vistos.add(t_code)

            # 3. FALLBACK LEGACY: Raíz (num_pax_nac, etc.)
            if not items_extraidos:
                fallbacks = [
                    ('NACIONAL', ['num_pax_nac', 'pax_nac', 'num_pax_nacional'], ['precio_nacional', 'p_nac']),
                    ('EXTRANJERO', ['num_pax_ext', 'pax_ext', 'num_pax_extranjero'], ['precio_extranjero', 'p_ext']),
                    ('CAN', ['num_pax_can', 'pax_can'], ['precio_can', 'p_can'])
                ]
                for t_code, c_keys, p_keys in fallbacks:
                    if t_code not in tipos_vistos:
                        c_f = 0
                        for ck in c_keys:
                            c_f = int(render.get(ck, 0) or 0)
                            if c_f > 0: break
                        if c_f > 0:
                            p_f_raw = 0.0
                            for pk in p_keys:
                                val_pk = render.get(pk, 0) or 0
                                try: p_f_raw = float(str(val_pk).replace(',', ''))
                                except: p_f_raw = 0.0
                                if p_f_raw > 0: break
                            p_f_soles = p_f_raw * tc_itin if t_code in ['EXTRANJERO', 'CAN'] else p_f_raw
                            items_extraidos.append({
                                "descripcion": f"Pax {t_code.capitalize()} (Legacy)", "cantidad": c_f, "precio_unitario": p_f_soles, "tipo": t_code, "p_raw": p_f_raw,
                                "moneda": "USD" if t_code in ['EXTRANJERO', 'CAN'] else "PEN"
                            })
                pax_gen = render.get('cantidad_pax') or render.get('pax_count') or render.get('num_pax') or 0
                if not pax_gen and ci: 
                    pax_gen = ci.get('total_pasajeros') or ci.get('total_pax') or 0
                
                if pax_gen:
                    p_sug_raw = render.get('total_final_calculado') or render.get('precio_cierre') or 0
                    try: p_sug_val = float(str(p_sug_raw).replace(',', ''))
                    except: p_sug_val = 0.0
                    items_extraidos.append({
                        "descripcion": "Pax (Itinerario)", 
                        "cantidad": int(pax_gen), 
                        "precio_unitario": p_sug_val / int(pax_gen) if int(pax_gen) > 0 else 0,
                        "tipo": "NACIONAL", 
                        "p_raw": p_sug_val
                    })

            # Cálculo de Total Final en Soles
            total_soles = sum(it['cantidad'] * it['precio_unitario'] for it in items_extraidos)

            if id_itinerario_dig:
                # Actualizar siempre los items en sesión B2B
                st.session_state[f"b2b_items_{id_itinerario_dig}"] = items_extraidos

                if id_itinerario_dig != st.session_state.get('b2b_last_itin_v2'):
                    st.session_state['b2b_m_total'] = total_soles
                    st.session_state['b2b_moneda_auto'] = 'PEN'
                    st.session_state['b2b_last_itin_v2'] = id_itinerario_dig
                    st.success(f"✅ Itinerario cargado: **{def_tour}** (Total calculado: S/ {total_soles:,.2f})")
                else:
                    st.success(f"✅ Itinerario cargado: **{def_tour}**")

    # ═══════════════════════════════════════════════════════════════
    # 4️⃣ BALANCE INTERACTIVO (Igual que Ventas Directas)
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 💰 Detalles de Pago B2B")
    c_p0, c_p1, c_p2, c_p3 = st.columns([1, 1.5, 1.5, 1.5])
    
    monedas_list = ["USD", "PEN"]
    m_auto = st.session_state.get('b2b_moneda_auto', 'USD')
    
    # --- MOSTRAR SUB-TOTALES POR NACIONALIDAD B2B (PEDIDO USUARIO) ---
    if id_itinerario_dig:
        items_ref_b2b = st.session_state.get(f"b2b_items_{id_itinerario_dig}", [])
        if items_ref_b2b:
            # Ahora filtramos por la MONEDA real del item, no solo el tipo
            sub_soles = sum(it['cantidad'] * it['p_raw'] for it in items_ref_b2b if it.get('moneda') == 'PEN')
            sub_dolares = sum(it['cantidad'] * it['p_raw'] for it in items_ref_b2b if it.get('moneda') == 'USD')
            
            st.markdown(f"📊 **SUB-TOTALES POR MONEDA:** Soles: **S/ {sub_soles:,.2f}** | Dólares: **$ {sub_dolares:,.2f}**")

    idx_m = monedas_list.index(m_auto) if m_auto in monedas_list else 0
    moneda_sel = c_p0.selectbox("Moneda", monedas_list, index=idx_m, key="b2b_final_moneda", disabled=(id_itinerario_dig is not None))
    
    # TC: Tipo de Cambio "Foto"
    tipo_cambio = c_p1.number_input("TC (Foto)", min_value=0.0, value=3.80, format="%.3f", key="b2b_tc")

    # --- RECÁLCULO DINÁMICO B2B: Usar el TC del usuario para actualizar el total ---
    if id_itinerario_dig and tipo_cambio > 0:
        items_recalc_b2b = st.session_state.get(f"b2b_items_{id_itinerario_dig}", [])
        if items_recalc_b2b:
            nuevo_total_b2b = 0.0
            for it in items_recalc_b2b:
                if it.get('moneda') == "USD":
                    nuevo_total_b2b += it['cantidad'] * it['p_raw'] * tipo_cambio
                else:
                    nuevo_total_b2b += it['cantidad'] * it['p_raw']
            st.session_state['b2b_m_total'] = round(nuevo_total_b2b, 2)

    if 'b2b_m_total' not in st.session_state: st.session_state['b2b_m_total'] = 0.0
    if 'b2b_m_pago' not in st.session_state: st.session_state['b2b_m_pago'] = 0.0
    
    monto_total = c_p2.number_input(f"Monto Total ({moneda_sel})", min_value=0.0, format="%.2f", key="b2b_m_total", disabled=(id_itinerario_dig is not None))
    monto_pagado = c_p3.number_input(f"Adelanto Agencia ({moneda_sel})", min_value=0.0, format="%.2f", key="b2b_m_pago")
    
    # --- MOSTRAR CONVERSIÓN EN TIEMPO REAL (B2B) ---
    if tipo_cambio > 0:
        if moneda_sel == "USD":
            c_p2.caption(f"🛡️ Equiv: **S/ {monto_total * tipo_cambio:,.2f}**")
            c_p3.caption(f"🛡️ Equiv: **S/ {monto_pagado * tipo_cambio:,.2f}**")
        else:
            c_p2.caption(f"🛡️ Equiv: **$ {monto_total / tipo_cambio:,.2f}**")
            c_p3.caption(f"🛡️ Equiv: **$ {monto_pagado / tipo_cambio:,.2f}**")

    saldo = monto_total - monto_pagado
    if monto_total > 0:
        if saldo <= 0.01: 
            st.success(f"✅ **VENTA B2B SALDADA**")
        else:
            # Mostrar saldo bilingüe
            if moneda_sel == "USD":
                info_s = f"⏳ **SALDO PENDIENTE AGENCIA: ${saldo:,.2f}** (S/ {saldo * tipo_cambio:,.2f})"
            else:
                info_s = f"⏳ **SALDO PENDIENTE AGENCIA: S/ {saldo:,.2f}** (${saldo / tipo_cambio:,.2f})"
            st.warning(info_s)

    # ═══════════════════════════════════════════════════════════════
    # 5️⃣ FORMULARIO DE REGISTRO
    # ═══════════════════════════════════════════════════════════════
    with st.form("form_b2b_redesigned"):
        col1, col2 = st.columns(2)
        
        # Agencia / Proveedor (Mandatorio)
        agencias = venta_controller.obtener_agencias_aliadas()
        nombres_ag = [a['nombre'] for a in agencias]
        mapa_ag = {a['nombre']: a['id_agencia'] for a in agencias}
        
        prov_final = col1.selectbox("🏢 Agencia / Partner Responsable", ["--- Seleccione ---"] + nombres_ag)
        
        is_disabled = bool(id_itinerario_dig)
        pax_name = col1.text_input("Pasajero Principal", value=def_pax, disabled=False)
        tel_pax = col1.text_input("Celular Contacto", value=def_cel)
        
        vendedor_log = st.session_state.get('user_id', 'Operaciones')
        col1.markdown(f"👤 **Vendedor Resp:** {vendedor_log}")

        tour_name = col2.text_input("Nombre del Programa B2B", value=def_tour, disabled=False)
        tipo_comp = col2.radio("Comprobante para Agencia", ["Boleta", "Factura", "Recibo Simple"], horizontal=True, key="b2b_tipo_comp_v2")
        metodo_pago = col2.selectbox("💳 Método de Pago", ["EFECTIVO", "TRANSFERENCIA", "YAPE", "PLIN", "TARJETA", "PAYPAL", "OTRO"], key="b2b_metodo_pago_v2")
        
        # --- NUEVO: FECHAS MANUALES SI NO HAY ITINERARIO ---
        if not id_itinerario_dig:
            c_f1, c_f2 = st.columns(2)
            def_f_inicio = c_f1.date_input("Fecha Inicio", value=def_f_inicio)
            def_f_fin = c_f2.date_input("Fecha Fin", value=def_f_fin)

        # --- DESGLOSE DE INGRESOS B2B (MÁS ROBUSTO) ---
        items_ingreso = []
        if id_itinerario_dig:
            cached_items_b2b = st.session_state.get(f"b2b_items_{id_itinerario_dig}", [])
            if cached_items_b2b:
                for it in cached_items_b2b:
                    desc_b2b = it['descripcion']
                    if it['tipo'] in ['EXTRANJERO', 'CAN']:
                        desc_b2b += f" (Ref: ${it['p_raw']:.2f} x {tc_itin})"
                    
                    items_ingreso.append({
                        "descripcion": desc_b2b,
                        "cantidad": it['cantidad'],
                        "precio_unitario": it['precio_unitario']
                    })
                    st.info(f"✨ **{desc_b2b}**: Se han cargado **{it['cantidad']}** pax a **S/ {it['precio_unitario']:,.2f}** c/u.")
            else:
                st.warning("⚠️ No se pudo procesar el desglose B2B automático.")
        else:
            st.caption("No hay itinerario vinculado. El desglose se generará automáticamente por el total.")


        st.divider()
        submitted = st.form_submit_button("✅ REGISTRAR VENTA B2B Y NOTIFICAR", use_container_width=True, type="primary")

        if submitted:
            if prov_final == "--- Seleccione ---":
                st.error("❌ Debe seleccionar una Agencia/Partner.")
            elif not pax_name or not tour_name:
                st.error("❌ El nombre del pasajero y del programa son obligatorios.")
            elif monto_total <= 0:
                st.error("❌ El monto total debe ser mayor a 0.")
            else:
                id_age = mapa_ag.get(prov_final)
                exito, msg = venta_controller.registrar_venta_proveedor(
                    nombre_proveedor=prov_final,
                    nombre_cliente=pax_name,
                    telefono=tel_pax,
                    vendedor=vendedor_log,
                    tour=tour_name,
                    monto_total=monto_total,
                    monto_depositado=monto_pagado,
                    id_agencia_aliada=id_age,
                    fecha_inicio=def_f_inicio.isoformat(),
                    fecha_fin=def_f_fin.isoformat(),
                    cantidad_pax=def_cant_pax,
                    id_itinerario_digital=id_itinerario_dig,
                    id_lead=None,
                    tipo_comprobante=tipo_comp,
                    tipo_cambio=tipo_cambio,
                    items_ingreso=items_ingreso if items_ingreso else None,
                    metodo_pago=metodo_pago
                )
                
                if exito:
                    st.success(f"🚀 {msg}")
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
                        render_data = res.data['datos_render']
                        if isinstance(render_data, str):
                            import json
                            render_data = json.loads(render_data)
                            
                        if isinstance(render_data, dict):
                            # Enriquecer con datos de la fila de auditoría
                            dr = ventas_con_itin[ventas_con_itin['ID Venta'] == sel_id_v].iloc[0]
                            render_data['num_pasajeros'] = dr.get('num_pasajeros') or dr.get('Pax', 1)
                            render_data['ninos'] = dr.get('ninos', 0)
                            
                            # Rescate de nombre seguro
                            new_name = dr.get('Cliente')
                            if new_name and str(new_name).strip() not in ["", "---", "None", "Desconocido"]:
                                render_data['nombre_pasajero'] = new_name
                                
                            render_itinerary_simple_download(render_data)
            else:
                st.info("Seleccione un servicio con itinerario para ver su detalle.")

def mostrar_pagina(nombre_modulo, rol_actual, user_id, supabase_client):
    """Punto de entrada de Streamlit para el área de Operaciones."""
    import controllers.operaciones_controller
    import controllers.venta_controller
    import models.venta_model
    import importlib
    
    # Forzar recarga de módulos para captar cambios en clases
    importlib.reload(models.venta_model)
    importlib.reload(controllers.operaciones_controller)
    importlib.reload(controllers.venta_controller)
    
    controller = controllers.operaciones_controller.OperacionesController(supabase_client)
    
    st.title("⚙️ Gestión de Operaciones")
    
    # --- 🔔 NUEVO: CENTRO DE ALERTAS ---
    render_centro_alertas(controller)
    
    st.markdown("---")
    
    if nombre_modulo in ["Gestión de Registros", "Logística y Proveedores"]:
        tab1, tab2, tab3 = st.tabs([
            "📊 Estructurador de Gastos (Master Sheet)",
            "🤝 Ventas B2B (Entrada)",
            "🏢 Directorio de Proveedores"
        ])
        
        with tab1:
            dashboard_simulador_costos(controller)
            
        with tab2:
            registro_ventas_proveedores(supabase_client)

        with tab3:
            render_directorio_proveedores(supabase_client)

    elif nombre_modulo == "Dashboard Diario":
        dashboard_tablero_diario(controller)
    elif nombre_modulo == "Reporte Operativo":
        reporte_operativo(controller)
    else:
        st.info("Seleccione una opción válida del menú lateral.")
            
# Función dashboard_pasajeros eliminada por simplificación de procesos
            
            


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
            v = mapa_ventas_pax.get(pax_sel)
            
            # Solo cargar si ha cambiado la venta para evitar bucles de rerun
            if st.session_state.get('last_loaded_id_venta') != v['id_venta']:
                st.session_state['master_pax_count'] = v.get('num_pasajeros', 1)
                
                # Actualizar venta actual
                st.session_state['last_loaded_id_venta'] = v['id_venta']
                st.rerun()

    # Carga de Archivos
    id_venta_act = st.session_state.get('last_loaded_id_venta')
    if not id_venta_act:
        st.info("Seleccione una venta para gestionar su información.")
        return

    # --- NUEVO: RECUPERAR DATOS DEL ITINERARIO PARA DESCARGA ---
    try:
        # Recuperar Venta Live de forma estándar (sin alias complejos para evitar fallos de PostgREST)
        res_v_live = controller.client.table('venta').select('*, cliente(nombre)').eq('id_venta', id_venta_act).single().execute()
        v_live = res_v_live.data or {}
        
        id_itin_dig = v_live.get('id_itinerario_digital')
        render_data = None
        try:
            if id_itin_dig:
                res_render = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_dig).single().execute()
                if res_render.data:
                    render_data = res_render.data.get('datos_render')
                    if isinstance(render_data, str):
                        import json
                        render_data = json.loads(render_data)
                    
                    if isinstance(render_data, dict):
                        # Rescate de nombre infalible
                        cliente_obj = v_live.get('cliente') or {}
                        # PostgREST a veces devuelve el objeto directo o en una lista de 1 elemento
                        nombre_raw = "CLIENTE"
                        if isinstance(cliente_obj, dict):
                            nombre_raw = cliente_obj.get('nombre')
                        elif isinstance(cliente_obj, list) and len(cliente_obj) > 0:
                            nombre_raw = cliente_obj[0].get('nombre')
                        
                        # Si sigue sin haber nombre, usar el del itinerario o un fallback genérico
                        nombre_final = nombre_raw or render_data.get('nombre_pasajero') or "CLIENTE"
                        
                        # Limpieza final: si es "---" o similar, forzar a "CLIENTE"
                        if str(nombre_final).strip() in ["", "---", "None", "Desconocido"]:
                            nombre_final = "CLIENTE"
                            
                        render_data['nombre_pasajero'] = str(nombre_final).upper()
                        render_data['num_pasajeros'] = v_live.get('num_pasajeros', 1)
                        render_data['ninos'] = v_live.get('ninos', 0)
                        render_data['fecha_inicio'] = v_live.get('fecha_inicio')
                        render_data['fecha_fin'] = v_live.get('fecha_fin')
                        
                        # Carga tours en vivo para sincronizar fechas
                        res_vt = controller.client.table('venta_tour').select('fecha_servicio').eq('id_venta', id_venta_act).order('n_linea').execute()
                        live_tours = res_vt.data or []
                        
                        itin_list = (render_data.get('itinerario_detalles') or 
                                     render_data.get('days') or 
                                     render_data.get('itinerario') or [])
                        
                        # Asegurar que itin_list es una lista mutable
                        if isinstance(itin_list, list):
                            for i, tour_live in enumerate(live_tours):
                                if i < len(itin_list) and isinstance(itin_list[i], dict):
                                    # Sincronizar ÚNICAMENTE la fecha operativa para el reporte
                                    itin_list[i]['fecha'] = tour_live.get('fecha_servicio') or itin_list[i].get('fecha')
                            
                            render_data['itinerario_detalles'] = itin_list
                    
                    # Renderizar los botones de descarga
                    if render_data:
                        with st.expander("📄 Ver Resumen de Itinerario (Simplificado)", expanded=False):
                            render_itinerary_simple_download(render_data)
        except Exception as e:
            st.warning(f"Nota: No se pudo cargar el resumen del itinerario PDF/Simple. ({e})")
        
        # --- SECCIÓN: EXPEDIENTE DIGITAL (DRIVE) ---
        st.markdown("### 📂 Expediente Digital")
        c_drive_1, c_drive_2 = st.columns([4, 1])
        with c_drive_1:
            url_actual = v_live.get('drive_url') or ""
            url_nueva = st.text_input("Link a Carpeta de Google Drive:", value=url_actual, placeholder="Pegue aquí el enlace del Drive del pasajero", key="drive_input")
        with c_drive_2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Guardar Link", use_container_width=True):
                try:
                    controller.client.table('venta').update({'drive_url': url_nueva}).eq('id_venta', id_venta_act).execute()
                    st.toast("✅ Enlace de Drive actualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar link: {e}")
        
        if url_actual:
            st.link_button("👉 Abrir Carpeta de Archivos (Drive)", url_actual, use_container_width=True, type="secondary")

        # Botón Maestro Operativo (Independiente del Itinerario Digital)
        # Se pone fuera del bloque anterior para que funcione aunque no haya Itinerario JSON
        st.markdown("---")
        render_operational_master_download(controller, id_venta_act)
    except Exception as e:
        st.error(f"❌ Error crítico en sección de descargas: {e}")

    # --- SECCIÓN DE ARCHIVOS (CSV/Excel) ---
    st.markdown("### 📝 Gestión de Información Externa")
    st.info("Suba los archivos correspondientes para el cierre y control de pasajeros.")

    # NUEVO: Botón de Plantilla
    import io
    template_df = pd.DataFrame(columns=["Dia", "Tipo_Servicio", "Proveedor", "Moneda", "Costo Unitario", "Pax"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Plantilla')
    
    st.download_button(
        label="📥 Descargar Plantilla Excel para Endoses",
        data=buffer.getvalue(),
        file_name="plantilla_endoses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    c_arch1, c_arch2 = st.columns(2)
    with c_arch1:
        st.subheader("📊 Liquidación")
        f_liq = st.file_uploader("Cierre de Operaciones (Excel/CSV):", type=['xlsx', 'xls', 'csv'], key="up_liqrar_final")
        
        # PROCESAMIENTO DE ENDOSES
        if f_liq:
            try:
                # Cargar datos
                if f_liq.name.endswith('.csv'):
                    df_preview = pd.read_csv(f_liq)
                else:
                    df_preview = pd.read_excel(f_liq)
                
                # Previsualización
                st.write("**Previsualización de datos a cargar:**")
                st.dataframe(df_preview, use_container_width=True, hide_index=True)
                
                # Validar columnas
                cols_req = ["Dia", "Tipo_Servicio", "Proveedor", "Moneda", "Costo Unitario", "Pax"]
                if all(c in df_preview.columns for c in cols_req):
                    if st.button("📦 Procesar y Guardar Endoses en DB", type="primary", use_container_width=True):
                        # Llamar al controlador (estamos en dashboard_simulador_costos(controller))
                        res_bulk = controller.vincular_endoses_masivos(st.session_state['last_loaded_id_venta'], df_preview)
                        
                        if res_bulk['exitos'] > 0:
                            st.success(f"✅ Se vincularon {res_bulk['exitos']} registros correctamente.")
                        if res_bulk['errores']:
                            with st.expander("⚠️ Ver errores de carga"):
                                for err in res_bulk['errores']:
                                    st.error(err)
                        
                        if res_bulk['exitos'] > 0:
                            st.balloons()
                            st.rerun()
                else:
                    st.error(f"El archivo debe tener las columnas: {', '.join(cols_req)}")
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

    with c_arch2:
        st.subheader("👥 Pasajeros")
        # Botón de Plantilla Pax
        pax_template_df = pd.DataFrame(columns=['Nombre Completo', 'Documento', 'Tipo Doc', 'Nacionalidad', 'Fecha Nacimiento', 'Genero', 'Cuidados', 'Es Principal'])
        pax_buffer = io.BytesIO()
        with pd.ExcelWriter(pax_buffer, engine='openpyxl') as writer:
            pax_template_df.to_excel(writer, index=False, sheet_name='Rooming')
        
        st.download_button(
            label="📥 Descargar Plantilla Rooming",
            data=pax_buffer.getvalue(),
            file_name="plantilla_rooming.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        f_pax = st.file_uploader("Lista de Pasajeros / Rooming (Excel/CSV):", type=['xlsx', 'xls', 'csv'], key="up_paxrar_final")
        if f_pax:
            try:
                if f_pax.name.endswith('.csv'):
                    df_pax = pd.read_csv(f_pax)
                else:
                    df_pax = pd.read_excel(f_pax)
                
                st.dataframe(df_pax, use_container_width=True, hide_index=True)
                
                if st.button("👥 Cargar Rooming a la DB", type="primary", use_container_width=True):
                    res_pax = controller.vincular_pasajeros_masivos(st.session_state['last_loaded_id_venta'], df_pax)
                    if res_pax['exitos'] > 0:
                        st.success(f"✅ Se cargaron {res_pax['exitos']} pasajeros.")
                    if res_pax['errores']:
                        with st.expander("⚠️ Errores"):
                            for e in res_pax['errores']: st.error(e)
                    if res_pax['exitos'] > 0:
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # --- SECCIÓN: RESUMEN DE ASIGNACIONES (VISUALIZACIÓN) ---
    c_res1, c_res2 = st.columns(2)
    
    with c_res1:
        st.markdown("### 📋 Resumen de Liquidaciones (Costos)")
        try:
            id_actual = st.session_state.get('last_loaded_id_venta')
            # 1. Obtener Itinerario base (Días) y Moneda/TC de la Venta
            res_v = controller.client.table('venta').select('moneda, tipo_cambio').eq('id_venta', id_actual).single().execute()
            v_meta = res_v.data or {"moneda": "USD", "tipo_cambio": 3.8}
            moneda_v = v_meta.get('moneda', 'USD')
            tc_v = float(v_meta.get('tipo_cambio') or 3.8)

            servicios_v = vc.obtener_detalles_itinerario_venta(id_actual)
            mapa_nombres_serv = {s['n_linea']: s['observacion'] for s in servicios_v}
            
            # 2. Obtener Liquidaciones Reales (Lo que se subió por Excel)
            liq_data = controller.get_liquidaciones_venta(id_actual)
            
            if liq_data:
                # 1. Preparar datos para el editor
                display_data = []
                for l in liq_data:
                    c_unit = float(l.get('costo_unitario', 0))
                    pax = float(l.get('cantidad_pax') or l.get('cantidad_items') or 1)
                    moneda_l = l.get('moneda', 'USD')
                    
                    l['DIA'] = l.get('n_linea')
                    l['SERVICIO'] = mapa_nombres_serv.get(l.get('n_linea'), "---")
                    l['PROVEEDOR'] = l.get('proveedor', {}).get('nombre_comercial') if l.get('proveedor') else "---"
                    l['PAX'] = int(pax)
                    l['COSTO ORIG.'] = c_unit * pax
                    
                    # CÁLCULO DE CONVERSIÓN A PEN
                    costo_pen = c_unit * pax
                    if moneda_l == 'USD':
                        costo_pen = (c_unit * pax) * tc_v
                    
                    l['TOTAL (PEN)'] = costo_pen
                    # ICONO DE ESTADO
                    l['Estado'] = "🟢 OK" if l.get('terminado') else "🔴 PENDIENTE"
                    display_data.append(l)

                df_edit = pd.DataFrame(display_data)
                
                # Definir columnas visibles
                cols_visible = ['Estado', 'terminado', 'DIA', 'SERVICIO', 'PROVEEDOR', 'PAX', 'TOTAL (PEN)']
                
                # 2. Renderizar Editor de Datos
                edited_result = st.data_editor(
                    df_edit[cols_visible],
                    column_config={
                        "Estado": st.column_config.TextColumn("Visual", width="small"),
                        "terminado": st.column_config.CheckboxColumn("Check", help="Marcar como Terminado"),
                        "DIA": st.column_config.NumberColumn("Día", format="%d", width="small"),
                        "PAX": st.column_config.NumberColumn("Pax", width="small"),
                        "TOTAL (PEN)": st.column_config.NumberColumn("Costo (S/.)", format="S/. %.2f")
                    },
                    disabled=['Estado', 'DIA', 'SERVICIO', 'PROVEEDOR', 'PAX', 'TOTAL (PEN)'],
                    hide_index=True,
                    use_container_width=True,
                    key="editor_liq_master"
                )

                # 3. Procesar cambios mediante botón de confirmación
                if "editor_liq_master" in st.session_state:
                    state = st.session_state.editor_liq_master
                    cambios_pendientes = state.get("edited_rows", {})
                    
                    if cambios_pendientes:
                        st.warning(f"⚠️ Tienes {len(cambios_pendientes)} cambios pendientes de guardar.")
                        if st.button("💾 Guardar Cambios en Operativa", type="primary", use_container_width=True):
                            exitos = 0
                            errores = []
                            for row_idx, changes in cambios_pendientes.items():
                                if "terminado" in changes:
                                    reg_id = df_edit.iloc[row_idx]['id']
                                    nuevo_estado = changes["terminado"]
                                    exito, msg = controller.actualizar_estado_servicio_proveedor(reg_id, nuevo_estado)
                                    if exito: exitos += 1
                                    else: errores.append(msg)
                            
                            if exitos > 0:
                                st.success(f"✅ Se actualizaron {exitos} servicios.")
                                # Limpiar el editor forzando un reset (esto es opcional pero recomendado)
                                st.rerun()
                            if errores:
                                for e in errores: st.error(e)
                
                with st.expander("🚨 Zona de Peligro: Limpieza de Endoses"):
                    st.warning("Se borrarán todos los costos y proveedores asignados.")
                    confirm_reset = st.checkbox("Confirmar borrado de todos los costos (Liquidación)", key="reset_end_confirm")
                    if st.button("🗑️ Resetear Liquidación", type="primary", disabled=not confirm_reset, use_container_width=True):
                        exito_r, msg_r = controller.borrar_endoses_venta(id_actual)
                        if exito_r: st.success(msg_r); st.rerun()
                        else: st.error(msg_r)
            else:
                st.info("Aún no has cargado la liquidación (Excel) para esta venta.")
        except Exception as e:
            st.error(f"Error cargando liquidaciones: {e}")

    with c_res2:
        st.markdown("### 👥 Resumen de Pasajeros (Rooming)")
        try:
            pax_data = controller.pasajero_model.get_by_venta_id(id_actual)
            if pax_data:
                df_pax_res = pd.DataFrame(pax_data)
                cols_pax = ['nombre_completo', 'nacionalidad', 'numero_documento', 'es_principal']
                st.table(df_pax_res[cols_pax])

                with st.expander("🚨 Zona de Peligro: Limpieza de Pasajeros"):
                    st.warning("Se borrarán todos los pasajeros de esta venta.")
                    confirm_pax = st.checkbox("Confirmar borrado de pasajeros", key="reset_pax_confirm")
                    if st.button("🗑️ Borrar Lista de Pasajeros", type="primary", disabled=not confirm_pax, use_container_width=True):
                        exito_p, msg_p = controller.borrar_pasajeros_venta(id_actual)
                        if exito_p: st.success(msg_p); st.rerun()
                        else: st.error(msg_p)
            else:
                st.info("Sin pasajeros registrados.")
        except Exception as e:
            st.error(f"Error cargando pasajeros: {e}")

    # Botón de sincronización con Itinerario Digital
    st.divider()
    if st.session_state.get('last_loaded_id_venta'):
        id_actual = st.session_state['last_loaded_id_venta']
        
        c_sync1, c_sync2, c_sync3 = st.columns([1, 2, 1])
        with c_sync2:
            st.warning("⚠️ **Sincronización:** Si el vendedor cambió el itinerario, presione este botón para actualizar la logística.")
            if st.button("🔄 Sincronizar Logística con Itinerario Cloud", use_container_width=True, help="Refresca los días y nombres de tours basándose en el diseño más reciente del vendedor."):
                # Necesitamos llamar al método desde venta_controller
                vc_temp = VentaController(supabase_client)
                exito_s, msg_s = vc_temp.sincronizar_venta_con_itinerario(id_actual)
                if exito_s:
                    st.success(msg_s)
                    st.rerun()
                else:
                    st.error(msg_s)

    # Botón de envío a contabilidad (Liquidación Final)
    st.divider()
    if st.session_state.get('last_loaded_id_venta'):
        id_actual = st.session_state['last_loaded_id_venta']
        
        c_arch_btn1, c_arch_btn2, c_arch_btn3 = st.columns([1, 2, 1])
        with c_arch_btn2:
            if st.button("📥 Liquidar y Archivar Expediente", type="primary", use_container_width=True, help="Finaliza el viaje, confirma todos los costos y oculta al pasajero de las listas activas."):
                exito, msg = controller.finalizar_liquidacion_venta(id_actual)
                if exito:
                    st.balloons()
                    st.success("✅ ¡Expediente Cerrado! El pasajero ha sido movido al historial y contabilidad.")
                    # Limpiar sesión para forzar refresco a una vista limpia
                    st.session_state['last_loaded_id_venta'] = None
                    st.session_state['simulador_adv_data'] = []
                    st.rerun()
                else:
                    st.error(msg)

def render_directorio_proveedores(supabase_client):
    """Módulo profesional para la gestión de proveedores con soporte JSONB dinámico."""
    from controllers.proveedor_controller import ProveedorController
    import json
    prov_ctrl = ProveedorController(supabase_client)

    st.subheader("🏢 Gestión de Socios Estratégicos (Proveedores)", divider="red")
    
    # ═══════════════════════════════════════════════════════════════
    # 1. GESTIÓN DE ESTADO (Draft)
    # ═══════════════════════════════════════════════════════════════
    if 'prov_edit_id' not in st.session_state:
        st.session_state.prov_edit_id = None
    if 'prov_draft' not in st.session_state:
        st.session_state.prov_draft = {}

    # ═══════════════════════════════════════════════════════════════
    # 2. SELECTOR DE PROVEEDOR
    # ═══════════════════════════════════════════════════════════════
    listado_prov = prov_ctrl.obtener_proveedores()
    mapa_nombres = {p['nombre_comercial']: p for p in listado_prov}
    
    col_sel1, col_sel2 = st.columns([2, 1])
    prov_sel = col_sel1.selectbox(
        "🔍 Buscar o Seleccionar Proveedor:", 
        ["--- Nuevo Proveedor ---"] + list(mapa_nombres.keys()),
        index=0 if st.session_state.prov_edit_id is None else (list(mapa_nombres.keys()).index(next(k for k, v in mapa_nombres.items() if v['id_proveedor'] == st.session_state.prov_edit_id)) + 1 if st.session_state.prov_edit_id in [p['id_proveedor'] for p in listado_prov] else 0)
    )

    # Cargar datos al cambiar selección
    if prov_sel == "--- Nuevo Proveedor ---":
        if st.session_state.prov_edit_id is not None:
            st.session_state.prov_edit_id = None
            st.session_state.prov_draft = {
                "nombre_comercial": "", "ruc": "", "email": "", "persona_contacto": "",
                "contacto_telefono": "", "pais": "Perú", "url_drive": "",
                "servicios_ofrecidos": ["GUIADO"], "cuentas_bancarias": [],
                "puntos_operacion": [], "detalles_categoria": {}, "activo": True
            }
            st.rerun()
    else:
        p_data = mapa_nombres[prov_sel]
        if st.session_state.prov_edit_id != p_data['id_proveedor']:
            st.session_state.prov_edit_id = p_data['id_proveedor']
            # Cargar todo el objeto a memoria (Draft)
            st.session_state.prov_draft = p_data.copy()
            # Asegurar que los JSON no sean None
            for key in ['cuentas_bancarias', 'puntos_operacion']:
                if not st.session_state.prov_draft.get(key): st.session_state.prov_draft[key] = []
            if not st.session_state.prov_draft.get('detalles_categoria'): 
                st.session_state.prov_draft['detalles_categoria'] = {}
            st.rerun()

    # Si no hay draft inicializado (caso primer carga), inicializarlo vacío
    if not st.session_state.prov_draft:
        st.session_state.prov_draft = {
            "nombre_comercial": "", "ruc": "", "email": "", "persona_contacto": "",
            "contacto_telefono": "", "pais": "Perú", "url_drive": "",
            "servicios_ofrecidos": ["GUIADO"], "cuentas_bancarias": [],
            "puntos_operacion": [], "detalles_categoria": {}, "activo": True
        }

    draft = st.session_state.prov_draft

    # ═══════════════════════════════════════════════════════════════
    # 3. FORMULARIO DINÁMICO
    # ═══════════════════════════════════════════════════════════════
    st.write("---")
    
    # --- BLOQUE A: INFORMACIÓN BÁSICA ---
    with st.expander("👤 Información General y Contacto", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        draft['nombre_comercial'] = c1.text_input("Nombre / Razón Social*", value=draft.get('nombre_comercial', ''))
        draft['ruc'] = c2.text_input("RUC / Tax ID", value=draft.get('ruc', ''))
        draft['persona_contacto'] = c3.text_input("Contacto Principal", value=draft.get('persona_contacto', ''))
        
        ca, cb, cc = st.columns(3)
        draft['contacto_telefono'] = ca.text_input("Teléfono / WhatsApp", value=draft.get('contacto_telefono', ''))
        draft['email'] = cb.text_input("Email de Reservas", value=draft.get('email', ''))
        draft['url_drive'] = cc.text_input("🔗 Link Drive (Tarifarios/Docs)", value=draft.get('url_drive', ''))

        serv_base = ["GUIA", "TRANSPORTE", "ALOJAMIENTO", "ALIMENTACION", "TICKETS", "AGENCIA", "OPERADOR", "OTROS"]
        draft['servicios_ofrecidos'] = st.multiselect(
            "Servicios que brinda*", 
            options=list(set(serv_base + (draft.get('servicios_ofrecidos') or []))),
            default=draft.get('servicios_ofrecidos', ["GUIA"])
        )

    # --- BLOQUE B: CUENTAS BANCARIAS (DINÁMICO) ---
    with st.expander(f"💳 Información de Pagos ({len(draft['cuentas_bancarias'])} cuentas)", expanded=False):
        for idx, cuenta in enumerate(draft['cuentas_bancarias']):
            colb1, colb2, colb3, colb4, colb_del = st.columns([1, 1, 1.5, 2, 0.5])
            cuenta['banco'] = colb1.text_input(f"Banco", value=cuenta.get('banco', ''), key=f"bnk_{idx}")
            cuenta['moneda'] = colb2.selectbox(f"Moneda", ["PEN", "USD"], index=0 if cuenta.get('moneda')=="PEN" else 1, key=f"mon_{idx}")
            cuenta['nro'] = colb3.text_input(f"N° Cuenta", value=cuenta.get('nro', ''), key=f"nro_{idx}")
            cuenta['cci'] = colb4.text_input(f"CCI (20 dígitos)", value=cuenta.get('cci', ''), key=f"cci_{idx}")
            if colb_del.button("❌", key=f"del_bnk_{idx}"):
                draft['cuentas_bancarias'].pop(idx)
                st.rerun()
        
        if st.button("➕ Agregar Cuenta Bancaria", use_container_width=True):
            draft['cuentas_bancarias'].append({"banco": "", "moneda": "PEN", "nro": ""})
            st.rerun()

    # --- BLOQUE C: LOGÍSTICA Y OPERACIÓN ---
    with st.expander("📍 Zonas de Operación y Logística", expanded=False):
        c_zonas_1, c_zonas_2 = st.columns([3, 1])
        nueva_zona = c_zonas_1.text_input("Agregar zona de operación:", placeholder="Ej: Cusco Centro, Ollantaytambo, Lima...")
        if c_zonas_2.button("➕ Añadir", use_container_width=True) and nueva_zona:
            if nueva_zona not in draft['puntos_operacion']:
                draft['puntos_operacion'].append(nueva_zona)
                st.rerun()
        
        if draft['puntos_operacion']:
            st.write("Zonas registradas:")
            cols_z = st.columns(4)
            for z_idx, z_val in enumerate(draft['puntos_operacion']):
                with cols_z[z_idx % 4]:
                    if st.button(f"{z_val} ❌", key=f"z_{z_idx}"):
                        draft['puntos_operacion'].pop(z_idx)
                        st.rerun()

    # --- BLOQUE D: CAMPOS INTELIGENTES POR CATEGORÍA ---
    # Detectar categoría principal para mostrar campos específicos
    servs = draft.get('servicios_ofrecidos', [])
    detalles = draft['detalles_categoria']
    
    if any(s in servs for s in ["GUIA", "GUIADO"]):
        with st.expander("🎓 Detalles Especializados: GUÍA", expanded=True):
            cg1, cg2 = st.columns(2)
            detalles['idiomas'] = cg1.text_input("Idiomas que habla", value=detalles.get('idiomas', 'Español, Inglés'))
            detalles['nro_carnet'] = cg2.text_input("N° Carnet GRL / Oficial", value=detalles.get('nro_carnet', ''))
            detalles['especialidad'] = st.text_input("Especialidad (Aventura, Cultural, etc)", value=detalles.get('especialidad', ''))

    if any(s in servs for s in ["ALOJAMIENTO", "HOTEL"]):
        with st.expander("🏨 Detalles Especializados: HOTEL", expanded=True):
            ch1, ch2, ch3 = st.columns(3)
            detalles['estrellas'] = ch1.selectbox("Categoría", ["1*", "2*", "3*", "4*", "5*", "Boutique", "Hostal"], index=2)
            detalles['check_in'] = ch2.text_input("Hora Check-In", value=detalles.get('check_in', '12:00 PM'))
            detalles['desayuno'] = ch3.toggle("¿Incluye Desayuno?", value=detalles.get('desayuno', True))

    if any(s in servs for s in ["TRANSPORTE"]):
        with st.expander("🚐 Detalles Especializados: TRANSPORTE", expanded=True):
            ct1, ct2, ct3 = st.columns(3)
            detalles['vehiculo'] = ct1.text_input("Marca/Modelo", value=detalles.get('vehiculo', ''))
            detalles['placa'] = ct2.text_input("Placa", value=detalles.get('placa', ''))
            detalles['capacidad'] = ct3.number_input("Capacidad Pax", value=detalles.get('capacidad', 1), min_value=1)

    # ═══════════════════════════════════════════════════════════════
    # 4. ACCIONES DE GUARDADO
    # ═══════════════════════════════════════════════════════════════
    st.write("---")
    draft['activo'] = st.toggle("Proveedor Activo", value=draft.get('activo', True))
    
    col_acc1, col_acc2 = st.columns(2)
    
    if col_acc1.button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
        if not draft['nombre_comercial']:
            st.error("Error: El nombre es obligatorio.")
        else:
            if st.session_state.prov_edit_id:
                # MODO EDICION
                exito, msg = prov_ctrl.actualizar_proveedor(
                    st.session_state.prov_edit_id,
                    draft['nombre_comercial'], draft['servicios_ofrecidos'],
                    draft['contacto_telefono'], draft.get('pais', 'Perú'),
                    draft['activo'], draft['ruc'], draft['email'],
                    draft['persona_contacto'], draft['url_drive'],
                    draft['cuentas_bancarias'], draft['puntos_operacion'],
                    draft['detalles_categoria']
                )
            else:
                # MODO REGISTRO
                exito, msg = prov_ctrl.registrar_proveedor(
                    draft['nombre_comercial'], draft['servicios_ofrecidos'],
                    draft['contacto_telefono'], draft.get('pais', 'Perú'),
                    draft['ruc'], draft['email'], draft['persona_contacto'],
                    draft['url_drive'], draft['cuentas_bancarias'],
                    draft['puntos_operacion'], draft['detalles_categoria']
                )
            
            if exito:
                st.success(msg)
                st.balloons()
                # Limpiar estado
                st.session_state.prov_edit_id = None
                st.session_state.prov_draft = {}
                st.rerun()
            else:
                st.error(msg)

    if col_acc2.button("🧹 LIMPIAR / CANCELAR", use_container_width=True):
        st.session_state.prov_edit_id = None
        st.session_state.prov_draft = {}
        st.rerun()

    # ═══════════════════════════════════════════════════════════════
    # 5. LISTADO GENERAL
    # ═══════════════════════════════════════════════════════════════
    with st.expander("📜 Ver Directorio General Completo", expanded=False):
        if not listado_prov:
            st.info("Sin proveedores registrados.")
        else:
            df_view = pd.DataFrame(listado_prov)
            # Limpiar servicios para vista
            df_view['Servicios'] = df_view['servicios_ofrecidos'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            st.dataframe(
                df_view,
                column_order=["nombre_comercial", "Servicios", "contacto_telefono", "ruc", "email", "activo"],
                column_config={
                    "nombre_comercial": "Proveedor",
                    "contacto_telefono": "Teléfono",
                    "ruc": "RUC",
                    "email": "Email",
                    "activo": st.column_config.CheckboxColumn("Activo")
                },
                use_container_width=True,
                hide_index=True
            )


    # ═══════════════════════════════════════════════════════════════
    # 3. TABLA DE PROVEEDORES EXISTENTES
    # ═══════════════════════════════════════════════════════════════
    st.write("### 📜 Directorio General")
    proveedores = listado_prov # Usamos la misma lista ya cargada
    
    if not proveedores:
        st.info("Aún no hay proveedores registrados en el directorio.")
    else:
        df_prov = pd.DataFrame(proveedores)
        
        # Formatear la columna de servicios para que sea más legible si es una lista
        if 'servicios_ofrecidos' in df_prov.columns:
            df_prov['servicios_ofrecidos'] = df_prov['servicios_ofrecidos'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        
        st.dataframe(
            df_prov,
            column_order=["nombre_comercial", "servicios_ofrecidos", "contacto_telefono", "pais", "activo"],
            column_config={
                "nombre_comercial": "Proveedor",
                "servicios_ofrecidos": "Servicios",
                "contacto_telefono": "Teléfono",
                "pais": "País",
                "activo": st.column_config.CheckboxColumn("Activo")
            },
            hide_index=True,
            use_container_width=True
        )
