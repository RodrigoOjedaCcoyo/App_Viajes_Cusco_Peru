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

def dashboard_tablero_diario(controller):
    """Implementa el Dashboard 2: Tablero de Ejecución Diaria (Reemplazo de Pizarra)."""
    st.subheader("2️⃣ Tablero de Ejecución Diaria", divider='green')
    
    col_filtros, col_kpi = st.columns([2, 2])
    
    with col_filtros:
        fecha_seleccionada = st.date_input("📅 Seleccionar Fecha de Operación", value=date.today())
        
    # Obtener Servicios del día
    servicios_dia = controller.get_servicios_por_fecha(fecha_seleccionada)
    
    with col_kpi:
        total_pax = sum([s['Pax'] for s in servicios_dia])
        st.metric("Total Pax en Operación", f"{total_pax} 👤")
        
    st.markdown("---")
    
    if not servicios_dia:
        st.info(f"No hay servicios programados para el {fecha_seleccionada.strftime('%Y-%m-%d')}.")
        return

    # Preparar DataFrame
    df_servicios = pd.DataFrame(servicios_dia)
    
    # UI: Tabla principal con edición de Guía
    st.markdown(f"##### Programación: {fecha_seleccionada.strftime('%d %B %Y')}")
    
    # Configuración de Columnas
    column_config = {
        "ID Servicio": st.column_config.NumberColumn(disabled=True),
        "ID Venta": st.column_config.NumberColumn(disabled=True),
        "Hora": st.column_config.TextColumn(disabled=True),
        "Servicio": st.column_config.TextColumn(disabled=True, width="medium"),
        "Pax": st.column_config.NumberColumn(disabled=True),
        "Cliente": st.column_config.TextColumn(disabled=True, width="medium"),
        "Estado Pago": st.column_config.TextColumn(disabled=True),
        # Guía es la única columna editable (Selectbox simulado con texto o Dropdown si tuviéramos lista)
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
        key="editor_tablero_diario"
    )
    
    # Detectar cambios y guardar (Simulación de Auto-Save al editar)
    # Comparamos el DF editado con el original
    # Nota: st.data_editor devuelve el DF final. Para detectar cambios específicos eficientemente
    # deberíamos usar on_change, pero en streamlit simple comparamos iterando.
    
    if st.button("💾 Guardar Asignaciones de Guías"):
        cambios_count = 0
        for index, row in edited_df.iterrows():
            # Buscar el valor original en servicios_dia
            original = next((s for s in servicios_dia if s['ID Servicio'] == row['ID Servicio']), None)
            if original and original['Guía'] != row['Guía']:
                # Hubo cambio
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