# vistas/page_operaciones.py

import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import date, timedelta
from controllers.operaciones_controller import OperacionesController

def dashboard_riesgo_documental(controller):
    """Implementa el Dashboard 1: Riesgo de Bloqueo Documental."""
    st.subheader("1️⃣ Dashboard de Riesgo Documental", divider='blue')

    # 1. Obtener el segmento inteligente de Ventas con riesgo
    ventas_en_riesgo = controller.get_ventas_con_documentos_pendientes()

    if not ventas_en_riesgo:
        st.success("✅ ¡Excelente! No hay ventas con documentación crítica PENDIENTE o RECIBIDA.")
        return

    st.warning(f"🚨 ¡ATENCIÓN! Hay {len(ventas_en_riesgo)} viajes con riesgo de bloqueo logístico.")
    
    df_resumen = pd.DataFrame(ventas_en_riesgo)
    
    if not df_resumen.empty and 'fecha_salida' in df_resumen.columns:
        df_resumen['fecha_salida'] = pd.to_datetime(df_resumen['fecha_salida'], errors='coerce').dt.date

    # Muestra la tabla informativa
    st.dataframe(
        df_resumen,
        column_order=('id', 'cliente', 'destino', 'fecha_salida', 'vendedor'),
        hide_index=True,
        column_config={
            "id": "ID Venta",
            "cliente": "Cliente Principal",
            "destino": "Destinos",
            "fecha_salida": st.column_config.DateColumn("Salida", format="YYYY-MM-DD"),
            "vendedor": "Vendedor"
        },
        height=200,
        use_container_width=True
    )

    # Selector Principal
    opciones_venta = {
        f"ID: {v['id']} - {v['cliente']} - {v['destino']} ({v['fecha_salida']})": v['id']
        for v in ventas_en_riesgo
    }
    
    st.markdown("---")
    selected_venta_label = st.selectbox("📂 Seleccionar Venta para Gestionar Documentos:", list(opciones_venta.keys()))
    
    if selected_venta_label:
        id_venta_sel = opciones_venta[selected_venta_label]
        venta_actual = next((v for v in ventas_en_riesgo if v['id'] == id_venta_sel), None)
        
        st.markdown(f"#### 📄 Detalle Documental: {venta_actual['cliente']} (ID: {id_venta_sel})")
        
        df_detalle = controller.get_detalle_documentacion_by_venta(id_venta_sel)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df_detalle, hide_index=True, use_container_width=True)
            
        with col2:
            st.markdown("##### Acciones")
            # Verificación de seguridad por si el DF no tiene la columna 'Estado'
            if not df_detalle.empty and 'Estado' in df_detalle.columns:
                doc_validables = df_detalle[df_detalle['Estado'].isin(['PENDIENTE', 'RECIBIDO'])]
                
                if not doc_validables.empty:
                    opciones_validar = {
                        f"{row['Tipo Documento']} - {row['ID Documento']}": row['ID Documento']
                        for _, row in doc_validables.iterrows()
                    }
                    
                    sel_doc_id = st.selectbox("Documento:", list(opciones_validar.keys()))
                    id_doc = opciones_validar[sel_doc_id]
                    
                    doc_info = doc_validables[doc_validables['ID Documento'] == id_doc].iloc[0]
                    estado_actual = doc_info['Estado']
                    
                    uploaded_file = st.file_uploader("Adjuntar Evidencia", key=f"up_{id_doc}")
                    
                    archivo_listo = (estado_actual == 'RECIBIDO')
                    if uploaded_file:
                        with st.spinner("Subiendo..."):
                            success, _ = controller.subir_documento(id_doc, uploaded_file)
                            if success:
                                st.success("✅ Recibido.")
                                archivo_listo = True
                    
                    if st.button("🔴 Validar Documento", disabled=not archivo_listo, key=f"val_{id_doc}"):
                        success, _ = controller.validar_documento(id_doc)
                        if success:
                            st.success("¡Validado!")
                            st.rerun()
                else:
                    st.info("Todo validado.")
            else:
                st.info("No hay documentos para gestionar.")

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
            column_order=('Hora', 'Servicio', 'Pax', 'Cliente', 'Guía', 'Estado Pago'),
            column_config={
                "Guía": st.column_config.TextColumn("Asignar Guía ✏️"),
                "Pax": st.column_config.NumberColumn(disabled=True),
                "Servicio": st.column_config.TextColumn(disabled=True),
                "Cliente": st.column_config.TextColumn(disabled=True),
                "Estado Pago": st.column_config.TextColumn(disabled=True),
            },
            hide_index=True, use_container_width=True, key=f"ed_{f_p}"
        )

        if st.button("💾 Guardar Asignaciones"):
            cc = 0
            for i, r in ed_df.iterrows():
                if r['Guía'] != df.iloc[i]['Guía']:
                    if controller.actualizar_guia_servicio(r['ID Servicio'], r['Guía'])[0]: cc += 1
            if cc > 0:
                st.success(f"¡{cc} cambios guardados!")
                st.rerun()

def dashboard_requerimientos(controller):
    """Implementa el Dashboard 3: Registro de Requerimientos."""
    st.subheader("📝 Registro de Requerimientos", divider='orange')
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown("#### ➕ Nuevo Requerimiento")
        with st.form("form_requerimiento", clear_on_submit=True):
            tipo_cliente = st.selectbox("Tipo de Cliente", ["B2B", "B2C"])
            nombre = st.text_input("Nombre de la Persona")
            motivo = st.text_area("Motivo")
            total = st.number_input("Total", min_value=0.0, step=0.01)
            n_cuenta = st.text_input("N° de Cuenta")
            
            submit = st.form_submit_button("Registrar Requerimiento")
            
            if submit:
                if not nombre or not motivo:
                    st.error("Por favor, complete los campos obligatorios (Nombre y Motivo).")
                else:
                    data = {
                        "tipo_cliente": tipo_cliente,
                        "nombre": nombre,
                        "motivo": motivo,
                        "total": total,
                        "n_cuenta": n_cuenta,
                        "fecha_registro": date.today().isoformat()
                    }
                    success, msg = controller.registrar_requerimiento(data)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                        
    with col2:
        st.markdown("#### 📋 Requerimientos Registrados")
        reqs = controller.get_requerimientos()
        if not reqs:
            st.info("No hay requerimientos registrados.")
        else:
            df_reqs = pd.DataFrame(reqs)
            st.dataframe(
                df_reqs,
                column_order=("tipo_cliente", "nombre", "total", "fecha_registro"),
                column_config={
                    "tipo_cliente": "Tipo",
                    "nombre": "Nombre",
                    "total": st.column_config.NumberColumn("Total", format="$ %.2f"),
                    "fecha_registro": "Fecha"
                },
                hide_index=True,
                use_container_width=True
            )

def mostrar_pagina(nombre_modulo, rol_actual, user_id, supabase_client):
    """Punto de entrada de Streamlit."""
    controller = OperacionesController(supabase_client)
    
    if "Requerimientos" in nombre_modulo:
        st.title("💼 Gestión de Requerimientos")
        dashboard_requerimientos(controller)
    else:
        st.title("💼 Gestión de Operaciones")
        t1, t2 = st.tabs(["🛡️ Riesgos", "📅 Planificación"])
        with t1: dashboard_riesgo_documental(controller)
        with t2: dashboard_tablero_diario(controller)