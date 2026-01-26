# vistas/page_contabilidad.py
import streamlit as st
import pandas as pd
from controllers.reporte_controller import ReporteController

# Renderiza el Botón para el PDF del Itinerario Simple.
def render_itinerary_simple_download(render):
    if not render:
        st.warning("No hay datos de itinerario para descargar.")
        return

    from controllers.pdf_controller import PDFController
    pdf_ctrl = PDFController()
    
    with st.container(border=True):
        st.markdown(f"#### 📄 Resumen Financiero: {render.get('titulo', 'Sin Título')}")
        st.info("Este documento es una versión simplificada (Ink Saver) para auditoría interna.")
        
        # Generar el PDF en memoria
        pdf_buffer = pdf_ctrl.generar_itinerario_simple_pdf(render)
        
        if pdf_buffer:
            st.download_button(
                label="📥 Descargar Resumen para Auditoría (PDF Simple)",
                data=pdf_buffer,
                file_name=f"auditoria_{render.get('titulo', 'itinerario')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("No se pudo generar el PDF en este momento.")

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
    data_reporte = reporte_controller.obtener_resumen_ventas()
    
    # Mostrar tabla de detalle
    st.write("### 📋 Detalle de Ventas (Auditoría)")
    
    ventas = data_reporte['detalle_ventas']
    if ventas:
        df_ventas = pd.DataFrame(ventas)
        
        # Seleccionamos y renombramos columnas para el reporte
        columnas_reporte = {
            'id_venta': 'Venta ID',
            'lead_id': 'Lead Origen ID',
            'monto_total': 'Monto ($)',
            'tour_paquete': 'Tour',
            'fecha_tour': 'Fecha Inicio Tour',
            'vendedor': 'Registrado Por'
        }
        
        if 'monto_total' not in df_ventas.columns and 'precio_total_cierre' in df_ventas.columns:
            df_ventas['monto_total'] = df_ventas['precio_total_cierre']
        
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
        
        # Un contador necesita ver el estado del pago, que en el modelo de ventas es 'estado_venta'
        # Usar nombres de columnas correctos según esquema
        columnas_auditoria = ['id_venta', 'precio_total_cierre', 'fecha_venta', 'estado_venta', 'url_itinerario']
        # Mapeo para visualización
        df_auditoria_show = df_auditoria.copy()
        df_auditoria_show.rename(columns={
            'id_venta': 'Venta ID',
            'precio_total_cierre': 'Monto ($)',
            'fecha_venta': 'Fecha',
            'estado_venta': 'Estado',
            'url_itinerario': 'PDF 📄'
        }, inplace=True)
        
        st.dataframe(
            df_auditoria_show[['Venta ID', 'Monto ($)', 'Fecha', 'Estado', 'PDF 📄']], 
            column_config={
                "PDF 📄": st.column_config.LinkColumn("PDF 📄", help="Abrir Itinerario Premium en la nube")
            },
            use_container_width=True, hide_index=True
        )

        # --- 🔍 DETALLE VISUAL PARA AUDITORÍA (ESTILO IMAGEN) ---
        st.markdown("---")
        st.subheader("📋 Verificación de Itinerario Digital")
        
        # Filtramos ventas que tengan un itinerario vinculado
        col_itin = 'id_itinerario_digital'
        if col_itin not in df_auditoria.columns:
            st.info("No se encontró la columna de itinerario digital.")
        else:
            ventas_con_itin = df_auditoria[df_auditoria[col_itin].notna()]
            
            if not ventas_con_itin.empty:
                sel_v_id = st.selectbox("Seleccione Venta para auditar su Itinerario:", 
                                     ventas_con_itin['id_venta'].tolist(),
                                     format_func=lambda x: f"{ventas_con_itin[ventas_con_itin['id_venta']==x]['cliente_nombre'].values[0]} ({x})",
                                     key="sb_audit_itin")
                
                # Obtener el UUID del itinerario
                id_itin_audit = ventas_con_itin[ventas_con_itin['id_venta'] == sel_v_id][col_itin].iloc[0]
                
                if id_itin_audit:
                    res_itin = st.session_state['reporte_controller'].client.table('itinerario_digital').select('datos_render').eq('id_itinerario_digital', id_itin_audit).single().execute()
                    if res_itin.data:
                        render_itinerary_simple_download(res_itin.data['datos_render'])
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
        tab1, tab2, tab3 = st.tabs(["📋 Requerimientos de Operaciones", "📊 Estructurador Financiero", "💎 Cuentas por Cobrar (B2B)"])
        
        with tab1:
            mostrar_requerimientos()
            
        with tab2:
            estructurador_contable()
            
        with tab3:
            dashboard_cuentas_por_cobrar_b2b(supabase_client)
    else:
        st.info("Utilice el Dashboard Contable para ver reportes.")

from controllers.venta_controller import VentaController

def dashboard_cuentas_por_cobrar_b2b(supabase_client):
    """Dashboard específico para controlar deudas de Agencias (B2B)."""
    st.subheader("💎 Cuentas por Cobrar (B2B)", divider='blue')
    
    vc = VentaController(supabase_client)
    ventas = vc.obtener_todas_ventas_b2b()
    
    if not ventas:
        st.info("No hay ventas B2B registradas.")
        return

    # Obtener pagos de estas ventas para calcular saldo real
    ids_ventas = [v['id_venta'] for v in ventas]
    pagos = supabase_client.table('pago').select('id_venta, monto_pagado').in_('id_venta', ids_ventas).execute().data
    
    mapa_pagos = {}
    for p in pagos:
        pid = p['id_venta']
        mapa_pagos[pid] = mapa_pagos.get(pid, 0) + (p['monto_pagado'] or 0)

    # Procesar data
    data_agencias = {}
    lista_detalle = []
    
    for v in ventas:
        id_agencia = v.get('id_agencia_aliada')
        nombre_agencia = v.get('nombre_agencia', 'Sin Nombre')
        monto = float(v.get('precio_total_cierre') or 0)
        pagado = float(mapa_pagos.get(v['id_venta'], 0))
        saldo = monto - pagado
        
        # Agregado por Agencia
        if id_agencia not in data_agencias:
            data_agencias[id_agencia] = {'Nombre': nombre_agencia, 'Total Ventas': 0.0, 'Cobrado': 0.0, 'Por Cobrar': 0.0, 'Count': 0}
        
        data_agencias[id_agencia]['Total Ventas'] += monto
        data_agencias[id_agencia]['Cobrado'] += pagado
        data_agencias[id_agencia]['Por Cobrar'] += saldo
        data_agencias[id_agencia]['Count'] += 1
        
        lista_detalle.append({
            'Agencia': nombre_agencia,
            'Pasajero': v.get('nombre_cliente'),
            'Fecha Venta': v.get('fecha_venta'),
            'Total ($)': monto,
            'A Cuenta ($)': pagado,
            'Saldo ($)': saldo,
            'Estado': '✅ PAGADO' if saldo <= 0.1 else '🔴 DEBE'
        })
        
    # Visualización 1: Métricas Globales
    total_deuda_b2b = sum(d['Por Cobrar'] for d in data_agencias.values())
    c1, c2 = st.columns(2)
    c1.metric("Total por Cobrar a Agencias", f"${total_deuda_b2b:,.2f}")
    c2.metric("Agencias con Deuda", len([d for d in data_agencias.values() if d['Por Cobrar'] > 1]))
    
    st.divider()
    
    # Visualización 2: Tabla Resumen por Agencia
    st.write("### 🏢 Resumen por Agencia")
    df_agencias = pd.DataFrame(data_agencias.values())
    if not df_agencias.empty:
        st.dataframe(
            df_agencias,
            column_config={
                "Total Ventas": st.column_config.NumberColumn(format="$ %.2f"),
                "Cobrado": st.column_config.NumberColumn(format="$ %.2f"),
                "Por Cobrar": st.column_config.NumberColumn(format="$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )

    # Visualización 3: Detalle Expandible
    with st.expander("🔎 Ver Detalle de Todas las Ventas B2B"):
        df_det = pd.DataFrame(lista_detalle)
        st.dataframe(df_det, use_container_width=True, hide_index=True)

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
    col_pen.metric("Total Soles (PEN)", f"S/. {float(total_pen or 0):,.2f}")
    col_usd.metric("Total Dólares (USD)", f"$ {float(total_usd or 0):,.2f}")

    # Exportar
    if st.button("📥 Exportar Reporte CSV", key="btn_exp_cont"):
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"gastos_contables_{date.today()}.csv",
            mime='text/csv',
        )
