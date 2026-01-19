# vistas/page_ventas.py
import streamlit as st
import pandas as pd
from datetime import date
from controllers.lead_controller import LeadController
from controllers.venta_controller import VentaController



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
    if not venta_controller or not lead_controller: 
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

    # --- 🕵️ BUSCADOR DE ITINERARIO (FUERA DEL FORMULARIO) ---
    st.info("💡 Tip: Pegue el código del itinerario y pulse **Consultar** para llenar los datos automáticamente.")
    col_uuid, col_btn = st.columns([3, 1])
    
    def_itin = lead_data.get('ultimo_itinerario_id', '') if lead_data else ''
    id_itinerario_dig = col_uuid.text_input(
        "🆔 Código Itinerario Digital (CLOUD)", 
        value=str(def_itin) if def_itin else "",
        placeholder="UUID del diseño generado",
        key="uuid_input_external"
    )
    
    if col_btn.button("🔍 Consultar", use_container_width=True):
        if id_itinerario_dig:
            with st.spinner("Buscando itinerario..."):
                it_data = st.session_state.itinerario_digital_controller.get_itinerario_by_id(id_itinerario_dig)
                if it_data:
                    render = it_data.get('datos_render', {})
                    nombre_pax_cloud = it_data.get('nombre_pasajero_itinerario', '')
                    tour_nombre_cloud = render.get('titulo', '')
                    
                    st.session_state[f"val_nom_{id_itinerario_dig}"] = nombre_pax_cloud
                    st.session_state[f"val_tour_{id_itinerario_dig}"] = tour_nombre_cloud
                    st.success("¡Datos recuperados de la nube! 🚀")
                    st.rerun()
                else:
                    st.error("No se encontró el itinerario. Verifique el código.")

    # --- 📝 FORMULARIO DE REGISTRO ---
    with st.form("form_registro_venta"):
        col1, col2 = st.columns(2)
        
        # Valores por defecto basados en Lead o en la Consulta Cloud
        def_nombre = st.session_state.get(f"val_nom_{id_itinerario_dig}", lead_data.get('nombre_pasajero', '') if lead_data else '')
        def_tour = st.session_state.get(f"val_tour_{id_itinerario_dig}", "")

        nombre = col1.text_input("Nombre Cliente", value=def_nombre)
        tel = col1.text_input("Celular", value=lead_data.get('numero_celular', '') if lead_data else '')
        
        # El Tour ahora es automático (se muestra pero no se edita manualmente aquí)
        id_paquete = def_tour
        if id_paquete:
            col2.success(f"📌 Tour Detectado: **{id_paquete}**")
        else:
            col2.warning("⚠️ Sin Tour asignado (Use 'Consultar')")

        # 2. Selector de Vendedor Dinámico (Jalando de la tabla 'vendedor')
        vendedores_map = lead_controller.obtener_mapeo_vendedores()
        nombres_vendedores = list(vendedores_map.values())
        vendedor_manual = col1.selectbox("Asignado a (Vendedor)", nombres_vendedores)
        tipo_comp = col2.radio("Tipo Comprobante", ["Boleta", "Factura", "Recibo Simple"], horizontal=True)

        monto_total = col1.number_input("Monto Total ($)", min_value=0.0, format="%.2f")
        monto_pagado = col2.number_input("Monto Pagado / Adelanto ($)", min_value=0.0, format="%.2f")
        
        st.markdown("---")
        st.write("📂 **Adjuntar Documentos**")
        c_file1, c_file2 = st.columns(2)
        file_itinerario = c_file1.file_uploader("Cargar Itinerario (PDF)", type=['pdf', 'docx'])
        file_boleta = c_file2.file_uploader("Cargar Boleta de Pago (Img/PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])

        submitted = st.form_submit_button("✅ REGISTRAR VENTA Y SUBIR ARCHIVOS", use_container_width=True)
        
        if submitted:
            exito, msg = venta_controller.registrar_venta_directa(
                nombre_cliente=nombre,
                telefono=tel,
                origen="Directo",
                vendedor=vendedor_manual, 
                tour=id_paquete,
                tipo_hotel="Estándar", 
                fecha_inicio=date.today().isoformat(),
                fecha_fin=date.today().isoformat(),
                monto_total=monto_total,
                monto_depositado=monto_pagado,
                tipo_comprobante=tipo_comp,
                id_itinerario_digital=id_itinerario_dig if id_itinerario_dig else None,
                file_itinerario=file_itinerario,
                file_pago=file_boleta
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
            tours_detalles.append({"nombre": t_nom, "descripcion": t_desc})

    st.write("📈 **Configuración de Precios**")
    cp1, cp2, cp3 = st.columns(3)
    p_nac = cp1.number_input("Precio Nacional ($)", min_value=0.0)
    p_ext = cp2.number_input("Precio Extranjero ($)", min_value=0.0)
    p_can = cp3.number_input("Precio CAN ($)", min_value=0.0)

    # Configuración de la "Culebrita" y Highlights
    highlights = st.text_area("Hitos / Highlights (Separados por comas)", placeholder="Machu Picchu, Montaña de Colores, Valle Sagrado")
    
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
                "itinerario_detales": tours_detalles, # Enviamos la lista de tours
                "precios": {
                    "nacional": p_nac,
                    "extranjero": p_ext,
                    "can": p_can
                },
                "vendedor_id": st.session_state.get('user_id'),
                "metadata": {
                    "version": "1.0",
                    "snake_code": "snake_default_vcp",
                    "generado_por": st.session_state.get('user_email')
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
            "🎨 Constructor de Itinerarios",
            "⏰ Largo Plazo (Recordatorios / Futuro)"
        ]
    )
    
    st.markdown("---")
    
    if "Venta Confirmada" in tipo_cliente:
        registro_ventas_directa()
    elif "Constructor de Itinerarios" in tipo_cliente:
        constructor_itinerarios()
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

