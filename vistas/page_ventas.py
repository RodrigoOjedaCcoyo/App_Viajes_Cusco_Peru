# vistas/page_ventas.py
import streamlit as st
import pandas as pd
from datetime import date
from controllers.itinerario_controller import ItinerarioController
from controllers.lead_controller import LeadController
from controllers.venta_controller import VentaController

# --- FUNCIONES DE APOYO CON CACHÉ ---
@st.cache_data(ttl=600)
def load_catalogo_paquetes(_controller):
    return _controller.get_catalogo_paquetes()

@st.cache_data(ttl=600)
def load_catalogo_tours(_controller):
    return _controller.get_catalogo_tours()

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

# --- MÓDULOS DEL NUEVO SISTEMA MODULAR ---

def flash_quote_view(controller):
    st.subheader("⚡ Consulta Rápida (Flash Quote)")
    col1, col2 = st.columns(2)
    with col1:
        df_p = load_catalogo_paquetes(controller)
        paquete_sel = st.selectbox("Paquete Base", options=df_p['nombre'].tolist() if not df_p.empty else ["No hay datos"])
    with col2:
        adultos = st.number_input("Adultos", min_value=1, value=2)
        ninos = st.number_input("Niños", min_value=0, value=0)
        
    if not df_p.empty and paquete_sel != "No hay datos":
        row = df_p[df_p['nombre'] == paquete_sel].iloc[0]
        # Búsqueda flexible de costo (puede llamarse costo_base, precio o monto)
        costo = float(row.get('costo_base') or row.get('precio') or row.get('monto') or 0)
        
        total_estimado = (costo * adultos) + (costo * 0.7 * ninos)
        st.metric("Precio Estimado (USD)", f"${total_estimado:,.2f}")
        
        if st.button("Registrar Interés Comercial"):
            controller.registrar_consulta_pasiva('FLASH', {
                "paquete": paquete_sel,
                "adultos": adultos,
                "ninos": ninos,
                "total": total_estimado,
                "vendedor_id": st.session_state.get('user_id')
            })
            st.success("Interés registrado para analítica comercial.")

def itinerary_builder_view(controller):
    st.subheader("🧩 Itinerary Builder (Módulo Independiente)")
    st.info("El constructor de itinerarios ahora funciona como una aplicación independiente para mayor velocidad.")
    
    if st.button("🚀 Abrir Constructor Externo", use_container_width=True):
        # Aquí podrías poner el link si el usuario tuviera una URL fija
        st.link_button("Ir al Constructor Premium", "https://app-itinerarios-cusco.streamlit.app/")
    
    st.divider()
    st.markdown("""
    **Nota para el equipo:**
    Para evitar lentitud en el sistema principal, el armado de PDFs se ha trasladado a su propia plataforma. 
    Los datos se sincronizan automáticamente con la base de datos central.
    """)



def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None): 
    # Inyectar controladores en session_state si no existen
    if 'lead_controller' not in st.session_state:
        st.session_state.lead_controller = LeadController(supabase_client)
    if 'venta_controller' not in st.session_state:
        st.session_state.venta_controller = VentaController(supabase_client)
    
    it_controller = ItinerarioController(supabase_client)
    st.session_state.user_id = user_id

    st.title(f"Módulo Ventas: {funcionalidad_seleccionada}")

    if funcionalidad_seleccionada == "Registro de Ventas":
        registro_ventas_directa()
    elif funcionalidad_seleccionada == "Automatización e Itinerarios":
        t1, t2, t3 = st.tabs(["⚡ Flash Quote", "🧩 Itinerary Builder", "📊 Dashboard Comercial"])
        with t1: flash_quote_view(it_controller)
        with t2: itinerary_builder_view(it_controller)
        with t3:
            from vistas.dashboard_analytics import render_sales_dashboard
            # Obtenemos data fresca
            rc = st.session_state.get('venta_controller') # Reusing existing controller connection logic indirectly via report controller pattern if needed, but here simple:
            # Better approach: Use the ReportController pattern which has the aggregations
            if 'reporte_controller' not in st.session_state:
                from controllers.reporte_controller import ReporteController
                st.session_state.reporte_controller = ReporteController(supabase_client)
            
            df_ventas, _ = st.session_state.reporte_controller.get_data_for_dashboard()
            render_sales_dashboard(df_ventas)
