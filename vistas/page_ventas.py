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
    # --- IMPORTACIÓN DINÁMICA DE RECURSOS ---
    import sys
    import os
    itinerario_path = os.path.join(os.getcwd(), 'Itinerario')
    if itinerario_path not in sys.path: sys.path.append(itinerario_path)
    
    try:
        from Itinerario.datos_tours import tours_db, paquetes_db
        from Itinerario.App_Ventas import generar_pdf_web
    except ImportError:
        st.error("No se pudieron cargar los módulos del constructor de itinerarios.")
        return

    # --- ESTILOS PREMIUM (TURQUESA) ---
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #55b7b0;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 8px 16px;
            font-weight: bold;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #449e98;
            color: white;
        }
        div[data-testid="column"] > div > div > div[data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-child(3)) button {
            background-color: transparent !important;
            border: 1px solid #e0e0e0 !important;
            color: #55b7b0 !important;
            padding: 0px !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.subheader("🛡️ Constructor de Itinerarios Premium")
    
    # --- ESTADO LOCAL DEL CONSTRUCTOR ---
    if 'curr_itinerario' not in st.session_state: st.session_state.curr_itinerario = []
    
    col1, col2 = st.columns([1, 1.8])

    with col1:
        st.markdown("#### 👤 Datos del Viaje")
        nombre_cliente = st.text_input("Nombre Cliente", placeholder="Ej: Juan Pérez")
        
        c1, c2 = st.columns(2)
        vendedor = c1.text_input("Vendedor", value=st.session_state.get('user_email', 'Agente'))
        celular = c2.text_input("Celular", placeholder="+51...")
        
        tc1, tc2 = st.columns(2)
        if 'origen_previo' not in st.session_state: st.session_state.origen_previo = "Nacional/Chileno"
        tipo_t = tc1.radio("Origen", ["Nacional/Chileno", "Extranjero"], key="it_origen")
        modo_s = tc2.radio("Servicio", ["Sistema Pool", "Servicio Privado"], key="it_servicio")
        
        # Actualización de precios al cambiar origen
        if tipo_t != st.session_state.origen_previo:
            for tour in st.session_state.curr_itinerario:
                t_base = next((t for t in tours_db if t['titulo'] == tour['titulo']), None)
                if t_base:
                    tour['costo'] = t_base['costo_nacional'] if "Nacional" in tipo_t else t_base['costo_extranjero']
            st.session_state.origen_previo = tipo_t
            st.rerun()

        st.markdown("#### 👥 Pasajeros")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            n_adultos_nac = st.number_input("Adt. Nac", 0, value=1 if "Nacional" in tipo_t else 0, key="num_an")
            n_ninos_nac = st.number_input("Niñ. Nac", 0, value=0, key="num_nn")
        with p_col2:
            n_adultos_ext = st.number_input("Adt. Ext", 0, value=1 if "Extranjero" in tipo_t else 0, key="num_ae")
            n_ninos_ext = st.number_input("Niñ. Ext", 0, value=0, key="num_ne")
        with p_col3:
            n_adultos_can = st.number_input("Adt. CAN", 0, value=0, key="num_ac")
            n_ninos_can = st.number_input("Niñ. CAN", 0, value=0, key="num_nc")
        
        total_pax = n_adultos_nac + n_ninos_nac + n_adultos_ext + n_ninos_ext + n_adultos_can + n_ninos_can
        
        # --- CARGADORES ---
        st.divider()
        st.markdown("#### 📦 Cargar Paquete")
        cat_sel = st.selectbox("Línea", ["-- Seleccione --", "Cusco Tradicional", "Perú para el Mundo"])
        if cat_sel != "-- Seleccione --":
            pkgs = [p for p in paquetes_db if cat_sel.upper() in p['nombre'].upper()]
            d_sel = st.selectbox("Duración", [p['nombre'].split(" ")[-1] for p in pkgs])
            if st.button("🚀 Cargar"):
                pkg = next(p for p in pkgs if d_sel in p['nombre'])
                st.session_state.curr_itinerario = []
                for t_n in pkg['tours']:
                    t_f = next((t for t in tours_db if t['titulo'] == t_n), None)
                    if t_f:
                        nt = t_f.copy()
                        nt['costo_nac'] = t_f.get('costo_nacional', 0)
                        nt['costo_ext'] = t_f.get('costo_extranjero', 0)
                        nt['costo_can'] = nt['costo_ext'] - 20 if "MACHU PICCHU" in t_f['titulo'] else nt['costo_ext']
                        st.session_state.curr_itinerario.append(nt)
                st.rerun()

        st.markdown("#### ➕ Añadir Tour")
        tour_sel = st.selectbox("Tour Individual", ["-- Seleccione --"] + [t['titulo'] for t in tours_db])
        if st.button("Añadir") and tour_sel != "-- Seleccione --":
            t_data = next(t for t in tours_db if t['titulo'] == tour_sel)
            nt = t_data.copy()
            nt['costo_nac'] = t_data.get('costo_nacional', 0)
            nt['costo_ext'] = t_data.get('costo_extranjero', 0)
            nt['costo_can'] = nt['costo_ext'] - 20 if "MACHU PICCHU" in t_data['titulo'] else nt['costo_ext']
            st.session_state.curr_itinerario.append(nt)
            st.rerun()

        # --- SECCIÓN DE GUARDADO (MIGRADA AL CUERPO PRINCIPAL) ---
        st.divider()
        st.markdown("#### 💾 Mis Paquetes")
        
        # Necesitamos las funciones de persistencia del módulo original
        from Itinerario.App_Ventas import cargar_paquetes_custom, guardar_itinerario_como_paquete
        
        # Cargar Paquete
        paquetes_c = cargar_paquetes_custom() # Lee del JSON en carpeta Itinerario
        if paquetes_c:
            p_sel = st.selectbox("📂 Cargar Guardado", ["-- Seleccione --"] + list(paquetes_c.keys()))
            if p_sel != "-- Seleccione --":
                if st.button("Recuperar"):
                    st.session_state.curr_itinerario = paquetes_c[p_sel]
                    st.success(f"Cargado: {p_sel}")
                    st.rerun()
        
        # Guardar Paquete
        with st.expander("➕ Guardar Actual como Nuevo"):
            nombre_p = st.text_input("Nombre del Paquete")
            if st.button("Guardar"):
                if nombre_p and st.session_state.curr_itinerario:
                    # Guardamos usando la función del módulo original
                    # Hack: Cambiamos dir para que escriba en el JSON correcto
                    cwd_orig = os.getcwd()
                    os.chdir(itinerario_path)
                    try:
                        guardar_itinerario_como_paquete(nombre_p, st.session_state.curr_itinerario)
                        st.success("¡Guardado!")
                        st.rerun()
                    finally:
                        os.chdir(cwd_orig)
                else:
                    st.warning("Escribe un nombre y ten items en la lista.")

    with col2:
        st.subheader("📋 Plan de Viaje")
        
        # Totales Unitarios
        total_nac, total_ext, total_can = 0, 0, 0
        es_pool = (modo_s == "Sistema Pool")
        
        if not st.session_state.curr_itinerario:
            st.info("Agrega servicios desde el panel izquierdo.")
        else:
            for i, tour in enumerate(st.session_state.curr_itinerario):
                total_nac += tour.get('costo_nac', 0)
                total_ext += tour.get('costo_ext', 0)
                total_can += tour.get('costo_can', 0)
                
                # --- VISUALIZACIÓN POR DÍA ---
                with st.expander(f"DÍA {i+1}: {tour['titulo']}", expanded=False):
                    ct, cn, ce, cc = st.columns([2, 0.8, 0.8, 0.8])
                    tour['titulo'] = ct.text_input("Título", tour['titulo'], key=f"t{i}", disabled=es_pool)
                    tour['costo_nac'] = cn.number_input("S/ Nac", value=float(tour.get('costo_nac', 0)), key=f"cn{i}", disabled=es_pool)
                    tour['costo_ext'] = ce.number_input("$ Ext", value=float(tour.get('costo_ext', 0)), key=f"ce{i}", disabled=es_pool)
                    tour['costo_can'] = cc.number_input("$ CAN", value=float(tour.get('costo_can', 0)), key=f"cc{i}", disabled=es_pool)
                    
                    st.text_area("Descripción", tour.get('descripcion', ''), height=70, key=f"d{i}", disabled=es_pool)
                    
                    # Controles
                    b1, b2, b3 = st.columns([1,1,1])
                    if b1.button("🔼", key=f"u{i}") and i>0:
                        st.session_state.curr_itinerario.insert(i-1, st.session_state.curr_itinerario.pop(i)); st.rerun()
                    if b2.button("🔽", key=f"dw{i}") and i<len(st.session_state.curr_itinerario)-1:
                        st.session_state.curr_itinerario.insert(i+1, st.session_state.curr_itinerario.pop(i)); st.rerun()
                    if b3.button("🗑️ Eliminar", key=f"dl{i}"):
                        st.session_state.curr_itinerario.pop(i); st.rerun()

            st.divider()
            
            # --- CÁLCULO FINAL ---
            pax_nac = n_adultos_nac + n_ninos_nac
            pax_ext = n_adultos_ext + n_ninos_ext
            pax_can = n_adultos_can + n_ninos_can
            
            gran_total_nac = total_nac * pax_nac
            gran_total_ext = total_ext * pax_ext
            gran_total_can = total_can * pax_can
            
            r1, r2, r3 = st.columns(3)
            r1.metric("Total Nacionales (S/)", f"S/ {gran_total_nac:,.2f}", f"{pax_nac} pax")
            r2.metric("Total Extranjeros ($)", f"$ {gran_total_ext:,.2f}", f"{pax_ext} pax")
            r3.metric("Total CAN ($)", f"$ {gran_total_can:,.2f}", f"{pax_can} pax")
            
            st.divider()
            
            # --- GENERADOR PDF OMNIPOTENTE ---
            # Inicializar estado del PDF si no existe
            if 'pdf_generated' not in st.session_state:
                st.session_state.pdf_generated = None
            
            if st.button("🖨️ GENERAR PDF (MOTOR WEB)", use_container_width=True):
                if not nombre_cliente:
                    st.error("⚠️ Por favor, ingresa el **Nombre del Cliente** antes de generar.")
                elif not st.session_state.curr_itinerario:
                    st.error("⚠️ El itinerario está vacío. Añade servicios primero.")
                else:
                    with st.spinner("⏳ Generando PDF de Alta Calidad... (Esto toma unos segundos)"):
                        try:
                            st.info("🔍 1/3: Preparando datos del itinerario...") # Debug activado
                            
                            info_p = {
                                'nac': (pax_nac, total_nac),
                                'ext': (pax_ext, total_ext),
                                'can': (pax_can, total_can)
                            }
                            
                            cover = "Captura de pantalla 2026-01-13 094212.png" if cat_sel == "Perú para el Mundo" else "Captura de pantalla 2026-01-13 094056.png"
                            t1, t2 = ("PERÚ", "PARA EL MUNDO") if cat_sel == "Perú para el Mundo" else ("CUSCO", "TRADICIONAL")
                            cat_final = f"{pax_nac+pax_ext+pax_can} Pasajeros"
                            rango = f"Programado"
                            
                            st.info("⚙️ 2/3: Ejecutando motor de renderizado PDF...") # Debug activado

                            pdf_path = generar_pdf_web(
                                tours=st.session_state.curr_itinerario,
                                pasajero=nombre_cliente,
                                fechas=rango,
                                categoria=cat_final,
                                modo=modo_s,
                                vendedor=vendedor,
                                celular=celular,
                                cover_img=cover,
                                title_1=t1, title_2=t2,
                                info_precios=info_p
                            )
                            
                            st.info(f"📄 3/3: Archivo generado exitosamente en: {pdf_path}") # Debug activado

                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            # Guardamos en sesión para que el botón de descarga persista
                            st.session_state.pdf_generated = {
                                "data": pdf_bytes,
                                "name": f"Itinerario_{nombre_cliente.replace(' ', '_')}.pdf"
                            }
                            st.success("¡Documento Generado! Descárgalo abajo 👇")
                            
                        except Exception as e:
                            st.error("❌ ERROR CRÍTICO al generar el PDF.")
                            st.code(f"Error Técnico: {str(e)}") # Mostrar el error texto plano
                            st.exception(e) # Muestra el stack trace completo

            # Botón de Descarga Persistente
            if st.session_state.pdf_generated:
                st.download_button(
                    label="📥 DESCARGAR ITINERARIO OFICIAL",
                    data=st.session_state.pdf_generated["data"],
                    file_name=st.session_state.pdf_generated["name"],
                    mime="application/pdf",
                    use_container_width=True
                )

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
