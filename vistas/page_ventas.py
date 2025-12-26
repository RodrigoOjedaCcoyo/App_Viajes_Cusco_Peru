# vistas/page_ventas.py

import streamlit as st
import pandas as pd
# Importar el controlador
from controllers.venta_controller import VentaController
from controllers.Leads_controller import LeadController

# Inicializar el controlador (se hace una sola vez)
venta_controller = VentaController()
Leads_controller = LeadController()
def _mostrar_formulario_leads():
    """Muestra la UI para el registro de nuevos leads (Clientes)."""
    st.header("📝 Registro de Nuevo Lead (Cliente)")
    
    # Adaptación del formulario HTML a Streamlit
    with st.form("form_registro_lead"):
        st.subheader("Datos del Nuevo Cliente")
        
        numero = st.text_input("Número de Celular", max_chars=15)
        red_social = st.selectbox("Red Social", ["Pagina Web", "Facebook", "Instagram", "Tik Tok", "No se sabe"])
        
        # El vendedor se toma del usuario logueado
        vendedor = st.session_state.get('vendedor_actual', 'Vendedor Desconocido')
        st.markdown(f"**Asignado a:** `{vendedor}`")
        
        submit_button = st.form_submit_button("REGISTRAR LEAD")
        
        if submit_button:
            if not numero or not red_social:
                st.error("Por favor, complete todos los campos obligatorios.")
                return
            
            datos = {
                'numero': numero,
                'red_social': red_social,
                'vendedor': vendedor,
                'estado': 'Nuevo' # Estado inicial fijo
            }
            
            # Llamada al Controlador
            try:
                resultado = lead_controller.registrar_nuevo_lead(datos)
                st.success(f"✅ Lead ({numero}) registrado correctamente y asignado a {vendedor}.")
            except ValueError as e:
                st.error(f"Error de validación: {e}")
            except Exception:
                st.error("Error al registrar en el sistema.")


def _mostrar_seguimiento():
    """Muestra la UI para el seguimiento de leads activos."""
    st.header("🔄 Seguimiento y Actualización de Leads")
    
    vendedor = st.session_state.get('vendedor_actual')
    if not vendedor:
        st.warning("No se pudo identificar al vendedor. Inicie sesión nuevamente.")
        return
        
    # 1. Obtener leads activos para el vendedor
    leads = lead_controller.obtener_leads_activos(vendedor)
    
    if not leads:
        st.info(f"No tiene leads activos asignados a usted ({vendedor}).")
        return
    
    # Convertir a DataFrame para mejor visualización y selección
    df_leads = pd.DataFrame(leads)
    df_leads['Selección'] = df_leads.apply(
        lambda row: f"{row['numero']} (Estado: {row['estado']})", axis=1
    )
    
    # 2. Formulario de Seguimiento
    with st.form("form_seguimiento"):
        lead_seleccionado = st.selectbox(
            "Seleccione el Lead para Seguimiento",
            options=df_leads['Selección'].tolist(),
            index=0
        )
        
        indice_seleccionado = df_leads[df_leads['Selección'] == lead_seleccionado].index[0]
        lead_data = df_leads.iloc[indice_seleccionado]
        
        st.markdown(f"**Estado actual:** `{lead_data['estado']}`")
        
        nuevo_estado = st.selectbox(
            "Cambiar Estado a",
            options=["Interesado", "Seguimiento", "Perdido", "Vendido"]
        )
        
        detalle = st.text_area("Detalle / Observaciones del Seguimiento")
        
        submit_button = st.form_submit_button("GUARDAR SEGUIMIENTO")
        
        if submit_button:
            datos_seguimiento = {
                'numero': lead_data['numero'],
                'estado_lead': nuevo_estado,
                'detalle': detalle,
                'vendedor': vendedor
            }
            # Llamada al Controlador para actualizar y registrar historial
            lead_controller.registrar_seguimiento(datos_seguimiento)
            st.success(f"✅ Estado del Lead {lead_data['numero']} actualizado a '{nuevo_estado}'.")


def _mostrar_registro_ventas():
    """Muestra la UI para el registro completo de una venta."""
    st.header("💵 Registrar Nueva Venta")
    
    # Adaptación del formulario HTML a Streamlit (simplificado)
    with st.form("form_registro_venta_completo"):
        
        # -----------------------------------------------------
        # Aquí van todos los campos de su Formulario.html
        # (Número, Vendedor, Tour, Nombre, Idioma, Montos, Fechas, Comprobante)
        # -----------------------------------------------------
        
        cel = st.text_input("Número de celular (11 dígitos)", max_chars=11)
        nombre = st.text_input("Nombre del Cliente", max_chars=10)
        tour = st.selectbox("Tour Seleccionado", ["Machu Picchu", "Cusco", "Lima", "Otro"])
        
        st.markdown("---")
        
        fecha_inicio = st.date_input("Fecha Inicio de Tour")
        monto_total = st.number_input("Monto Total ($)", min_value=0.0, step=0.01)
        monto_depositado = st.number_input("Monto Depositado ($)", min_value=0.0, step=0.01)
        
        # Archivos (Subida pendiente de integrar con Drive/Storage)
        archivos_subir = st.file_uploader("Documentos de la Venta (Ej. Pasaporte, Comprobante)", accept_multiple_files=True)
        
        submit_button = st.form_submit_button("REGISTRAR VENTA COMPLETA")
        
        if submit_button:
            # 1. Recolectar datos
            datos = {
                'numero': cel,
                'nombre': nombre,
                'tour': tour,
                # ... el resto de los campos ...
                'fecha_inicio': str(fecha_inicio),
                'monto_total': monto_total,
                'monto_depositado': monto_depositado,
                'vendedor': st.session_state.get('vendedor_actual')
            }
            
            # 2. Llamada al Controlador de Ventas
            try:
                # El controlador simulará la subida de archivos
                resultado = venta_controller.registrar_nueva_venta(datos, archivos_subir)
                st.success(f"✅ Venta registrada correctamente (ID {resultado.get('venta_id')}).")
            except Exception as e:
                st.error(f"Error al registrar la venta: {e}")


# --- Función Principal (El CEREBRO de la Vista) ---

def mostrar_pagina(funcionalidad_seleccionada):
    """
    Función que recibe el nombre del menú seleccionado y llama a la UI específica.
    """
    st.title("Módulo de Leads y Ventas")
    st.caption(f"Funcionalidad actual: **{funcionalidad_seleccionada}**")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Registro de Leads":
        _mostrar_formulario_leads()
        
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        _mostrar_seguimiento()
        
    elif funcionalidad_seleccionada == "Registro de Ventas":
        _mostrar_registro_ventas()
        
    else:
        st.error(f"Funcionalidad '{funcionalidad_seleccionada}' no implementada para este módulo.")