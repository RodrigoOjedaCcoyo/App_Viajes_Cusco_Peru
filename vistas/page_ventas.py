# vistas/page_ventas.py (CÓDIGO FINAL CORREGIDO)
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# --- INICIALIZACIONES GLOBALES ELIMINADAS ---
# Estas líneas causaban un TypeError porque LeadController ya no acepta 0 argumentos.
# lead_controller = LeadController() 
# venta_controller = VentaController()


# --- Funcionalidades Internas ---
def get_vendedor_id():
    """
    Retorna el rol del usuario logueado.
    """
    return st.session_state.get('user_id')

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
    
    # Obtener leads
    # Obtener leads (VISTA GENERAL - TODOS LOS LEADS)
    st.info(f"Modo Vista General: Mostrando todos los leads del sistema.") 
    leads_a_seguir = lead_controller.obtener_todos_leads()
    
    if leads_a_seguir:
        st.write(f"Total de leads encontrados: {len(leads_a_seguir)}")
        
        # Mostrar tabla de datos
        df = pd.DataFrame(leads_a_seguir)
        if not df.empty:
            st.dataframe(df)

        st.markdown("### Actualizar Estado de Lead")
        with st.form("form_seguimiento"):
            # Crear diccionario para selectbox: ID -> Texto
            # Corrección de claves: 'id' -> 'id_lead', 'telefono' -> 'numero_celular'
            opciones_leads = {l['id_lead']: f"Lead #{l['id_lead']} - {l.get('numero_celular', 'Sin Celular')}" for l in leads_a_seguir}
            
            lead_id_selec = st.selectbox(
                "Seleccione Lead a Actualizar",
                options=list(opciones_leads.keys()),
                format_func=lambda x: opciones_leads[x]
            )
            
            nuevo_estado = st.selectbox(
                "Nuevo Estado",
                ["Nuevo", "Contactado", "En Negociación", "Cierre Ganado", "Cierre Perdido"]
            )
            
            submitted = st.form_submit_button("Actualizar Estado")
            
            if submitted:
                exito, mensaje = lead_controller.actualizar_estado_lead(lead_id_selec, nuevo_estado)
                
                if exito:
                    st.success(mensaje)
                    st.rerun() 
                else:
                    st.error(mensaje)
    else:
        st.info(f"No tienes leads asignados actualmente.")


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
    
    with st.form("form_registro_venta", clear_on_submit=False):
        st.subheader("1. Datos del Cliente")
        col1, col2 = st.columns(2)
        n_nombre = col1.text_input("Nombre Completo Cliente")
        n_celular = col1.text_input("Celular Cliente")
        n_origen = col2.selectbox("Red Social Origen", ["---Seleccione---", "Facebook", "Instagram", "TikTok", "Web", "Recomendado", "Otro"])
        n_vendedor = st.selectbox("Vendedor Responsable", ["---Seleccione---", "Angel", "Abel", "Otro"])

        st.subheader("2. Detalle del Viaje")
        c1, c2, c3 = st.columns(3)
        n_tour = c1.selectbox("Tour Principal", ["---Seleccione---", "Machu Picchu Full Day", "Montaña 7 Colores", "Laguna Humantay", "Valle Sagrado", "City Tour", "Paquete Personalizado"])
        n_tipo_hotel = c2.radio("¿Incluye Hotel?", ["Sin Hotel", "Con Hotel"], horizontal=True)
        # Placeholder para fechas (inicio/fin)
        n_fecha_inicio = c1.date_input("Fecha Inicio Viaje", value=date.today())
        n_fecha_fin = c2.date_input("Fecha Fin Viaje", value=date.today())

        st.subheader("3. Pagos y Comprobantes")
        pc1, pc2, pc3 = st.columns(3)
        n_monto_total = pc1.number_input("Monto Total (USD)", min_value=0.0, step=10.0, format="%.2f")
        n_monto_depositado = pc2.number_input("Monto Depositado (USD)", min_value=0.0, step=10.0, format="%.2f")
        
        # Calculo visual del saldo (solo informativo aquí, real en backend)
        saldo_visual = n_monto_total - n_monto_depositado
        pc3.metric("Saldo Pendiente", f"${saldo_visual:.2f}")

        n_tipo_comprobante = st.selectbox("Tipo de Comprobante", ["Boleta", "Factura", "Recibo Simple"])

        st.subheader("4. Evidencias y Archivos")
        f1, f2 = st.columns(2)
        file_itinerario = f1.file_uploader("Cargar Itinerario (PDF/Img)", type=['png', 'jpg', 'jpeg', 'pdf'])
        file_pago = f2.file_uploader("Cargar Comprobante Pago (PDF/Img)", type=['png', 'jpg', 'jpeg', 'pdf'])

        # Botón REGISTRAR
        st.markdown("---")
        submitted = st.form_submit_button("REGISTRAR VENTA", type="primary", use_container_width=True)

        if submitted:
            # --- Logica de validacion y envio ---
            errores = []
            if not n_nombre: errores.append("Falta Nombre del Cliente")
            if not n_celular: errores.append("Falta Celular del Cliente")
            if n_vendedor =='---Seleccione---': errores.append("Seleccione un Vendedor")
            if n_tour == '---Seleccione---': errores.append("Seleccione un Tour")
            if n_monto_total <= 0: errores.append("El Monto Total debe ser mayor a 0")
            if n_fecha_fin < n_fecha_inicio: errores.append("La fecha fin no puede ser anterior a la fecha inicio")

            if errores:
                for e in errores: st.error(e)
            else:
                # Uso de venta_controller corregido
                exito, mensaje = venta_controller.registrar_venta_directa(
                    nombre_cliente=n_nombre,
                    telefono=n_celular,
                    origen=n_origen,
                    vendedor=n_vendedor,
                    tour=n_tour,
                    tipo_hotel=n_tipo_hotel,
                    fecha_inicio=str(n_fecha_inicio),
                    fecha_fin=str(n_fecha_fin),
                    monto_total=n_monto_total,
                    monto_depositado=n_monto_depositado,
                    tipo_comprobante=n_tipo_comprobante,
                    file_itinerario=file_itinerario,
                    file_pago=file_pago
                )
                if exito:
                    st.success(mensaje)
                    st.balloons()
                else:
                    st.error(mensaje)

# ----------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE LA VISTA (Llamada por main.py)
# ----------------------------------------------------------------------

# Se asume que main.py pasa rol_actual, aunque no esté en la firma original.
# La función debe aceptar todos los argumentos que le pasa main.py.
def mostrar_pagina(funcionalidad_seleccionada: str, supabase_client, rol_actual='Desconocido', user_id=None): 
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
    st.session_state['user_id'] = user_id

    st.title(f'Modulo de Ventas / {funcionalidad_seleccionada}')

    if funcionalidad_seleccionada == "Registro de Leads":
        formulario_registro_leads()
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        seguimiento_leads()
    elif funcionalidad_seleccionada == "Registro de Ventas":
        registro_ventas()
    else:
        st.error("Funcionalidad de Ventas no encontrada.")