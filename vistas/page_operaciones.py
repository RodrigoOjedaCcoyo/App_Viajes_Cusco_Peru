# vistas/page_operaciones.py

import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import date, timedelta
import urllib.parse
from controllers.operaciones_controller import OperacionesController
from controllers.venta_controller import VentaController


def dashboard_tablero_diario(controller):
    """Dashboard 2: Tablero con vistas Duplicadas (Mensual/Semanal)."""
    st.subheader("2️⃣ Tablero de Planificación Logística", divider='green')
    
    if 'cal_current_date' not in st.session_state:
        st.session_state['cal_current_date'] = date.today()
    if 'cal_selected_date' not in st.session_state:
        st.session_state['cal_selected_date'] = date.today()
    if 'view_mode' not in st.session_state:
        st.session_state['view_mode'] = "Mensual"

    v_mode = st.radio("Filtro de Vista:", ["Mensual", "Semanal"], 
                      index=0 if st.session_state['view_mode'] == "Mensual" else 1, horizontal=True)
    st.session_state['view_mode'] = v_mode

    current_date = st.session_state['cal_current_date']
    year, month = current_date.year, current_date.month
    nombres_meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    if st.session_state['view_mode'] == "Mensual":
        # --- MES ---
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("◀ Mes Ant"):
                m, y = (12, year-1) if month == 1 else (month-1, year)
                st.session_state['cal_current_date'] = date(y, m, 1)
                st.rerun()
        with c2:
            st.markdown(f"<h3 style='text-align:center;'>{nombres_meses[month]} {year}</h3>", unsafe_allow_html=True)
        with c3:
            if st.button("Mes Sig ▶"):
                m, y = (1, year+1) if month == 12 else (month+1, year)
                st.session_state['cal_current_date'] = date(y, m, 1)
                st.rerun()

        st.markdown("---")
        cal_grid = calendar.monthcalendar(year, month)
        fechas_activas = controller.get_fechas_con_servicios(year, month)
        
        cols = st.columns(7)
        headers = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        for i, h in enumerate(headers): cols[i].markdown(f"<center><b>{h}</b></center>", unsafe_allow_html=True)
            
        for week in cal_grid:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    d_obj = date(year, month, day)
                    sel = (d_obj == st.session_state['cal_selected_date'])
                    act = d_obj in fechas_activas
                    lbl = f"{day}{' 🟢' if act else ''}"
                    if d_obj == date.today(): lbl += "\n(Hoy)"
                    if cols[i].button(lbl, key=f"d_{d_obj}", use_container_width=True, type="primary" if sel else "secondary"):
                        st.session_state['cal_selected_date'] = d_obj
                        st.rerun()

    else:
        # --- SEMANA ---
        d_sel = st.session_state['cal_selected_date']
        lunes = d_sel - timedelta(days=d_sel.weekday())
        domingo = lunes + timedelta(days=6)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("◀ Semana Ant"):
                st.session_state['cal_selected_date'] -= timedelta(days=7)
                st.rerun()
        with c2:
            st.markdown(f"<h3 style='text-align:center;'>Semana de {lunes.day} {nombres_meses[lunes.month]}</h3>", unsafe_allow_html=True)
        with c3:
            if st.button("Semana Sig ▶"):
                st.session_state['cal_selected_date'] += timedelta(days=7)
                st.rerun()
        
        st.markdown("---")
        servicios_w = controller.get_servicios_rango_fechas(lunes, domingo)
        cols_w = st.columns(7)
        headers_w = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        
        for i in range(7):
            f_dia = lunes + timedelta(days=i)
            with cols_w[i]:
                estilo = f"background:{'#1E88E5' if f_dia==date.today() else '#444'}; padding:5px; border-radius:5px; text-align:center; margin-bottom:5px;"
                st.markdown(f"<div style='{estilo}'><small>{headers_w[i]}</small><br><b>{f_dia.day}</b></div>", unsafe_allow_html=True)
                
                s_dia = [s for s in servicios_w if s['Fecha'] == f_dia.isoformat()]
                if not s_dia:
                    st.markdown("<p style='text-align:center; color:gray; font-size:10px;'>Vacío</p>", unsafe_allow_html=True)
                else:
                    for s in s_dia:
                        with st.container(border=True):
                            st.markdown(f"<p style='font-size:11px; margin:0;'><b>{s['Servicio']}</b></p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='font-size:9px; margin:0; color:#aaa;'>{s['Cliente']}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='font-size:9px; margin:0;'>👮 {s['Guía']}</p>", unsafe_allow_html=True)
                
                if st.button("Ver", key=f"v_{f_dia}", use_container_width=True):
                    st.session_state['cal_selected_date'] = f_dia
                    st.rerun()

    # --- DETALLE ---
    st.markdown("---")
    f_p = st.session_state['cal_selected_date']
    st.markdown(f"### 📋 Detalle: {f_p.day} de {nombres_meses[f_p.month]} de {f_p.year}")
    
    servicios = controller.get_servicios_por_fecha(f_p)
    if not servicios:
        st.info("Sin operaciones este día.")
    else:
        st.success(f"Pax totales: {sum(s['Pax'] for s in servicios)}")
        df = pd.DataFrame(servicios)
        ed_df = st.data_editor(
            df,
            column_order=('Hora', 'Día Itin.', 'Servicio', 'Pax', 'Cliente', 'Guía', 'Estado Pago', 'ID Itinerario'),
            column_config={
                "Día Itin.": st.column_config.NumberColumn("Día", format="%d", disabled=True),
                "Guía": st.column_config.TextColumn("Asignar Guía ✏️"),
                "Pax": st.column_config.NumberColumn(disabled=True),
                "Servicio": st.column_config.TextColumn(disabled=True),
                "Cliente": st.column_config.TextColumn(disabled=True),
                "Estado Pago": st.column_config.TextColumn(disabled=True),
                "ID Itinerario": st.column_config.TextColumn("Itin. Cloud ☁️", disabled=True, help="UUID del diseño original en la nube"),
            },
            hide_index=True, use_container_width=True, key=f"ed_{f_p}"
        )

        if st.button("💾 Guardar Asignaciones"):
            cc = 0
            for i, r in ed_df.iterrows():
                if r['Guía'] != df.iloc[i]['Guía']:
                    # Nueva firma usando claves compuestas SQL
                    if controller.actualizar_guia_servicio(r['ID Venta'], r['N Linea'], r['Guía'])[0]: 
                        cc += 1
            if cc > 0:
                st.success(f"¡{cc} cambios guardados!")
                st.rerun()

def generar_mensaje_whatsapp(data):
    """Genera un link de WhatsApp con el mensaje formateado."""
    mensaje = (
        f"*REQUERIMIENTO:*\n"
        f"{data['nombre'].upper()} - {data['motivo'].upper()}\n"
        f"TOTAL: {data['total']:.2f} SOLES\n\n"
        f"N° DE CUENTA:\n{data['n_cuenta'].upper()}"
    )
    # Codificar para URL
    mensaje_codificado = urllib.parse.quote(mensaje)
    return f"https://wa.me/?text={mensaje_codificado}"

def dashboard_requerimientos(controller):
    """Módulo para el registro de requerimientos de operaciones."""
    st.subheader("📝 Registro de Requerimientos", divider='orange')

    # Formulario
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        tipo_cliente = col1.selectbox("Tipo de Cliente", ["B2B", "B2C"])
        nombre = col2.text_input("Nombre / Razón Social")
        total = col3.number_input("Total (SOLES)", min_value=0.0, step=1.0, format="%.2f")

        motivo = st.text_area("Motivo del Requerimiento", height=100)
        n_cuenta = st.text_area("N° de Cuenta / Detalles de Pago", height=150)

        if st.button("🔴 Registrar Requerimiento", use_container_width=True):
            if not nombre or not motivo:
                st.error("Por favor completa nombre y motivo.")
            else:
                nuevo_req = {
                    "tipo_cliente": tipo_cliente,
                    "nombre": nombre.upper(),
                    "motivo": motivo.upper(),
                    "total": total,
                    "n_cuenta": n_cuenta.upper() if n_cuenta else ""
                }
                success, msg = controller.registrar_requerimiento(nuevo_req)
                if success:
                    st.success(msg)
                    st.session_state['last_req'] = nuevo_req
                else:
                    st.error(msg)

    # Botón de WhatsApp
    if 'last_req' in st.session_state:
        req = st.session_state['last_req']
        msg_wa = generar_mensaje_whatsapp(req)
        msg_encoded = urllib.parse.quote(msg_wa)
        wa_link = f"https://wa.me/?text={msg_encoded}"
        st.markdown(f"""
            <a href="{wa_link}" target="_blank">
                <button style="width:100%; padding:10px; background-color:#25D366; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">
                    🟢 Enviar a Grupo de WhatsApp
                </button>
            </a>
        """, unsafe_allow_html=True)
        if st.button("Limpiar Registro Actual"):
            del st.session_state['last_req']
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Requerimientos Registrados")
    reqs = controller.get_requerimientos()
    if reqs:
        df_reqs = pd.DataFrame(reqs)
        st.dataframe(df_reqs, hide_index=True, use_container_width=True)
    else:
        st.info("No hay requerimientos registrados.")


def dashboard_registro_ventas_compartido(controller):
    """Vista de Ventas compartida para Operaciones y Contabilidad."""
    st.subheader("💰 Registro de Ventas (Confirmadas)", divider='blue')
    ventas = controller.get_all_ventas()
    
    if not ventas:
        st.info("No hay ventas registradas actualmente.")
    else:
        df_v = pd.DataFrame(ventas)
        st.dataframe(
            df_v,
            column_config={
                "Total": st.column_config.NumberColumn("Monto Cierre", format="$ %.2f"),
                "Fecha": st.column_config.DateColumn("Fecha Venta")
            },
            hide_index=True,
            use_container_width=True
        )


def registro_ventas_proveedores(supabase_client):
    if 'venta_controller' not in st.session_state:
        st.session_state.venta_controller = VentaController(supabase_client)
    venta_controller = st.session_state.venta_controller

    st.subheader("🤝 Registro de Venta para Proveedores (B2B)")
    st.info("Utilice este formulario para registrar ventas gestionadas por agencias o proveedores externos.")
    
    with st.form("form_registro_venta_proveedores_ops"):
        col1, col2 = st.columns(2)
        proveedor = col1.text_input("Nombre de la Agencia / Proveedor")
        nombre_pax = col1.text_input("Nombre del Pasajero Principal")
        tel = col1.text_input("Celular de Contacto")
        
        id_tour = col2.text_input("ID_Paquete / Tour") 
        
        # Conectar con DB para vendedores
        from controllers.lead_controller import LeadController
        lc = LeadController(supabase_client)
        vend_map = lc.obtener_mapeo_vendedores()
        vendedor_ref = col2.selectbox("Referido por Vendedor", list(vend_map.values()))
        
        monto_neto = col1.number_input("Monto Neto (Lo que paga el proveedor) ($)", min_value=0.0, format="%.2f")
        monto_adelanto = col2.number_input("Adelanto Recibido ($)", min_value=0.0, format="%.2f")
        
        submitted = st.form_submit_button("REGISTRAR VENTA PROVEEDOR", use_container_width=True)
        
        if submitted:
            # Buscar ID
            id_vend = next((id for id, name in vend_map.items() if name == vendedor_ref), None)
            
            exito, msg = venta_controller.registrar_venta_proveedor(
                nombre_proveedor=proveedor,
                nombre_cliente=nombre_pax,
                telefono=tel,
                vendedor=id_vend,
                tour=id_tour,
                monto_total=monto_neto,
                monto_depositado=monto_adelanto
            )
            
            if exito: st.success(msg)
            else: st.error(msg)


def mostrar_pagina(nombre_modulo, rol_actual, user_id, supabase_client):
    """Punto de entrada de Streamlit."""
    controller = OperacionesController(supabase_client)
    
    st.title("⚙️ Gestión de Operaciones")
    st.markdown("---")
    
    if nombre_modulo == "Gestión de Registros":
        tab1, tab2, tab3 = st.tabs([
            "📝 Registro de Requerimientos", 
            "📊 Estructurador de Costos",
            "🤝 Ventas de Proveedores (B2B)"
        ])
        
        with tab1:
            dashboard_requerimientos(controller)
            
        with tab2:
            dashboard_simulador_costos(controller)
            
        with tab3:
            registro_ventas_proveedores(supabase_client)
    else:
        st.info("Utilice el Dashboard Operativo para ver el estado de la logística.")


def dashboard_simulador_costos(controller):
    """
    Herramienta para estructurar costos de un paquete.
    Permite editar fecha, servicio, costos unitarios y calcula totales.
    """
    st.subheader("Estructurador de Costos Operativos", divider='rainbow')

    if 'simulador_data' not in st.session_state:
        # Datos iniciales vacíos con la estructura requerida
        st.session_state['simulador_data'] = [
            {"FECHA": date.today(), "SERVICIO": "Servicio Ejemplo", "COSTO UNITARIO": 0.0, "COSTO TOTAL": 0.0},
        ]

    # Barra de herramientas superior
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.info("💡 Edita las celdas directamente. Añade filas con el botón '+'.")
    with c2:
        if st.button("🗑️ Limpiar Todo", use_container_width=True):
            st.session_state['simulador_data'] = [{"FECHA": date.today(), "SERVICIO": "", "COSTO UNITARIO": 0.0, "COSTO TOTAL": 0.0}]
            st.rerun()

    # Data Editor (El "Excel")
    df = pd.DataFrame(st.session_state['simulador_data'])
    
    # Configuración de columnas
    column_config = {
        "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", required=True),
        "SERVICIO": st.column_config.TextColumn("Descripción del Servicio", required=True, width="large"),
        "COSTO UNITARIO": st.column_config.NumberColumn("Costo Unitario ($)", format="$ %.2f", min_value=0.0),
        "COSTO TOTAL": st.column_config.NumberColumn("Costo Total ($)", format="$ %.2f", min_value=0.0, disabled=False) # Editable si desean override
    }

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_simulador"
    )

    # Lógica de Actualización y Cálculos en tiempo real
    total_paquete = edited_df['COSTO TOTAL'].sum()

    # Actualizar estado para persistencia en sesión
    st.session_state['simulador_data'] = edited_df.to_dict('records')

    st.divider()
    
    # Métricas Finales
    m1, m2, m3 = st.columns(3)
    m1.metric("Costo Total Operativo", f"$ {total_paquete:,.2f}")
    
    # Utilidad Estimada
    precio_venta = m2.number_input("Precio de Venta Sugerido ($)", min_value=0.0, value=total_paquete * 1.3)
    utilidad = precio_venta - total_paquete
    margen = (utilidad / precio_venta * 100) if precio_venta > 0 else 0
    
    m3.metric("Utilidad Estimada", f"$ {utilidad:,.2f}", delta=f"{margen:.1f}%")

    # Opción de Exportar
    if st.button("📥 Exportar a CSV"):
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"estructura_costos_{date.today()}.csv",
            mime='text/csv',
        )