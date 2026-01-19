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
    
    # Nuevo Dashboard Financiero Integrado
    from vistas.dashboard_analytics import render_financial_dashboard
    df_ventas, df_reqs = reporte_controller.get_data_for_dashboard()
    
    # Renderizamos Dashboard
    render_financial_dashboard(df_ventas, df_reqs)
    
    st.divider()
    
    # Mantener funcionalidad anterior: tabla de detalle
    # data_reporte = reporte_controller.obtener_resumen_ventas() # Ya lo tenemos en df_ventas
    
    # Mostrar tabla de detalle
    st.write("### 📋 Detalle de Ventas (Auditoría)")
    
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

        # --- 🔍 DETALLE VISUAL PARA AUDITORÍA (ESTILO IMAGEN) ---
        st.markdown("---")
        st.subheader("📋 Verificación de Itinerario Digital")
        
        # Filtramos ventas que tengan un itinerario vinculado
        ventas_con_itin = df_auditoria[df_auditoria['id_itinerario_digital'].notna()]
        
        if not ventas_con_itin.empty:
            sel_v_id = st.selectbox("Seleccione Venta para auditar su Itinerario:", 
                                 ventas_con_itin['id'].tolist(),
                                 key="sb_audit_itin")
            
            # Obtener el UUID del itinerario
            id_itin_audit = ventas_con_itin[ventas_con_itin['id'] == sel_v_id]['id_itinerario_digital'].iloc[0]
            
            if id_itin_audit:
                res_itin = st.session_state['reporte_controller'].client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_audit).single().execute()
                if res_itin.data:
                    render = res_itin.data['datos_render']
                    tours = render.get('itinerario_detales', []) or render.get('days', [])
                    
                    with st.container(border=True):
                        st.info(f"💎 **Programa Vendido:** {render.get('titulo', 'General')}")
                        for i, t in enumerate(tours):
                            with st.expander(f"🗓️ DIA {i+1}: {(t.get('nombre') or t.get('titulo') or 'Servicio').upper()}", expanded=(i==0)):
                                # Inclusiones/Exclusiones (Estilo Imagen)
                                inc = t.get('incluye') or t.get('inclusiones', [])
                                if inc:
                                    st.markdown("<span style='color:green; font-weight:bold; font-size:12px;'>INCLUYE:</span>", unsafe_allow_html=True)
                                    for item in inc: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✔️ <small>{item}</small>", unsafe_allow_html=True)
                                
                                exc = t.get('no_incluye') or t.get('exclusiones', [])
                                if exc:
                                    st.markdown("<span style='color:red; font-weight:bold; font-size:12px;'>NO INCLUYE:</span>", unsafe_allow_html=True)
                                    for item in exc: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;❌ <small>{item}</small>", unsafe_allow_html=True)
        else:
            st.info("No hay ventas con itinerarios digitales para auditar en esta lista.")
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
    if supabase_client:
        st.session_state['reporte_controller'] = ReporteController(supabase_client)

    st.title(f"📝 Gestión Contable")
    st.markdown("---")
    
    if funcionalidad_seleccionada == "Gestión de Registros":
        tab1, tab2 = st.tabs(["📋 Requerimientos de Operaciones", "📊 Estructurador Financiero"])
        
        with tab1:
            mostrar_requerimientos()
            
        with tab2:
            estructurador_contable()
    else:
        st.info("Utilice el Dashboard Contable para ver reportes.")

def estructurador_contable():
    """
    Herramienta tipo Excel para Contabilidad.
    Registro de gastos con distinción de moneda (PEN/USD).
    """
    st.subheader("📊 Estructurador de Gastos (Multimoneda)", divider='violet')

    from datetime import date # Importación local o asegurar que esté arriba

    if 'simulador_contable_data' not in st.session_state:
        st.session_state['simulador_contable_data'] = [
            {"FECHA": date.today(), "SERVICIO": "Servicio Ejemplo", "MONEDA": "PEN", "TOTAL": 0.0},
        ]

    # Barra de herramientas
    c1, c2 = st.columns([3, 1])
    with c1:
        st.info("💡 Ingresa los gastos. El sistema separará automáticamente Soles y Dólares.")
    with c2:
        if st.button("🗑️ Limpiar Tabla", use_container_width=True, key="btn_clear_cont"):
            st.session_state['simulador_contable_data'] = [{"FECHA": date.today(), "SERVICIO": "", "MONEDA": "PEN", "TOTAL": 0.0}]
            st.rerun()

    # Data Editor
    df = pd.DataFrame(st.session_state['simulador_contable_data'])
    
    column_config = {
        "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", required=True),
        "SERVICIO": st.column_config.TextColumn("Descripción del Servicio", required=True, width="large"),
        "MONEDA": st.column_config.SelectboxColumn("Moneda", options=["PEN", "USD"], required=True, width="small"),
        "TOTAL": st.column_config.NumberColumn("Total", format="%.2f", min_value=0.0)
    }

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_contable"
    )

    # Cálculos por Moneda
    total_pen = edited_df[edited_df['MONEDA'] == 'PEN']['TOTAL'].sum()
    total_usd = edited_df[edited_df['MONEDA'] == 'USD']['TOTAL'].sum()

    st.session_state['simulador_contable_data'] = edited_df.to_dict('records')

    st.divider()
    
    # Mostrar Totales
    col_pen, col_usd = st.columns(2)
    col_pen.metric("Total Soles (PEN)", f"S/. {total_pen:,.2f}")
    col_usd.metric("Total Dólares (USD)", f"$ {total_usd:,.2f}")

    # Exportar
    if st.button("📥 Exportar Reporte CSV", key="btn_exp_cont"):
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"gastos_contables_{date.today()}.csv",
            mime='text/csv',
        )
