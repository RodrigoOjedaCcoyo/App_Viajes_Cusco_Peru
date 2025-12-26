# vistas/page_ventas.py
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
    # Usamos el rol como ID de vendedor, ya que eliminamos la variable específica.
    return st.session_state.get('user_role', 'Rol Desconocido')

def formulario_registro_leads():
    """1. Sub-función para la funcionalidad 'Registro de Leads'."""
    st.subheader("📝 Registro de Nuevo Lead")
    
    vendedor_actual = get_vendedor_id()
    st.info(f"Registrando a cargo de: **{vendedor_actual}**")
        
    with st.form("form_nuevo_lead"):
        nombre = st.text_input("Nombre Completo del Cliente")
        email = st.text_input("Email")
        telefono = st.text_input("Teléfono / WhatsApp")
        origen = st.selectbox("Origen del Lead", ["Instagram", "Facebook", "Web", "Referido", "Otro"])
        
        submitted = st.form_submit_button("Guardar Lead")
        
        if submitted:
            # Llama al controlador para procesar los datos
            exito, mensaje = lead_controller.registrar_nuevo_lead(
                nombre, 
                email, 
                telefono, 
                origen, 
                vendedor_actual
            )
            
            if exito:
                st.success(mensaje)
                # Opcional: recargar para limpiar formulario
                st.rerun() 
            else:
                st.error(mensaje)
                
def seguimiento_leads():
    """2. Sub-función para la funcionalidad 'Seguimiento de Leads'."""
    st.subheader("🔎 Seguimiento de Leads (Mis Pendientes)")
    
    vendedor_actual = get_vendedor_id()
    
    # Llama al controlador para obtener los leads activos
    # Solo mostrar leads que NO están en estado 'Convertido'
    todos_los_leads = lead_controller.obtener_leads_del_vendedor(vendedor_actual)
    leads_activos = [l for l in todos_los_leads if 'Convertido' not in l['estado']]
    
    if leads_activos:
        df_leads = pd.DataFrame(leads_activos)
        
        # Columnas a mostrar para el seguimiento
        columnas_a_mostrar = ['id', 'nombre', 'email', 'telefono', 'origen', 'estado', 'fecha_creacion']
        st.dataframe(
            df_leads[columnas_a_mostrar].sort_values(by='id', ascending=False), # Mostrar el más reciente primero
            use_container_width=True, 
            hide_index=True
        )
        
        st.markdown(f"**Total de Leads en Seguimiento:** `{len(leads_activos)}`")
        
    else:
        st.info(f"No tienes leads activos en seguimiento. ¡Hora de registrar uno!")

def registro_ventas():
    """3. Sub-función para la funcionalidad 'Registro de Ventas' (Conversión)."""
    st.subheader("💰 Conversión y Registro de Venta")
    
    vendedor_actual = get_vendedor_id()
    
    # 1. Obtener Leads disponibles para la conversión (no convertidos)
    todos_los_leads = lead_controller.obtener_leads_del_vendedor(vendedor_actual)
    leads_activos = [l for l in todos_los_leads if 'Convertido' not in l['estado']]
    
    if not leads_activos:
        st.warning("No tienes Leads activos en estado 'Nuevo' o 'Seguimiento' para convertir en venta.")
        return

    # Mapeo de leads para el selector: 'ID 1 - Nombre (Email)'
    opciones_leads = [f"ID {l['id']} - {l['nombre']} ({l['email']})" for l in leads_activos]
    
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
                # Recarga para actualizar las tablas de seguimiento (ya no aparecerá el lead)
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
    
    # 💡 La lógica de main.py nos garantiza que la cadena 'funcionalidad_seleccionada'
    # solo contendrá uno de los tres nombres definidos en MODULOS_VISIBLES.
    
    if funcionalidad_seleccionada == "Registro de Leads":
        formulario_registro_leads()
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        seguimiento_leads()
    elif funcionalidad_seleccionada == "Registro de Ventas":
        registro_ventas()
    else:
        # Esto no debería ocurrir si main.py está bien configurado
        st.error("Funcionalidad de Ventas no encontrada.")