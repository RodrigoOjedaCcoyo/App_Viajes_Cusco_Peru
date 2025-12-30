# vistas/page_operaciones.py

import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import date, timedelta
from controllers.operaciones_controller import OperacionesController

# Inicializar el controlador para usar la lógica de negocio
controller = OperacionesController()

def dashboard_riesgo_documental():
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
                
                if st.button("🔴 Validar Documento (Desbloquear)"):
                    id_doc_a_validar = opciones_validar[selected_doc_key]
                    success, message = controller.validar_documento(id_doc_a_validar)
                    if success:
                        st.success(f"Documento ID {id_doc_a_validar} validado. Recargando...")
                        st.rerun()
                    else:
                        st.error(f"Error al validar: {message}")
            else:
                 st.info("Todos los documentos PENDIENTES/RECIBIDOS ya están validados para esta venta.")

def dashboard_ejecucion_logistica():
    """Implementa el Dashboard 2: Ejecución de Tareas Logísticas."""
    st.subheader("2️⃣ Dashboard de Ejecución Logística (Prioridad)", divider='green')

    # Filtro por Responsable
    # Asume que 'Angel' y 'Abel' son los responsables de las tareas de ejemplo
    responsables = ['Todos', 'Angel', 'Abel']
    responsable_seleccionado = st.selectbox("Filtrar por Responsable:", responsables)
    
    # Obtener las tareas ejecutables (aplicando la lógica de desbloqueo)
    responsable_filtro = responsable_seleccionado if responsable_seleccionado != 'Todos' else None
    df_tareas_ejecutables = controller.get_tareas_ejecutables(responsable=responsable_filtro)

    # 1. Indicadores (KPIs) de Avance Global
    all_tareas = controller.tarea_model.get_all()
    total_tareas = len(all_tareas)
    completadas = len([t for t in all_tareas if t['estado_cumplimiento'] == 'COMPLETADO'])
    pendientes = total_tareas - completadas

    col_kpi1, col_kpi2 = st.columns(2)
    
    with col_kpi1:
        st.metric(label="Total de Tareas a Ejecutar", value=total_tareas)

    if total_tareas > 0:
        avance_global = (completadas / total_tareas) * 100
        data_kpi = pd.DataFrame({
            'Estado': ['COMPLETADO', 'PENDIENTE'], 
            'Cantidad': [completadas, pendientes]
        })
        fig = px.pie(
            data_kpi, 
            values='Cantidad', 
            names='Estado', 
            title=f"Avance Global: {avance_global:.1f}%",
            color='Estado',
            color_discrete_map={'COMPLETADO': 'green', 'PENDIENTE': 'red'}
        )
        col_kpi2.plotly_chart(fig, use_container_width=True)
    else:
        col_kpi2.info("No hay tareas definidas.")

    st.markdown("---")

    # 2. Segmentador y Tabla de Ejecución
    if df_tareas_ejecutables.empty:
        st.info("🎉 No hay tareas pendientes o en proceso que cumplan con los requisitos de documentación para este responsable.")
        return

    st.markdown("##### Tareas **PENDIENTES** y **EN PROCESO** que están **DESBLOQUEADAS** para su ejecución:")

    # Añadir columna de Riesgo
    hoy = date.today()
    proximo_riesgo = hoy + timedelta(days=7) # Definir riesgo como 'próximos 7 días'

    df_tareas_ejecutables['Riesgo Fecha'] = df_tareas_ejecutables['Fecha Límite'].apply(
        lambda x: "🟥 CRÍTICO" if x <= hoy else ("🟨 ALERTA" if x <= proximo_riesgo else "🟢 Normal")
    )
    
    # Ordenar por Riesgo y luego por Fecha Límite
    orden_riesgo = {"🟥 CRÍTICO": 1, "🟨 ALERTA": 2, "🟢 Normal": 3}
    df_tareas_ejecutables['Orden Riesgo'] = df_tareas_ejecutables['Riesgo Fecha'].map(orden_riesgo)
    df_tareas_ejecutables = df_tareas_ejecutables.sort_values(by=['Orden Riesgo', 'Fecha Límite'], ascending=[True, True])
    df_tareas_ejecutables = df_tareas_ejecutables.drop(columns=['Orden Riesgo'])

    col_tabla, col_accion = st.columns([3, 1])

    with col_tabla:
        st.dataframe(
            df_tareas_ejecutables,
            column_config={
                "Fecha Salida": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "Fecha Límite": st.column_config.DateColumn(format="YYYY-MM-DD"),
            },
            hide_index=True,
            key='data_editor_tareas',
        )

    with col_accion:
        st.markdown("##### Acción Rápida")
        
        # Opciones para el selectbox
        opciones_tarea = {
            f"{row['Descripción']} (Venta {row['ID Venta']}) - ID: {row['ID Tarea']}": row['ID Tarea']
            for index, row in df_tareas_ejecutables.iterrows()
        }
        
        selected_tarea_key = st.selectbox(
            "Marcar como completada:", 
            list(opciones_tarea.keys())
        )
        
        if st.button("✅ Tarea Completada"):
            id_tarea_a_completar = opciones_tarea[selected_tarea_key]
            success, message = controller.completar_tarea(id_tarea_a_completar)
            if success:
                st.success(f"Tarea ID {id_tarea_a_completar} completada. Recargando...")
                st.rerun()
            else:
                st.error(f"Error al completar: {message}")

def main_operaciones():
    """Función principal que dibuja la página de Operaciones."""
    st.title("🎯 Dashboards de Control de Operaciones")
    st.markdown("Esta sección consolida el riesgo documental y la ejecución logística priorizada.")
    st.markdown("---")
    
    # Uso de pestañas (tabs) para organizar los dashboards
    tab1, tab2 = st.tabs(["🚦 Riesgo Documental", "🚀 Ejecución Logística"])
    
    with tab1:
        dashboard_riesgo_documental()
        
    with tab2:
        dashboard_ejecucion_logistica()
        
    st.sidebar.markdown("---")
    st.sidebar.caption("Datos simulados en Session State.")

if __name__ == "__main__":
    main_operaciones()