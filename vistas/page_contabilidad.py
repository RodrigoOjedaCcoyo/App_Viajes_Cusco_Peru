# vistas/page_contabilidad.py
import streamlit as st
import pandas as pd
from controllers.reporte_controller import ReporteController

# Inicializar controladores (Se hace dentro de mostrar_pagina ahora)

def reporte_de_montos():
    """Sub-función para la funcionalidad 'Reporte de Montos'."""
    reporte_controller = st.session_state.get('reporte_controller')
    if not reporte_controller:
        st.error("Error: Controlador no inicializado.")
        return

    st.subheader("💰 Reporte de Ingresos Totales")
    
    data_reporte = reporte_controller.obtener_resumen_ventas()
    
    # Mostrar métricas clave
    col1, col2 = st.columns(2)
    col1.metric("Ventas Totales Registradas", data_reporte['total_ventas_registradas'])
    col2.metric("Monto Total Acumulado (USD)", f"${data_reporte['monto_total_acumulado']:,.2f}")
    
    st.markdown("---")
    
    # Mostrar tabla de detalle
    st.write("### Detalle de Ventas")
    
    ventas = data_reporte['detalle_ventas']
    if ventas:
        df_ventas = pd.DataFrame(ventas)
        
        # Seleccionamos y renombramos columnas para el reporte
        columnas_reporte = {
            'id': 'Venta ID',
            'lead_id': 'Lead Origen ID',
            'monto_total': 'Monto ($)',
            'tour_paquete': 'Tour',
            'fecha_tour': 'Fecha Inicio Tour',
            'vendedor': 'Registrado Por'
        }
        
        df_display = df_ventas.rename(columns=columnas_reporte)
        st.dataframe(df_display[list(columnas_reporte.values())], use_container_width=True, hide_index=True)
        
    else:
        st.info("Aún no hay ventas registradas en el sistema.")


def auditoria_de_pagos():
    """Sub-función para la funcionalidad 'Auditoría de Pagos'."""
    reporte_controller = st.session_state.get('reporte_controller')
    if not reporte_controller:
        st.error("Error: Controlador no inicializado.")
        return

    st.subheader("🏦 Auditoría de Pagos y Estados")
    
    # Llama a la función que devuelve el detalle de ventas (por ahora)
    ventas_para_auditoria = reporte_controller.obtener_detalle_auditoria()

    if ventas_para_auditoria:
        df_auditoria = pd.DataFrame(ventas_para_auditoria)
        
        # Un contador necesita ver el estado del pago, que en el modelo de ventas es 'estado_pago'
        columnas_auditoria = ['id', 'monto_total', 'fecha_registro', 'estado_pago', 'vendedor']
        
        st.dataframe(df_auditoria[columnas_auditoria], use_container_width=True, hide_index=True)
    else:
        st.info("No hay transacciones para auditar.")


def mostrar_requerimientos():
    """Muestra la lista de requerimientos enviados por Operaciones."""
    reporte_controller = st.session_state.get('reporte_controller')
    
    # Verificación de seguridad: si el método no existe, forzamos reinicialización
    if reporte_controller and not hasattr(reporte_controller, 'obtener_requerimientos'):
        if 'supabase_client' in st.session_state:
            reporte_controller = ReporteController(st.session_state['supabase_client'])
            st.session_state['reporte_controller'] = reporte_controller
        else:
            st.error("Error: Atributo 'obtener_requerimientos' no encontrado y no se pudo reiniciar el controlador.")
            return

    if not reporte_controller:
        st.error("Error: Controlador no inicializado.")
        return

    st.subheader("📋 Requerimientos de Operaciones")
    reqs = reporte_controller.obtener_requerimientos()
    
    if not reqs:
        st.info("No hay requerimientos registrados por el equipo de Operaciones.")
    else:
        df_reqs = pd.DataFrame(reqs)
        
        # Formatear columnas para visualización contable
        st.dataframe(
            df_reqs,
            column_order=("fecha_registro", "nombre", "tipo_cliente", "motivo", "total", "n_cuenta"),
            column_config={
                "fecha_registro": "Fecha",
                "nombre": "Solicitante",
                "tipo_cliente": "Tipo",
                "motivo": "Concepto / Motivo",
                "total": st.column_config.NumberColumn("Importe", format="$ %.2f"),
                "n_cuenta": "N° de Cuenta / Destino"
            },
            hide_index=True,
            use_container_width=True
        )


# ----------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE LA VISTA (Llamada por main.py)
# ----------------------------------------------------------------------

def mostrar_pagina(funcionalidad_seleccionada, rol_actual=None, user_id=None, supabase_client=None):
    """
    Función que main.py usa para cargar el módulo. 
    Redirige a la función de sub-página correcta según la selección del sidebar.
    """
    # Inicialización del controlador con dependencia inyectada
    if supabase_client:
        st.session_state['reporte_controller'] = ReporteController(supabase_client)

    st.title(f"Módulo de Contabilidad / {funcionalidad_seleccionada}")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Reporte de Montos":
        reporte_de_montos()
    elif funcionalidad_seleccionada == "Auditoría de Pagos":
        auditoria_de_pagos()
    elif funcionalidad_seleccionada == "Requerimientos de Operaciones":
        mostrar_requerimientos()
    elif funcionalidad_seleccionada == "Registro de Ventas":
        # Reutilizamos la lógica de reporte pero con título específico
        st.info("Visualizando historial de ventas confirmadas desde el área comercial.")
        reporte_de_montos()
    else:
        st.warning("Funcionalidad no reconocida.")
