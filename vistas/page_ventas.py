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
        vendedor = st.selectbox("Asignar a", ["---Seleccione---","Angel", "Abel"])
        submitted = st.form_submit_button("Guardar Lead")
        
        if submitted:
            exito, mensaje = lead_controller.registrar_nuevo_lead(telefono, origen, vendedor)
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
    if not venta_controller: st.error("Error de inicialización de VentaController."); return

    st.subheader("💰 Registro de Venta")
    with st.form("form_registro_venta"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre Cliente")
        tel = col1.text_input("Celular")
        
        # Cambio solicitado: Tour -> ID_Paquete
        id_paquete = col2.text_input("ID_Paquete / Tour") 
        
        # Nuevos campos solicitados (Vendedor y Comprobante)
        vendedor_manual = col1.text_input("Vendedor (Nombre)", value=st.session_state.get('user_email', ''))
        tipo_comp = col2.radio("Tipo Comprobante", ["Boleta", "Factura", "Recibo Simple"], horizontal=True)

        monto_total = col1.number_input("Monto Total ($)", min_value=0.0, format="%.2f")
        monto_pagado = col2.number_input("Monto Pagado / Adelanto ($)", min_value=0.0, format="%.2f")
        
        # Archivos adjuntos
        st.markdown("---")
        st.write("📂 **Adjuntar Documentos**")
        c_file1, c_file2 = st.columns(2)
        file_itinerario = c_file1.file_uploader("Cargar Itinerario (PDF)", type=['pdf', 'docx'])
        file_boleta = c_file2.file_uploader("Cargar Boleta de Pago (Img/PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])

        submitted = st.form_submit_button("REGISTRAR VENTA", use_container_width=True)
        
        if submitted:
            # Llamada al controlador con los nuevos campos
            exito, msg = venta_controller.registrar_venta_directa(
                nombre_cliente=nombre,
                telefono=tel,
                origen="Directo",
                vendedor=vendedor_manual, # Usamos el valor del campo
                tour=id_paquete,
                tipo_hotel="Estándar", 
                fecha_inicio=date.today().isoformat(),
                fecha_fin=date.today().isoformat(),
                monto_total=monto_total,
                monto_depositado=monto_pagado,
                tipo_comprobante=tipo_comp, # Usamos el valor del campo
                file_itinerario=file_itinerario,
                file_pago=file_boleta
            )
            
            if exito:
                st.success(msg)
                # Mostrar link a boleta si el sistema de archivos estuviera real
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
                if st.button(f"Marcar como contactado {r.get('id_lead')}"):
                    # Aquí iría lógica para actualizar estado
                    st.success("Estado actualizado (Simulado)")

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
        
        vendedor = st.selectbox("Asignar a Vendedor", ["Angel", "Abel", "Agente Externo"])
        comentario = st.text_area("Notas / Observaciones (¿Por qué no compra ahora?)")
        
        submitted = st.form_submit_button("GUARDAR RECORDATORIO", use_container_width=True)
        
        if submitted:
            if not telefono or not nombre:
                st.warning("El Nombre y el Celular son obligatorios.")
            else:
                exito, mensaje = lead_controller.registrar_nuevo_lead(
                    telefono=telefono, 
                    origen=f"REC: {servicio_interes}", 
                    vendedor=vendedor,
                    comentario=f"CLIENTE: {nombre} | {comentario}",
                    fecha_seguimiento=fecha_proxima.isoformat()
                )
                
                if exito:
                    st.success(f"📌 Recordatorio para {nombre} guardado correctamente.")
                    st.balloons()
                else:
                    st.error(mensaje)

def render_reminder_visual_list():
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: return
    
    leads = lead_controller.obtener_todos_leads()
    if not leads: 
        st.info("Sin recordatorios pendientes.")
        return
        
    df = pd.DataFrame(leads)
    if 'red_social' in df.columns:
        df_rec = df[df['red_social'].str.contains("REC:", na=False)].copy()
        if not df_rec.empty:
            hoy = date.today()
            if 'fecha_seguimiento' in df_rec.columns:
                df_rec['fecha_seguimiento'] = pd.to_datetime(df_rec['fecha_seguimiento']).dt.date
            
            df_rec = df_rec.sort_values(by='fecha_seguimiento', ascending=True)
            
            # Clasificación simple sin botones
            atrasados = len(df_rec[df_rec['fecha_seguimiento'] < hoy])
            hoy_p = len(df_rec[df_rec['fecha_seguimiento'] == hoy])
            
            if atrasados > 0:
                st.error(f"🚨 Tienes {atrasados} contactos atrasados.")
            if hoy_p > 0:
                st.warning(f"📅 Tienes {hoy_p} contactos para hoy.")
            
            st.write("**Próximos Seguimientos:**")
            st.dataframe(df_rec[['fecha_seguimiento', 'numero_celular', 'comentario']].head(10), use_container_width=True, hide_index=True)

def render_dashboard_comercial():
    st.subheader("📊 Dashboard de Performance Comercial")
    
    # KPIs Estáticos
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas Mes", "$2,450", delta="+15%")
    c2.metric("Leads en Proceso", "42", delta="5")
    c3.metric("Conversión", "12%", delta="-2%")
    
    st.divider()
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write("📈 **Tendencia de Ventas**")
        # Aquí se podría llamar a render_sales_dashboard de dashboard_analytics
        from vistas.dashboard_analytics import render_sales_dashboard
        venta_controller = st.session_state.get('venta_controller')
        if 'reporte_controller' not in st.session_state:
            from controllers.reporte_controller import ReporteController
            st.session_state.reporte_controller = ReporteController(venta_controller.model.client)
        
        df_ventas, _ = st.session_state.reporte_controller.get_data_for_dashboard()
        if not df_ventas.empty:
             # Solo mostramos chart de ranking para no saturar
             sales_by_vendor = df_ventas.groupby('vendedor')['monto_total'].sum().reset_index()
             import plotly.express as px
             fig = px.bar(sales_by_vendor, x='vendedor', y='monto_total', title="Ranking de Ventas")
             st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ventas para graficar.")

    with col_b:
        st.write("🔔 **Agenda de Contacto**")
        render_reminder_visual_list()

def gestion_registros_multicanal():
    st.subheader("📝 Gestión de Ingreso de Clientes")
    tipo_cliente = st.selectbox(
        "¿Qué tipo de registro desea realizar?",
        ["💰 Venta Confirmada (Dinero Recibido)", "⏰ Largo Plazo (Recordatorios / Futuro)", "🧩 Potencial (Desde Itinerario)", "📱 Curioso (Facebook API / Leads Fríos)"]
    )
    
    st.markdown("---")
    
    if "Venta Confirmada" in tipo_cliente:
        registro_ventas_directa()
    elif "Largo Plazo" in tipo_cliente:
        formulario_recordatorio()
    elif "Potencial" in tipo_cliente:
        st.info("🎯 **Clientes provenientes del Motor de Itinerarios**")
        st.button("Sincronizar con Motor Externo")
    elif "Curioso" in tipo_cliente:
        st.info("📱 **Leads de Redes Sociales**")
        st.button("Cargar desde Meta API")

def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None): 
    if 'lead_controller' not in st.session_state:
        st.session_state.lead_controller = LeadController(supabase_client)
    if 'venta_controller' not in st.session_state:
        st.session_state.venta_controller = VentaController(supabase_client)
    
    st.session_state.user_id = user_id

    if funcionalidad_seleccionada == "Dashboard Comercial":
        render_dashboard_comercial()
    elif funcionalidad_seleccionada == "Gestión de Registros":
        gestion_registros_multicanal()
        st.divider()
        if st.checkbox("Ver historial de alertas y recordatorios"):
             render_reminders_dashboard()

