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
            render_data = it.get('datos_render', {})
            if isinstance(render_data, str):
                try: render_data = json.loads(render_data)
                except: render_data = {}

            # --- FILTRO B2B: Solo mostrar itinerarios generados como B2B ---
            tipo_v = render_data.get('metadata', {}).get('tipo_venta', 'B2C')
            if tipo_v != 'B2B':
                continue

            # --- FILTRO ESTRATEGIA: Solo mostrar los que dicen 'General' ---
            estrategia = it.get('lead', {}).get('estrategia_venta', 'General')
            if estrategia != 'General':
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
            
            # Mostrar Pax Count (Búsqueda robusta)
            def_cant_pax = 1
            if render.get('control_interno'):
                def_cant_pax = render['control_interno'].get('total_pasajeros') or render['control_interno'].get('total_pax') or 1
            elif render.get('detalle_ingresos'):
                def_cant_pax = sum(int(d.get('cantidad', 0)) for d in render['detalle_ingresos'])
            else:
                def_cant_pax = int(render.get('cantidad_pax') or 1)

            # 3. Fallback: Raíz (num_pax_nac, etc.)
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
                            p_f_raw = float(render.get(pk, 0) or 0)
                            if p_f_raw > 0: break
                        p_f_soles = p_f_raw * tc_itin if t_code in ['EXTRANJERO', 'CAN'] else p_f_raw
                        items_extraidos.append({"descripcion": f"Pax {t_code.capitalize()} (Legacy)", "cantidad": c_f, "precio_unitario": p_f_soles, "tipo": t_code, "p_raw": p_f_raw})

            # --- FALLBACK FINAL B2B: SI NO HAY NADA, USAR CONTEO GENÉRICO ---
            if not items_extraidos:
                pax_gen = render.get('cantidad_pax') or render.get('pax_count') or render.get('num_pax') or 0
                if not pax_gen and ci: 
                    pax_gen = ci.get('total_pasajeros') or ci.get('total_pax') or 0
                
                if pax_gen:
                    p_sug_raw = render.get('total_final_calculado') or render.get('precio_cierre') or 0
                    try: p_sug_val = float(p_sug_raw)
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
            sub_nac_b2b = sum(it['cantidad'] * it['p_raw'] for it in items_ref_b2b if it['tipo'] == 'NACIONAL')
            sub_ext_b2b = sum(it['cantidad'] * it['p_raw'] for it in items_ref_b2b if it['tipo'] in ['EXTRANJERO', 'CAN'])
            
            st.markdown(f"📊 **SUB-TOTALES B2B:** Nac: **S/ {sub_nac_b2b:,.2f}** | Ext (CAN): **$ {sub_ext_b2b:,.2f}**")

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
                if it['tipo'] in ['EXTRANJERO', 'CAN']:
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
        pax_name = col1.text_input("Pasajero Principal", value=def_pax, disabled=is_disabled)
        tel_pax = col1.text_input("Celular Contacto", value=def_cel)
        
        vendedor_log = st.session_state.get('user_id', 'Operaciones')
        col1.markdown(f"👤 **Vendedor Resp:** {vendedor_log}")

        tour_name = col2.text_input("Nombre del Programa B2B", value=def_tour, disabled=is_disabled)
        tipo_comp = col2.radio("Comprobante para Agencia", ["Boleta", "Factura", "Recibo Simple"], horizontal=True)
        metodo_pago = col2.selectbox("💳 Método de Pago", ["EFECTIVO", "TRANSFERENCIA", "YAPE", "PLIN", "TARJETA", "PAYPAL", "OTRO"], key="b2b_metodo_pago")
        
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
                        render_itinerary_simple_download(res.data['datos_render'])
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
    st.markdown("---")
    
    if nombre_modulo == "Gestión de Registros":
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
        res_itin = controller.client.table('venta').select('id_itinerario_digital').eq('id_venta', id_venta_act).single().execute()
        id_itin_dig = res_itin.data.get('id_itinerario_digital') if res_itin.data else None
        
        if id_itin_dig:
            res_render = controller.client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_dig).single().execute()
            if res_render.data:
                render_data = res_render.data.get('datos_render')
                if isinstance(render_data, str):
                    import json
                    render_data = json.loads(render_data)
                
                # Renderizar los botones de descarga
                render_itinerary_simple_download(render_data)
    except Exception as e:
        st.warning(f"Nota: No se pudo cargar el resumen del itinerario para descarga. ({e})")

    # --- SECCIÓN DE ARCHIVOS (CSV/Excel) ---
    st.markdown("### 📝 Gestión de Información Externa")
    st.info("Suba los archivos correspondientes para el cierre y control de pasajeros.")

    # NUEVO: Botón de Plantilla
    import io
    template_df = pd.DataFrame(columns=["Dia", "Tipo_Servicio", "Proveedor", "Moneda", "Costo Unitario"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
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
                cols_req = ["Dia", "Tipo_Servicio", "Proveedor", "Moneda", "Costo Unitario"]
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
        with pd.ExcelWriter(pax_buffer, engine='xlsxwriter') as writer:
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
        st.markdown("### 📋 Resumen de Endoses y Guías")
        try:
            data_db = controller.get_servicios_rango_fechas(date(2000, 1, 1), date(2100, 1, 1))
            id_actual = st.session_state.get('last_loaded_id_venta')
            data_actual = [d for d in data_db if d['ID Venta'] == id_actual]
            
            if data_actual:
                df_resumen = pd.DataFrame(data_actual)
                cols_show = ['Día Itin.', 'Servicio', 'Proveedor', 'Endoso?', 'Pax']
                st.table(df_resumen[cols_show])
                
                with st.expander("🚨 Zona de Peligro: Limpieza de Endoses"):
                    st.warning("Se borrarán todos los costos y proveedores asignados.")
                    confirm_reset = st.checkbox("Confirmar borrado de endoses", key="reset_end_confirm")
                    if st.button("🗑️ Borrar Endoses", type="primary", disabled=not confirm_reset, use_container_width=True):
                        exito_r, msg_r = controller.borrar_endoses_venta(id_actual)
                        if exito_r: st.success(msg_r); st.rerun()
                        else: st.error(msg_r)
            else:
                st.info("Sin endoses registrados.")
        except Exception as e:
            st.error(f"Error cargando endoses: {e}")

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

    # Botón de envío a contabilidad
    st.divider()
    if st.session_state.get('last_loaded_id_venta'):
        if st.button("🚀 Enviar Reportes a Contabilidad", type="primary", use_container_width=True):
            st.balloons()
            st.success("Correcto: Documentos enviados satisfactoriamente (Simulado).")

def render_directorio_proveedores(supabase_client):
    """Módulo para el registro y gestión de proveedores logísticos."""
    from controllers.proveedor_controller import ProveedorController
    prov_ctrl = ProveedorController(supabase_client)

    st.subheader("🏢 Directorio de Proveedores Logísticos", divider="gray")
    
    # ═══════════════════════════════════════════════════════════════
    # 1. FORMULARIO DE REGISTRO
    # ═══════════════════════════════════════════════════════════════
    with st.expander("➕ Registrar Nuevo Proveedor", expanded=False):
        with st.form("form_nuevo_proveedor"):
            c1, c2 = st.columns(2)
            
            nombre = c1.text_input("Nombre Comercial / Razón Social*", placeholder="Ej: Transportes Cóndor")
            contacto = c1.text_input("Teléfono de Contacto", placeholder="Ej: +51 987 654 321")
            
            pais = c2.text_input("País origen", value="Perú")
            servicios = c2.multiselect(
                "Servicios que ofrece",
                ["GUIA", "TRANSPORTE", "ALIMENTACION", "ALOJAMIENTO", "TICKETS", "ENDOSE", "OTROS"],
                default=["ENDOSE"]
            )
            
            st.caption("* Campos obligatorios")
            
            # --- NUEVO: OPCIÓN PARA CATEGORÍAS PERSONALIZADAS ---
            custom_services = []
            if "OTROS" in servicios:
                otros_texto = c2.text_input("Especifique otros servicios (separados por coma)", placeholder="Ej: Vuelos, Entradas Especiales")
                if otros_texto:
                    custom_services = [s.strip().upper() for s in otros_texto.split(",") if s.strip()]

            submit_prov = st.form_submit_button("🔨 Registrar Proveedor", use_container_width=True, type="primary")
            
            if submit_prov:
                if not nombre:
                    st.error("El nombre del proveedor es obligatorio.")
                else:
                    # Limpiar lista de servicios: quitar 'OTROS' y añadir personalizados
                    servicios_finales = [s for s in servicios if s != "OTROS"]
                    servicios_finales.extend(custom_services)
                    # Quitar duplicados
                    servicios_finales = list(set(servicios_finales))
                    
                    exito, msg = prov_ctrl.registrar_proveedor(nombre, servicios_finales, contacto, pais)
                    if exito:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)

    # ═══════════════════════════════════════════════════════════════
    # 2. EDITOR DE PROVEEDORES (NUEVO)
    # ═══════════════════════════════════════════════════════════════
    st.write("### 🖋️ Editor / Actualización de Datos")
    listado_prov = prov_ctrl.obtener_proveedores()
    
    if listado_prov:
        mapa_nombres = {p['nombre_comercial']: p for p in listado_prov}
        prov_sel_edit = st.selectbox("Seleccione el proveedor que desea modificar:", ["--- Seleccione ---"] + list(mapa_nombres.keys()))
        
        if prov_sel_edit != "--- Seleccione ---":
            p_data = mapa_nombres[prov_sel_edit]
            
            with st.form("form_editar_proveedor"):
                st.info(f"Editando: **{p_data['nombre_comercial']}** (ID: {p_data['id_proveedor']})")
                col_e1, col_e2 = st.columns(2)
                
                new_nombre = col_e1.text_input("Nombre Comercial", value=p_data['nombre_comercial'])
                new_contacto = col_e1.text_input("Contacto", value=p_data.get('contacto_telefono', '') or '')
                
                # Manejar servicios (lista)
                servicios_actuales = p_data.get('servicios_ofrecidos', [])
                if not isinstance(servicios_actuales, list): servicios_actuales = []
                
                new_servicios = col_e2.multiselect(
                    "Servicios Actualizados",
                    ["GUIA", "TRANSPORTE", "ALIMENTACION", "ALOJAMIENTO", "TICKETS", "ENDOSE", "OTROS"],
                    default=servicios_actuales
                )
                
                new_pais = col_e2.text_input("País", value=p_data.get('pais', 'Perú'))
                new_activo = col_e2.toggle("Proveedor Activo", value=p_data.get('activo', True), help="Desactiva esto para ocultar al proveedor en las listas de selección.")
                
                # --- NUEVO EN EDITOR: CATEGORÍAS PERSONALIZADAS ---
                custom_services_edit = []
                if "OTROS" in new_servicios:
                    otros_texto_edit = col_e2.text_input("Especifique nuevos servicios (separados por coma)", key="edit_otros")
                    if otros_texto_edit:
                        custom_services_edit = [s.strip().upper() for s in otros_texto_edit.split(",") if s.strip()]

                submit_edit = st.form_submit_button("✅ Guardar Cambios", use_container_width=True)
                
                if submit_edit:
                    # Mezclar servicios
                    servicios_finales_edit = [s for s in new_servicios if s != "OTROS"]
                    servicios_finales_edit.extend(custom_services_edit)
                    servicios_finales_edit = list(set(servicios_finales_edit))

                    exito_e, msg_e = prov_ctrl.actualizar_proveedor(
                        p_data['id_proveedor'], 
                        new_nombre, 
                        servicios_finales_edit, 
                        new_contacto, 
                        new_pais, 
                        new_activo
                    )
                    if exito_e:
                        st.success(msg_e)
                        st.rerun()
                    else:
                        st.error(msg_e)

    st.divider()

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
