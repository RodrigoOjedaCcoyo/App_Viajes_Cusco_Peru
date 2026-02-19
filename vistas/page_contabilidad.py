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
    
    from controllers.excel_controller import ExcelController
    xl_ctrl = ExcelController()
    
    with st.container(border=True):
        st.markdown(f"#### 📄 Resumen Financiero: {render.get('titulo', 'Sin Título')}")
        st.info("Este documento es una versión simplificada (Ink Saver) para auditoría interna.")
        
        c1, c2 = st.columns(2)
        
        with c1:
            # Generar el PDF en memoria
            pdf_buffer = pdf_ctrl.generar_itinerario_simple_pdf(render)
            if pdf_buffer:
                st.download_button(
                    label="📥 Bajar Resumen (PDF Simple)",
                    data=pdf_buffer,
                    file_name=f"auditoria_{render.get('titulo', 'itinerario')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with c2:
            # Generar el Excel en memoria
            xlsx_buffer = xl_ctrl.generar_resumen_itinerario_xlsx(render)
            if xlsx_buffer:
                st.download_button(
                    label="📊 Bajar Resumen (Excel XLSX)",
                    data=xlsx_buffer,
                    file_name=f"resumen_{render.get('titulo','itin')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        if not pdf_buffer and not xlsx_buffer:
            st.error("No se pudo generar el documento en este momento.")

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

    st.subheader("🏦 Bandeja de Pagos Operativos (Caja Chica)")
    st.info("💡 Aquí aparecen las solicitudes de fondos (Entradas, Hoteles, Endosos) enviadas desde el Estructurador de Operaciones.")
    
    reqs = reporte_controller.obtener_requerimientos()
    
    if not reqs:
        st.success("✅ ¡Todo pagado! No hay requerimientos pendientes.")
    else:
        df_reqs = pd.DataFrame(reqs)
        
        # Mostrar tabla interactiva
        st.dataframe(
            df_reqs,
            column_order=("fecha", "cliente", "concepto", "monto", "moneda", "datos_pago"),
            column_config={
                "fecha": "Fecha Serv.",
                "cliente": "Cliente/Pax",
                "concepto": "Concepto / Servicio",
                "monto": st.column_config.NumberColumn("Importe", format="%.2f"),
                "moneda": "Divisa",
                "datos_pago": "🏦 Destino (Cuenta/Yape/Plin)"
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        st.write("### 🖋️ Procesar Pago")
        
        # Selector para elegir cuál de la lista pagar
        opciones_pagar = [f"Venta:{r['id_venta']} L:{r['n_linea']} | {r['cliente']} - {r['monto']} {r['moneda']}" for r in reqs]
        sel_pago = st.selectbox("Seleccione el requerimiento a liquidar:", opciones_pagar)
        
        if sel_pago:
            # Extraer IDs
            req_idx = opciones_pagar.index(sel_pago)
            req_data = reqs[req_idx]
            
            c1, c2 = st.columns(2)
            with c1:
                archivo_voucher = st.file_uploader("📎 Subir Comprobante de Pago (Imagen/PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])
            
            with c2:
                st.write("**Datos de Destino:**")
                st.code(req_data['datos_pago'])
                
                if st.button("🚀 Marcar como PAGADO", use_container_width=True, type="primary"):
                    # Lógica de actualización
                    try:
                        url_voucher = None
                        if archivo_voucher:
                            # Subir a storage (simulado o implementar en StorageController)
                            # Por ahora guardamos el nombre si no hay storage configurado
                            url_voucher = f"voucher_{req_data['id_venta']}_{req_data['n_linea']}.pdf"
                        
                        reporte_controller.client.table('venta_tour').update({
                            'estado_pago_operativo': 'PAGADO',
                            'url_voucher_operativo': url_voucher,
                            'pagado_por': st.session_state.get('user_email', 'Contabilidad')
                        }).match({'id_venta': req_data['id_venta'], 'n_linea': req_data['n_linea']}).execute()
                        
                        st.success(f"✅ Pago registrado para {req_data['cliente']}. El equipo de operaciones ya puede ver el voucher.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error procesando el pago: {e}")


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
            # Ahora usamos la versión avanzada (Pro) en Contabilidad
            estructurador_liquidacion_pro(st.session_state['reporte_controller'])
            
        with tab3:
            dashboard_cuentas_por_cobrar_b2b(supabase_client)
    else:
        st.info("Utilice el Dashboard Contable para ver reportes.")

def estructurador_liquidacion_pro(controller):
    """
    Herramienta avanzada para estructurar liquidaciones (Versión Contabilidad).
    Permite cargar ventas y asignar costos/proveedores directamente.
    """
    from datetime import date
    st.subheader("📊 Estructurador de Liquidación Profesional", divider='rainbow')

    if 'simulador_contable_adv_data' not in st.session_state:
        st.session_state['simulador_contable_adv_data'] = [
            {"FECHA": date.today(), "SERVICIO": "Servicio Ejemplo", "MONEDA": "USD", "TOTAL": 0.0},
        ]

    st.info("💡 Selecciona la venta para cargar su desglose de servicios e itinerario.")
    
    # Barra de ventas
    from controllers.venta_controller import VentaController
    vc = VentaController(controller.client)
    
    c_tipo, c_pax = st.columns([1, 2])
    with c_tipo:
        tipo_v = st.selectbox("1️⃣ Tipo:", ["--- Seleccione ---", "🏢 B2B (Agencias)", "👤 B2C (Directas)"], key="acc_sel_tipo")
    
    ventas_data = []
    if tipo_v == "🏢 B2B (Agencias)":
        agencias = vc.obtener_agencias_aliadas()
        nombres_ag = [a['nombre'] for a in agencias]
        mapa_ag = {a['nombre']: a['id_agencia'] for a in agencias}
        ag_sel = st.selectbox("2️⃣ Agencia:", ["--- Seleccione ---"] + nombres_ag, key="acc_sel_ag")
        if ag_sel != "--- Seleccione ---":
            ventas_data = vc.obtener_ventas_agencia(mapa_ag[ag_sel])
    elif tipo_v == "👤 B2C (Directas)":
        ventas_data = vc.obtener_ventas_directas()

    if ventas_data:
        opciones_p = [f"{v['nombre_cliente']} | {v.get('tour_nombre', 'Sin Tour')} ({v['id_venta']})" for v in ventas_data]
        mapa_v = {opciones_p[i]: v for i, v in enumerate(ventas_data)}
        
        with c_pax:
            p_sel = st.selectbox("2️⃣ Cargar Venta:", ["--- Seleccione ---"] + opciones_p, key="acc_sel_pax")
        
        if p_sel != "--- Seleccione ---":
            if st.button(f"📥 Cargar Datos de {p_sel.split('|')[0].strip()}", use_container_width=True):
                v_act = mapa_v.get(p_sel)
                detalles = vc.obtener_detalles_itinerario_venta(v_act['id_venta'])
                if detalles:
                    st.session_state['simulador_contable_adv_data'] = [{
                        "FECHA": date.fromisoformat(d['fecha_servicio']),
                        "SERVICIO": d.get('observaciones') or "Servicio",
                        "MONEDA": d.get('moneda_costo', 'USD'),
                        "TOTAL": float(d.get('costo_applied') or 0.0),
                        "id_venta": d['id_venta'],
                        "n_linea": d['n_linea']
                    } for d in detalles]
                    st.success("Datos cargados correctamente.")
                    st.rerun()

    # Editor estilo Excel
    df = pd.DataFrame(st.session_state['simulador_contable_adv_data'])
    if not df.empty and 'FECHA' in df.columns:
        df.sort_values(by='FECHA', inplace=True)

    lista_prov = ["--- Sin Asignar ---"]
    res_prov_data = []
    try:
        res_prov = controller.client.table('proveedor').select('id_provider' if 'id_provider' in str(controller.client.table('proveedor').select('*').limit(1).execute().data) else 'id_proveedor', 'nombre', 'tipo_servicio').execute()
        res_prov_data = res_prov.data or []
        lista_prov += [f"{p['nombre']} ({p['tipo_servicio']})" for p in res_prov_data]
    except: pass

    # VISTA DE SOLO LECTURA
    st.dataframe(
        df, 
        column_config={
            "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "SERVICIO": st.column_config.TextColumn("Servicio", width="large"),
            "MONEDA": "💵",
            "TOTAL": st.column_config.NumberColumn("Costo", format="%.2f")
        },
        use_container_width=True, 
        hide_index=True
    )

    # Totales
    t_costos = df['TOTAL'].sum() if not df.empty else 0.0
    st.divider()
    st.metric("COSTO TOTAL REGISTRADO", f"$ {t_costos:,.2f}")
    
    st.info("💡 Esta vista es de solo consulta (Auditoría). Para modificar costos o asignar proveedores, utiliza el Google Sheet Maestro.")

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
        df_det = pd.DataFrame(lista_detalle, index=None)
        st.dataframe(df_det, use_container_width=True, hide_index=True)
