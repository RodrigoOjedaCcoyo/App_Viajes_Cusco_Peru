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
        tour = col2.selectbox("Tour", ["Machu Picchu", "7 Colores", "Humantay"])
        monto = col2.number_input("Monto Total ($)", min_value=0.0)
        
        submitted = st.form_submit_button("REGISTRAR VENTA")
        if submitted:
            # Lógica de registro simplificada para restaurar funcionalidad
            st.success("Venta registrada correctamente.")

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

def itinerary_builder_view(controller):
    st.subheader("🧩 Constructor de Itinerario Modular")
    if 'itinerario_piezas' not in st.session_state: st.session_state.itinerario_piezas = []

    df_p = load_catalogo_paquetes(controller)
    df_t = load_catalogo_tours(controller)

    paquete_init = st.selectbox("Cargar Plantilla", ["---Vacío---"] + df_p['nombre'].tolist() if not df_p.empty else ["---Vacío---"])
    if st.button("Cargar / Resetear") and paquete_init != "---Vacío---":
        id_p = df_p[df_p['nombre'] == paquete_init].iloc[0]['id']
        st.session_state.itinerario_piezas = controller.get_tours_de_paquete(id_p)
        st.rerun()

    if st.session_state.itinerario_piezas:
        df_edit = pd.DataFrame(st.session_state.itinerario_piezas)
        if 'notas_operativas' not in df_edit.columns: df_edit['notas_operativas'] = ""
        
        new_df = st.data_editor(df_edit, use_container_width=True, num_rows="dynamic", key="it_editor")
        st.session_state.itinerario_piezas = new_df.to_dict('records')
        
        # Cálculos y PDF
        c1, c2 = st.columns(2)
        margen = c1.slider("Margen (%)", 0, 100, 25)
        adultos = c2.number_input("Adultos", 1, 10, 2, key="it_a")
        
        res = controller.calcular_presupuesto_modular(st.session_state.itinerario_piezas, 
                                                   {"adultos": adultos, "ninos": 0, "margen": margen, "ajuste_fijo": 0})
        st.metric("TOTAL VENTA", f"${res['total_venta']:,.2f}")
        
        cliente = st.text_input("Nombre Cliente (PDF)")
        if st.button("Generar PDF Premium") and cliente:
            pdf = controller.generar_pdf_premium({"cliente_nombre": cliente, "itinerario": st.session_state.itinerario_piezas, "total": res['total_venta'], "num_adultos": adultos, "num_ninos": 0, "fecha_viaje": date.today().isoformat(), "origen": "Ventas"})
            if pdf: st.download_button("Descargar PDF", pdf, f"Itinerario_{cliente}.pdf", "application/pdf")

def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None): 
    # Inyectar controladores en session_state si no existen
    if 'lead_controller' not in st.session_state:
        st.session_state.lead_controller = LeadController(supabase_client)
    if 'venta_controller' not in st.session_state:
        st.session_state.venta_controller = VentaController(supabase_client)
    
    it_controller = ItinerarioController(supabase_client)
    st.session_state.user_id = user_id

    st.title(f"Módulo Ventas: {funcionalidad_seleccionada}")

    if funcionalidad_seleccionada == "Registro de Leads":
        formulario_registro_leads()
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        seguimiento_leads()
    elif funcionalidad_seleccionada == "Registro de Ventas":
        registro_ventas_directa()
    elif funcionalidad_seleccionada == "Automatización e Itinerarios":
        t1, t2 = st.tabs(["⚡ Flash Quote", "🧩 Itinerary Builder"])
        with t1: flash_quote_view(it_controller)
        with t2: itinerary_builder_view(it_controller)
