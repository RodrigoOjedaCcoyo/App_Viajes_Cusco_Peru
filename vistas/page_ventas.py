# vistas/page_ventas.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from controllers.lead_controller import LeadController
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



def get_vendedor_id():
    return st.session_state.get('user_id')

# --- MÓDULOS DE LEADS Y VENTAS (RESTAURADOS) ---

def formulario_registro_leads():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return
    
    st.subheader("📝 Registro de Nuevo Lead")
    vendedor_actual = get_vendedor_id()
    st.info(f"Registrando a cargo de: **{vendedor_actual}**")
        
    with st.form("form_nuevo_lead"):
        telefono = st.text_input("Número de Celular")
        origen = st.selectbox("Seleccione Red Social", ["---Seleccione---","Instagram", "Facebook", "TikTok", "Web", "Otro"])
        vendedores_map = lead_controller.obtener_mapeo_vendedores()
        nombres_vendedores = list(vendedores_map.values())
        vendedor_sel = st.selectbox("Asignar a", ["---Seleccione---"] + nombres_vendedores)
        submitted = st.form_submit_button("Guardar Lead")
        
        if submitted:
            # Encontrar el ID del vendedor seleccionado
            id_vendedor = None
            for vid, vnom in vendedores_map.items():
                if vnom == vendedor_sel:
                    id_vendedor = vid
                    break
            
            exito, mensaje = lead_controller.registrar_nuevo_lead(telefono, origen, id_vendedor)
            if exito: st.success(mensaje)
            else: st.error(mensaje)

def seguimiento_leads():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return

    st.subheader("🔎 Seguimiento de Clientes")
    leads = lead_controller.obtener_todos_leads()
    
    if leads:
        df = pd.DataFrame(leads)
        # Mapeo de vendedores y filtros sugeridos en la versión anterior...
        st.data_editor(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay leads para mostrar.")

def registro_ventas_directa():
    venta_controller = st.session_state.get('venta_controller')
    lead_controller = st.session_state.get('lead_controller')
    it_controller = st.session_state.get('itinerario_digital_controller')
    
    if not venta_controller or not lead_controller or not it_controller: 
        st.error("Error de inicialización de controladores.")
        return

    st.subheader("💰 Registro de Venta Confirmada")
    
    # 1. Buscador/Selector de Lead para auto-completar
    leads = lead_controller.obtener_todos_leads()
    lead_opt = ["--- Ingreso Manual / Sin Lead ---"]
    lead_map = {}
    
    if leads:
        for l in leads:
            lbl = f"{l['numero_celular']} - {l.get('nombre_pasajero') or 'Sin Nombre'}"
            lead_opt.append(lbl)
            lead_map[lbl] = l

    lead_sel = st.selectbox("🎯 Vincular con un Lead existente (Opcional)", lead_opt)
    lead_data = lead_map.get(lead_sel)

    # --- 🕵️ SELECTOR DE ITINERARIO (Buscador por Contacto) ---
    id_lead_seleccionado = lead_data.get('id_lead') if lead_data else None
    
    if id_lead_seleccionado:
        itinerarios_recuperados = it_controller.listar_itinerarios_lead(id_lead_seleccionado)
    else:
        # Si no hay lead, mostrar itinerarios recientes (opción de búsqueda global)
        itinerarios_recuperados = it_controller.obtener_todos_recientes(limit=30)
    
    # Crear opciones para el selector
    opciones_itinerario = ["--- Sin Itinerario ---"]
    mapa_itinerarios = {}
    
    if itinerarios_recuperados:
        for it in itinerarios_recuperados:
            uuid = it.get('id_itinerario_digital', '')
            render_data = it.get('datos_render', {})
            
            # Soportar ambas estructuras
            titulo = render_data.get('titulo', '')
            if not titulo:
                title_1 = render_data.get('title_1', '')
                title_2 = render_data.get('title_2', '')
                titulo = f"{title_1} {title_2}".strip() or 'Sin título'
            
            fecha = it.get('fecha_generacion', '')[:10] if it.get('fecha_generacion') else 'Sin fecha'
            
            # Celular para el label (muy importante según feedback)
            celular = it.get('lead', {}).get('numero_celular', '') if it.get('lead') else lead_data.get('numero_celular', '') if lead_data else ''
            cel_label = f"📱 {celular} | " if celular else ""
            
            label = f"{cel_label}{titulo} ({fecha})"
            opciones_itinerario.append(label)
            mapa_itinerarios[label] = it
    
    itinerario_seleccionado = st.selectbox(
        "✨ Seleccionar Itinerario Visual (Diseño Cloud)", 
        opciones_itinerario,
        help="Seleccione el diseño que corresponde a esta venta"
    )
    
    # Auto-completar datos si se seleccionó un itinerario
    id_itinerario_dig = None
    if itinerario_seleccionado != "--- Sin Itinerario ---":
        it_data = mapa_itinerarios.get(itinerario_seleccionado)
        if it_data:
            id_itinerario_dig = it_data.get('id_itinerario_digital')
            render = it_data.get('datos_render', {})
            
            # Extraer nombre del pasajero (soporta ambas estructuras)
            nombre_pax_cloud = it_data.get('nombre_pasajero_itinerario', '') or render.get('pasajero', '')
            
            # Extraer título del tour (soporta ambas estructuras)
            # Estructura interna: render.get('titulo')
            # Estructura externa: title_1 + title_2
            tour_nombre_cloud = render.get('titulo', '')
            if not tour_nombre_cloud:
                title_1 = render.get('title_1', '')
                title_2 = render.get('title_2', '')
                tour_nombre_cloud = f"{title_1} {title_2}".strip()
            
            st.session_state[f"val_nom_{id_itinerario_dig}"] = nombre_pax_cloud
            st.session_state[f"val_tour_{id_itinerario_dig}"] = tour_nombre_cloud
            if id_itinerario_dig and id_itinerario_dig != st.session_state.get('last_loaded_itin'):
                # 1. Intentar obtener el precio de cierre directo (Nivel raíz)
                precio_raw = render.get('precio_cierre')
                
                # 2. Si no existe, buscar en la estructura de precios (Nivel 'precios')
                if not precio_raw:
                    precios = render.get('precios', {})
                    # La estructura puede ser directa (float) o diccionario ({"monto": "..."})
                    def extract_val(val):
                        if isinstance(val, dict): return val.get('total') or val.get('monto')
                        return val

                    p_ext = extract_val(precios.get('extranjero') or precios.get('ext'))
                    p_nac = extract_val(precios.get('nacional') or precios.get('nac'))
                    p_can = extract_val(precios.get('can'))
                    
                    precio_raw = p_ext or p_nac or p_can or "0.00"

                # 3. Limpiar y convertir a float
                try:
                    if isinstance(precio_raw, (int, float)):
                        p_sug = float(precio_raw)
                    else:
                        # Eliminar comas y espacios, ej: "1,180.00" -> "1180.00"
                        clean_str = str(precio_raw).replace(',', '').replace(' ', '').strip()
                        p_sug = float(clean_str) if clean_str else 0.0
                except:
                    p_sug = 0.0

                st.session_state['m_total'] = p_sug
                st.session_state['last_loaded_itin'] = id_itinerario_dig
                st.success(f"✅ Itinerario cargado: **{tour_nombre_cloud}** (Precio sugerido: ${p_sug:,.2f})")
            else:
                st.success(f"✅ Itinerario cargado: **{tour_nombre_cloud}**")


    # --- 💳 BALANCE Y MONEDA (TIEMPO REAL / INTERACTIVO) ---
    st.markdown("### 💰 Detalles de Pago")
    c_m0, c_m1, c_m2 = st.columns([1, 2, 2])
    moneda_sel = c_m0.selectbox("Moneda", ["USD", "PEN"], help="Seleccione la moneda del pago")
    # Usamos session_state para persistencia y auto-llenado
    if 'm_total' not in st.session_state: st.session_state['m_total'] = 0.0
    if 'm_pago' not in st.session_state: st.session_state['m_pago'] = 0.0
    
    monto_total = c_m1.number_input(f"Monto Total ({moneda_sel})", min_value=0.0, format="%.2f", key="m_total")
    monto_pagado = c_m2.number_input(f"Monto Pagado ({moneda_sel})", min_value=0.0, format="%.2f", key="m_pago")
    
    saldo = monto_total - monto_pagado
    
    # Visualización Dinámica del Saldo
    if monto_total > 0:
        col_saldo = st.container()
        if saldo <= 0.01: # Margen de error flotante
             col_saldo.success(f"✅ **VENTA SALDADA** (Saldo: $0.00)")
        else:
             porcentaje = (monto_pagado / monto_total) * 100
             col_saldo.warning(f"⏳ **SALDO PENDIENTE: ${saldo:,.2f}** (A cuenta: {porcentaje:.0f}%)")
             
    # --- 📝 FORMULARIO DE REGISTRO ---
    with st.form("form_registro_venta"):
        col1, col2 = st.columns(2)
        
        # Valores por defecto basados en Lead o en la Consulta Cloud
        def_nombre = st.session_state.get(f"val_nom_{id_itinerario_dig}", lead_data.get('nombre_pasajero', '') if lead_data else '')
        def_tour = st.session_state.get(f"val_tour_{id_itinerario_dig}", "")

        # --- SE HA MOVIDO EL BALANCE FUERA DEL FORMULARIO PARA INTERACTIVIDAD --
        
        st.divider()

        # Opciones de bloqueo si hay itinerario
        edit_manual = False
        is_disabled = False
        if id_itinerario_dig and not edit_manual:
            is_disabled = True
            
        nombre = col1.text_input("Nombre Cliente", value=def_nombre, disabled=is_disabled)
        tel = col1.text_input("Celular", value=lead_data.get('numero_celular', '') if lead_data else '')
        
        vendedor_actual = st.session_state.get('user_id', 'Admin')
        col1.markdown(f"👤 **Vendedor:** {vendedor_actual}")
        
        # Tour: Auto-completado desde itinerario, pero editable manualmente
        id_paquete = col2.text_input(
            "Nombre del Tour / Paquete", 
            value=def_tour,
            placeholder="Ej: Cusco Mágico & Machu Picchu",
            disabled=is_disabled,
            help="Se auto-completa si seleccionas un itinerario"
        )
        tipo_comp = col2.radio("Tipo Comprobante", ["Boleta", "Factura", "Recibo Simple"], horizontal=True)
        
        # --- 📅 CÁLCULO AUTOMÁTICO DE FECHAS ---
        itin_fecha_inicio = date.today()
        itin_fecha_fin = date.today()
        
        if id_itinerario_dig:
            render = mapa_itinerarios.get(itinerario_seleccionado, {}).get('datos_render', {})
            f_viaje = render.get('fecha_viaje')
            if f_viaje:
                try: itin_fecha_inicio = date.fromisoformat(f_viaje)
                except: pass
            
            # Calcular Fin basado en Duración (ej: "3D")
            itin_fecha_fin = itin_fecha_inicio
            duracion_raw = render.get('duracion')
            if duracion_raw and isinstance(duracion_raw, str) and 'D' in duracion_raw.upper():
                try:
                    num_dias_str = ''.join(filter(str.isdigit, duracion_raw.split('D')[0]))
                    if num_dias_str:
                        num_dias = int(num_dias_str)
                        itin_fecha_fin = itin_fecha_inicio + timedelta(days=num_dias - 1)
                except Exception as e:
                    print(f"Error calculando fecha fin: {e}")
            
            # Mostrar Pax Count si existe
            num_pax = render.get('cantidad_pax') or render.get('pax_count') or 1
            st.success(f"🗓️ **Viaje Programado:** Del {itin_fecha_inicio.strftime('%d/%m/%Y')} al {itin_fecha_fin.strftime('%d/%m/%Y')} | 👥 **Pax:** {num_pax}")
            fecha_inicio_sel = itin_fecha_inicio
            fecha_fin_sel = itin_fecha_fin
        else:
            with st.expander("📅 Programación de Viaje (Manual)", expanded=True):
                col_f1, col_f2 = st.columns(2)
                fecha_inicio_sel = col_f1.date_input("Fecha Inicio", value=date.today())
                fecha_fin_sel = col_f2.date_input("Fecha Fin", value=date.today())
        
        submitted = st.form_submit_button("🚀 REGISTRAR VENTA Y NOTIFICAR", use_container_width=True)

        if submitted:
            # Validación previa
            if not nombre or not tel:
                st.error("❌ El Nombre y el Celular son obligatorios.")
            elif not id_paquete:
                st.error("❌ El nombre del Tour/Paquete es obligatorio.")
            elif monto_total <= 0:
                st.error("❌ El Monto Total debe ser mayor a 0.")
            else:
                exito, msg = venta_controller.registrar_venta_directa(
                    nombre_cliente=nombre,
                    telefono=tel,
                    origen="Directo",
                    vendedor=vendedor_actual, 
                    tour=id_paquete,
                    tipo_hotel="Estándar", 
                    fecha_inicio=fecha_inicio_sel.isoformat(),
                    fecha_fin=fecha_fin_sel.isoformat(),
                    monto_total=monto_total,
                    monto_depositado=monto_pagado,
                    tipo_comprobante=tipo_comp,
                    moneda=moneda_sel,
                    id_itinerario_digital=id_itinerario_dig if id_itinerario_dig else None,
                    file_itinerario=None,
                    file_pago=None
                )
                
                if exito:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)


def render_reminders_dashboard():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización."); return
    
    st.subheader("🔔 Panel de Alertas de Seguimiento")
    leads = lead_controller.obtener_todos_leads()
    
    if not leads:
        st.info("No hay recordatorios pendientes.")
        return
        
    df = pd.DataFrame(leads)
    
    # Filtrar solo recordatorios (asumiendo que los marcamos con REC: o tienen fecha_seguimiento)
    if 'red_social' in df.columns:
        df_rec = df[df['red_social'].str.contains("REC:", na=False)].copy()
    else:
        df_rec = pd.DataFrame()

    if df_rec.empty:
        st.info("No hay clientes en la agenda de recordatorios.")
        return

    # Procesar fechas para alertas
    hoy = date.today()
    
    # Intentar obtener fecha_seguimiento, si no, parsear de red_social si lo guardamos ahí temporalmente
    # Pero ahora ya tenemos el campo en el modelo.
    if 'fecha_seguimiento' in df_rec.columns:
        df_rec['fecha_seguimiento'] = pd.to_datetime(df_rec['fecha_seguimiento']).dt.date
    else:
        df_rec['fecha_seguimiento'] = hoy # Fallback
        
    df_rec = df_rec.sort_values(by='fecha_seguimiento', ascending=True)

    # Clasificación
    atrasados = df_rec[df_rec['fecha_seguimiento'] < hoy]
    hoy_pendientes = df_rec[df_rec['fecha_seguimiento'] == hoy]
    futuros = df_rec[df_rec['fecha_seguimiento'] > hoy]

    # Visualización con Columnas
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Atrasados", len(atrasados))
    c2.metric("🟠 Para Hoy", len(hoy_pendientes))
    c3.metric("🟢 Próximos", len(futuros))

    st.markdown("---")
    
    if not atrasados.empty:
        st.error("🚨 **CLIENTES QUE DEBISTE LLAMAR (ATRASADOS)**")
        for _, r in atrasados.iterrows():
            with st.expander(f"⚠️ {r.get('numero_celular')} - {r.get('fecha_seguimiento')}"):
                st.write(f"**Notas:** {r.get('comentario', 'Sin notas')}")
                st.write(f"**Vendedor:** {r.get('id_vendedor')}")
                if st.button(f"Llamada Realizada {r.get('id_lead')}"):
                    # Aquí iría lógica para actualizar estado
                    st.success("Gestión de seguimiento registrada.")

    if not hoy_pendientes.empty:
        st.warning("📅 **GESTIONES PARA HOY**")
        st.dataframe(hoy_pendientes[['numero_celular', 'comentario', 'id_vendedor']], use_container_width=True)

    st.write("📖 **Agenda Completa de Seguimiento**")
    st.dataframe(df_rec[['fecha_seguimiento', 'numero_celular', 'red_social', 'comentario']], use_container_width=True)

def formulario_recordatorio():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return
    
    st.subheader("⏰ Nuevo Cliente Potencial (Recordatorio)")
    st.markdown("Registra aquí a los clientes que han mostrado interés pero comprarán en otra fecha.")
    
    with st.form("form_recordatorio"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre del Cliente")
        telefono = col1.text_input("Celular/WhatsApp")
        
        fecha_proxima = col2.date_input("Fecha Tentativa de Contacto/Compra")
        servicio_interes = col2.selectbox("Servicio de Interés", ["Cusco Tradicional", "Machu Picchu Full Day", "Valle Sagrado", "Montaña 7 Colores", "Laguna Humantay", "Otros"])
        
        vendedores_map = lead_controller.obtener_mapeo_vendedores()
        vendedor_sel = st.selectbox("Asignar a Vendedor", list(vendedores_map.values()))
        comentario = st.text_area("Notas / Observaciones (¿Por qué no compra ahora?)")
        
        submitted = st.form_submit_button("GUARDAR RECORDATORIO", use_container_width=True)
        
        if submitted:
            # Buscar ID del vendedor
            id_vendedor = next((id for id, name in vendedores_map.items() if name == vendedor_sel), None)
            
            if not telefono or not nombre:
                st.warning("El Nombre y el Celular son obligatorios.")
            else:
                exito, mensaje = lead_controller.registrar_nuevo_lead(
                    telefono=telefono, 
                    origen=f"REC: {servicio_interes}", 
                    vendedor=id_vendedor,
                    comentario=f"CLIENTE: {nombre} | {comentario}",
                    fecha_seguimiento=fecha_proxima.isoformat()
                )
                
                if exito:
                    st.success(f"📌 Recordatorio para {nombre} guardado correctamente.")
                    st.balloons()
                else:
                    st.error(mensaje)

def constructor_itinerarios():
    """Interfaz para generar el Itinerario Digital y sincronizar con Cloud."""
    it_controller = st.session_state.get('itinerario_digital_controller')
    lead_controller = st.session_state.get('lead_controller')
    
    st.subheader("🎨 Constructor de Itinerario Automático")
    st.info("Esta sección genera el diseño visual y lo sincroniza con el Lead en la nube.")

    # 1. Selección de Lead
    leads = lead_controller.obtener_todos_leads()
    if not leads:
        st.warning("No hay leads registrados para asignar un itinerario.")
        return

    df_leads = pd.DataFrame(leads)
    lead_options = {f"{r['numero_celular']} - {r['id_lead']}": r['id_lead'] for _, r in df_leads.iterrows()}
    lead_sel = st.selectbox("Seleccione el Lead (Cliente)", options=list(lead_options.keys()))
    id_lead_actual = lead_options[lead_sel]

    # 2. Datos del Itinerario
    with st.expander("📝 Datos Generales del Pasajero", expanded=True):
        col1, col2 = st.columns(2)
        nombre_pasajero = col1.text_input("Nombre que aparecerá en el PDF", placeholder="Ej: Familia Rodriguez")
        titulo_viaje = col2.text_input("Título del Programa", placeholder="Ej: Cusco Mágico & Machu Picchu")
        duracion = col1.text_input("Duración", placeholder="Ej: 4D-3N")
        fecha_viaje = col2.date_input("Fecha Tentativa")
        es_b2b = st.checkbox("🚩 Este itinerario es para Venta B2B / Agencia", value=False)

    # 3. Construcción del Itinerario por Días
    st.markdown("---")
    st.write("📅 **Detalle de Tours por Día**")
    
    # Sistema dinámico de ingreso de tours (Simplificado para este ejemplo)
    num_dias = st.number_input("Número de días a detallar", min_value=1, max_value=15, value=1)
    tours_detalles = []
    
    for i in range(num_dias):
        with st.expander(f"Día {i+1}", expanded=(i==0)):
            t_nom = st.text_input(f"Nombre del Tour Día {i+1}", key=f"t_nom_{i}")
            t_desc = st.text_area(f"Descripción breve Día {i+1}", key=f"t_desc_{i}")
            
            c_inc, c_exc = st.columns(2)
            t_inc = c_inc.text_area(f"Incluye (Día {i+1}) - Uno por línea", key=f"t_inc_{i}", placeholder="Ticket de Ingreso\nAlmuerzo Buffet")
            t_exc = c_exc.text_area(f"No Incluye (Día {i+1}) - Uno por línea", key=f"t_exc_{i}", placeholder="Cena\nPropinas")
            
            tours_detalles.append({
                "numero": i + 1,
                "fecha": (fecha_viaje + timedelta(days=i)).strftime("%d / %m / %Y"),
                "nombre": t_nom, 
                "descripcion": t_desc,
                "incluye": [x.strip() for x in t_inc.split("\n") if x.strip()],
                "no_incluye": [x.strip() for x in t_exc.split("\n") if x.strip()]
            })

    st.write("📈 **Configuración de Precios**")
    cp1, cp2, cp3 = st.columns(3)
    p_nac = cp1.number_input("Precio Nacional ($)", min_value=0.0)
    p_ext = cp2.number_input("Precio Extranjero ($)", min_value=0.0)
    p_can = cp3.number_input("Precio CAN ($)", min_value=0.0)

    # Configuración de la "Culebrita" y Highlights
    st.markdown("---")
    st.write("🌍 **Inclusiones y Exclusiones Generales (Globales)**")
    highlights = st.text_area("Hitos / Highlights (Separados por comas)", placeholder="Machu Picchu, Montaña de Colores, Valle Sagrado")
    
    col_g1, col_g2 = st.columns(2)
    inc_global = col_g1.text_area("Incluye (Global) - Uno por línea", placeholder="Traslados Aeropuerto\nSeguro de Viaje")
    exc_global = col_g2.text_area("No Incluye (Global) - Uno por línea", placeholder="Vuelos Internacionales\nGastos Personales")
    
    # 4. Botón de Generación y Sincronización
    if st.button("🚀 GENERAR ITINERARIO PDF & SINCRONIZAR CLOUD", use_container_width=True):
        if not nombre_pasajero:
            st.error("El nombre del pasajero es obligatorio para el PDF.")
        else:
            # Construir el paquete JSON (datos_render) solicitado por el usuario
            datos_render = {
                "titulo": titulo_viaje,
                "duracion": duracion,
                "fecha_viaje": fecha_viaje.isoformat(),
                "highlights": [h.strip() for h in highlights.split(",")],
                "inclusiones_globales": [h.strip() for h in inc_global.split("\n") if h.strip()],
                "exclusiones_globales": [h.strip() for h in exc_global.split("\n") if h.strip()],
                "itinerario_detalles": tours_detalles, # Enviamos la lista de tours con nombre corregido
                "precios": {
                    "nacional": p_nac,
                    "extranjero": p_ext,
                    "can": p_can
                },
                "vendedor_id": st.session_state.get('user_id'),
                "metadata": {
                    "version": "1.0",
                    "snake_code": "snake_default_vcp",
                    "generado_por": st.session_state.get('user_email'),
                    "tipo_venta": "B2B" if es_b2b else "B2C"
                }
            }

            with st.spinner("Generando PDF y sincronizando con Supabase..."):
                exito, msg, url_pdf = it_controller.registrar_generacion_itinerario(
                    id_lead=id_lead_actual,
                    nombre_pasajero=nombre_pasajero,
                    id_vendedor=st.session_state.get('user_id'),
                    datos_render=datos_render
                )
                
                if exito:
                    st.success(f"✅ {msg}")
                    if url_pdf:
                        st.markdown(f"### [📥 DESCARGAR ITINERARIO PDF]({url_pdf})")
                        st.info("El link también ha sido guardado en la ficha del lead.")
                    st.balloons()
                else:
                    st.error(msg)

def gestion_registros_multicanal():
    st.subheader("📝 Gestión de Ingreso de Clientes")
    tipo_cliente = st.selectbox(
        "¿Qué tipo de registro desea realizar?",
        [
            "💰 Venta Confirmada (Directa)", 
            "⏰ Largo Plazo (Recordatorios / Futuro)"
        ]
    )
    
    st.markdown("---")
    
    if "Venta Confirmada" in tipo_cliente:
        registro_ventas_directa()
    elif "Largo Plazo" in tipo_cliente:
        formulario_recordatorio()

from controllers.itinerario_digital_controller import ItinerarioDigitalController

def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None): 
    if 'lead_controller' not in st.session_state:
        st.session_state.lead_controller = LeadController(supabase_client)
    if 'venta_controller' not in st.session_state:
        st.session_state.venta_controller = VentaController(supabase_client)
    if 'itinerario_digital_controller' not in st.session_state:
        st.session_state.itinerario_digital_controller = ItinerarioDigitalController(supabase_client)
    
    st.session_state.user_id = user_id

    if funcionalidad_seleccionada == "Gestión de Registros":
        gestion_registros_multicanal()
        st.divider()
        if st.checkbox("Ver historial de alertas y recordatorios"):
             render_reminders_dashboard()

