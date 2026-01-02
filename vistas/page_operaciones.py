# vistas/page_operaciones.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from controllers.operaciones_controller import OperacionesController

# NOTA: EL controlador se inicializa dentro de mostrar_pagina para evitar ejecucion temprana
# controller = OperacionesController() 

def dashboard_riesgo_documental(controller):
    """Implementa el Dashboard 1: Riesgo de Bloqueo Documental."""
    st.subheader("1️⃣ Dashboard de Riesgo Documental (Bloqueo de Tareas)", divider='blue')

    # 1. Obtener el segmento inteligente de Ventas con riesgo
    ventas_en_riesgo = controller.get_ventas_con_documentos_pendientes()

    if not ventas_en_riesgo:
        st.success("✅ ¡Excelente! No hay ventas con documentación crítica PENDIENTE o RECIBIDA. No hay riesgo de bloqueo.")
        return

    st.warning(f"🚨 ¡ATENCIÓN! Hay {len(ventas_en_riesgo)} viajes con riesgo de bloqueo logístico.")
    
    # Prepara un DataFrame para la tabla principal (Resumen de Ventas)
    df_resumen = pd.DataFrame([
        {'ID Venta': v['id'], 'Destino': v['destino'], 'Fecha Salida': v['fecha_salida'], 'Vendedor': v['vendedor']}
        for v in ventas_en_riesgo
    ])
    
    # --- CORRECCIÓN CRÍTICA DE TIPOS ---
    # Asegurar que 'Fecha Salida' sea datetime.date (y manejar NaT/None)
    if not df_resumen.empty and 'Fecha Salida' in df_resumen.columns:
        df_resumen['Fecha Salida'] = pd.to_datetime(df_resumen['Fecha Salida'], errors='coerce').dt.date
    
    # --- CORRECCIÓN CRÍTICA DE TIPOS ---
    # Asegurar que 'Fecha Salida' sea datetime.date (y manejar NaT/None)
    if not df_resumen.empty and 'Fecha Salida' in df_resumen.columns:
        df_resumen['Fecha Salida'] = pd.to_datetime(df_resumen['Fecha Salida'], errors='coerce').dt.date

    # Utiliza st.data_editor para seleccionar una fila
    st.markdown("##### Selecciona una venta para ver el detalle de los documentos:")
    edited_df = st.data_editor(
        df_resumen,
        column_order=('ID Venta', 'Destino', 'Fecha Salida', 'Vendedor'),
        hide_index=True,
        key='data_editor_riesgo',
        # Configuración para hacer que la tabla sea seleccionable y más pequeña
        column_config={
            "Fecha Salida": st.column_config.DateColumn(format="YYYY-MM-DD")
        },
        height=200,
    )

    # Identificar la fila seleccionada
    selected_rows = edited_df[edited_df.apply(lambda x: tuple(x) in df_resumen.itertuples(index=False), axis=1)]
    
    if not selected_rows.empty:
        id_venta_seleccionada = selected_rows.iloc[0]['ID Venta']
        st.markdown(f"---")
        st.markdown(f"#### Detalle Documental de Venta ID: {id_venta_seleccionada} ({selected_rows.iloc[0]['Destino']})")
        
        # 2. Obtener el detalle de la documentación
        df_detalle = controller.get_detalle_documentacion_by_venta(id_venta_seleccionada)
        
        col1, col2 = st.columns([3, 1])

        with col1:
            st.dataframe(
                df_detalle,
                column_config={
                    "Fecha Entrega": st.column_config.DateColumn(format="YYYY-MM-DD")
                },
                hide_index=True,
            )
            
        with col2:
            st.markdown("##### Acciones")
            
            # Filtra solo los documentos que pueden ser validados (PENDIENTE o RECIBIDO)
            doc_validables = df_detalle[df_detalle['Estado'].isin(['PENDIENTE', 'RECIBIDO'])]
            
            if not doc_validables.empty:
                # Selector para la acción de validar
                opciones_validar = {
                    f"{row['Tipo Documento']} ({row['Pasajero']}) - ID: {row['ID Documento']}": row['ID Documento']
                    for index, row in doc_validables.iterrows()
                }
                
                selected_doc_key = st.selectbox(
                    "Selecciona Documento a validar:", 
                    list(opciones_validar.keys())
                )
                
                if st.button("🔴 Validar Documento"):
                    id_doc_a_validar = opciones_validar[selected_doc_key]
                    success, message = controller.validar_documento(id_doc_a_validar)
                    if success:
                        st.success(f"Documento ID {id_doc_a_validar} validado. Recargando...")
                        st.rerun()
                    else:
                        st.error(f"Error al validar: {message}")
            else:
                 st.info("Todos los documentos PENDIENTES/RECIBIDOS ya están validados para esta venta.")

import calendar

def dashboard_tablero_diario(controller):
    """Implementa el Dashboard 2: Tablero de Ejecución Diaria con Calendario Visual."""
    st.subheader("2️⃣ Tablero de Ejecución Diaria", divider='green')
    
    # --- GESTIÓN DEL ESTADO DEL CALENDARIO ---
    if 'cal_current_date' not in st.session_state:
        st.session_state['cal_current_date'] = date.today()
    if 'cal_selected_date' not in st.session_state:
        st.session_state['cal_selected_date'] = date.today()
        
    current_date = st.session_state['cal_current_date']
    year = current_date.year
    month = current_date.month
    
    # --- CONTROLES DE NAVEGACIÓN MES ---
    col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 4, 1])
    
    with col_nav_1:
        if st.button("◀ Prev"):
            # Restar un mes
            new_month = month - 1
            new_year = year
            if new_month == 0:
                new_month = 12
                new_year -= 1
            st.session_state['cal_current_date'] = date(new_year, new_month, 1)
            st.rerun()

    with col_nav_2:
        # Título del Mes Centrado
        month_name = calendar.month_name[month]
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{month_name} {year}</h3>", unsafe_allow_html=True)

    with col_nav_3:
        if st.button("Next ▶"):
             # Sumar un mes
            new_month = month + 1
            new_year = year
            if new_month == 13:
                new_month = 1
                new_year += 1
            st.session_state['cal_current_date'] = date(new_year, new_month, 1)
            st.rerun()
            
    st.markdown("---")
    
    # --- GRID DEL CALENDARIO ---
    cal = calendar.monthcalendar(year, month)
    
    # Encabezados de Días
    cols = st.columns(7)
    days_header = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    for idx, col in enumerate(cols):
        col.markdown(f"**{days_header[idx]}**")
        
    # Filas de Días
    for week in cal:
        cols = st.columns(7)
        for idx, day in enumerate(week):
            with cols[idx]:
                if day != 0:
                    day_date = date(year, month, day)
                    # Estilo condicional para el día seleccionado
                    is_selected = (day_date == st.session_state['cal_selected_date'])
                    
                    label = f"{day}"
                    if day_date == date.today():
                        label += " (Hoy)"
                        
                    # Botón por día
                    if st.button(label, key=f"btn_day_{year}_{month}_{day}", use_container_width=True, type="primary" if is_selected else "secondary"):
                        st.session_state['cal_selected_date'] = day_date
                        st.rerun()
                else:
                    st.write("") # placeholder vacío para días fuera de mes
                    
    # --- DETALLE DE LA FECHA SELECCIONADA ---
    fecha_seleccionada = st.session_state['cal_selected_date']
    st.markdown(f"### 📅 Operaciones del: {fecha_seleccionada.strftime('%d de %B de %Y')}")
    
    # Obtener Servicios del día
    servicios_dia = controller.get_servicios_por_fecha(fecha_seleccionada)
    
    total_pax = sum([s['Pax'] for s in servicios_dia])
    st.info(f"👥 Total Pax en Operación: {total_pax}")
    
    if not servicios_dia:
        st.warning(f"No hay servicios programados para el {fecha_seleccionada.strftime('%Y-%m-%d')}.")
        return

    # Preparar DataFrame
    df_servicios = pd.DataFrame(servicios_dia)
    
    # Configuración de Columnas
    column_config = {
        "ID Servicio": st.column_config.NumberColumn(disabled=True),
        "ID Venta": st.column_config.NumberColumn(disabled=True),
        "Hora": st.column_config.TextColumn(disabled=True),
        "Servicio": st.column_config.TextColumn(disabled=True, width="medium"),
        "Pax": st.column_config.NumberColumn(disabled=True),
        "Cliente": st.column_config.TextColumn(disabled=True, width="medium"),
        "Estado Pago": st.column_config.TextColumn(disabled=True),
        "Guía": st.column_config.TextColumn(
            "Guía Asignado ✏️",
            help="Escribe el nombre del guía para asignar",
            max_chars=50,
            required=True
        )
    }
    
    edited_df = st.data_editor(
        df_servicios,
        column_order=("Hora", "Servicio", "Pax", "Cliente", "Guía", "Estado Pago"),
        column_config=column_config,
        hide_index=True,
        num_rows="fixed",
        key=f"editor_tablero_{fecha_seleccionada}" # Key dinámica para resetear si cambia la fecha
    )
    
    if st.button("💾 Guardar Asignaciones de Guías", key="btn_save_guides"):
        cambios_count = 0
        for index, row in edited_df.iterrows():
            original = next((s for s in servicios_dia if s['ID Servicio'] == row['ID Servicio']), None)
            if original and original['Guía'] != row['Guía']:
                success, msg = controller.actualizar_guia_servicio(row['ID Servicio'], row['Guía'])
                if success:
                    cambios_count += 1
        
        if cambios_count > 0:
            st.success(f"✅ Se actualizaron {cambios_count} servicios correctamente.")
            st.rerun()
        else:
            st.info("No se detectaron cambios en los guías.")

def mostrar_pagina(nombre_modulo, rol_actual, user_id, supabase_client):
    """Función principal (Entrada) del módulo de Operaciones."""
    st.title("🎯 Dashboards de Control de Operaciones")
    st.markdown("Esta sección consolida el riesgo documental y la ejecución logística priorizada.")
    st.markdown("---")
    
    # Inicializamos el controlador AQUI (CON INYECCIÓN REAL)
    controller = OperacionesController(supabase_client)

    # Uso de pestañas (tabs) para organizar los dashboards
    tab1, tab2 = st.tabs(["🚦 Riesgo Documental", "🚀 Ejecución Logística"])
    
    with tab1:
        dashboard_riesgo_documental(controller)
        
    with tab2:
        dashboard_tablero_diario(controller)
        
    st.sidebar.markdown("---")
    st.sidebar.caption("Datos simulados en Session State.")

if __name__ == "__main__":
    # Test local
    mostrar_pagina("Operaciones", "OPERACIONES", 1, None)