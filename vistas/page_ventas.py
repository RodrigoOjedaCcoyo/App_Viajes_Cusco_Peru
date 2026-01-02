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
    # Obtener leads (VISTA GENERAL - TODOS LOS LEADS)
    leads_a_seguir = lead_controller.obtener_todos_leads()
    
    if leads_a_seguir:
        
        # 1. Convertir a DataFrame
        df = pd.DataFrame(leads_a_seguir)

        if not df.empty:
            # Obtener mapeo de vendedores {id: nombre}
            mapeo_vendedores = lead_controller.obtener_mapeo_vendedores()
            
            # Crear nueva columna 'Vendedor' mapeando el ID
            # Si no encuentra el ID, pone 'Desconocido'
            df['Vendedor'] = df['id_vendedor'].map(mapeo_vendedores).fillna('Desconocido')

            # --- SECCIÓN DE FILTROS (SEGMENTADORES) ---
            st.subheader("Filtros de Búsqueda")
            col_f1, col_f2 = st.columns(2)
            
            # Obtener valores únicos para los filtros (NOMBRES, no IDs)
            vendedores_unicos = sorted(df['Vendedor'].unique().astype(str))
            estados_unicos = sorted(df['estado_lead'].unique().astype(str))

            with col_f1:
                filtro_vendedor = st.multiselect("Filtrar por Vendedor", options=vendedores_unicos)
            
            with col_f2:
                filtro_estado = st.multiselect("Filtrar por Estado", options=estados_unicos)

            # Aplicar filtros
            if filtro_vendedor:
                df = df[df['Vendedor'].isin(filtro_vendedor)]
            
            if filtro_estado:
                df = df[df['estado_lead'].astype(str).isin(filtro_estado)]

            st.write(f"Resultados: {len(df)} registros.")

            # --- CONFIGURACIÓN DE COLUMNAS PARA EDITOR ---
            # Definimos estados permitidos (Normalizados según DB)
            opciones_estado = ["NUEVO", "CONTACTADO", "COTIZACION", "SEGUIMIENTO", "CIERRE GANADO", "CIERRE PERDIDO", "DESCARTADO", "CONVERTIDO"]

            column_config = {
                "estado_lead": st.column_config.SelectboxColumn(
                    "Estado (Editable)",
                    help="Seleccione el nuevo estado",
                    width="medium",
                    options=opciones_estado,
                    required=True
                ),
                "Vendedor": st.column_config.TextColumn(
                    "Vendedor Asignado",
                    width="medium",
                    disabled=True # Solo lectura
                ),
                "numero_celular": st.column_config.TextColumn("Celular", disabled=True),
                "red_social": st.column_config.TextColumn("Red Social", disabled=True),
            }

            # Columnas a ocultar VISUALMENTE (pero mantener en datos para índices)
            # Usamos column_order para definir qué mostrar y en qué orden
            # Ocultamos: id_lead, id_vendedor, fecha_creacion, whatsapp
            
            cols_mostrar = ['Vendedor', 'estado_lead', 'numero_celular', 'red_social'] 
            # Añadimos cualquier otra columna que venga del DF y no sea de las ocultas explícitamente ni de las ya listadas
            extras = [c for c in df.columns if c not in cols_mostrar and c not in ['id_lead', 'id_vendedor', 'fecha_creacion', 'whatsapp']]
            column_order = cols_mostrar + extras

            # --- DATA EDITOR ---
            edited_df = st.data_editor(
                df,
                column_config=column_config,
                column_order=column_order,
                use_container_width=True,
                hide_index=True,
                key="editor_leads",
                disabled=extras # Deshabilitar edición en columnas extra por defecto
            )

            # --- DETECCIÓN DE CAMBIOS Y GUARDADO ---
            # Verificamos si hubo cambios en la sesión
            if "editor_leads" in st.session_state and st.session_state["editor_leads"]["edited_rows"]:
                updates = st.session_state["editor_leads"]["edited_rows"]
                
                cambios_realizados = False
                for idx_str, cambios in updates.items():
                    idx = int(idx_str) # El índice viene como int en versiones nuevas, pero aseguramos
                    
                    if 'estado_lead' in cambios:
                        nuevo_estado = cambios['estado_lead']
                        # Recuperar ID del Lead original usando el índice del DF filtrado
                        # IMPORTANTE: df es el dataframe filtrado actual, por lo que el índice idx corresponde a él
                        id_lead_actual = df.iloc[idx]['id_lead']
                        
                        exito, msg = lead_controller.actualizar_estado_lead(int(id_lead_actual), nuevo_estado)
                        if exito:
                            st.toast(f"✅ Lead #{id_lead_actual}: {nuevo_estado}")
                            cambios_realizados = True
                        else:
                            st.error(f"Error actualizando Lead #{id_lead_actual}: {msg}")
                
                if cambios_realizados:
                    # Esperar brevemente y recargar para refrescar datos limpios
                    import time
                    time.sleep(0.5)
                    st.rerun()

    else:
        st.info(f"No hay leads registrados.")



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

def crear_itinerario_automatico():
    """4. Sub-función para la funcionalidad 'Automatización e Itinerarios'."""
    from controllers.itinerario_controller import ItinerarioController
    supabase_client = st.session_state.get('supabase_client_ventas')
    user_id = st.session_state.get('user_id')
    
    controller = ItinerarioController(supabase_client)
    
    st.subheader("📝 Generador de Itinerario con Cotización", divider='green')
    st.info("Complete las 9 preguntas básicas para generar la propuesta comercial.")

    # --- CARGA DE CATÁLOGOS ---
    df_leads = controller.get_leads_activos()
    df_catalogo = controller.get_catalogo_paquetes()
    
    # 1. Formulario Principal (Basic)
    with st.container(border=True):
        st.subheader("🟢 Formulario Básico")
        
        c1, c2 = st.columns(2)
        with c1:
            lead_sel = st.selectbox("1. Lead / Prospecto", options=df_leads['id_lead'].tolist() if not df_leads.empty else [0], 
                                  format_func=lambda x: f"Lead #{x}" if x != 0 else "No hay leads disponibles")
            
            paquete_sel = st.selectbox("3. Paquete Base Inicial", options=df_catalogo['nombre'].tolist())
            row_paquete = df_catalogo[df_catalogo['nombre'] == paquete_sel].iloc[0]
            
        with c2:
            st.info(f"👨‍💼 Vendedor: **{user_id}**")
            fecha_vi = st.date_input("4. Fecha Tentativa de Llegada", date.today())
            
        st.divider()
        
        c3, c4 = st.columns(2)
        with c3:
            tipo_t = st.radio("5. ¿Nacionales o Extranjeros?", ["Nacional", "Extranjero"], horizontal=True)
            adultos = st.number_input("6. Número de Adultos", min_value=1, value=1)
        with c4:
            ninos_text = st.text_input("7. Edades de Niños (Separe por coma)", help="Ej: 5, 8")
            ninos_lista = [int(e.strip()) for e in ninos_text.split(',') if e.strip().isdigit()]
            
        st.divider()
        
        c5, c6 = st.columns(2)
        with c5:
            alojamiento = st.selectbox("8. Categoría de Alojamiento", ["Económico", "Turista", "Superior", "Lujo", "Sin Alojamiento"])
        with c6:
            tren = st.selectbox("9. Tipo de Tren (Machu Picchu)", ["Vistadome", "Expedition", "Hiram Bingham", "Local (Solo DNI)"])

    # --- SECCIÓN DE COMPLEJIDAD ---
    with st.expander("⚙️ Personalización Avanzada y Margen"):
        st.subheader("🔴 Control de Ajustes")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### V. Servicios Extra")
            st.multiselect("Añadir/Quitar del Paquete", ["+ Montaña 7 Colores", "- Tour Valle Sur", "+ Cena Show"])
        with col_p2:
            st.markdown("##### VI. Ajuste de Ganancia")
            margen = st.slider("Margen (%)", 0, 100, 20)
            ajuste_manual = st.number_input("Opcional: Ajuste Fijo ($)", value=0.0)

    # --- CÁLCULOS ---
    datos_cotizacion = {
        "id_lead": lead_sel,
        "nombre_paquete": paquete_sel,
        "costo_base_paquete": row_paquete.get('costo_base', 0),
        "num_adultos": adultos,
        "edades_ninos_json": ninos_lista,
        "tipo_turista": tipo_t,
        "fecha_llegada": fecha_vi,
        "alojamiento": alojamiento,
        "tren": tren,
        "servicios_extra": servicios_extra,
        "margen_ganancia": margen,
        "ajuste_manual_fijo": ajuste_manual
    }
    
    res = controller.calcular_presupuesto(datos_cotizacion)
    
    st.divider()
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("Costo Base", f"${res['subtotal_costo']:,.2f}")
    
    if res['sobrecosto_fiestas'] > 0:
        res_col2.metric("Recargo Feriado", f"${res['sobrecosto_fiestas']:,.2f}", delta="Temp. Alta", delta_color="inverse")
    else:
        res_col2.metric("Precio Venta", f"${res['total_venta']:,.2f}", delta=f"Ganancia: ${res['ganancia_estimada']:,.2f}")
    
    if res['sobrecosto_fiestas'] > 0:
        res_col3.metric("Precio Venta Final", f"${res['total_venta']:,.2f}", delta=f"Ganancia: ${res['ganancia_estimada']:,.2f}")

    # --- GENERACIÓN DE PDF REAL ---
    pdf_bytes = controller.generar_pdf_itinerario(datos_cotizacion, res)
    
    st.download_button(
        label="🚀 Descargar Itinerario y Cotización (PDF)",
        data=pdf_bytes,
        file_name=f"Itinerario_Lead_{lead_sel}_{date.today()}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )

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
    st.session_state['supabase_client_ventas'] = supabase_client

    st.title(f'Modulo de Ventas / {funcionalidad_seleccionada}')

    if funcionalidad_seleccionada == "Registro de Leads":
        formulario_registro_leads()
    elif funcionalidad_seleccionada == "Seguimiento de Leads":
        seguimiento_leads()
    elif funcionalidad_seleccionada == "Registro de Ventas":
        registro_ventas()
    elif funcionalidad_seleccionada == "Automatización e Itinerarios":
        crear_itinerario_automatico()
    else:
        st.error("Funcionalidad de Ventas no encontrada.")
