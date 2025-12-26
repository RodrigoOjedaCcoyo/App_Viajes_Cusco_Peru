# vistas/page_ventas.py (CÓDIGO COMPLETO FINAL)
import streamlit as st
import pandas as pd
from controllers.lead_controller import LeadController
from controllers.venta_controller import VentaController
from datetime import date

# Inicializar controladores
lead_controller = LeadController()
venta_controller = VentaController()

# --- Funcionalidades Internas ---

def get_vendedor_id():
    """Función auxiliar para obtener el ID del usuario/rol logueado."""
    return st.session_state.get('user_role', 'Rol Desconocido')

def formulario_registro_leads():
    """1. Sub-función para la funcionalidad 'Registro de Leads'."""
    st.title("📝 Registro de Nuevo Lead")
    st.markdown("---")

    vendedor_actual = get_vendedor_id()
    st.info(f"Registrando a cargo de: **{vendedor_actual}**")
        
    with st.form("form_nuevo_lead"):
        telefono = st.text_input("Número de Celular", help="Ingrese el número de contacto principal")
        Red_Social_Origen = st.selectbox(
            "Seleccione Red Social",
            ["Instagram", "Facebook", "Tik Tok", "Web", "Otro"],
            help= "Medio por el cual ingreso el Lead"
        )
        # Opciones de vendedores: Puedes cambiar esto para que filtre por rol si lo prefieres.
        vendedor_seleccionado = st.selectbox(
            "Seleccione vendedor",
            ["Angel", "Abel"]
        )

        submitted = st.form_submit_button("Guardar Lead")
        
        if submitted:
            exito, mensaje = lead_controller.registrar_nuevo_lead(
                telefono,
                Red_Social_Origen,
                vendedor_seleccionado
            )
            
            if exito:
                st.success(mensaje)
                st.rerun() 
            else:
                st.error(mensaje)
                
# ----------------------------------------------------------------------
# FUNCIONALIDAD DE SEGUIMIENTO DE LEADS (Incluye formulario de actualización)
# ----------------------------------------------------------------------

def seguimiento_leads():
    """2. Sub-función para la funcionalidad 'Seguimiento de Leads'."""
    st.title("🔎 Seguimiento de Cliente")
    st.markdown("---")
    
    vendedor_actual = get_vendedor_id()
    
    todos_los_leads = lead_controller.obtener_leads_del_vendedor(vendedor_actual)
    # Solo leads que el vendedor puede seguir o convertir
    leads_a_seguir = [l for l in todos_los_leads if l['estado'] not in ["Convertido (Vendido)", "No Interesado"]]
    
    if leads_a_seguir:
        # --- Creación del Formulario de Seguimiento ---
        with st.form("form_seguimiento_lead"):
            
            st.subheader("Actualizar Estado de Lead")
            
            # Mapeo de leads para el selector: 'ID - Número de Celular'
            opciones_leads = [f"ID {l['id']} - {l['telefono']} (Estado: {l['estado']})" for l in leads_a_seguir]
            
            lead_seleccionado_str = st.selectbox(
                "Seleccione Lead por Número de Celular",
                opciones_leads,
                help="Seleccione el cliente a quien actualizará el estado."
            )
            
            # Extracción del ID del Lead
            lead_id = int(lead_seleccionado_str.split(' ')[1])

            nuevo_estado = st.selectbox(
                "Nuevo Estado del Lead",
                ["Nuevo", "Seguimiento (Llamada)", "Seguimiento (Email)", "Cotización Enviada", "No Interesado"]
            )
            
            submitted = st.form_submit_button("Guardar")
            
            if submitted:
                exito, mensaje = lead_controller.actualizar_estado_lead(lead_id, nuevo_estado)
                
                if exito:
                    st.success(mensaje)
                    st.rerun() 
                else:
                    st.error(mensaje)
    else:
        st.info(f"No tienes leads pendientes de seguimiento o activos.")
                
    st.markdown("---")
    
    # --- Mostrar la Tabla de Referencia ---
    st.subheader("Tabla de Leads Activos")
    if leads_a_seguir:
        df_leads = pd.DataFrame(leads_a_seguir)
        columnas_a_mostrar = ['id', 'telefono', 'origen', 'estado', 'vendedor', 'fecha_creacion']
        st.dataframe(
            df_leads[columnas_a_mostrar].sort_values(by='id', ascending=False), 
            use_container_width=True, 
            hide_index=True
        )
    elif todos_los_leads:
         st.info("No hay leads activos, revisa los leads 'Convertido (Vendido)' o 'No Interesado'.")
    else:
         st.info("No hay leads registrados en el sistema.")


# ----------------------------------------------------------------------
# FUNCIONALIDAD DE REGISTRO DE VENTA (Conversión)
# ----------------------------------------------------------------------

def registro_ventas():
    """3. Sub-función para la funcionalidad 'Registro de Ventas' (Conversión)."""
    st.title("💰 Conversión y Registro de Venta")
    st.markdown("---")
    
    vendedor_actual = get_vendedor_id()
    
    # Obtener Leads disponibles para la conversión (solo los que no están convertidos o no interesados)
    todos_los_leads = lead_controller.obtener_leads_del_vendedor(vendedor_actual)
    leads_convertibles = [l for l in todos_los_leads if l['estado'] not in ["Convertido (Vendido)", "No Interesado"]]
    
    if not leads_convertibles:
        st.warning("No tienes Leads activos (Nuevos o en Seguimiento) para convertir en venta.")
        return

    # Mapeo de leads para el selector: 'ID - Teléfono (Estado)'
    opciones_leads = [f"ID {l['id']} - {l['telefono']} ({l['estado']})" for l in leads_convertibles]
    
    with st.form("form_registro_venta"):
        st.write(f"Registrando Venta a cargo de: **{vendedor_actual}**")
        
        # Selector de Lead
        lead_seleccionado_str = st.selectbox(
            "Seleccione el Lead a convertir en Venta",
            opciones_leads
        )
        
        # Extracción del ID del Lead
        lead_id = int(lead_seleccionado_str.split(' ')[1])

        # Campos de la Venta
        col1, col2 = st.columns(2)
        with col1:
            monto_total = st.number_input("Monto Total de la Venta (USD)", min_value=10.0, step=1.0, key="monto_venta")
            tour_paquete = st.text_input("Nombre del Tour o Paquete Vendido", key="tour_nombre")
        with col2:
            fecha_tour = st.date_input("Fecha de Inicio del Tour", date.today(), key="fecha_tour_venta")
        
        submitted = st.form_submit_button("Confirmar Venta y Marcar Lead como Convertido")
        
        if submitted:
            exito, mensaje = venta_controller.registrar_nueva_venta(
                lead_id, 
                monto_total, 
                tour_paquete, 
                fecha_tour.strftime("%Y-%m-%d"), 
                vendedor_actual
            )
            
            if exito:
                st.success(mensaje)
                st.rerun() 
            else:
                st.error(mensaje)


# ----------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE LA VISTA (Llamada por main.py)
# ----------------------------------------------------------------------

def mostrar_pagina(funcionalidad_seleccionada: str):
    """
    Punto de entrada para el módulo de Ventas.
    Redirige la ejecución según lo seleccionado en el menú lateral.
    """
    st.title(f"Módulo de Ventas / {funcionalidad_seleccionada}")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Registro de Leads":
        formulario_registro_leads()
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        seguimiento_leads()
    elif funcionalidad_seleccionada == "Registro de Ventas":
        registro_ventas()
    else:
        st.error("Funcionalidad de Ventas no encontrada.")