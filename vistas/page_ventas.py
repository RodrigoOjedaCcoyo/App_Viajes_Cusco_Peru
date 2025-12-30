# vistas/page_ventas.py (CÓDIGO FINAL CORREGIDO)
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import date
#import matplotlib as mp

# --- INICIALIZACIONES GLOBALES ELIMINADAS ---
# Estas líneas causaban un TypeError porque LeadController ya no acepta 0 argumentos.
# lead_controller = LeadController() 
# venta_controller = VentaController()


# --- Funcionalidades Internas ---
def get_vendedor_id():
    """
    Retorna el rol del usuario logueado.
    """
    return st.session_state.get('user_role', 'Desconocido')

def formulario_registro_leads():
    """1. Sub-función para la funcionalidad 'Registro de Leads'."""
    # <--- CORRECCIÓN CLAVE: ACCEDER AL CONTROLADOR DESDE SESSION STATE --->
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return
    
    st.title("📝 Registro de Nuevo Lead")
    st.markdown("---")

    vendedor_actual = get_vendedor_id()
    st.info(f"Registrando a cargo de: **{vendedor_actual}**")
        
    with st.form("form_nuevo_lead"):
        telefono = st.text_input("Número de Celular", help="Ingrese el número de contacto principal")
        Red_Social_Origen = st.selectbox(
            "Seleccione Red Social",
            ["---Seleccione---","Instagram", "Facebook", "Tik Tok", "Web", "Otro"],
            help= "Medio por el cual ingreso el Lead",
            index=0
        )
        # Opciones de vendedores:
        vendedor_seleccionado = st.selectbox(
            "Seleccione vendedor",
            ["---Seleccione---","Angel", "Abel"],
            index=0
        )

        submitted = st.form_submit_button("Guardar Lead")
        
        if submitted:
            # Uso de lead_controller corregido
            exito, mensaje = lead_controller.registrar_nuevo_lead(
                telefono,
                Red_Social_Origen,
                vendedor_seleccionado
            )
            
            if exito:
                st.success(mensaje) 
            else:
                st.error(mensaje)
                
# ----------------------------------------------------------------------
# FUNCIONALIDAD DE SEGUIMIENTO DE LEADS (Incluye formulario de actualización)
# ----------------------------------------------------------------------

def seguimiento_leads():
    """2. Sub-función para la funcionalidad 'Seguimiento de Leads'."""
    # <--- CORRECCIÓN CLAVE: ACCEDER AL CONTROLADOR DESDE SESSION STATE --->
    lead_controller = st.session_state.get('lead_controller')
    if not lead_controller: st.error("Error de inicialización de LeadController."); return

    st.title("🔎 Seguimiento de Cliente")
    st.markdown("---")
    
    vendedor_actual = get_vendedor_id()
    
    # Uso de lead_controller corregido
    todos_los_leads = lead_controller.obtener_leads_del_vendedor(vendedor_actual)
    # ... (el resto de la función es correcto) ...
    
    if leads_a_seguir:
        # ... (Creación del Formulario de Seguimiento) ...
        # ... (extracción de lead_id) ...
            
        submitted = st.form_submit_button("Guardar")
        
        if submitted:
            # Uso de lead_controller corregido
            exito, mensaje = lead_controller.actualizar_estado_lead(lead_id, nuevo_estado)
            
            if exito:
                st.success(mensaje)
                st.rerun() 
            else:
                st.error(mensaje)
    else:
        st.info(f"No tienes leads pendientes de seguimiento o activos.")
        # ... (Resto de la función) ...


# ----------------------------------------------------------------------
# FUNCIONALIDAD DE REGISTRO DE VENTA (Conversión)
# ----------------------------------------------------------------------

def registro_ventas():
    """3. Sub-función para la funcionalidad 'Registro de Ventas'."""
    # <--- CORRECCIÓN CLAVE: ACCEDER AL CONTROLADOR DESDE SESSION STATE --->
    venta_controller = st.session_state.get('venta_controller')
    if not venta_controller: st.error("Error de inicialización de VentaController."); return

    st.title("💰 Registro de Venta")
    st.markdown("---")
    
    # ... (Lógica de formulario) ...

    # Botón REGISTRAR
    submitted = st.form_submit_button("REGISTRAR", type="primary", use_container_width=True)

    if submitted:
        # --- Logica de validacion y envio minimo ---
        if not n_celular or n_vendedor =='Seleccione vendedor' or n_monto_total <=0:
            st.error('Los campos Celular, Vendedor y Monto Total son obligatorios')
        elif n_tour == 'Seleccione Tour':
            st.error('Debe seleccionar un Tour Valido')
        else:
            # Uso de venta_controller corregido
            exito, mensaje = venta_controller.registrar_venta_directa(
                telefono=n_celular,
                origen=n_tour,
                monto=n_monto_total,
                tour=n_tour,
                fecha_tour = n_fecha_inicio.strftime("%Y-%m-%d"),
                vendedor=n_vendedor
            )
        if exito:
            st.success(mensaje)
        else:
            st.error(mensaje)

# ----------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE LA VISTA (Llamada por main.py)
# ----------------------------------------------------------------------

# Se asume que main.py pasa rol_actual, aunque no esté en la firma original.
# La función debe aceptar todos los argumentos que le pasa main.py.
def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido'): 
    """
    Punto de entrada para el módulo de Ventas.
    Inicializa los controladores con la dependencia inyectada.
    """

    from controllers.lead_controller import LeadController
    from controllers.venta_controller import VentaController
    # 1. Inicializar e inyectar dependencias (CORRECTO)
    lead_controller = LeadController(supabase_client=supabase_client)
    venta_controller = VentaController(supabase_client=supabase_client)

    # 2. Guardar controladores y rol para acceso en otras funciones (CORRECTO)
    st.session_state['lead_controller'] = lead_controller
    st.session_state['venta_controller'] = venta_controller
    st.session_state['user_role'] = rol_actual

    st.title(f'Modulo de Ventas / {funcionalidad_seleccionada}')

    if funcionalidad_seleccionada == "Registro de Leads":
        formulario_registro_leads()
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        seguimiento_leads()
    elif funcionalidad_seleccionada == "Registro de Ventas":
        registro_ventas()
    else:
        st.error("Funcionalidad de Ventas no encontrada.")